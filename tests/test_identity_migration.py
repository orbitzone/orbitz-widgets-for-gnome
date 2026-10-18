"""ID-01 tests: temporary installs/settings only, no live GNOME or user data."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from gi.repository import GLib

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('identity_migration', ROOT/'tools/migrate-identity.py')
identity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(identity)


def entry(kind, data, user=True):
    value = GLib.Variant(kind, data).print_(True)
    return dict(type=kind, value=value, user=value if user else None)


class FakeSettings:
    def __init__(self):
        self.data = {
            identity.LEGACY_SCHEMA: {'widget-data':entry('aaa{ss}', [[{'Text_Command':"python3 '/custom path/job.py' --arg", 'Text_Size':'8'}]]), 'changed-data':entry('a{ss}', {'WidgetIndex':'0'})},
            identity.NEW_SCHEMA: {'widget-data':entry('aaa{ss}', [], False), 'changed-data':entry('a{ss}', {}, False)},
        }
        self.defaults = copy.deepcopy(self.data[identity.NEW_SCHEMA])
        self.active = {'enabled-extensions':GLib.Variant('as',[identity.LEGACY_UUID]).print_(True), 'disabled-extensions':'@as []', 'disable-user-extensions':'false'}
        self.writes = []
        self.fail_once = None

    def snapshot(self, schema):return copy.deepcopy(self.data[schema])
    def activation(self):return dict(self.active)
    def write(self, schema, key, value):
        self.writes.append((schema,key,value))
        if value is None:self.data[schema][key] = copy.deepcopy(self.defaults[key])
        else:self.data[schema][key] = dict(self.data[schema][key],value=value,user=value)
        if self.fail_once == key:
            self.fail_once = None
            raise OSError('synthetic write failed after mutation')


class IdentityMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.extensions = self.root/'extensions';self.extensions.mkdir()
        self.old = self.extensions/identity.LEGACY_UUID;self.old.mkdir()
        self.new = self.extensions/identity.NEW_UUID
        self.source = self.root/'source';self.source.mkdir()
        self.backups = self.root/'private-backups'
        for folder, uuid, schema in [(self.old,identity.LEGACY_UUID,identity.LEGACY_SCHEMA),(self.source,identity.NEW_UUID,identity.NEW_SCHEMA)]:
            (folder/'metadata.json').write_text(json.dumps({'uuid':uuid,'settings-schema':schema}))
            (folder/'schemas').mkdir()
        for xml in (ROOT/'extension/schemas').glob('*.xml'):
            shutil.copy2(xml,self.source/'schemas'/xml.name)
            if 'orbitz-widgets' not in xml.name:shutil.copy2(xml,self.old/'schemas'/xml.name)
        (self.old/'speedtest').write_bytes(b'installed-binary-kept');(self.old/'speedtest').chmod(0o755)
        (self.old/'vendor').mkdir();(self.old/'vendor/existing').write_text('existing vendor')
        (self.old/'media').mkdir();(self.old/'media/custom.svg').write_text('installed custom asset')
        (self.source/'extension.js').write_text('new source')
        (self.source/'helper.py').write_text('new module')
        (self.source/'speedtest').write_bytes(b'never overlay installed binary')
        self.settings = FakeSettings()

    def prepare(self,apply=True):
        return identity.prepare(self.old,self.new,self.source,self.backups,self.settings,apply)

    def test_plan_makes_no_install_config_or_backup_changes(self):
        original = identity.tree_hashes(self.old)
        self.assertEqual(self.prepare(False)['state'],'plan')
        self.assertFalse(self.new.exists());self.assertFalse(self.backups.exists())
        self.assertEqual(self.settings.writes,[])
        self.assertEqual(identity.tree_hashes(self.old),original)

    def test_prepare_copies_whole_install_overlays_and_rolls_back_privately(self):
        original = identity.tree_hashes(self.old)
        old_settings = self.settings.snapshot(identity.LEGACY_SCHEMA)
        target_before = self.settings.snapshot(identity.NEW_SCHEMA)
        activation = self.settings.activation()
        result = self.prepare()
        self.assertEqual(result['state'],'prepared')
        self.assertEqual(self.new.joinpath('speedtest').read_bytes(),b'installed-binary-kept')
        self.assertEqual(stat.S_IMODE((self.new/'speedtest').stat().st_mode),0o755)
        self.assertEqual((self.new/'vendor/existing').read_text(),'existing vendor')
        self.assertEqual((self.new/'media/custom.svg').read_text(),'installed custom asset')
        self.assertEqual((self.new/'helper.py').read_text(),'new module')
        self.assertEqual(json.loads((self.new/'metadata.json').read_text())['uuid'],self.new.name)
        self.assertTrue((self.new/'schemas/gschemas.compiled').is_file())
        self.assertEqual(self.settings.snapshot(identity.LEGACY_SCHEMA),old_settings)
        self.assertEqual(self.settings.activation(),activation)
        for key,value in old_settings.items():
            self.assertEqual(self.settings.snapshot(identity.NEW_SCHEMA)[key]['value'],value['value'])
            self.assertEqual(self.settings.snapshot(identity.NEW_SCHEMA)[key]['type'],value['type'])
        folder = Path(result['backup'])
        self.assertEqual(stat.S_IMODE(folder.stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((folder/'manifest.json').stat().st_mode),0o600)
        identity.rollback(folder,self.old,self.new,self.settings)
        self.assertFalse(self.new.exists())
        self.assertEqual(identity.tree_hashes(self.old),original)
        self.assertEqual(self.settings.snapshot(identity.NEW_SCHEMA),target_before)
        self.assertEqual(self.settings.activation(),activation)

    def test_divergent_settings_types_and_existing_destination_are_refused(self):
        original = self.settings.snapshot(identity.NEW_SCHEMA)
        self.settings.data[identity.NEW_SCHEMA]['changed-data'] = entry('a{ss}',{'custom':'preserve'})
        with self.assertRaisesRegex(RuntimeError,'divergente'):self.prepare()
        self.assertFalse(self.backups.exists())
        self.settings.data[identity.NEW_SCHEMA] = original
        self.settings.data[identity.NEW_SCHEMA]['changed-data'] = entry('as',[],False)
        with self.assertRaisesRegex(RuntimeError,'Tipo'):self.prepare()
        self.settings.data[identity.NEW_SCHEMA] = original
        self.new.mkdir()
        with self.assertRaisesRegex(RuntimeError,'já existe'):self.prepare()
        self.assertEqual(self.settings.writes,[])

    def test_dual_identity_and_symlinks_are_refused(self):
        self.settings.active['enabled-extensions'] = GLib.Variant('as',[identity.LEGACY_UUID,identity.NEW_UUID]).print_(True)
        with self.assertRaisesRegex(RuntimeError,'enabled-extensions'):self.prepare()
        self.settings.active['enabled-extensions'] = '@as []'
        (self.old/'outside-link').symlink_to(self.source)
        with self.assertRaisesRegex(RuntimeError,'simbólico'):self.prepare()
        self.assertFalse(self.new.exists())

    def test_failed_config_write_recovers_install_and_previous_user_values(self):
        before = self.settings.snapshot(identity.NEW_SCHEMA)
        self.settings.fail_once = 'widget-data'
        with self.assertRaisesRegex(OSError,'synthetic'):self.prepare()
        self.assertFalse(self.new.exists())
        self.assertEqual(self.settings.snapshot(identity.NEW_SCHEMA),before)
        manifest = json.loads(next(self.backups.glob('*/manifest.json')).read_text())
        self.assertEqual(manifest['state'],'recovered')
        self.assertEqual(manifest['recovery_pending'],[])

    def test_compilation_failure_never_publishes_or_changes_configuration(self):
        with patch.object(identity,'compile_schemas',side_effect=subprocess.CalledProcessError(1,'glib-compile-schemas')):
            with self.assertRaises(subprocess.CalledProcessError):self.prepare()
        self.assertFalse(self.new.exists())
        self.assertEqual(self.settings.writes,[])
        self.assertTrue(self.old.exists())

    def test_rollback_refuses_active_new_changed_files_and_config(self):
        result = self.prepare();folder = Path(result['backup'])
        self.settings.active['enabled-extensions'] = GLib.Variant('as',[identity.NEW_UUID]).print_(True)
        with self.assertRaisesRegex(RuntimeError,'enabled-extensions'):identity.rollback(folder,self.old,self.new,self.settings)
        self.settings.active['enabled-extensions'] = '@as []'
        (self.new/'helper.py').write_text('user modified')
        with self.assertRaisesRegex(RuntimeError,'Instalação nova mudou'):identity.rollback(folder,self.old,self.new,self.settings)
        (self.new/'helper.py').write_text('new module')
        self.settings.data[identity.NEW_SCHEMA]['changed-data'] = entry('a{ss}',{'later':'keep'})
        before = self.settings.snapshot(identity.NEW_SCHEMA)
        with self.assertRaisesRegex(RuntimeError,'Configuração nova mudou'):identity.rollback(folder,self.old,self.new,self.settings)
        self.assertEqual(self.settings.snapshot(identity.NEW_SCHEMA),before)
        self.assertTrue(self.new.exists())

    def test_partial_rollback_records_pending_and_can_retry(self):
        before = self.settings.snapshot(identity.NEW_SCHEMA)
        result = self.prepare();folder = Path(result['backup'])
        self.settings.fail_once = 'changed-data'
        with self.assertRaisesRegex(RuntimeError,'pendente'):identity.rollback(folder,self.old,self.new,self.settings)
        self.assertTrue(self.new.exists())
        self.assertEqual(json.loads((folder/'manifest.json').read_text())['state'],'rollback-pending')
        identity.rollback(folder,self.old,self.new,self.settings)
        self.assertFalse(self.new.exists())
        self.assertEqual(self.settings.snapshot(identity.NEW_SCHEMA),before)

    def test_partial_directory_removal_retries_only_intact_registered_subset(self):
        original = identity.tree_hashes(self.old)
        before = self.settings.snapshot(identity.NEW_SCHEMA)
        result = self.prepare();folder = Path(result['backup'])
        real_remove = identity.shutil.rmtree
        def fail_partially(path, *args, **kwargs):
            if path == self.new:
                (self.new/'helper.py').unlink()
                raise OSError('synthetic partial removal')
            return real_remove(path, *args, **kwargs)
        with patch.object(identity.shutil,'rmtree',side_effect=fail_partially):
            with self.assertRaisesRegex(OSError,'partial removal'):
                identity.rollback(folder,self.old,self.new,self.settings)
        manifest = json.loads((folder/'manifest.json').read_text())
        self.assertEqual(manifest['state'],'rollback-pending')
        self.assertTrue(manifest['removal_started'])
        (self.new/'unregistered').write_text('preserve new file')
        with self.assertRaisesRegex(RuntimeError,'Instalação nova mudou'):
            identity.rollback(folder,self.old,self.new,self.settings)
        self.assertEqual((self.new/'unregistered').read_text(),'preserve new file')
        (self.new/'unregistered').unlink()
        (self.new/'extension.js').write_text('preserve changed file')
        with self.assertRaisesRegex(RuntimeError,'Instalação nova mudou'):
            identity.rollback(folder,self.old,self.new,self.settings)
        self.assertEqual((self.new/'extension.js').read_text(),'preserve changed file')
        (self.new/'extension.js').write_text('new source')
        identity.rollback(folder,self.old,self.new,self.settings)
        self.assertFalse(self.new.exists())
        self.assertEqual(identity.tree_hashes(self.old),original)
        self.assertEqual(self.settings.snapshot(identity.NEW_SCHEMA),before)

    def test_interrupted_preparation_manifest_can_restore_partial_config(self):
        before = self.settings.snapshot(identity.NEW_SCHEMA)
        result = self.prepare();folder = Path(result['backup'])
        manifest_path = folder/'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['state'] = 'staged'  # Simulate interruption after first setting.
        identity.private_json(manifest_path,manifest)
        self.settings.data[identity.NEW_SCHEMA]['changed-data'] = copy.deepcopy(before['changed-data'])
        identity.rollback(folder,self.old,self.new,self.settings)
        self.assertFalse(self.new.exists())
        self.assertEqual(self.settings.snapshot(identity.NEW_SCHEMA),before)

    def test_real_gio_uses_memory_backend_and_compiled_schema_types(self):
        # A separate process forces the memory backend before Gio is imported.
        script = '''import importlib.util,sys,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('m',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
b=m.DesktopSettings(Path(sys.argv[2]),Path(sys.argv[3]))
s=b.snapshot(m.LEGACY_SCHEMA);t=b.snapshot(m.NEW_SCHEMA);m.check_contract(s,t)
b.write(m.NEW_SCHEMA,'changed-data',"{'WidgetIndex': '17'}")
assert b.snapshot(m.NEW_SCHEMA)['changed-data']['type']=='a{ss}'
assert b.snapshot(m.LEGACY_SCHEMA)['changed-data']==s['changed-data']
print('MEMORY_BACKEND_OK')
'''
        result = subprocess.run([sys.executable,'-c',script,str(ROOT/'tools/migrate-identity.py'),str(self.old),str(self.source)], env={**os.environ,'GSETTINGS_BACKEND':'memory'},capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'MEMORY_BACKEND_OK')


if __name__ == '__main__':unittest.main()

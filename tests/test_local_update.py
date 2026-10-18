"""Reversible installer contracts; all targets/settings are synthetic."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from gi.repository import GLib

SPEC = importlib.util.spec_from_file_location('local_update', Path(__file__).resolve().parents[1] / 'tools/update-local.py')
update = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(update)


class LocalUpdateTests(unittest.TestCase):
    def test_path_migration_is_exact_and_preserves_unrelated_fields(self):
        old = str(update.OLD_DIRS[0] / 'cpu-ram-widget.py')
        data = [[{'Location_X': '31'}, {'Text_Command': f'python3 {old} --details', 'Name': 'CPU'},
                 {'Text_Command': f'python3 {old}.backup'}, {'Text_Command': 'echo custom'}, {'Text_Command': 'echo prefix'+old}]]
        value, count = update.migrate(GLib.Variant('aaa{ss}', data).print_(True))
        actual = GLib.Variant.parse(None, value, None, None).unpack()
        self.assertEqual(count, 1)
        self.assertEqual(actual[0][1]['Text_Command'], f'python3 {update.COLLECTORS}/cpu-ram-widget.py --details')
        self.assertEqual(actual[0][0], data[0][0])
        self.assertEqual(actual[0][1]['Name'], 'CPU')
        self.assertEqual(actual[0][2:], data[0][2:])
        self.assertEqual(update.migrate(value), (value, 0))

    def test_identity_selection_prefers_new_and_refuses_mismatches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            extensions = root/'extensions';extensions.mkdir()
            repo = root/'repo';(repo/'extension').mkdir(parents=True)
            (repo/'extension/metadata.json').write_text(json.dumps({'uuid':update.NEW_UUID,'settings-schema':'org.gnome.shell.extensions.orbitz-widgets'}))
            old = extensions/update.LEGACY_UUID;old.mkdir()
            (old/'metadata.json').write_text(json.dumps({'uuid':update.LEGACY_UUID,'settings-schema':'org.gnome.shell.extensions.azclock'}))
            with patch.object(update,'EXTENSIONS',extensions), patch.object(update,'REPO',repo), patch.object(update,'EXT',old), patch.object(update,'SCHEMA',update.SCHEMA):
                with self.assertRaisesRegex(RuntimeError,'outra identidade'):update.select_identity()
                new = extensions/update.NEW_UUID;new.mkdir()
                (new/'metadata.json').write_text(json.dumps({'uuid':update.NEW_UUID,'settings-schema':'org.gnome.shell.extensions.orbitz-widgets'}))
                self.assertEqual(update.select_identity(),new)
                self.assertEqual(update.SCHEMA,'org.gnome.shell.extensions.orbitz-widgets')
                (new/'metadata.json').write_text(json.dumps({'uuid':update.LEGACY_UUID}))
                with self.assertRaisesRegex(RuntimeError,'difere do diretório'):update.select_identity()

    def test_legacy_backup_without_identity_never_targets_new_schema(self):
        with patch.object(update,'EXT',update.EXTENSIONS/update.NEW_UUID), patch.object(update,'SCHEMA','org.gnome.shell.extensions.orbitz-widgets'):
            update.identity_from_manifest({'old_settings':'synthetic'})
            self.assertEqual(update.EXT,update.EXTENSIONS/update.LEGACY_UUID)
            self.assertEqual(update.SCHEMA,'org.gnome.shell.extensions.azclock')
            with self.assertRaisesRegex(RuntimeError,'Identidade/schema'):
                update.identity_from_manifest({'extension':str(update.EXTENSIONS/update.NEW_UUID),'schema':'org.gnome.shell.extensions.azclock'})

    def test_brand_metadata_and_logo_apply_hashes_and_rollback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root/'repo';extension = repo/'extension';(extension/'media').mkdir(parents=True)
            (repo/'widgets').mkdir();(repo/'sticky-notes').mkdir()
            extensions = root/'extensions';new = extensions/update.NEW_UUID;new.mkdir(parents=True)
            old_metadata = {'uuid':update.NEW_UUID,'settings-schema':'org.gnome.shell.extensions.orbitz-widgets','version':1}
            new_metadata = {**old_metadata,'version-name':'1.0'}
            (new/'metadata.json').write_text(json.dumps(old_metadata))
            original_metadata = (new/'metadata.json').read_bytes()
            (extension/'metadata.json').write_text(json.dumps(new_metadata))
            (extension/'media/orbitz-logo.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            for relative in ['youtube.json','notes.json','nested/metadata.json','speedtest','binary.bin','media/other.svg','vendor/extra.py']:
                path = extension/relative;path.parent.mkdir(exist_ok=True,parents=True);path.write_text('not an update target')
            state = [GLib.Variant('aaa{ss}',[]).print_(True)]
            def settings(action,*args):
                if action == 'get':return state[0]
                if action == 'set':state[0]=args[1];return ''
                raise AssertionError(action)
            with patch.object(update,'REPO',repo), patch.object(update,'EXTENSIONS',extensions), patch.object(update,'EXT',new), patch.object(update,'SCHEMA',old_metadata['settings-schema']), patch.object(update,'NOTES',root/'notes'), patch.object(update,'COLLECTORS',root/'collectors'), patch.object(update,'BACKUPS',root/'backups'), patch.object(update,'settings',side_effect=settings), patch.object(update,'preflight'), patch('sys.argv',['update-local.py','--apply']):
                self.assertEqual({str(a.relative_to(extension)) for a,_ in update.files()}, {'metadata.json','media/orbitz-logo.svg'})
                update.main()
                self.assertEqual((new/'metadata.json').read_bytes(),(extension/'metadata.json').read_bytes())
                self.assertEqual(update.digest(new/'media/orbitz-logo.svg'),update.digest(extension/'media/orbitz-logo.svg'))
                self.assertEqual(update.files(),[])
                backup = next((root/'backups').iterdir())
                manifest = json.loads((backup/'manifest.json').read_text())
                self.assertEqual(manifest['extension'],str(new))
                for item in manifest['files']:
                    self.assertEqual(update.digest(Path(item['target'])),item['new_hash'])
                update.restore(backup)
                self.assertEqual((new/'metadata.json').read_bytes(),original_metadata)
                self.assertFalse((new/'media/orbitz-logo.svg').exists())
                self.assertEqual(state[0],manifest['old_settings'])

    def test_brand_copy_refuses_uuid_schema_mismatch_and_missing_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            new = root/update.NEW_UUID;new.mkdir()
            target = new/'metadata.json';target.write_text('original')
            source = root/'source-metadata.json'
            for metadata in [{'uuid':update.LEGACY_UUID,'settings-schema':'org.gnome.shell.extensions.orbitz-widgets'}, {'uuid':update.NEW_UUID,'settings-schema':'org.gnome.shell.extensions.azclock'}, {'uuid':update.NEW_UUID}]:
                with self.subTest(metadata=metadata), patch.object(update,'EXT',new), patch.object(update,'SCHEMA','org.gnome.shell.extensions.orbitz-widgets'):
                    source.write_text(json.dumps(metadata))
                    with self.assertRaisesRegex(RuntimeError,'incompatível'):update.atomic_copy(source,target)
                    self.assertEqual(target.read_text(),'original')

    def exercise_apply(self, fail=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'; source.write_text('new\n')
            target = root / 'target'; target.write_text('old\n')
            extra_source = root / 'new-source'; extra_source.write_text('module\n')
            extra_target = root / 'new-target'
            state = ['old-settings']
            def settings(action, *args):
                if action == 'get': return state[0]
                if action == 'set': state[0] = args[1]; return ''
                raise AssertionError(action)
            real_copy = update.atomic_copy
            def copy(source_path, destination):
                if fail and source_path == extra_source:
                    raise OSError('simulated failure')
                real_copy(source_path, destination)
            with patch.object(update, 'BACKUPS', root / 'backups'), patch.object(update, 'preflight'), \
                 patch.object(update, 'files', return_value=[(source, target), (extra_source, extra_target)]), \
                 patch.object(update, 'settings', side_effect=settings), \
                 patch.object(update, 'migrate', return_value=('new-settings', 1)), \
                 patch.object(update, 'atomic_copy', side_effect=copy), \
                 patch('sys.argv', ['update-local.py', '--apply']):
                if fail:
                    with self.assertRaises(OSError): update.main()
                    self.assertEqual(target.read_text(), 'old\n')
                    self.assertFalse(extra_target.exists())
                    self.assertEqual(state[0], 'old-settings')
                else:
                    update.main()
                    self.assertEqual(target.read_text(), 'new\n')
                    self.assertEqual(extra_target.read_text(), 'module\n')
                    self.assertEqual(state[0], 'new-settings')
                    folder = next((root / 'backups').iterdir())
                    backup_file = folder / 'files/0'
                    original_backup = backup_file.read_bytes()
                    backup_file.write_bytes(b'corrupted backup')
                    with self.assertRaisesRegex(RuntimeError, 'Backup inválido'):
                        update.restore(folder)
                    self.assertEqual(target.read_text(), 'new\n')
                    self.assertEqual(state[0], 'new-settings')
                    backup_file.write_bytes(original_backup)
                    update.restore(folder)
                    self.assertEqual(target.read_text(), 'old\n')
                    self.assertFalse(extra_target.exists())
                    self.assertEqual(state[0], 'old-settings')

    def test_apply_and_explicit_rollback(self):
        self.exercise_apply()

    def test_partial_failure_restores_only_attempted_files(self):
        self.exercise_apply(fail=True)

    def test_preflight_failure_does_not_touch_installation(self):
        with patch.object(update, 'files', return_value=[]), patch.object(update, 'settings', return_value='original'), \
             patch.object(update, 'migrate', return_value=('updated', 1)), \
             patch.object(update, 'preflight', side_effect=PermissionError('sandbox')), \
             patch.object(update, 'atomic_copy') as copy, patch('sys.argv', ['update-local.py', '--apply']):
            with self.assertRaises(PermissionError): update.main()
            copy.assert_not_called()

    def test_recovery_continues_after_one_restore_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pairs = []
            for index in range(3):
                source = root / f'source{index}'; source.write_text('new')
                target = root / f'target{index}'; target.write_text('old')
                pairs.append((source, target))
            state = ['old-settings']
            def settings(action, *args):
                if action == 'get': return state[0]
                state[0] = args[1]; return ''
            real_copy = update.atomic_copy
            def copy(source, target):
                if source == pairs[2][0]: raise OSError('original apply failure')
                if source.name == '1' and source.parent.name == 'files':
                    raise OSError('one recovery failure')
                real_copy(source, target)
            with patch.object(update, 'BACKUPS', root / 'backups'), patch.object(update, 'preflight'), \
                 patch.object(update, 'files', return_value=pairs), patch.object(update, 'settings', side_effect=settings), \
                 patch.object(update, 'migrate', return_value=('new-settings', 1)), \
                 patch.object(update, 'atomic_copy', side_effect=copy), \
                 patch('sys.argv', ['update-local.py', '--apply']):
                with self.assertRaisesRegex(OSError, 'original apply failure'):
                    update.main()
            self.assertEqual([target.read_text() for _, target in pairs], ['old', 'new', 'old'])

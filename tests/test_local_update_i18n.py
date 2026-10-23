"""Catalog/schema apply and rollback, entirely under temporary directories."""
import contextlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from gi.repository import GLib, Gio

SPEC = importlib.util.spec_from_file_location('update_i18n', Path(__file__).resolve().parents[1] / 'tools/update-local.py')
update = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(update)
LANGUAGE = "<key name='ui-language' type='s'><default>'pt-BR'</default><choices><choice value='pt-BR'/><choice value='en-US'/></choices></key>"


def xml(schema, language=False, sentinel='installed-default'):
    return (f'<schemalist><schema id="{schema}" path="/test/{schema.split(".")[-1]}/">'
            "<key name='widget-data' type='aaa{ss}'><default>[]</default></key>"
            f"<key name='sentinel' type='s'><default>'{sentinel}'</default></key>" +
            (LANGUAGE if language else '') + '</schema></schemalist>')


class UpdateLanguageTests(unittest.TestCase):
    @contextlib.contextmanager
    def installation(self, legacy=False):
        with tempfile.TemporaryDirectory() as temporary, contextlib.ExitStack() as stack:
            root = Path(temporary)
            repo = root / 'repo'
            (repo / 'extension/schemas').mkdir(parents=True)
            (repo / 'sticky-notes').mkdir(); (repo / 'widgets').mkdir(); (repo / 'i18n').mkdir()
            for name in ('pt-BR', 'en-US'):
                (repo / 'i18n' / (name + '.json')).write_text(json.dumps({'ui.example': name}))
            (repo / 'i18n/ui_i18n.py').write_text('# shared GUI runtime\n')
            identity = update.LEGACY_UUID if legacy else update.NEW_UUID
            schema = 'org.gnome.shell.extensions.azclock' if legacy else 'org.gnome.shell.extensions.orbitz-widgets'
            inactive = 'org.gnome.shell.extensions.orbitz-widgets' if legacy else 'org.gnome.shell.extensions.azclock'
            extensions = root / 'extensions'; target = extensions / identity
            (target / 'schemas').mkdir(parents=True)
            metadata = json.dumps({'uuid': identity, 'settings-schema': schema})
            (target / 'metadata.json').write_text(metadata); (repo / 'extension/metadata.json').write_text(metadata)
            active_path = target / 'schemas' / (schema + '.gschema.xml')
            inactive_path = target / 'schemas' / (inactive + '.gschema.xml')
            active_path.write_text(xml(schema)); inactive_path.write_text(xml(inactive))
            (repo / 'extension/schemas' / active_path.name).write_text(xml(schema, True, 'source-default'))
            subprocess.run(['glib-compile-schemas', '--strict', str(target / 'schemas')], check=True)
            original = {p: p.read_bytes() for p in (active_path, inactive_path, target / 'schemas/gschemas.compiled')}
            shared = root / 'shared/i18n'; shared.mkdir(parents=True)
            (shared / 'pt-BR.json').write_text('{"old":"translation"}')
            original[shared / 'pt-BR.json'] = (shared / 'pt-BR.json').read_bytes()
            state = [GLib.Variant('aaa{ss}', [[{'Name':'User name', 'Text_Command':'echo custom'}]]).print_(True)]
            def settings(action, *args):
                self.assertEqual(args[0], 'widget-data')
                if action == 'get': return state[0]
                if action == 'set': state[0] = args[1]; return ''
                if action == 'writable': return 'true'
                raise AssertionError(action)
            for key, value in dict(REPO=repo, EXTENSIONS=extensions, EXT=target, SCHEMA=schema,
                                   NOTES=root/'notes', COLLECTORS=root/'collectors', I18N=shared, BACKUPS=root/'backups').items():
                stack.enter_context(patch.object(update, key, value))
            stack.enter_context(patch.object(update, 'settings', side_effect=settings))
            yield root, target, shared, original, state

    def test_shared_catalog_active_schema_apply_idempotency_and_rollback(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy), self.installation(legacy) as (root, target, shared, original, state):
                before = state[0]
                with patch('sys.argv', ['update-local.py', '--apply']): update.main()
                update.validate_language_schema(target / 'schemas')
                schema_source = Gio.SettingsSchemaSource.new_from_directory(str(target / 'schemas'), None, False)
                active = schema_source.lookup(update.SCHEMA, False)
                self.assertEqual(active.get_key('sentinel').get_default_value().unpack(), 'installed-default')
                self.assertEqual(state[0], before)
                self.assertEqual(json.loads((shared / 'en-US.json').read_text()), {'ui.example':'en-US'})
                self.assertEqual(update.files(), [])
                backup = next((root/'backups').iterdir())
                manifest = json.loads((backup/'manifest.json').read_text())
                self.assertEqual(len(manifest['files']), 5)
                for item in manifest['files']:
                    self.assertEqual(update.digest(Path(item['target'])), item['new_hash'])
                update.restore(backup)
                for path, raw in original.items(): self.assertEqual(path.read_bytes(), raw)
                self.assertFalse((shared / 'en-US.json').exists())
                self.assertFalse((shared / 'ui_i18n.py').exists())
                self.assertEqual(state[0], before)

    def test_mid_apply_failure_restores_catalog_and_schema_bytes(self):
        with self.installation() as (root, target, shared, original, state):
            before = state[0]
            real_copy = update.atomic_copy
            def copy(source, destination):
                if destination == target / 'schemas/gschemas.compiled' and source.parent.name.startswith('orbitz-schema-'):
                    raise OSError('synthetic compile installation failure')
                real_copy(source, destination)
            with patch.object(update, 'atomic_copy', side_effect=copy), patch('sys.argv', ['update-local.py','--apply']):
                with self.assertRaisesRegex(OSError, 'synthetic'): update.main()
            for path, raw in original.items(): self.assertEqual(path.read_bytes(), raw)
            self.assertFalse((shared/'en-US.json').exists())
            self.assertEqual(state[0], before)

    def test_bad_catalog_or_schema_refuses_before_installed_changes(self):
        with self.installation() as (_, target, _, original, _):
            source = update.REPO / 'i18n/en-US.json'
            source.write_text('{"different":"IDs"}')
            with self.assertRaisesRegex(RuntimeError, 'IDs diferentes'): update.files()
            source.write_text('{"ui.example":"English"}')
            schema = update.REPO / 'extension/schemas' / (update.SCHEMA + '.gschema.xml')
            schema.write_text(xml(update.SCHEMA, True).replace("'pt-BR'</default>", "'invalid'</default>"))
            with self.assertRaisesRegex(RuntimeError, 'Compilação temporária'): update.files()
            for path, raw in original.items(): self.assertEqual(path.read_bytes(), raw)

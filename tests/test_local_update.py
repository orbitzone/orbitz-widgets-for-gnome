"""Reversible installer contracts; all targets/settings are synthetic."""
import importlib.util
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

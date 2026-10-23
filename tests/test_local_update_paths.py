"""No-follow path traversal and descriptor-relative mutation regressions."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('update_paths', Path(__file__).resolve().parents[1] / 'tools/update-local.py')
update = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(update)


class UpdatePathTests(unittest.TestCase):
    def test_preflight_rejects_symlink_grandparent_before_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            ext = root / update.LEGACY_UUID; ext.mkdir()
            (ext/'metadata.json').write_text(json.dumps({'uuid':update.LEGACY_UUID}))
            outside = root/'outside'; (outside/'nested/notes').mkdir(parents=True)
            link = root/'linked'; link.symlink_to(outside, target_is_directory=True)
            with patch.object(update,'EXT',ext), patch.object(update,'NOTES',link/'nested/notes'), patch.object(update,'COLLECTORS',root/'collectors'), patch.object(update,'I18N',root/'i18n'), patch.object(update,'settings') as settings:
                with self.assertRaises((OSError,RuntimeError)): update.preflight()
                settings.assert_not_called()
            self.assertEqual(list(outside.rglob('.orbitz-preflight-*')), [])

    def test_copy_and_unlink_reject_symlink_at_every_ancestor_depth(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'source'; source.write_text('new')
            for depth in (0,1,2):
                base=root/str(depth); outside=base/'outside'; outside.mkdir(parents=True)
                (outside/'target').write_text('outside')
                parent=base
                for index in range(depth): parent=parent/f'nested{index}'; parent.mkdir()
                link=parent/'linked'; link.symlink_to(outside, target_is_directory=True)
                with self.subTest(depth=depth):
                    with self.assertRaises((OSError,RuntimeError)): update.atomic_copy(source,link/'target')
                    with self.assertRaises((OSError,RuntimeError)): update.secure_unlink(link/'target')
                    self.assertEqual((outside/'target').read_text(),'outside')
                    self.assertEqual(list(outside.glob('.orbitz-update-*')),[])

    def test_copy_rejects_symlink_in_source_and_broken_destination_chain(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); real=root/'real'; real.mkdir(); (real/'file').write_text('source')
            link=root/'link'; link.symlink_to(real,target_is_directory=True)
            with self.assertRaises((OSError,RuntimeError)): update.atomic_copy(link/'file',root/'target')
            self.assertFalse((root/'target').exists())
            broken=root/'broken'; broken.symlink_to(root/'missing',target_is_directory=True)
            with self.assertRaises((OSError,RuntimeError)): update.atomic_copy(real/'file',broken/'nested/target')
            self.assertFalse((root/'missing').exists())

    def test_parent_swap_between_open_and_replace_cannot_redirect_write(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); source=root/'source'; source.write_text('new')
            parent=root/'parent'; parent.mkdir(); (parent/'target').write_text('old')
            outside=root/'outside'; outside.mkdir(); (outside/'target').write_text('outside')
            moved=root/'original-parent'
            replace=os.replace
            def swap_then_replace(src,dst,**kwargs):
                parent.rename(moved); parent.symlink_to(outside,target_is_directory=True)
                self.assertIn('src_dir_fd',kwargs);self.assertIn('dst_dir_fd',kwargs)
                return replace(src,dst,**kwargs)
            with patch.object(update.os,'replace',side_effect=swap_then_replace):
                update.atomic_copy(source,parent/'target')
            self.assertEqual((outside/'target').read_text(),'outside')
            self.assertEqual((moved/'target').read_text(),'new')
            self.assertEqual(list(outside.glob('.orbitz-update-*')),[])
            self.assertEqual(list(moved.glob('.orbitz-update-*')),[])

    def test_rollback_refuses_symlink_ancestor_even_with_force(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); outside=root/'outside';outside.mkdir();(outside/'target.py').write_text('new')
            link=root/'collectors';link.symlink_to(outside,target_is_directory=True)
            backup=root/'backup';(backup/'files').mkdir(parents=True);(backup/'files/0').write_text('old')
            schema='org.gnome.shell.extensions.azclock'; extensions=root/'extensions'
            manifest={'extension':str(extensions/update.LEGACY_UUID),'schema':schema,'old_settings':'old','new_settings':'new',
                      'files':[{'target':str(link/'target.py'),'source':str(root/'repo/widgets/target.py'),'backup':'files/0','old_hash':hashlib.sha256(b'old').hexdigest(),'new_hash':hashlib.sha256(b'new').hexdigest()}]}
            (backup/'manifest.json').write_text(json.dumps(manifest))
            with patch.object(update,'EXTENSIONS',extensions),patch.object(update,'EXT',extensions/update.LEGACY_UUID),patch.object(update,'SCHEMA',schema),patch.object(update,'REPO',root/'repo'),patch.object(update,'COLLECTORS',link),patch.object(update,'settings') as settings:
                for force in (False,True):
                    with self.subTest(force=force),self.assertRaises((OSError,RuntimeError)):update.restore(backup,force)
                settings.assert_not_called()
            self.assertEqual((outside/'target.py').read_text(),'new')

    def test_rollback_backup_ancestor_symlink_rejected_before_reading_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); real=root/'real';real.mkdir();(real/'manifest.json').write_text('{}')
            link=root/'link';link.symlink_to(real,target_is_directory=True)
            with patch.object(update,'settings') as settings:
                with self.assertRaises((OSError,RuntimeError)):update.restore(link)
                settings.assert_not_called()

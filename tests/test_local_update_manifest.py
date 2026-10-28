"""AUD-01: reject rollback manifests before settings or installed mutations."""
import contextlib
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('update_manifest',Path(__file__).resolve().parents[1]/'tools/update-local.py')
update=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(update)


class RollbackManifestTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.repo=self.root/'repo'
        self.extensions=self.root/'extensions';self.ext=self.extensions/update.LEGACY_UUID
        self.collectors=self.root/'collectors';self.notes=self.root/'notes/app'
        self.shared=self.root/'shared/i18n';self.backup=self.root/'backup'
        for path in (self.repo/'widgets',self.repo/'extension',self.repo/'sticky-notes',self.ext,self.collectors,self.notes,self.shared,self.backup/'files'):
            path.mkdir(parents=True,exist_ok=True)
        self.target=self.collectors/'weather.py';self.target.write_bytes(b'new')
        self.source=self.repo/'widgets/weather.py';self.source.write_bytes(b'new')
        (self.backup/'files/0').write_bytes(b'old')
        self.outside=self.root/'unrelated';self.outside.write_bytes(b'untouched')
        self.manifest=dict(repo=str(self.repo),extension=str(self.ext),schema='org.gnome.shell.extensions.azclock',old_settings='old-settings',new_settings='new-settings',files=[dict(target=str(self.target),source=str(self.source),backup='files/0',old_hash=hashlib.sha256(b'old').hexdigest(),new_hash=hashlib.sha256(b'new').hexdigest())])
        stack=contextlib.ExitStack();self.addCleanup(stack.close)
        for key,value in dict(REPO=self.repo,EXTENSIONS=self.extensions,EXT=self.ext,SCHEMA=self.manifest['schema'],COLLECTORS=self.collectors,NOTES=self.notes,I18N=self.shared).items():stack.enter_context(patch.object(update,key,value))

    def write(self,manifest):
        (self.backup/'manifest.json').write_text(json.dumps(manifest))

    def reject(self,manifest):
        self.write(manifest)
        before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        for force in (False,True):
            with patch.object(update,'settings') as settings,patch.object(update,'preflight') as preflight,patch.object(update,'atomic_copy') as copy_file,patch.object(update,'secure_unlink') as unlink:
                with self.subTest(force=force),self.assertRaises((RuntimeError,OSError)):
                    update.restore(self.backup,force,preflight_check=True)
                settings.assert_not_called();preflight.assert_not_called()
                copy_file.assert_not_called();unlink.assert_not_called()
            self.assertEqual({p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()},before)

    def test_target_outside_allowlist_rejected_for_restore_and_delete(self):
        for target in (self.outside,self.extensions/update.NEW_UUID/'other.py',self.notes.parent/'notes.sqlite3',self.ext/'vendor/other.py',self.shared/'other.json',self.ext/'schemas/org.gnome.shell.extensions.orbitz-widgets.gschema.xml'):
            for absent_backup in (False,True):
                manifest=copy.deepcopy(self.manifest);item=manifest['files'][0];item['target']=str(target)
                if absent_backup:item.update(backup=None,old_hash=None)
                with self.subTest(target=target,backup_null=absent_backup):self.reject(manifest)

    def test_backup_absolute_traversal_and_noncanonical_paths_rejected(self):
        for path in (str(self.outside),'../unrelated','files/../../unrelated','files/../files/0','files/./0','files//0','','.'):
            manifest=copy.deepcopy(self.manifest);manifest['files'][0]['backup']=path
            with self.subTest(path=path):self.reject(manifest)

    def test_source_must_match_allowed_root_and_target_relative_path(self):
        for path in (self.outside,self.repo/'widgets/other.py',self.repo/'extension/weather.py',self.repo/'widgets/../widgets/weather.py'):
            manifest=copy.deepcopy(self.manifest);manifest['files'][0]['source']=str(path)
            with self.subTest(path=path):self.reject(manifest)
        manifest=copy.deepcopy(self.manifest);manifest['repo']=str(self.root/'untrusted-repo');self.reject(manifest)

    def test_all_entries_validated_before_first_entry_can_mutate(self):
        manifest=copy.deepcopy(self.manifest)
        manifest['files'].append({**manifest['files'][0],'target':str(self.outside),'backup':None,'old_hash':None})
        self.reject(manifest)

    def test_manifest_format_hashes_and_duplicate_targets_rejected(self):
        bad=[None,[],{}, {**self.manifest,'files':{}},{**self.manifest,'old_settings':[]}, {**self.manifest,'files':[None]}]
        for key,value in (('source',None),('target','relative.py'),('new_hash','invalid'),('old_hash',None),('backup',None)):
            manifest=copy.deepcopy(self.manifest);manifest['files'][0][key]=value;bad.append(manifest)
        bad.append({**self.manifest,'files':self.manifest['files']*2})
        for manifest in bad:
            with self.subTest(manifest=manifest):self.reject(manifest)

    def test_allowlisted_legacy_youtube_removal_can_be_rolled_back(self):
        target=self.ext/'youtube-widget'/'youtube-widget.py'
        target.parent.mkdir(parents=True,exist_ok=True)
        self.manifest['files']=[dict(target=str(target),source=None,backup='files/0',
            old_hash=hashlib.sha256(b'old').hexdigest(),new_hash=None)]
        self.write(self.manifest)
        update.validate_rollback_manifest(self.manifest,self.backup)
        state=['new-settings']
        def settings(action,key,value=None):
            if action=='get':return state[0]
            state[0]=value
        with patch.object(update,'settings',side_effect=settings):
            update.restore(self.backup)
        self.assertEqual(target.read_bytes(),b'old')
        self.assertEqual(state[0],'old-settings')

    def test_apply_records_and_removes_allowlisted_legacy_youtube_file(self):
        target=self.ext/'youtube-widget'/'youtube-widget.py'
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'legacy')
        pyc=self.ext/'youtube-widget'/'__pycache__'/'youtube-widget.cpython-310.pyc'
        pyc.parent.mkdir(parents=True,exist_ok=True);pyc.write_bytes(b'compiled legacy')
        state=['old-settings']
        def settings(action,key,value=None):
            if action=='get':return state[0]
            state[0]=value
        with patch.object(update,'files',return_value=[(None,target),(None,pyc)]), \
             patch.object(update,'settings',side_effect=settings), \
             patch.object(update,'migrate',return_value=('new-settings',0)), \
             patch.object(update,'preflight'), \
             patch.object(update,'BACKUPS',self.root/'backups'), \
             patch('sys.argv',['update-local.py','--apply']), redirect_stdout(StringIO()):
            update.main()
            self.assertFalse(target.exists());self.assertFalse(pyc.exists())
        manifests=list((self.root/'backups').glob('*/manifest.json'))
        self.assertEqual(len(manifests),1)
        items=json.loads(manifests[0].read_text())['files']
        self.assertEqual(len(items),2)
        for item,expected in zip(items,(b'legacy',b'compiled legacy')):
            self.assertIsNone(item['source']);self.assertIsNone(item['new_hash'])
            self.assertEqual((manifests[0].parent/item['backup']).read_bytes(),expected)
        self.assertEqual(state[0],'new-settings')
        with patch.object(update,'settings',side_effect=settings):
            update.restore(manifests[0].parent,preflight_check=False)
        self.assertEqual(target.read_bytes(),b'legacy')
        self.assertEqual(pyc.read_bytes(),b'compiled legacy')
        self.assertEqual(state[0],'old-settings')

    def test_legacy_youtube_removal_rejects_unlisted_files_or_missing_backup(self):
        target=self.ext/'youtube-widget'/'youtube-widget.py'
        cases=[]
        unlisted=copy.deepcopy(self.manifest);unlisted['files']=[dict(target=str(self.ext/'other.py'),source=None,backup='files/0',old_hash=hashlib.sha256(b'old').hexdigest(),new_hash=None)];cases.append(unlisted)
        no_backup=copy.deepcopy(self.manifest);no_backup['files']=[dict(target=str(target),source=None,backup=None,old_hash=None,new_hash=None)];cases.append(no_backup)
        wrong_hash=copy.deepcopy(self.manifest);wrong_hash['files']=[dict(target=str(target),source=None,backup='files/0',old_hash=hashlib.sha256(b'old').hexdigest(),new_hash=hashlib.sha256(b'new').hexdigest())];cases.append(wrong_hash)
        for manifest in cases:
            with self.subTest(manifest=manifest):self.reject(manifest)

    def test_cli_rejects_invalid_manifest_before_preflight(self):
        manifest=copy.deepcopy(self.manifest);manifest['files'][0]['target']=str(self.outside)
        self.write(manifest)
        with patch('sys.argv',['update-local.py','--rollback',str(self.backup),'--force']),patch.object(update,'preflight') as preflight,patch.object(update,'settings') as settings:
            with self.assertRaises(RuntimeError):update.main()
            preflight.assert_not_called();settings.assert_not_called()
        self.assertEqual(self.outside.read_bytes(),b'untouched')

    def test_legacy_identity_omissions_and_missing_source_still_restore(self):
        manifest=copy.deepcopy(self.manifest)
        for key in ('repo','extension','schema'):manifest.pop(key)
        self.source.unlink()  # Restoring uses backup bytes, not a current source.
        self.write(manifest);state=['new-settings']
        def settings(action,*args):
            if action=='get':return state[0]
            if action=='set':state[0]=args[1];return ''
            raise AssertionError(action)
        with patch.object(update,'settings',side_effect=settings):update.restore(self.backup)
        self.assertEqual(self.target.read_bytes(),b'old');self.assertEqual(state[0],'old-settings')

    def test_legitimate_notes_code_and_null_backup_remove_only_allowed_file(self):
        target=self.notes/'card.py';target.write_bytes(b'new')
        manifest=copy.deepcopy(self.manifest)
        manifest['files'][0].update(target=str(target),source=str(self.repo/'sticky-notes/card.py'),backup=None,old_hash=None)
        self.write(manifest);state=['new-settings']
        def settings(action,*args):
            if action=='get':return state[0]
            state[0]=args[1];return ''
        with patch.object(update,'settings',side_effect=settings):update.restore(self.backup)
        self.assertFalse(target.exists());self.assertEqual(self.outside.read_bytes(),b'untouched')

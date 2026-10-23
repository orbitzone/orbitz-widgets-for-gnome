import gc
import ast
from types import SimpleNamespace
from unittest.mock import Mock
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('orbitz_ui_language_test',ROOT/'i18n/ui_i18n.py')
ui=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui)

class Widget:
    def __init__(self,**props):self.props=props
    def set_property(self,key,value):self.props[key]=value
    def set_text(self,value):self.props['label']=value

class LanguageTests(unittest.TestCase):
    def setUp(self):ui.refresh('pt-BR')
    def tearDown(self):ui.refresh('pt-BR')
    def test_live_binding_never_translates_user_content(self):
        label=ui.widget(Widget,label=ui.msg('settings.add_widget'))
        user=ui.widget(Widget,label='Adicionar widget…')
        ui.refresh('en-US')
        self.assertEqual(label.props['label'],'Add widget…')
        self.assertEqual(user.props['label'],'Adicionar widget…')
        ui.call(label,'set_text',ui.msg('sticky.save_error',error='CONTEÚDO DO USUÁRIO'))
        ui.refresh('pt-BR')
        self.assertEqual(label.props['label'],'Não foi salvo: CONTEÚDO DO USUÁRIO')
        ui.set(label,'label','user data');ui.refresh('en-US')
        self.assertEqual(label.props['label'],'user data')
    def test_catalog_id_and_placeholder_parity(self):
        catalogs=[json.loads((ROOT/'i18n'/name).read_text()) for name in ('pt-BR.json','en-US.json')]
        self.assertEqual(set(catalogs[0]),set(catalogs[1]))
        for key in catalogs[0]:
            with self.subTest(key=key):
                self.assertRegex(key,r'^[a-z][a-z0-9_.]+$')
                self.assertEqual(set(re.findall(r'\{([a-zA-Z_]\w*)\}',catalogs[0][key])),set(re.findall(r'\{([a-zA-Z_]\w*)\}',catalogs[1][key])))
    def test_explicit_message_references_exist_in_both_catalogs(self):
        catalogs=[json.loads((ROOT/'i18n'/name).read_text()) for name in ('pt-BR.json','en-US.json')]
        pattern=re.compile(r"(?:Language|ui)\.(?:msg|tr)\(['\"]([a-z][a-z0-9_.]+)['\"]")
        for folder in ('extension','sticky-notes'):
            for source in (ROOT/folder).rglob('*'):
                if source.suffix not in ('.js','.py'):continue
                for key in pattern.findall(source.read_text()):
                    with self.subTest(file=str(source.relative_to(ROOT)),key=key):
                        self.assertTrue(all(key in catalog for catalog in catalogs))

    def test_sticky_backup_error_is_live_and_does_not_retry_or_change_backup(self):
        tree=ast.parse((ROOT/'sticky-notes/postits.py').read_text())
        cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='Postits')
        method=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='backup_store')
        namespace={'ui':ui}
        exec(compile(ast.Module(body=[method],type_ignores=[]),'postits.py','exec'),namespace)
        status=Widget();status.show=Mock()
        backup=Mock(side_effect=OSError('USER external error'))
        host=SimpleNamespace(store=SimpleNamespace(backup=backup),get_windows=lambda:[SimpleNamespace(status=status)])
        self.assertTrue(namespace['backup_store'](host))
        self.assertEqual(status.props['label'],'Não foi possível criar o backup: USER external error')
        ui.refresh('en-US')
        self.assertEqual(status.props['label'],'Could not create the backup: USER external error')
        backup.assert_called_once_with();status.show.assert_called_once_with()

    def test_materialized_error_updates_live_only_with_explicit_orbitz_metadata(self):
        error=ui.exception(ValueError,'domain.calendar_http.token_exchange_failure',status=401,detail='USER external detail')
        original=error.args
        self.assertIs(type(error),ValueError);self.assertIs(type(error.args[0]),str)
        tagged=Widget();external=Widget()
        ui.call(tagged,'set_text',ui.error_message(error))
        # Same characters from an external exception must never be classified by matching.
        raw=ValueError(error.args[0]);ui.call(external,'set_text',ui.error_message(raw))
        ui.refresh('en-US')
        self.assertEqual(tagged.props['label'],'Google OAuth - token exchange (HTTP 401): USER external detail')
        self.assertEqual(external.props['label'],original[0])
        self.assertEqual(error.args,original);self.assertEqual(raw.args,original)
        ui.refresh('pt-BR')
        self.assertEqual(tagged.props['label'],original[0])

    def test_dead_widget_bindings_are_pruned(self):
        widget=ui.widget(Widget,label=ui.msg('settings.title'))
        reference=__import__('weakref').ref(widget);del widget;gc.collect();ui.refresh('en-US')
        self.assertIsNone(reference())
        self.assertTrue(all(item[0]() is not None for item in ui._bindings))

if __name__=='__main__':unittest.main()

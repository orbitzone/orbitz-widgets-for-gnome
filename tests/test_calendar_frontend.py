"""Provider UI workflow contracts; no accounts, OAuth sockets, vault or browser."""
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

PLANNER=Path(__file__).resolve().parents[1]/'extension/planner'
sys.path.insert(0,str(PLANNER))
from provider_connection_ui import ConnectionAttempt, launch_google_auth, GOOGLE_PROGRESS
from ui_language import ui as language


class ConnectionTests(unittest.TestCase):
    def test_google_ack_and_calendly_use_exact_provider_contracts(self):
        for provider in ('google','calendly'):
            account={'id':'synthetic-'+provider,'provider':provider,'calendars':[]}
            service=SimpleNamespace(connect_google=Mock(return_value=account),connect_calendly=Mock(return_value=account),disconnect=Mock())
            attempt=ConnectionAttempt(service,provider)
            browser=Mock()
            result=attempt.connect('Teste','synthetic-private-input',lambda value:attempt.accept(),open_browser=browser)
            self.assertEqual(result,account);service.disconnect.assert_not_called()
            if provider=='google':service.connect_google.assert_called_once_with(None,'Teste',cancel_event=attempt.cancelled,open_browser=browser)
            else:service.connect_calendly.assert_called_once_with('synthetic-private-input','Teste',cancel_event=attempt.cancelled)

    def test_cancel_before_start_never_calls_backend(self):
        service=SimpleNamespace(connect_google=Mock(),connect_calendly=Mock(),disconnect=Mock())
        attempt=ConnectionAttempt(service,'google');attempt.cancelled.set()
        self.assertIsNone(attempt.connect('Teste','synthetic',Mock()))
        service.connect_google.assert_not_called();service.disconnect.assert_not_called()

    def test_cancel_after_commit_or_dropped_ui_callback_rolls_back(self):
        for dropped in (False,True):
            account={'id':'synthetic','provider':'google'}
            service=SimpleNamespace(connect_google=Mock(return_value=account),disconnect=Mock())
            attempt=ConnectionAttempt(service,'google')
            deliver=(lambda value:None) if dropped else (lambda value:attempt.cancelled.set())
            self.assertIsNone(attempt.connect('Teste','synthetic',deliver,acknowledge_timeout=0))
            service.disconnect.assert_called_once_with(account)
            self.assertFalse(attempt.accept())  # A delayed UI callback cannot accept a rolled-back account.

    def test_workspace_cancel_while_ui_ack_is_pending_finishes_worker_cleanup(self):
        ready=threading.Event()
        account={'id':'synthetic','provider':'google'}
        service=SimpleNamespace(connect_google=Mock(return_value=account),disconnect=Mock())
        attempt=ConnectionAttempt(service,'google')
        with ThreadPoolExecutor(max_workers=1) as executor:
            future=executor.submit(attempt.connect,'Teste','synthetic',lambda value:ready.set(),None,5)
            self.assertTrue(ready.wait(3))
            attempt.cancelled.set()
            self.assertIsNone(future.result(timeout=3))
        service.disconnect.assert_called_once_with(account)
        self.assertFalse(attempt.accept())

    def test_google_browser_destination_rejects_foreign_or_unsafe_origins(self):
        launch=Mock(return_value=True)
        url='https://accounts.google.com/o/oauth2/v2/auth?client_id=synthetic&state=synthetic'
        self.assertTrue(launch_google_auth(url,launch));launch.assert_called_once_with(url)
        for invalid in ('http://accounts.google.com/auth','https://example.invalid/auth',
                'https://user:pass@accounts.google.com/auth','https://accounts.google.com:444/auth'):
            with self.assertRaises(ValueError):launch_google_auth(invalid,Mock())

    def test_google_default_login_never_forwards_a_custom_path(self):
        service=SimpleNamespace(connect_google=Mock(return_value={'id':'synthetic'}),disconnect=Mock())
        attempt=ConnectionAttempt(service,'google')
        attempt.connect('Google pessoal',None,lambda _:attempt.accept())
        service.connect_google.assert_called_once_with(None,'Google pessoal',
            cancel_event=attempt.cancelled,open_browser=None)
        service.disconnect.assert_not_called()

    def ui_callbacks(self, attempt):
        tree=ast.parse((PLANNER/'provider_connection_ui.py').read_text())
        dialog=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='connect_provider')
        callbacks=[n for n in dialog.body if isinstance(n,ast.FunctionDef) and n.name in ('progress','failed','complete','start')]
        namespace=dict(ui=language,GOOGLE_PROGRESS=GOOGLE_PROGRESS,pending=[attempt],result=[None],alive=lambda:True,
            status=Mock(),name=Mock(),credential=None,dialog=Mock(),Gtk=SimpleNamespace(ResponseType=SimpleNamespace(OK=1,ACCEPT=2)))
        namespace.update(ConnectionAttempt=ConnectionAttempt,calendar_accounts=attempt.service,provider='google',google=True,
            controller=SimpleNamespace(cancel_events=[],executor=SimpleNamespace(submit=lambda work:work())),
            GLib=SimpleNamespace(idle_add=lambda callback,*args:callback(*args)))
        exec(compile(ast.Module(body=callbacks,type_ignores=[]),'provider_connection_ui.py','exec'),namespace)
        return namespace

    def test_backend_failure_reenables_google_and_stale_callbacks_are_ignored(self):
        attempt=ConnectionAttempt(SimpleNamespace(),'google')
        ui=self.ui_callbacks(attempt)
        ui['progress'](attempt,'loading_calendars')
        ui['status'].set_text.assert_called_once_with(str(GOOGLE_PROGRESS['loading_calendars']))
        ui['status'].reset_mock()
        ui['progress'](attempt,'untrusted-token-or-error')
        ui['status'].set_text.assert_not_called()
        ui['failed'](attempt,ValueError('Falha segura'))
        self.assertIsNone(ui['pending'][0])
        ui['name'].set_sensitive.assert_called_once_with(True)
        ui['dialog'].set_response_sensitive.assert_called_once_with(1,True)
        ui['status'].reset_mock()
        ui['progress'](attempt,'saving_credentials')
        ui['failed'](attempt,ValueError('Obsoleto'))
        ui['complete'](attempt,{'id':'obsolete'})
        ui['status'].set_text.assert_not_called()
        ui['dialog'].response.assert_not_called()
        self.assertTrue(attempt.cancelled.is_set())

    def test_google_progress_changes_language_in_the_open_status(self):
        attempt=ConnectionAttempt(SimpleNamespace(),'google')
        state=self.ui_callbacks(attempt)
        try:
            language.refresh('pt-BR')
            state['progress'](attempt,'loading_calendars')
            state['status'].set_text.assert_called_with('Consultando seus calendários Google…')
            language.refresh('en-US')
            state['status'].set_text.assert_called_with('Fetching your Google calendars…')
            self.assertIs(state['pending'][0],attempt)
            language.refresh('pt-BR')
            state['status'].set_text.assert_called_with('Consultando seus calendários Google…')
        finally:language.refresh('pt-BR')

    def test_failed_orbitz_error_already_displayed_tracks_locale_without_restarting_login(self):
        attempt=ConnectionAttempt(SimpleNamespace(),'google')
        state=self.ui_callbacks(attempt)
        try:
            language.refresh('pt-BR')
            error=language.exception(ValueError,'domain.calendar_http.token_exchange_failure',status=401,detail='USER detail')
            original=error.args
            state['failed'](attempt,error)
            state['status'].set_text.assert_called_with(original[0])
            language.refresh('en-US')
            state['status'].set_text.assert_called_with('Google OAuth - token exchange (HTTP 401): USER detail')
            self.assertEqual(error.args,original);self.assertIs(type(error.args[0]),str)
            self.assertIsNone(state['pending'][0])
            state['dialog'].response.assert_not_called()
            state['name'].set_sensitive.assert_called_once_with(True)
        finally:language.refresh('pt-BR')

    def test_worker_backend_failure_after_progress_reenables_login(self):
        def connect(*args,**kwargs):
            kwargs['on_progress']('exchanging_token')
            raise ValueError('Falha segura de autorização')
        service=SimpleNamespace(connect_google=Mock(side_effect=connect),disconnect=Mock())
        ui=self.ui_callbacks(ConnectionAttempt(service,'google'))
        ui['start']('Teste',None)
        self.assertIsNone(ui['pending'][0])
        self.assertEqual(ui['status'].set_text.call_args_list[0].args,
            (str(GOOGLE_PROGRESS['exchanging_token']),))
        ui['status'].set_text.assert_called_with('Falha segura de autorização')
        ui['dialog'].set_response_sensitive.assert_called_once_with(1,True)
        ui['name'].set_sensitive.assert_called_once_with(True)
        ui['dialog'].response.assert_not_called()
        service.disconnect.assert_not_called()



class SyncTests(unittest.TestCase):
    def build(self,provider,side_effect=None):
        account={'id':'synthetic','provider':provider,'email':'synthetic@example.invalid'}
        calendar={'id':'calendar','url':'https://example.invalid/calendar.ics'}
        context=(account,calendar,'2026-10')
        vault=SimpleNamespace(get=Mock(return_value='synthetic-private-token'),delete=Mock())
        remote=SimpleNamespace(cache_key=lambda *args:'synthetic-cache',read=lambda:{'cache':{},'accounts':[account]},put_cache=Mock(),Vault=lambda:vault,remove_account=Mock(),is_builtin=lambda a:False)
        events=[{'title':'Sintético'}]
        service=SimpleNamespace(events=Mock(return_value=events,side_effect=side_effect),disconnect=Mock())
        apple_client=SimpleNamespace(events=Mock(return_value=events))
        apple=SimpleNamespace(AppleClient=Mock(return_value=apple_client))
        ics=SimpleNamespace(events=Mock(return_value=events))
        namespace={'ui':language,'threading':threading,'datetime':datetime,'timezone':timezone,'remote':remote,'apple':apple,'ics_client':ics,
            'Gtk':SimpleNamespace(),'GLib':SimpleNamespace()}
        node=next(node for node in ast.parse((PLANNER/'external_ui.py').read_text()).body if isinstance(node,ast.ClassDef))
        exec(compile(ast.Module(body=[node],type_ignores=[]),'external_ui.py','exec'),namespace)
        obj=object.__new__(namespace['ExternalCalendars'])
        obj.alive=True;obj.busy=set();obj.cancel_events=[];obj.sync_cancels={}
        obj.context=lambda:context;obj.status=Mock();obj.render=Mock()
        obj.window=SimpleNamespace(mark_days=Mock());obj.selected_cache=lambda:(context,{})
        obj.cache_status=Mock()
        def run(work,done):
            try:result=work();error=None
            except Exception as failure:result=None;error=failure
            done(result,error)
        obj.run=run
        return obj,context,remote,service,apple,ics,vault

    def test_sync_google_calendly_and_legacy_routes_preserve_cache_contract(self):
        for provider in ('google','calendly','ics','icloud'):
            obj,context,remote,service,apple,ics,vault=self.build(provider)
            with patch.dict(sys.modules,{'calendar_accounts':service}):obj.sync_context(context,force=True)
            remote.put_cache.assert_called_once()
            self.assertEqual(obj.busy,set())
            if provider in ('google','calendly'):
                service.events.assert_called_once();apple.AppleClient.assert_not_called();ics.events.assert_not_called()
            elif provider=='ics':ics.events.assert_called_once();service.events.assert_not_called()
            else:apple.AppleClient.assert_called_once_with('synthetic@example.invalid','synthetic-private-token');service.events.assert_not_called()

    def test_cancelled_or_failed_sync_never_replaces_cache(self):
        def cancel(*args,**kwargs):kwargs['cancel_event'].set();return []
        for failure in (cancel,ValueError('Sintético indisponível')):
            obj,context,remote,service,*_=self.build('google',side_effect=failure)
            with patch.dict(sys.modules,{'calendar_accounts':service}):obj.sync_context(context,force=True)
            remote.put_cache.assert_not_called()
            self.assertEqual(obj.busy,set())

    def test_disconnect_new_providers_uses_vault_aware_service_only(self):
        for provider in ('google','calendly','icloud','ics'):
            obj,context,remote,service,apple,ics,vault=self.build(provider)
            cancel=threading.Event();obj.sync_cancels={'key':('synthetic',cancel)}
            with patch.dict(sys.modules,{'calendar_accounts':service}):obj.disconnect_account(context[0])
            self.assertTrue(cancel.is_set())
            if provider in ('google','calendly'):
                service.disconnect.assert_called_once_with(context[0]);remote.remove_account.assert_not_called()
            else:remote.remove_account.assert_called_once_with('synthetic')


class BuiltinSourceTests(unittest.TestCase):
    build=SyncTests.build

    def test_toggle_preserves_source_and_cancels_only_its_jobs_with_local_fallback(self):
        obj,context,remote,service,*_=self.build('ics')
        account,calendar,_=context;calendar['name']='Brasil';account['calendars']=[calendar]
        other=dict(id='private',provider='google',label='Privado',calendars=[dict(id='private-calendar',name='Pessoal')])
        state=dict(accounts=[account,other],cache={'retained':'cached'})
        remote.read=lambda:state
        remote.ensure_default_calendar=Mock(return_value=account)
        remote.set_builtin_enabled=Mock(side_effect=lambda identity,enabled:account.update(enabled=enabled))
        selected=[account['id']+'|'+calendar['id']];choices=[]
        obj.selector=SimpleNamespace(get_active_id=lambda:selected[0],remove_all=lambda:choices.clear(),
            append=lambda identity,label:choices.append(identity),set_active_id=lambda identity:selected.__setitem__(0,identity))
        obj.status=Mock();obj.window.calendar=Mock();obj.window.calendar.get_date.return_value=(2026,9,1)
        obj.context=obj.__class__.context.__get__(obj)
        obj.populate.__globals__['ui_state']=SimpleNamespace(get=lambda *args:'local')
        own=threading.Event();private=threading.Event()
        obj.sync_cancels={'own':(account['id'],own),'private':('private',private)}
        obj.selection_changed=Mock()
        obj.set_builtin_enabled(account,False)
        self.assertTrue(own.is_set());self.assertFalse(private.is_set())
        self.assertEqual(selected[0],'local');self.assertNotIn(account['id']+'|'+calendar['id'],choices)
        self.assertIn('private|private-calendar',choices);self.assertIsNone(obj.context())
        self.assertEqual(state['cache'],{'retained':'cached'})
        self.assertEqual(len(state['accounts']),2)
        obj.set_builtin_enabled(account,True)
        self.assertIn(account['id']+'|'+calendar['id'],choices)
        remote.ensure_default_calendar.assert_called()
        obj.selection_changed.assert_called()

    def test_manage_builtin_uses_toggle_and_never_disconnect(self):
        obj,context,remote,*_=self.build('ics')
        account=context[0];account['label']='Nome legado'
        remote.ensure_default_calendar=Mock(return_value=account)
        remote.is_builtin=lambda value:True
        labels=[]
        box=Mock();box.get_children.return_value=[]
        gtk=SimpleNamespace(Dialog=Mock(return_value=Mock()),Box=Mock(return_value=box),
            Label=Mock(return_value=Mock()),Button=lambda **kw:(labels.append(kw['label']) or Mock()),
            Orientation=SimpleNamespace(VERTICAL=1),ResponseType=SimpleNamespace(CLOSE=1))
        namespace=obj.manage.__globals__;namespace['Gtk']=gtk
        namespace['Pango']=SimpleNamespace(WrapMode=SimpleNamespace(WORD_CHAR=1))
        previous_locale=language.get_locale()
        self.addCleanup(language.refresh,previous_locale)
        for locale,disable,enable,title in (
                ('pt-BR','Desativar','Ativar','Brasil · Datas comemorativas'),
                ('en-US','Disable','Enable','Brazil · Holidays')):
            with self.subTest(locale=locale):
                language.refresh(locale)
                for enabled,expected in ((True,disable),(False,enable)):
                    labels.clear();gtk.Label.reset_mock();account['enabled']=enabled;obj.manage()
                    self.assertEqual(labels,[expected])
                    self.assertTrue(any(call.kwargs.get('label','').startswith(title)
                        for call in gtk.Label.call_args_list))
        remote.remove_account.assert_not_called()
        remote.ensure_default_calendar.assert_called()

    def test_periodic_sync_skips_disabled_and_keeps_other_accounts(self):
        obj,context,remote,*_=self.build('ics')
        account,calendar,_=context;account.update(enabled=False,calendars=[calendar])
        other=dict(id='private',provider='google',calendars=[dict(id='main')])
        obj.accounts=[account,other];obj.context=lambda:None;obj.sync_context=Mock()
        obj.window.calendar=Mock();obj.window.calendar.get_date.return_value=(2026,9,1)
        obj.sync()
        obj.sync_context.assert_called_once_with((other,other['calendars'][0],'2026-10'),False)
        account['enabled']=True;obj.sync_context.reset_mock();obj.sync()
        self.assertEqual(obj.sync_context.call_count,2)

    def test_disabled_context_never_enqueues_and_queued_work_checks_latest_state(self):
        obj,context,remote,service,apple,ics,_=self.build('ics')
        account,_,_=context;account['enabled']=False
        obj.run=Mock();obj.sync_context(context,True);obj.run.assert_not_called()
        account['enabled']=True;captured=[]
        obj.run=lambda work,done:captured.append((work,done))
        obj.sync_context(context,True)
        account['enabled']=False
        captured[0][0]()
        ics.events.assert_not_called();remote.put_cache.assert_not_called()
        captured[0][1](None,None)
        self.assertEqual(obj.busy,set());self.assertEqual(obj.sync_cancels,{})

    def test_cancelled_queued_work_never_contacts_source(self):
        obj,context,remote,service,apple,ics,_=self.build('ics');captured=[]
        obj.run=lambda work,done:captured.append((work,done))
        obj.sync_context(context,True)
        obj.cancel_sync(account_id=context[0]['id'])
        captured[0][0]();captured[0][1](None,None)
        ics.events.assert_not_called();remote.put_cache.assert_not_called()
        self.assertEqual(obj.busy,set())


if __name__=='__main__':unittest.main()

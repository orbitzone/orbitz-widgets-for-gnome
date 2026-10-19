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
from provider_connection_ui import ConnectionAttempt, launch_google_auth


class ConnectionTests(unittest.TestCase):
    def test_google_ack_and_calendly_use_exact_provider_contracts(self):
        for provider in ('google','calendly'):
            account={'id':'synthetic-'+provider,'provider':provider,'calendars':[]}
            service=SimpleNamespace(connect_google=Mock(return_value=account),connect_calendly=Mock(return_value=account),disconnect=Mock())
            attempt=ConnectionAttempt(service,provider)
            browser=Mock()
            result=attempt.connect('Teste','synthetic-private-input',lambda value:attempt.accept(),open_browser=browser)
            self.assertEqual(result,account);service.disconnect.assert_not_called()
            if provider=='google':service.connect_google.assert_called_once_with('synthetic-private-input','Teste',cancel_event=attempt.cancelled,open_browser=browser)
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


class SyncTests(unittest.TestCase):
    def build(self,provider,side_effect=None):
        account={'id':'synthetic','provider':provider,'email':'synthetic@example.invalid'}
        calendar={'id':'calendar','url':'https://example.invalid/calendar.ics'}
        context=(account,calendar,'2026-10')
        vault=SimpleNamespace(get=Mock(return_value='synthetic-private-token'),delete=Mock())
        remote=SimpleNamespace(cache_key=lambda *args:'synthetic-cache',read=lambda:{'cache':{}},put_cache=Mock(),Vault=lambda:vault,remove_account=Mock())
        events=[{'title':'Sintético'}]
        service=SimpleNamespace(events=Mock(return_value=events,side_effect=side_effect),disconnect=Mock())
        apple_client=SimpleNamespace(events=Mock(return_value=events))
        apple=SimpleNamespace(AppleClient=Mock(return_value=apple_client))
        ics=SimpleNamespace(events=Mock(return_value=events))
        namespace={'threading':threading,'datetime':datetime,'timezone':timezone,'remote':remote,'apple':apple,'ics_client':ics,
            'Gtk':SimpleNamespace(),'GLib':SimpleNamespace()}
        node=next(node for node in ast.parse((PLANNER/'external_ui.py').read_text()).body if isinstance(node,ast.ClassDef))
        exec(compile(ast.Module(body=[node],type_ignores=[]),'external_ui.py','exec'),namespace)
        obj=object.__new__(namespace['ExternalCalendars'])
        obj.alive=True;obj.busy=set();obj.cancel_events=[];obj.sync_cancels={}
        obj.context=lambda:context;obj.status=SimpleNamespace(set_text=Mock());obj.render=Mock()
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


if __name__=='__main__':unittest.main()

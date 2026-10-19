"""CAL-01 fixed-host clients and OAuth lifecycle with synthetic secrets only."""
import base64
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs,urlsplit,urlencode
from urllib.request import Request,urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'extension/planner'))
import calendar_http as http
import calendar_api_events as normalized
import google_oauth as oauth
import google_client
import calendly_client
import calendar_accounts as accounts
import external_store
import store
import credential_vault
from calendar_events import CalendarError

ACCESS='synthetic-access-SENTINEL'
REFRESH='synthetic-refresh-SENTINEL'
PAT='synthetic-pat-SENTINEL'
CLIENT=dict(client_id='fixture.apps.googleusercontent.com',client_secret='synthetic-client-secret-SENTINEL')
SCOPES=' '.join(oauth.SCOPES)
GCAL=dict(id=hashlib.sha256(b'primary-fixture').hexdigest(),remote_id='primary-fixture',name='Calendário sintético',color='#82cfff',timezone='America/Sao_Paulo',primary=True,default_reminders=[dict(method='popup',minutes=15)])
CCAL=dict(id=hashlib.sha256(b'user-fixture').hexdigest(),user_uri='https://api.calendly.com/users/fixture',name='Calendly sintético',color='#006bff')


def grant(**kwargs):return dict(access_token=ACCESS,refresh_token=REFRESH,token_type='Bearer',scope=SCOPES,expires_in=3600,**kwargs)


def google_event(**kwargs):return dict(id='event-fixture',summary='Evento sintético',start=dict(dateTime='2026-10-19T12:00:00Z'),end=dict(dateTime='2026-10-19T13:00:00Z'),reminders=dict(useDefault=True),**kwargs)


def calendly_event(**kwargs):return dict(uri='https://api.calendly.com/scheduled_events/fixture',status='active',name='Reunião sintética',start_time='2026-10-19T12:00:00Z',end_time='2026-10-19T13:00:00Z',**kwargs)


class ProviderHttpTests(unittest.TestCase):
    def test_fixed_host_redirect_no_bearer_query_and_generic_errors(self):
        class Response(io.BytesIO):pass
        seen=[]
        class Opener:
            def open(self,request,timeout):seen.append(request);return Response(b'{"items":[]}')
        with patch.object(http,'build_opener',return_value=Opener()):
            self.assertEqual(http.request_json('https://www.googleapis.com/calendar/v3/test',host='www.googleapis.com',path_prefix='/calendar/v3/',bearer=ACCESS),{'items':[]})
        self.assertNotIn(ACCESS,seen[0].full_url)
        self.assertEqual(seen[0].get_header('Authorization'),'Bearer '+ACCESS)
        self.assertIsNone(http.NoRedirect().redirect_request(None,None,302,'',{},'https://evil.invalid'))
        for url in ['https://evil.invalid/calendar/v3/x','http://www.googleapis.com/calendar/v3/x','https://user:pass@www.googleapis.com/calendar/v3/x','https://www.googleapis.com:444/calendar/v3/x']:
            with self.assertRaises(CalendarError):http.request_json(url,host='www.googleapis.com',path_prefix='/calendar/v3/',bearer=ACCESS)
        error=HTTPError('https://api.calendly.com/?secret='+PAT,403,'secret '+PAT,{},io.BytesIO(PAT.encode()))
        with patch.object(http,'build_opener') as opener:
            opener.return_value.open.side_effect=error
            with self.assertRaises(CalendarError) as failed:http.request_json('https://api.calendly.com/users/me',host='api.calendly.com',path_prefix='/users/me',bearer=PAT)
        self.assertNotIn(PAT,str(failed.exception))
        with self.assertRaises(CalendarError):http.request_json('https://api.calendly.com/scheduled_events',host='api.calendly.com',path_prefix='/',form={'token':PAT})

    def test_response_limits_and_cancel(self):
        with patch.object(http,'build_opener') as opener:
            opener.return_value.open.return_value=io.BytesIO(b'{}xxxx')
            with self.assertRaises(CalendarError):http.request_json('https://api.calendly.com/users/me',host='api.calendly.com',path_prefix='/',limit=2)
        cancel=threading.Event();cancel.set()
        with patch.object(http,'build_opener') as opener:
            with self.assertRaises(CalendarError):http.request_json('https://api.calendly.com/users/me',host='api.calendly.com',path_prefix='/',cancel_event=cancel)
            opener.assert_not_called()


class MemoryServer:
    """Dispatch the production callback Handler without creating network sockets."""
    def __init__(self,address,handler):
        self.address=address;self.handler=handler;self.server_port=43210;self.closed=False;self.queue=[];self.results=[]
    def handle_request(self):
        if not self.queue:
            time.sleep(.002);return
        path,host=self.queue.pop(0)
        handler=object.__new__(self.handler)
        handler.path=path;handler.client_address=('127.0.0.1',12345);handler.headers={'Host':host};handler.wfile=io.BytesIO()
        result={'headers':{}}
        handler.send_response=lambda status:result.update(status=status)
        handler.send_header=lambda key,value:result['headers'].update({key:value})
        handler.end_headers=lambda:None
        handler.do_GET();result['body']=handler.wfile.getvalue();self.results.append(result)
    def server_close(self):self.closed=True


class MemoryCallbackTests(unittest.TestCase):
    def test_production_callback_state_host_pkce_no_secrets_and_success_in_memory(self):
        with patch.object(oauth,'HTTPServer',MemoryServer):flow=oauth.Loopback()
        try:
            self.assertEqual(flow.server.address,('127.0.0.1',0))
            params=parse_qs(urlsplit(flow.authorization_url(CLIENT)).query)
            expected=base64.urlsafe_b64encode(hashlib.sha256(flow.verifier.encode()).digest()).rstrip(b'=').decode()
            self.assertEqual(params['code_challenge'],[expected]);self.assertEqual(params['code_challenge_method'],['S256'])
            self.assertNotIn(CLIENT['client_secret'],flow.authorization_url(CLIENT))
            host='127.0.0.1:43210'
            flow.server.queue=[('/?'+urlencode({'state':'wrong','code':'private-code'}),host),('/?'+urlencode({'state':flow.state,'code':'private-code'}),'evil.invalid'),('/?'+urlencode({'state':flow.state,'code':'private-code'}),host)]
            self.assertEqual(flow.wait(timeout=2),'private-code')
            self.assertEqual([value['status'] for value in flow.server.results],[400,400,200])
            for value in flow.server.results:
                self.assertNotIn(b'private-code',value['body']);self.assertEqual(value['headers']['Cache-Control'],'no-store')
        finally:flow.close()
        self.assertTrue(flow.server.closed)

    def test_callback_denial_cancel_timeout_duplicate_state_and_clear_memory(self):
        with patch.object(oauth,'HTTPServer',MemoryServer):flow=oauth.Loopback()
        try:
            flow.server.queue=[('/?state='+flow.state+'&state=duplicate&code=private-code','127.0.0.1:43210'),('/?'+urlencode({'state':flow.state,'error':'access_denied'}),'127.0.0.1:43210')]
            with self.assertRaisesRegex(CalendarError,'não foi concedida'):flow.wait(timeout=2)
            self.assertEqual(flow.server.results[0]['status'],400)
        finally:flow.close()
        with patch.object(oauth,'HTTPServer',MemoryServer):flow=oauth.Loopback()
        cancel=threading.Event();cancel.set()
        try:
            with self.assertRaisesRegex(CalendarError,'cancelada'):flow.wait(cancel)
            with self.assertRaisesRegex(CalendarError,'expirou'):flow.wait(timeout=.001)
        finally:flow.close()
        self.assertEqual(flow.state,'');self.assertEqual(flow.verifier,'')


class VaultBoundaryTests(unittest.TestCase):
    def test_provider_schema_attributes_payload_only_in_secret_service_and_redacted_failures(self):
        class Secret:
            COLLECTION_DEFAULT='default'
            stored=None
            def password_store_sync(self,schema,attributes,collection,label,value,cancel):self.stored=value;return True
            def password_lookup_sync(self,*args):return self.stored
            def password_clear_sync(self,*args):self.stored=None;return True
        service=Secret();vault=credential_vault.ProviderVault();identity='google-'+'a'*64
        with patch.object(vault,'_service',return_value=(service,'fixture-schema')):
            vault.put('google',identity,dict(refresh_token=REFRESH,config=CLIENT))
            self.assertEqual(vault.get('google',identity)['refresh_token'],REFRESH)
            with patch.object(service,'password_store_sync',side_effect=RuntimeError(PAT)):
                with self.assertRaises(CalendarError) as failed:vault.put('google',identity,dict(refresh_token=REFRESH))
                self.assertNotIn(PAT,str(failed.exception))
            service.stored=PAT
            with self.assertRaises(CalendarError) as failed:vault.get('google',identity)
            self.assertNotIn(PAT,str(failed.exception))
            vault.delete('google',identity);self.assertIsNone(service.stored)
            with self.assertRaises(CalendarError):vault.get('unknown',identity)


class OAuthTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.config=Path(self.temporary.name)/'client.json';self.config.write_text(json.dumps({'installed':CLIENT}))

    def test_desktop_config_required_no_remote_endpoint_injection(self):
        self.assertEqual(oauth.load_config(self.config),CLIENT)
        for value in [{'web':CLIENT},{'installed':dict(CLIENT,token_uri='https://evil.invalid/token')},{'installed':{'client_id':'not-a-desktop-client'}}]:
            self.config.write_text(json.dumps(value))
            with self.assertRaises(CalendarError):oauth.load_config(self.config)

    def test_loopback_state_pkce_host_and_no_logging_real_synthetic_callback(self):
        output=io.StringIO()
        with contextlib.redirect_stderr(output),contextlib.redirect_stdout(output):
            try:flow=oauth.Loopback()
            except PermissionError:self.skipTest('Sandbox bloqueia sockets; executar cenário loopback fora do sandbox.')
            result=[];failures=[]
            try:
                url=flow.authorization_url(CLIENT);params=parse_qs(urlsplit(url).query)
                self.assertEqual(urlsplit(url).netloc,'accounts.google.com')
                self.assertEqual(params['code_challenge_method'],['S256'])
                expected=base64.urlsafe_b64encode(hashlib.sha256(flow.verifier.encode()).digest()).rstrip(b'=').decode()
                self.assertEqual(params['code_challenge'],[expected]);self.assertNotIn(CLIENT['client_secret'],url)
                self.assertEqual(flow.server.server_address[0],'127.0.0.1')
                def wait():
                    try:result.append(flow.wait(timeout=3))
                    except Exception as error:failures.append(error)
                thread=threading.Thread(target=wait);thread.start()
                for query,host in [({'state':'wrong','code':'synthetic-code-SENTINEL'},None),({'state':flow.state,'code':'synthetic-code-SENTINEL'},'evil.invalid')]:
                    request=Request(flow.redirect_uri+'?'+urlencode(query),headers={'Host':host} if host else {})
                    with self.assertRaises(HTTPError) as failed:urlopen(request,timeout=2)
                    failed.exception.close()
                with urlopen(flow.redirect_uri+'?'+urlencode({'state':flow.state,'code':'synthetic-code-SENTINEL'}),timeout=2) as response:
                    self.assertEqual(response.status,200);self.assertEqual(response.headers['Cache-Control'],'no-store')
                thread.join(timeout=4)
                self.assertEqual(result,['synthetic-code-SENTINEL']);self.assertEqual(failures,[])
            finally:flow.close()
        self.assertNotIn('synthetic-code-SENTINEL',output.getvalue())
        self.assertNotIn('GET /',output.getvalue())

    def test_loopback_cancel_timeout_denial_and_socket_closed(self):
        try:flow=oauth.Loopback()
        except PermissionError:self.skipTest('Sandbox bloqueia sockets; executar cenário loopback fora do sandbox.')
        cancel=threading.Event();cancel.set()
        try:
            with self.assertRaisesRegex(CalendarError,'cancelada'):flow.wait(cancel)
            with self.assertRaisesRegex(CalendarError,'expirou'):flow.wait(timeout=.01)
        finally:flow.close()
        self.assertEqual(flow.server.fileno(),-1)
        flow=oauth.Loopback()
        def deny():
            time.sleep(.02)
            with urlopen(flow.redirect_uri+'?'+urlencode({'state':flow.state,'error':'access_denied'}),timeout=2):pass
        thread=threading.Thread(target=deny);thread.start()
        try:
            with self.assertRaisesRegex(CalendarError,'não foi concedida'):flow.wait(timeout=2)
        finally:thread.join(timeout=3);flow.close()

    def test_authorize_code_verifier_only_in_token_post_and_browser_failure_redacted(self):
        class FakeFlow:
            state='state';verifier='verifier';redirect_uri='http://127.0.0.1:1234/'
            def authorization_url(self,config):return oauth.AUTH_URL+'?client_id='+config['client_id']
            def wait(self,cancel_event):return 'synthetic-code'
            def close(self):self.closed=True
        flow=FakeFlow()
        with patch.object(oauth,'Loopback',return_value=flow),patch.object(http,'request_json',return_value=grant()) as request:
            value=oauth.authorize(self.config,open_browser=lambda url:True)
            self.assertEqual(value['refresh_token'],REFRESH)
            self.assertEqual(request.call_args.kwargs['form']['code_verifier'],'verifier')
            self.assertTrue(flow.closed)
        with patch.object(oauth,'Loopback',return_value=FakeFlow()):
            with self.assertRaises(CalendarError) as failure:oauth.authorize(self.config,open_browser=lambda url:(_ for _ in ()).throw(RuntimeError(PAT)))
            self.assertNotIn(PAT,str(failure.exception))

    def test_refresh_keeps_old_token_when_omitted_and_rotated_token_when_present(self):
        previous=dict(config=CLIENT,refresh_token=REFRESH,scope=SCOPES)
        response=grant();response.pop('refresh_token');response.pop('scope')
        with patch.object(http,'request_json',return_value=response):self.assertEqual(oauth.refresh(previous)['refresh_token'],REFRESH)
        response['refresh_token']='rotated-refresh-SENTINEL'
        with patch.object(http,'request_json',return_value=response):self.assertEqual(oauth.refresh(previous)['refresh_token'],'rotated-refresh-SENTINEL')
        response['scope']=oauth.SCOPES[0]
        with patch.object(http,'request_json',return_value=response):
            with self.assertRaises(CalendarError):oauth.refresh(previous)


class ApiClientTests(unittest.TestCase):
    def test_google_discovery_pagination_and_events_cancel_recurrence_timezone(self):
        first={'items':[dict(id='primary-fixture',summary='Fixture',timeZone='America/Sao_Paulo',primary=True)],'nextPageToken':'next'}
        with patch.object(http,'request_json',side_effect=[first,{'items':[]}]) as request:
            calendars=google_client.GoogleClient(ACCESS).discover()
            self.assertIn('pageToken=next',request.call_args.args[0])
            self.assertEqual(calendars[0]['remote_id'],'primary-fixture')
        recurring=google_event(originalStartTime={'dateTime':'2026-10-19T09:00:00-03:00'})
        all_day=dict(id='all-day',summary='Dia inteiro',start={'date':'2026-10-20'},end={'date':'2026-10-22'})
        with patch.object(http,'request_json',return_value={'items':[{'status':'cancelled','id':'gone'},recurring,all_day]}):
            events=google_client.GoogleClient(ACCESS).events(GCAL,'account','2026-10')
        self.assertEqual(len(events),2);self.assertEqual(events[0]['start'],'2026-10-19T09:00:00-03:00')
        self.assertEqual(events[0]['alarm_minutes'],[15]);self.assertNotEqual(events[0]['occurrence'],'single')
        self.assertTrue(events[1]['all_day']);self.assertEqual(events[1]['end'],'2026-10-22')

    def test_google_page_loop_and_invalid_event_abort_without_partial_result(self):
        with patch.object(http,'request_json',return_value={'items':[],'nextPageToken':'loop'}):
            with self.assertRaises(CalendarError):google_client.GoogleClient(ACCESS).discover()
        with patch.object(http,'request_json',return_value={'items':[google_event(),{'id':'broken'}]}):
            with self.assertRaises(CalendarError):google_client.GoogleClient(ACCESS).events(GCAL,'account','2026-10')

    def test_calendly_discover_and_safe_page_canceled_rescheduled_fuso(self):
        with patch.object(http,'request_json',return_value={'resource':{'uri':CCAL['user_uri'],'name':'Fixture'}}):
            self.assertEqual(calendly_client.CalendlyClient(PAT).discover()[0]['user_uri'],CCAL['user_uri'])
        pages=[dict(collection=[{'status':'canceled'},calendly_event()],pagination=dict(next_page='https://api.calendly.com/scheduled_events?'+urlencode(dict(user=CCAL['user_uri'],page_token='next')))),dict(collection=[dict(calendly_event(),uri='https://api.calendly.com/scheduled_events/rescheduled',start_time='2026-10-20T15:00:00Z',end_time='2026-10-20T16:00:00Z')],pagination={})]
        with patch.object(http,'request_json',side_effect=pages) as request:
            events=calendly_client.CalendlyClient(PAT).events(CCAL,'account','2026-10')
        self.assertEqual(len(events),2);self.assertEqual(events[0]['start'],'2026-10-19T09:00:00-03:00')
        self.assertEqual(events[1]['uid'],'rescheduled')
        self.assertNotIn(PAT,request.call_args.args[0]);self.assertTrue(request.call_args.args[0].startswith('https://api.calendly.com/scheduled_events?'))

    def test_calendly_foreign_pagination_uri_query_and_loop_refused(self):
        for next_page in ['https://evil.invalid/scheduled_events?page_token=next','https://api.calendly.com/scheduled_events?page_token=next&token=bad','https://api.calendly.com/users/me?page_token=next','https://api.calendly.com/scheduled_events?page_token=next&user=other']:
            with self.subTest(next_page=next_page),patch.object(http,'request_json',return_value=dict(collection=[],pagination={'next_page':next_page})) as request:
                with self.assertRaises(CalendarError):calendly_client.CalendlyClient(PAT).events(CCAL,'account','2026-10')
                self.assertEqual(request.call_count,1)
        with patch.object(http,'request_json',return_value=dict(collection=[],pagination={'next_page_token':'loop'})):
            with self.assertRaises(CalendarError):calendly_client.CalendlyClient(PAT).events(CCAL,'account','2026-10')

    def test_urls_descriptions_credentials_not_persisted_in_normalized_events(self):
        item=google_event(description='secret link '+REFRESH,location='https://meet.invalid/?pass=secret',access_token=ACCESS)
        value=normalized.google(item,'account',GCAL)
        self.assertEqual(value['description'],'');self.assertEqual(value['location'],'')
        self.assertNotIn(REFRESH,json.dumps(value));self.assertNotIn(ACCESS,json.dumps(value))


class FakeVault:
    def __init__(self):self.data={};self.cancel_on_put=None
    def put(self,provider,identity,payload):
        self.data[(provider,identity)]=copy.deepcopy(payload)
        if self.cancel_on_put:self.cancel_on_put.set()
    def get(self,provider,identity):return copy.deepcopy(self.data[(provider,identity)])
    def delete(self,provider,identity):self.data.pop((provider,identity),None)


class AccountLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.base=Path(self.temporary.name);self.vault=FakeVault()
        for target,name,value in [(external_store,'PATH',self.base/'data/external-calendars.json'),(accounts,'LOCK_ROOT',self.base/'data/locks'),(accounts,'_ACCESS',{})]:
            patcher=patch.object(target,name,value);patcher.start();self.addCleanup(patcher.stop)
        patcher=patch.object(accounts,'ProviderVault',return_value=self.vault);patcher.start();self.addCleanup(patcher.stop)
        self.credentials=dict(config=CLIENT,refresh_token=REFRESH,scope=SCOPES,access_token=ACCESS,expires_at=time.time()+3600)

    def connect_google(self):
        with patch.object(oauth,'authorize',return_value=self.credentials),patch.object(accounts.GoogleClient,'discover',return_value=[GCAL]):return accounts.connect_google('provided-client.json','Google teste')

    def test_connect_cache_and_disconnect_never_write_secrets_or_mutate_local_tasks(self):
        account=self.connect_google()
        notes=self.base/'data/notes.json';store.modify(dict(action='task',text='Local',date='2026-10-19'),notes);before=notes.read_bytes()
        external_store.put_cache(account['id'],GCAL,'2026-10',[], '2026-10-19T12:00:00+00:00')
        raw=external_store.PATH.read_text()
        for value in (ACCESS,REFRESH,CLIENT['client_secret'],'provided-client.json'):self.assertNotIn(value,raw)
        payload=self.vault.get('google',account['id']);self.assertNotIn('access_token',payload)
        accounts.disconnect(account)
        self.assertEqual(external_store.read(),{'accounts':[],'cache':{}});self.assertEqual(self.vault.data,{})
        self.assertEqual(notes.read_bytes(),before);self.assertNotIn(account['id'],accounts._ACCESS)

    def test_refresh_serialized_preserves_rotated_grant_on_cancel(self):
        account=self.connect_google();accounts._ACCESS.clear()
        cancel=threading.Event();self.vault.cancel_on_put=cancel
        renewed=dict(self.credentials,refresh_token='rotated-refresh-SENTINEL')
        with patch.object(oauth,'refresh',return_value=renewed):
            with self.assertRaises(CalendarError):accounts.events(account,GCAL,'2026-10',cancel_event=cancel)
        self.assertEqual(self.vault.get('google',account['id'])['refresh_token'],'rotated-refresh-SENTINEL')
        self.assertNotIn(account['id'],accounts._ACCESS)

    def test_cancel_and_store_failure_cleanup_vault_without_deleting_existing_credentials(self):
        cancel=threading.Event();self.vault.cancel_on_put=cancel
        with patch.object(oauth,'authorize',return_value=self.credentials),patch.object(accounts.GoogleClient,'discover',return_value=[GCAL]):
            with self.assertRaises(CalendarError):accounts.connect_google('provided','Fixture',cancel_event=cancel)
        self.assertEqual(self.vault.data,{});self.assertEqual(external_store.read()['accounts'],[])
        self.vault.cancel_on_put=None
        with patch.object(oauth,'authorize',return_value=self.credentials),patch.object(accounts.GoogleClient,'discover',return_value=[GCAL]),patch.object(external_store,'add_account',side_effect=OSError('synthetic store failure')):
            with self.assertRaises(OSError):accounts.connect_google('provided','Fixture')
        self.assertEqual(self.vault.data,{})
        account=self.connect_google();existing=copy.deepcopy(self.vault.data)
        with self.assertRaises(CalendarError):self.connect_google()
        self.assertEqual(self.vault.data,existing)

    def test_pat_saved_only_after_validation_and_failed_sync_keeps_cache(self):
        with patch.object(accounts.CalendlyClient,'discover',side_effect=CalendarError('Denied')):
            with self.assertRaises(CalendarError):accounts.connect_calendly(PAT,'Fixture')
        self.assertEqual(self.vault.data,{})
        with patch.object(accounts.CalendlyClient,'discover',return_value=[CCAL]):account=accounts.connect_calendly(PAT,'Fixture')
        external_store.put_cache(account['id'],CCAL,'2026-10',[], '2026-10-19T12:00:00+00:00');before=external_store.PATH.read_bytes()
        with patch.object(accounts.CalendlyClient,'events',side_effect=CalendarError('Pagination failed')):
            with self.assertRaises(CalendarError):accounts.events(account,CCAL,'2026-10')
        self.assertEqual(external_store.PATH.read_bytes(),before);self.assertNotIn(PAT,before.decode())

    def test_concurrent_calendar_sync_refreshes_once_without_losing_grant(self):
        account=self.connect_google();accounts._ACCESS.clear();results=[];errors=[]
        renewed=dict(self.credentials,refresh_token='rotated-refresh-SENTINEL')
        def refresh(*args,**kwargs):time.sleep(.025);return renewed
        def worker():
            try:results.append(accounts.events(account,GCAL,'2026-10'))
            except Exception as error:errors.append(error)
        with patch.object(oauth,'refresh',side_effect=refresh) as refreshed,patch.object(accounts.GoogleClient,'events',return_value=[]):
            jobs=[threading.Thread(target=worker) for _ in range(3)]
            for job in jobs:job.start()
            for job in jobs:job.join(timeout=3)
            self.assertEqual(errors,[]);self.assertEqual(results,[[],[],[]]);self.assertEqual(refreshed.call_count,1)
        self.assertEqual(self.vault.get('google',account['id'])['refresh_token'],'rotated-refresh-SENTINEL')

    def test_google_and_calendly_events_import_as_tasks_without_touching_hours(self):
        path=self.base/'notes.json'
        for provider in ('google','calendly'):
            key=hashlib.sha256(provider.encode()).hexdigest()
            source=dict(provider=provider,key=key,account_id='fixture',calendar_id='fixture',calendar_name='Fixture',uid='fixture',occurrence='single',start='2026-10-19T09:00:00-03:00',end='2026-10-19T10:00:00-03:00',all_day=False)
            value=store.modify(dict(action='external_task',source=source,text='Importação explícita',date='2026-10-19'),path)
        self.assertEqual(len(value['tasks']),2);self.assertEqual(value['timesheets'][0]['timesheet'],[])


if __name__=='__main__':unittest.main()

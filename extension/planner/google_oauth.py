"""Google Desktop authorization using browser, loopback, state and S256 PKCE."""
import base64
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import os
from pathlib import Path
import secrets
import stat
import time
from urllib.parse import urlencode,urlsplit,parse_qs
import webbrowser
import calendar_http as http
from calendar_events import CalendarError

SCOPES=('https://www.googleapis.com/auth/calendar.calendarlist.readonly','https://www.googleapis.com/auth/calendar.events.readonly')
AUTH_URL='https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL='https://oauth2.googleapis.com/token'


def load_config(path):
    try:
        fd=os.open(Path(path),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError()
            raw=stream.read(32769)
        if len(raw)>32768:raise ValueError()
        data=json.loads(raw)['installed']
        import re
        if not isinstance(data,dict) or not isinstance(data.get('client_id'),str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,200}\.apps\.googleusercontent\.com',data['client_id']):raise ValueError()
        if data.get('token_uri',TOKEN_URL)!=TOKEN_URL or data.get('auth_uri',AUTH_URL) not in (AUTH_URL,'https://accounts.google.com/o/oauth2/auth'):raise ValueError()
        result=dict(client_id=data['client_id'])
        if data.get('client_secret'):result['client_secret']=http.secret(data['client_secret'])
        return result
    except (OSError,ValueError,KeyError,TypeError):raise CalendarError('Selecione o JSON de um cliente OAuth Google do tipo Desktop válido.') from None


class Loopback:
    def __init__(self):
        self.state=secrets.token_urlsafe(32)
        self.verifier=secrets.token_urlsafe(64)
        self.code=None;self.denied=False
        owner=self
        class Server(HTTPServer):
            def get_request(self):
                sock,address=super().get_request();sock.settimeout(2);return sock,address
            def handle_error(self,*args):pass
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                valid=False;code=None;denied=False
                try:
                    part=urlsplit(self.path)
                    query=parse_qs(part.query,max_num_fields=10,keep_blank_values=True)
                    host='127.0.0.1:'+str(owner.server.server_port)
                    if self.client_address[0]!='127.0.0.1' or self.headers.get('Host')!=host or part.path!='/' or part.scheme or part.netloc or part.fragment or len(self.path)>8192:raise ValueError()
                    state=query.get('state',[])
                    if len(state)!=1 or not secrets.compare_digest(state[0],owner.state):raise ValueError()
                    if 'error' in query:
                        denied=True;valid=True
                    elif len(query.get('code',[]))==1 and 0<len(query['code'][0])<=4096:
                        code=http.secret(query['code'][0]);valid=True
                except (ValueError,TypeError):pass
                message=('Autorização recebida. Pode fechar esta página.' if valid else 'Resposta de autorização inválida.').encode('utf-8')
                self.send_response(200 if valid else 400)
                self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(message)))
                self.send_header('Cache-Control','no-store');self.send_header('Referrer-Policy','no-referrer');self.end_headers()
                self.wfile.write(message)
                if valid:owner.code=code;owner.denied=denied
        self.server=Server(('127.0.0.1',0),Handler)
        self.server.timeout=.2
        self.redirect_uri='http://127.0.0.1:'+str(self.server.server_port)+'/'

    def authorization_url(self,config):
        challenge=base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode('ascii')).digest()).rstrip(b'=').decode('ascii')
        return AUTH_URL+'?'+urlencode(dict(client_id=config['client_id'],redirect_uri=self.redirect_uri,response_type='code',scope=' '.join(SCOPES),state=self.state,code_challenge=challenge,code_challenge_method='S256',access_type='offline',prompt='consent'))

    def wait(self,cancel_event=None,timeout=180):
        if not isinstance(timeout,(int,float)) or not 0<timeout<=300:raise CalendarError('Tempo de autorização inválido.')
        deadline=time.monotonic()+timeout
        while self.code is None and not self.denied:
            http.cancelled(cancel_event)
            if time.monotonic()>=deadline:raise CalendarError('Autorização Google expirou; tente novamente.')
            self.server.handle_request()
        http.cancelled(cancel_event)
        if self.denied:raise CalendarError('A autorização Google não foi concedida.')
        result=self.code;self.code=None
        return result

    def close(self):self.server.server_close();self.code=None;self.state='';self.verifier=''


def _tokens(response,previous=None):
    previous=previous or {}
    try:
        access=http.secret(response['access_token'])
        refresh=http.secret(response.get('refresh_token') or previous['refresh_token'])
        scopes=response.get('scope',previous.get('scope',''))
        if response.get('token_type','').lower()!='bearer' or not isinstance(scopes,str) or not set(SCOPES)<=set(scopes.split()):raise ValueError()
        expires=response.get('expires_in')
        if type(expires) is not int or not 30<=expires<=86400:raise ValueError()
        return dict(access_token=access,refresh_token=refresh,scope=scopes,expires_at=time.time()+expires)
    except (ValueError,KeyError,TypeError,AttributeError):raise CalendarError('Autorização Google incompleta; conceda os dois escopos de leitura e tente novamente.') from None


def authorize(config_path,*,cancel_event=None,open_browser=None):
    config=load_config(config_path);http.cancelled(cancel_event)
    try:flow=Loopback()
    except OSError:raise CalendarError('Não foi possível abrir o retorno local OAuth. Verifique as permissões de rede local.') from None
    try:
        try:opened=(open_browser or webbrowser.open)(flow.authorization_url(config))
        except Exception:raise CalendarError('Não foi possível abrir o navegador para autorizar o Google.') from None
        if opened is False:raise CalendarError('Não foi possível abrir o navegador para autorizar o Google.')
        code=flow.wait(cancel_event)
        form=dict(config,code=code,code_verifier=flow.verifier,redirect_uri=flow.redirect_uri,grant_type='authorization_code')
        result=_tokens(http.request_json(TOKEN_URL,host='oauth2.googleapis.com',path_prefix='/token',form=form,cancel_event=cancel_event))
        http.cancelled(cancel_event)
        return dict(result,config=config)
    finally:flow.close()


def refresh(payload,*,cancel_event=None):
    try:
        config=payload['config']
        if not isinstance(config,dict):raise ValueError()
        form=dict(client_id=http.secret(config['client_id']),refresh_token=http.secret(payload['refresh_token']),grant_type='refresh_token')
        if config.get('client_secret'):form['client_secret']=http.secret(config['client_secret'])
    except (KeyError,TypeError,ValueError):raise CalendarError('Autorização Google no cofre inválida; reconecte a conta.') from None
    result=_tokens(http.request_json(TOKEN_URL,host='oauth2.googleapis.com',path_prefix='/token',form=form,cancel_event=cancel_event),payload)
    return dict(result,config=dict(config))

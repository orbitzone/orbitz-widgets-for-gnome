"""Bounded fixed-host calendar HTTP; credentials only in headers/form, never errors."""
import json
import time
from urllib.error import HTTPError,URLError
from urllib.parse import urlsplit,urlencode
from urllib.request import Request,build_opener,HTTPRedirectHandler
from calendar_events import CalendarError

MAX_PAGES=20
MAX_ITEMS=10000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def cancelled(event):
    if event is not None and event.is_set():raise CalendarError('Conexão cancelada.')


def secret(value):
    if not isinstance(value,str) or not 0<len(value)<=16384 or any(ord(c)<33 or ord(c)>126 for c in value):
        raise CalendarError('Credencial inválida; informe o valor completo sem espaços.')
    return value


def checked_url(url,host,path_prefix):
    try:
        part=urlsplit(url)
        if part.scheme!='https' or part.hostname!=host or part.port not in (None,443) or part.username or part.password or part.fragment or not part.path.startswith(path_prefix):raise ValueError()
        if any(ord(c)<33 for c in url):raise ValueError()
    except (TypeError,ValueError):raise CalendarError('Endereço de calendário inválido; consulta recusada.') from None
    return part


def request_json(url,*,host,path_prefix,bearer=None,form=None,cancel_event=None,timeout=15,limit=2*1024*1024):
    cancelled(cancel_event);checked_url(url,host,path_prefix)
    headers={'Accept':'application/json','User-Agent':'OrbitzCalendar/1.0'}
    if bearer is not None:headers['Authorization']='Bearer '+secret(bearer)
    body=None
    if form is not None:
        if host!='oauth2.googleapis.com' or url!='https://oauth2.googleapis.com/token':raise CalendarError('Escrita remota não permitida.')
        body=urlencode(form).encode('ascii');headers['Content-Type']='application/x-www-form-urlencoded'
    request=Request(url,data=body,headers=headers,method='POST' if form is not None else 'GET')
    try:
        with build_opener(NoRedirect()).open(request,timeout=timeout) as response:
            raw=response.read(limit+1)
        cancelled(cancel_event)
        if len(raw)>limit:raise CalendarError('Resposta do calendário excedeu o limite de leitura.')
        value=json.loads(raw)
        if not isinstance(value,dict):raise ValueError()
        return value
    except HTTPError as error:
        error.close()
        if error.code in (400,401):message='Autorização indisponível ou expirada; reconecte a conta.'
        elif error.code==403:message='Permissão recusada; confira os escopos de leitura concedidos.'
        elif error.code==429:message='Limite de consultas atingido; aguarde antes de atualizar.'
        else:message='Não foi possível consultar o calendário. Os dados locais foram preservados.'
        raise CalendarError(message) from None
    except (URLError,OSError,TimeoutError,ValueError,UnicodeError):
        raise CalendarError('Falha de conexão ou resposta inválida do calendário; dados locais preservados.') from None


def page_token(value):
    if not isinstance(value,str) or not 0<len(value)<=4096 or any(ord(c)<33 or ord(c)>126 for c in value):raise CalendarError('Paginação do calendário inválida.')
    return value


def check_page(index,deadline,count,cancel_event):
    cancelled(cancel_event)
    if index>=MAX_PAGES or time.monotonic()>deadline or count>MAX_ITEMS:
        raise CalendarError('Consulta excedeu o limite; cache anterior preservado.')

#!/usr/bin/python3
"""Small local YouTube window with official API search and embedded player."""
import html
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = Path(__file__).resolve().parent
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'orbitz-widgets'/'youtube.json'


class MissingAPIKey(ValueError):
    pass


def read_key():
    try:
        fd=os.open(CONFIG,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd) as stream:
            return json.loads(stream.read(4096)).get('key','')
    except (OSError,ValueError):
        return ''


def save_key(key):
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{20,200}',key):
        raise ValueError('Formato da chave inválido.')
    CONFIG.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(CONFIG,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        os.fchmod(stream.fileno(),0o600)
        json.dump({'key':key},stream)


def search(query=None):
    key=read_key()
    if not key: raise MissingAPIKey('Configure uma chave da API ou cole um link do YouTube.')
    options=dict(part='snippet',type='video',maxResults=8,videoEmbeddable='true',key=key)
    if query is None:
        options.update(regionCode='BR',relevanceLanguage='pt',order='viewCount',
            publishedAfter=(datetime.now(timezone.utc)-timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ'))
    else:
        options['q']=query
    params=urllib.parse.urlencode(options)
    endpoint='search'
    try:
        with urllib.request.urlopen('https://www.googleapis.com/youtube/v3/'+endpoint+'?'+params,timeout=10) as response:
            raw=response.read(262145)
        if len(raw)>262144: raise ValueError('Resposta muito grande.')
        data=json.loads(raw)
    except urllib.error.HTTPError as error:
        if error.code==403: raise ValueError('Consulta recusada: confira a chave, a ativação da API e a quota diária.') from None
        raise ValueError('O YouTube não conseguiu concluir a busca.') from None
    except (OSError,ValueError):
        raise ValueError('Não foi possível consultar o YouTube. Verifique a conexão.') from None
    items=[]
    for item in data.get('items',[])[:16]:
        identity=item.get('id',{}).get('videoId','')
        if not re.fullmatch(r'[\w-]{11}',identity):continue
        snippet=item.get('snippet',{})
        items.append(dict(id=identity,title=html.unescape(snippet.get('title',''))[:300],channel=html.unescape(snippet.get('channelTitle',''))[:200],thumbnail='https://i.ytimg.com/vi/'+identity+'/default.jpg'))
        if len(items)>=8:break
    return items


def recommendations():
    cache_path=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'orbitz-widgets'/'youtube-suggestions.json'
    try:
        cached=json.loads(cache_path.read_text())
        if 0<=time.time()-cached['time']<21600 and isinstance(cached['items'],list) and cached['items']:
            return cached['items']
    except (OSError,ValueError,KeyError,TypeError):
        pass
    items=search()
    try:
        cache_path.parent.mkdir(parents=True,exist_ok=True)
        temporary=cache_path.with_name('youtube-suggestions-'+secrets.token_hex(8)+'.tmp')
        temporary.write_text(json.dumps({'time':time.time(),'items':items}))
        os.replace(temporary,cache_path)
    except OSError:
        pass
    return items


def comments(video, page=''):
    if not isinstance(video,str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}',video):
        raise ValueError('Selecione um vídeo válido para ver os comentários.')
    if not isinstance(page,str) or len(page)>1024:
        raise ValueError('Página de comentários inválida.')
    key=read_key()
    if not key:raise MissingAPIKey('Configure uma chave da API para carregar os comentários.')
    options=dict(part='snippet',videoId=video,maxResults=20,order='relevance',textFormat='plainText',key=key)
    if page:options['pageToken']=page
    try:
        with urllib.request.urlopen('https://www.googleapis.com/youtube/v3/commentThreads?'+urllib.parse.urlencode(options),timeout=10) as response:
            raw=response.read(1048577)
        if len(raw)>1048576:raise ValueError('Resposta de comentários muito grande.')
        data=json.loads(raw)
    except urllib.error.HTTPError as error:
        try:reasons={item.get('reason') for item in json.loads(error.read(65536)).get('error',{}).get('errors',[])}
        except (OSError,ValueError,TypeError,AttributeError):reasons=set()
        if 'commentsDisabled' in reasons:raise ValueError('Os comentários estão desativados neste vídeo.') from None
        if reasons & {'quotaExceeded','dailyLimitExceeded'}:
            raise ValueError('A quota para carregar comentários foi excedida. A busca e a reprodução podem continuar funcionando.') from None
        if error.code==404:raise ValueError('Este vídeo não está disponível para consulta de comentários.') from None
        raise ValueError('O YouTube não permitiu carregar os comentários. Tente novamente mais tarde.') from None
    except (OSError,ValueError):
        raise ValueError('Não foi possível carregar os comentários. Verifique a conexão.') from None
    items=[]
    for item in data.get('items',[])[:20]:
        snippet=item.get('snippet',{}).get('topLevelComment',{}).get('snippet',{})
        items.append(dict(author=snippet.get('authorDisplayName','')[:200],text=snippet.get('textDisplay','')[:20000],
            likes=snippet.get('likeCount',0),published=snippet.get('publishedAt','')))
    return dict(items=items,nextPage=data.get('nextPageToken',''))


def make_handler(token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,status,body,kind='application/json'):
            raw=body if isinstance(body,bytes) else json.dumps(body,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('Referrer-Policy','strict-origin-when-cross-origin');self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if self.path!='/'+token+'/':self.reply(404,{});return
            self.reply(200,(BASE/'index.html').read_bytes(),'text/html')
        def do_POST(self):
            action=self.path.removeprefix('/'+token+'/')
            origin='http://127.0.0.1:'+str(self.server.server_port)
            if not self.path.startswith('/'+token+'/') or self.headers.get('Origin')!=origin:
                self.reply(403,{'error':'Origem inválida.'});return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=4096:raise ValueError('Requisição inválida.')
                data=json.loads(self.rfile.read(length))
                if action=='key':
                    save_key(data.get('key'));self.server.cache.clear();self.reply(200,{'saved':True})
                elif action=='recommendations':
                    cache=self.server.cache.get(None)
                    if not cache or time.time()-cache[0]>900:
                        cache=(time.time(),recommendations());self.server.cache[None]=cache
                    self.reply(200,{'items':cache[1]})
                elif action=='comments':
                    video=data.get('video');page=data.get('page','')
                    # Validate before using user input as a cache key.
                    if not isinstance(video,str) or not isinstance(page,str):raise ValueError('Consulta de comentários inválida.')
                    cache_store=getattr(self.server,'comment_cache',{})
                    identity=(video,page);cached=cache_store.get(identity)
                    if not cached or time.time()-cached[0]>300:
                        cached=(time.time(),comments(video,page))
                        if len(cache_store)>=30:cache_store.clear()
                        cache_store[identity]=cached
                    self.server.comment_cache=cache_store
                    self.reply(200,cached[1])
                elif action=='search':
                    query=data.get('query')
                    if not isinstance(query,str) or not 0<len(query.strip())<=300:raise ValueError('Busca inválida.')
                    cache=self.server.cache.get(query)
                    if not cache or time.time()-cache[0]>300:
                        cache=(time.time(),search(query));self.server.cache={k:v for k,v in self.server.cache.items() if k is None};self.server.cache[query]=cache
                    self.reply(200,{'items':cache[1]})
                else:self.reply(404,{})
            except (ValueError,TypeError,OSError):
                import sys
                error=sys.exc_info()[1]
                self.reply(400,{'error':str(error)[:250],'code':'key_required' if isinstance(error,MissingAPIKey) else 'request_failed'})
    return Handler


def main():
    import gi
    gi.require_version('Gtk','3.0');gi.require_version('WebKit2','4.0')
    from gi.repository import Gtk,WebKit2,Gio,Gdk
    app=Gtk.Application(application_id='io.orbitz.YouTubeWidget',flags=Gio.ApplicationFlags.FLAGS_NONE)
    holder={}
    def activate(app):
        if 'window' in holder:holder['window'].present();return
        token=secrets.token_urlsafe(24)
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(token));server.cache={};server.daemon_threads=True
        threading.Thread(target=server.serve_forever,daemon=True).start()
        window=Gtk.ApplicationWindow(application=app,title='YouTube · Orbitz')
        display=Gdk.Display.get_default()
        monitor=display.get_monitor_at_point(*display.get_default_seat().get_pointer().get_position()[1:]) or display.get_primary_monitor()
        area=monitor.get_workarea() if monitor else Gdk.Rectangle(x=0,y=0,width=1280,height=900)
        window.set_default_size(min(1100,max(320,area.width-48)),min(1250,max(400,area.height-64)))
        window.set_resizable(True)
        view=WebKit2.WebView();view.get_settings().set_property('enable-developer-extras',False)
        view.get_settings().set_media_playback_requires_user_gesture(False)
        def policy(view,decision,kind):
            if kind==WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
                uri=decision.get_navigation_action().get_request().get_uri()
                if uri.startswith('https://'):Gio.AppInfo.launch_default_for_uri(uri,None)
                decision.ignore();return True
            return False
        view.connect('decide-policy',policy)
        def enter_fullscreen(*_):
            window.fullscreen()
            return True
        def leave_fullscreen(*_):
            window.unfullscreen()
            return True
        view.connect('enter-fullscreen',enter_fullscreen)
        view.connect('leave-fullscreen',leave_fullscreen)
        def key_press(_window,event):
            if event.keyval==Gdk.KEY_F11:
                state=window.get_window().get_state()
                window.unfullscreen() if state & Gdk.WindowState.FULLSCREEN else window.fullscreen()
                return True
            if event.keyval==Gdk.KEY_Escape and window.get_window().get_state() & Gdk.WindowState.FULLSCREEN:
                view.run_javascript('if(document.fullscreenElement)document.exitFullscreen();',None,None,None)
                window.unfullscreen()
                return False
            return False
        window.connect('key-press-event',key_press)
        def terminated(_view,reason):
            window.unfullscreen()
            dialog=Gtk.MessageDialog(transient_for=window,modal=True,message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,text='O player de vídeo foi interrompido.')
            dialog.format_secondary_text('Reabrir o player? Sua chave permanece salva. Você pode usar F11 para ampliar a janela.')
            if dialog.run()==Gtk.ResponseType.OK:view.reload()
            dialog.destroy()
        view.connect('web-process-terminated',terminated)
        window.add(view);view.load_uri(f'http://127.0.0.1:{server.server_port}/{token}/')
        window.connect('destroy',lambda *_:(server.shutdown(),holder.clear()))
        holder['window']=window;window.show_all()
    app.connect('activate',activate);app.run(None)

if __name__=='__main__':main()

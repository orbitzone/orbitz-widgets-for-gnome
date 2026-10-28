#!/usr/bin/python3
"""GTK/WebKit YouTube window and local server lifecycle."""
from http.server import ThreadingHTTPServer
from ui_language import ui
import json
import re
import secrets
import sys
import threading
import urllib.parse
from youtube_server import make_handler

MAX_NATIVE_BRIDGE_PAYLOAD_CHARS = 4096

def target_window_height(state, workarea_height):
    """Return a compact, monitor-bounded height for a page layout state."""
    # Keep enough room for four search results even before the dropdown opens.
    preferred = {'idle': 520, 'settings': 320, 'panel': 520, 'player': 700}
    if state not in preferred:
        raise ValueError('Estado de janela inválido.')
    workarea_height=max(1,int(workarea_height))
    available = max(96, workarea_height - 64)
    return min(preferred[state], available, workarea_height)

def user_resized_from_target(current_height, target_height, programmatic=False):
    """Detect deliberate height changes without mistaking our resize for one."""
    return target_height is not None and not programmatic and abs(current_height-target_height)>8

def bridge_value(result, token):
    """Return a native bridge value only when its per-window token matches."""
    try:
        raw = result.get_js_value().to_string()
    except (AttributeError, TypeError, ValueError):
        return None
    if not isinstance(raw, str) or len(raw) > MAX_NATIVE_BRIDGE_PAYLOAD_CHARS:
        return None
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict) or set(payload) != {'token', 'value'}:
        return None
    supplied = payload.get('token')
    if not isinstance(supplied, str) or not supplied.isascii():
        return None
    try:
        if not secrets.compare_digest(supplied, token):
            return None
    except TypeError:
        return None
    return payload['value']

def external_uri_allowed(uri):
    """Allow only fixed Orbitz/Google links and validated YouTube pages."""
    if not isinstance(uri, str):
        return False
    try:
        parsed = urllib.parse.urlsplit(uri)
        if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port or parsed.fragment:
            return False
    except ValueError:
        return False
    if parsed.netloc == 'www.orbit.zone':
        return parsed.path == '/' and not parsed.query
    if parsed.netloc == 'console.cloud.google.com':
        return parsed.path == '/apis/credentials' and not parsed.query
    if parsed.netloc == 'www.youtube.com':
        if parsed.path == '/' and not parsed.query:
            return True
        if parsed.path != '/watch':
            return False
        try:
            query = urllib.parse.parse_qs(parsed.query, strict_parsing=True)
        except ValueError:
            return False
        video_ids = query.get('v', [])
        return set(query) == {'v'} and len(video_ids) == 1 and bool(re.fullmatch(r'[A-Za-z0-9_-]{11}', video_ids[0]))
    return False

def main():
    import gi
    gi.require_version('Gtk','3.0');gi.require_version('WebKit2','4.0')
    from gi.repository import Gtk,WebKit2,Gio,Gdk,GLib
    app=Gtk.Application(application_id='io.orbitz.YouTubeWidget',flags=Gio.ApplicationFlags.FLAGS_NONE)
    holder={}
    def activate(app):
        if 'window' in holder:holder['window'].present();return
        token=secrets.token_urlsafe(24)
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(token));server.cache={};server.daemon_threads=True
        threading.Thread(target=server.serve_forever,daemon=True).start()
        window=ui.widget(Gtk.ApplicationWindow,application=app,title=ui.msg('youtube.window_title'))
        window.set_position(Gtk.WindowPosition.CENTER)
        display=Gdk.Display.get_default()
        monitor=display.get_monitor_at_point(*display.get_default_seat().get_pointer().get_position()[1:]) or display.get_primary_monitor()
        area=monitor.get_workarea() if monitor else Gdk.Rectangle(x=0,y=0,width=1280,height=900)
        initial_height=target_window_height('idle',area.height)
        initial_width=min(1100,max(1,area.width-48))
        window.set_default_size(initial_width,initial_height)
        window.set_resizable(True)
        resize_state={'enabled':True,'target':initial_height,'programmatic':False,'page':'idle','source':0}
        def window_size_locked():
            native=window.get_window()
            return bool(native and native.get_state() & (Gdk.WindowState.FULLSCREEN|Gdk.WindowState.MAXIMIZED))
        def workarea_height():
            try:
                screen=window.get_screen();index=screen.get_monitor_at_window(window.get_window())
                return screen.get_monitor_workarea(index).height
            except (AttributeError,TypeError,ValueError):
                return area.height
        def clear_programmatic(expected):
            if resize_state['target']==expected:resize_state['programmatic']=False
            return False
        def apply_page_size():
            resize_state['source']=0
            if not resize_state['enabled'] or window_size_locked():return False
            width,current=window.get_size();target=target_window_height(resize_state['page'],workarea_height())
            if user_resized_from_target(current,resize_state['target'],resize_state['programmatic']):
                resize_state['enabled']=False
                return False
            if abs(current-target)<=2:
                resize_state['target']=target
                return False
            resize_state['target']=target;resize_state['programmatic']=True
            window.resize(width,target)
            GLib.timeout_add(900,clear_programmatic,target)
            return False
        def request_page_size(state):
            if state not in ('idle','settings','panel','player'):return
            resize_state['page']=state
            if resize_state['source']:GLib.source_remove(resize_state['source'])
            resize_state['source']=GLib.timeout_add(90,apply_page_size)
        def configure_size(_window,event):
            if window_size_locked():return False
            if resize_state['programmatic']:
                if abs(event.height-resize_state['target'])<=3:resize_state['programmatic']=False
            elif resize_state['enabled'] and user_resized_from_target(event.height,resize_state['target']):
                resize_state['enabled']=False
            return False
        window.connect('configure-event',configure_size)
        def window_state_changed(_window,event):
            if not event.new_window_state & (Gdk.WindowState.FULLSCREEN|Gdk.WindowState.MAXIMIZED):
                request_page_size(resize_state['page'])
            return False
        window.connect('window-state-event',window_state_changed)
        content_manager=WebKit2.UserContentManager()
        content_manager.register_script_message_handler('orbitzWindow')
        content_manager.register_script_message_handler('orbitzOpenExternal')
        content_manager.register_script_message_handler('orbitzCopyLink')
        content_manager.connect('script-message-received::orbitzWindow',
            lambda _manager,result:request_page_size(bridge_value(result,token)))
        view=WebKit2.WebView.new_with_user_content_manager(content_manager)
        settings=view.get_settings()
        settings.set_property('enable-developer-extras',False)
        # WebKit disables the Fullscreen API by default; YouTube's iframe
        # button otherwise cannot emit enter-fullscreen for this GTK window.
        settings.set_property('enable-fullscreen',True)
        settings.set_media_playback_requires_user_gesture(False)
        def open_external(_manager,result):
            uri=bridge_value(result,token)
            if external_uri_allowed(uri):
                try:Gio.AppInfo.launch_default_for_uri(uri,None)
                except GLib.Error as error:print(f'Could not open YouTube link: {error}',file=sys.stderr)
        content_manager.connect('script-message-received::orbitzOpenExternal',open_external)
        def copy_youtube_link(_manager,result):
            uri=bridge_value(result,token)
            if not isinstance(uri,str) or not re.fullmatch(r'https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}',uri):return
            clipboard=Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(uri,-1)
            clipboard.store()
        content_manager.connect('script-message-received::orbitzCopyLink',copy_youtube_link)
        def policy(view,decision,kind):
            if kind==WebKit2.PolicyDecisionType.NEW_WINDOW_ACTION:
                # Never treat a popup requested inside the cross-origin player
                # as an external-app launch (the native fullscreen control is
                # handled by WebKit's fullscreen API). Outer UI links use the
                # explicit orbitzOpenExternal bridge instead.
                decision.ignore();return True
            return False
        view.connect('decide-policy',policy)
        def language_changed(*_):
            payload={'locale':ui.get_locale(),'catalog':ui._load()['pt-BR']|ui._load().get(ui.get_locale(),{})}
            view.run_javascript('window.orbitzSetLanguage && window.orbitzSetLanguage('+json.dumps(payload,ensure_ascii=True)+');',None,None,None)
        holder['language_callback']=language_changed
        unwatch_language=ui.watch(language_changed)
        view.connect('load-changed',lambda _view,event:language_changed() if event==WebKit2.LoadEvent.FINISHED else None)

        # Do not connect enter/leave-fullscreen: WebKit's default handlers
        # must own the iframe's fullscreen request and its toplevel changes.
        def key_press(_window,event):
            if event.keyval==Gdk.KEY_F11:
                state=window.get_window().get_state()
                if state & Gdk.WindowState.FULLSCREEN:
                    window.unfullscreen();request_page_size(resize_state['page'])
                else:window.fullscreen()
                return True
            if event.keyval==Gdk.KEY_Escape and window.get_window().get_state() & Gdk.WindowState.FULLSCREEN:
                view.run_javascript('if(document.fullscreenElement)document.exitFullscreen();',None,None,None)
                window.unfullscreen();request_page_size(resize_state['page'])
                return False
            return False
        window.connect('key-press-event',key_press)
        def terminated(_view,reason):
            window.unfullscreen()
            dialog=ui.widget(Gtk.MessageDialog,transient_for=window,modal=True,message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,text=ui.msg('youtube.player_interrupted'))
            ui.call(dialog,'format_secondary_text',ui.msg('youtube.reopen_player'))
            if dialog.run()==Gtk.ResponseType.OK:view.reload()
            dialog.destroy()
        view.connect('web-process-terminated',terminated)
        window.add(view);view.load_uri(f'http://127.0.0.1:{server.server_port}/{token}/')
        window.connect('destroy',lambda *_:(unwatch_language(),server.shutdown(),holder.clear()))
        holder['window']=window;window.show_all()
    app.connect('activate',activate);app.run(None)

if __name__=='__main__':main()

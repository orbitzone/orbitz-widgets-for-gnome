#!/usr/bin/python3
"""GTK/WebKit YouTube window and local server lifecycle."""
from http.server import ThreadingHTTPServer
import secrets
import threading
from youtube_server import make_handler

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

#!/usr/bin/python3
"""Independent sticky cards: no GNOME Shell imports, grabs or window manipulation."""
import signal
import sys
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gio,GLib,Gdk
from storage import Store,DATA

from card import Card

class Postits(Gtk.Application):
    def __init__(self,store=None):
        super().__init__(application_id='io.orbitz.Postits',flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.store=store;self.monitor_timer=0
        self.connect('activate',self.activate_cards)
        self.connect('startup',self.startup_cards)
        self.connect('shutdown',self.shutdown_cards)

    def startup_cards(self,*_):
        self.hold()
        quit_action=Gio.SimpleAction.new('quit',None)
        quit_action.connect('activate',lambda *_:self.safe_quit())
        self.add_action(quit_action)
        if self.store is None:
            legacy=DATA.parent/'orbitz-widgets/notes.json'
            try:self.store=Store(legacy=legacy)
            except Exception as error:
                dialog=Gtk.MessageDialog(message_type=Gtk.MessageType.ERROR,buttons=Gtk.ButtonsType.CLOSE,text='Não foi possível abrir os post-its.')
                dialog.format_secondary_text(str(error)+'\nOs arquivos foram preservados.');dialog.run();dialog.destroy();self.quit();return
        self.screen=Gdk.Screen.get_default()
        self.monitor_signal=self.screen.connect('monitors-changed',self.monitors_changed)
        self.backup_timer=GLib.timeout_add_seconds(3600,self.backup_store)
        self.term_signal=GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGTERM,lambda:self.safe_quit() or False)

    def backup_store(self):
        try:self.store.backup()
        except Exception as error:
            for card in self.get_windows():
                card.status.set_text('Não foi possível criar o backup: '+str(error));card.status.show()
        return True

    def activate_cards(self,*_):
        if not self.store:return
        windows=self.get_windows()
        if not windows:
            notes=self.store.all()
            if not notes:notes=[self.store.create()]
            for note in notes:
                card=Card(self,note);self.fit_monitor(card)
        else:
            for window in windows:window.show();window.present()

    def new_card(self,previous=None):
        x,y=previous.get_position() if previous else (100,100)
        card=Card(self,self.store.create(x+30,y+30));self.fit_monitor(card);card.present()
        return card

    def restore(self,note):
        self.store.properties(note['id'],archived=0)
        card=Card(self,self.store.get(note['id']));self.fit_monitor(card);card.present()

    def fit_monitor(self,card):
        display=Gdk.Display.get_default();rectangles=[display.get_monitor(i).get_geometry() for i in range(display.get_n_monitors())]
        if not rectangles:return
        x,y=card.get_position();width,height=card.get_size()
        def overlap(rect):return max(0,min(x+width,rect.x+rect.width)-max(x,rect.x))*max(0,min(y+height,rect.y+rect.height)-max(y,rect.y))
        rect=max(rectangles,key=overlap)
        width=min(width,rect.width);height=min(height,rect.height)
        nx=max(rect.x,min(x,rect.x+rect.width-width));ny=max(rect.y,min(y,rect.y+rect.height-height))
        if (nx,ny,width,height)!=(x,y,*card.get_size()):card.resize(width,height);card.move(nx,ny)

    def monitors_changed(self,*_):
        if self.monitor_timer:GLib.source_remove(self.monitor_timer)
        self.monitor_timer=GLib.timeout_add(500,self.fit_all)

    def fit_all(self):
        self.monitor_timer=0
        for card in self.get_windows():self.fit_monitor(card)
        return False

    def safe_quit(self):
        for card in self.get_windows():
            if not card.flush():return
            card.save_geometry()
        self.quit()

    def shutdown_cards(self,*_):
        if hasattr(self,'screen'):self.screen.disconnect(self.monitor_signal)
        if self.monitor_timer:GLib.source_remove(self.monitor_timer)
        if hasattr(self,'term_signal'):GLib.source_remove(self.term_signal)
        if hasattr(self,'backup_timer'):GLib.source_remove(self.backup_timer)
        for card in list(self.get_windows()):card.destroy()
        if self.store:self.store.close()

if __name__=='__main__':sys.exit(Postits().run(sys.argv))

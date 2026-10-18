#!/usr/bin/python3
"""Multiline editor isolated from GNOME Shell; shared locked planner storage."""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, Gdk
import store

COLORS = [('Amarelo','#ffe293'), ('Rosa','#ffd6df'), ('Verde','#d9edb5'),
          ('Azul','#cce7ff'), ('Lilás','#e5d7fa'), ('Pêssego','#ffdbb5')]

class NoteWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title='Notas rápidas · Orbitz')
        self.set_default_size(530, 480)
        self.set_size_request(350, 300)
        self.timer=0; self.dirty=False; self.loading=False; self.read_error=False
        self.history=[]; self.position=0; self.history_timer=0
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=18)
        self.add(box)
        header=Gtk.Box(spacing=8); box.pack_start(header,False,False,0)
        heading=Gtk.Label(label='NOTAS RÁPIDAS', xalign=0)
        header.pack_start(heading,True,True,0)
        save=Gtk.Button(label='Salvar'); save.connect('clicked',lambda *_:self.flush())
        header.pack_end(save,False,False,0)
        palette=Gtk.Box(spacing=5); box.pack_start(palette,False,False,0)
        for name,color in COLORS:
            button=Gtk.Button(label='●'); button.set_tooltip_text(name)
            css=Gtk.CssProvider(); css.load_from_data(f'button {{color:{color};background:#30343b;background-image:none;}}'.encode())
            button.get_style_context().add_provider(css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            button.connect('clicked',self.color_changed,color); palette.pack_start(button,False,False,0)
        self.text=Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, left_margin=14,right_margin=14,top_margin=14,bottom_margin=14)
        self.buffer=self.text.get_buffer()
        scroll=Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.text); box.pack_start(scroll,True,True,0)
        self.status=Gtk.Label(xalign=0,wrap=True); box.pack_start(self.status,False,False,0)
        hint=Gtk.Label(label='Salvamento automático · Ctrl+Z desfaz · Ctrl+Shift+Z refaz', xalign=0,wrap=True)
        box.pack_start(hint,False,False,0)
        self.css=Gtk.CssProvider()
        self.text.get_style_context().add_provider(self.css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.saved=''; self.color='#ffe293'
        try:
            data=store.modify({'action':'get'}); self.saved=data['notes'];self.color=data.get('note_color',self.color)
        except (OSError,ValueError) as error:
            self.read_error=True;self.status.set_text(str(error));self.text.set_editable(False);save.set_sensitive(False);palette.set_sensitive(False)
        self.apply_color(); self.buffer.set_text(self.saved);self.history=[self.saved]
        if not self.read_error:self.status.set_text('Tudo salvo neste computador')
        self.buffer.connect('changed',self.changed)
        self.connect('delete-event',self.on_close)
        self.connect('key-press-event',self.key_press)
        self.show_all(); self.text.grab_focus()

    def value(self):
        return self.buffer.get_text(self.buffer.get_start_iter(),self.buffer.get_end_iter(),True)

    def apply_color(self):
        if self.color not in dict(COLORS).values():self.color=COLORS[0][1]
        self.css.load_from_data(f'textview, textview text {{background-color:{self.color};color:#161616;caret-color:#161616;font:15px Sans;}}'.encode())

    def color_changed(self,_button,color):
        try:store.modify({'action':'note_color','color':color})
        except (OSError,ValueError) as error:self.status.set_text(str(error));return
        self.color=color;self.apply_color()

    def record(self):
        if self.history_timer:GLib.source_remove(self.history_timer);self.history_timer=0
        value=self.value()
        if value!=self.history[self.position]:
            self.history=self.history[:self.position+1]+[value]
            self.history=self.history[-60:];self.position=len(self.history)-1
        return False

    def changed(self,*_):
        if self.loading or self.read_error:return
        self.dirty=self.value()!=self.saved
        self.status.set_text('Salvando…' if self.dirty else 'Tudo salvo neste computador')
        if self.timer:GLib.source_remove(self.timer)
        self.timer=GLib.timeout_add(500,self.flush)
        if self.history_timer:GLib.source_remove(self.history_timer)
        self.history_timer=GLib.timeout_add(300,self.record)

    def flush(self):
        if self.timer:GLib.source_remove(self.timer);self.timer=0
        if self.read_error or not self.dirty:return False
        try:
            value=self.value()
            store.modify({'action':'notes','notes':value,'expected_notes':self.saved})
        except (OSError,ValueError) as error:
            self.status.set_text('Não foi salvo: '+str(error));return False
        self.saved=value;self.dirty=False
        self.status.set_text('Tudo salvo neste computador');return False

    def undo(self,redo=False):
        self.record();next_position=self.position+(1 if redo else -1)
        if not 0<=next_position<len(self.history):return
        self.position=next_position;self.loading=True
        self.buffer.set_text(self.history[self.position]);self.loading=False
        # Schedule save without creating another history branch.
        self.dirty=self.value()!=self.saved
        if self.timer:GLib.source_remove(self.timer)
        self.timer=GLib.timeout_add(500,self.flush)
        self.status.set_text('Salvando…' if self.dirty else 'Tudo salvo neste computador')

    def key_press(self,_window,event):
        if event.state&Gdk.ModifierType.CONTROL_MASK:
            key=Gdk.keyval_name(event.keyval).lower()
            if key=='s':self.flush();return True
            if key in ('z','y'):
                self.undo(key=='y' or bool(event.state&Gdk.ModifierType.SHIFT_MASK));return True
        return False

    def on_close(self,*_):
        self.flush()
        if self.dirty:
            self.status.set_text('A janela continua aberta porque há texto não salvo. Copie o texto ou tente Ctrl+S.');return True
        if self.history_timer:GLib.source_remove(self.history_timer);self.history_timer=0
        return False


def main():
    app=Gtk.Application(application_id='io.orbitz.StickyEditor',flags=Gio.ApplicationFlags.FLAGS_NONE)
    def activate(application):
        window=application.get_active_window() or NoteWindow(application)
        window.present()
    app.connect('activate',activate)
    return app.run(sys.argv)

if __name__=='__main__':sys.exit(main())

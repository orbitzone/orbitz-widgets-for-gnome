"""GTK sticky card editing, interaction and geometry."""
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,GLib,Gdk
from storage import COLORS

NAMES=['Amarelo','Rosa','Verde','Azul','Lilás','Pêssego']

class Card(Gtk.ApplicationWindow):
    def __init__(self,app,note):
        super().__init__(application=app,title='Sticky Notes · Orbitz')
        note=dict(note)
        display=Gdk.Display.get_default()
        for index in range(display.get_n_monitors()):
            monitor=display.get_monitor(index)
            for rect in [monitor.get_geometry(),monitor.get_workarea()]:
                if abs(note['width']-rect.width)<=2 and abs(note['height']-rect.height)<=2:
                    note.update(width=310,height=300)
        self.app=app;self.note=note;self.revision=note['revision'];self.saved=note['text']
        self.dirty=False;self.loading=False;self.history=[self.saved];self.index=0
        self.history_timer=0;self.geometry_timer=0;self.alive=True;self.pending_restore=False
        self.set_decorated(False);self.set_skip_taskbar_hint(True)
        self.set_default_size(note['width'],note['height']);self.set_size_request(220,160)
        self.set_focus_on_map(False);self.set_keep_above(bool(note['above']));self.stick()
        visual=self.get_screen().get_rgba_visual()
        if visual:self.set_visual(visual)
        self.css=Gtk.CssProvider()
        self.get_style_context().add_class('postit')
        self.get_style_context().add_provider(self.css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        outer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,margin=18);self.add(outer)
        header=Gtk.EventBox();header.set_visible_window(False)
        title=Gtk.Label(label='STICKY NOTES',xalign=0);title.get_style_context().add_class('heading')
        header.add(title)
        heading_row=Gtk.Box(spacing=8)
        heading_row.pack_start(header,True,True,0)
        self.close_button=Gtk.Button.new_from_icon_name('window-close-symbolic',Gtk.IconSize.MENU)
        self.close_button.set_relief(Gtk.ReliefStyle.NONE)
        self.close_button.set_tooltip_text('Fechar nota · o texto permanece salvo')
        self.close_button.get_accessible().set_name('Fechar nota')
        self.close_button.connect('clicked',lambda *_:self.close_requested())
        heading_row.pack_end(self.close_button,False,False,0)
        outer.pack_start(heading_row,False,False,0)
        header.set_tooltip_text('Arraste para mover · Botão direito para opções')
        header.connect('button-press-event',self.header_press)
        self.text=Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.buffer=self.text.get_buffer();self.buffer.set_text(self.saved)
        scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_width(1);scroll.set_min_content_height(1);scroll.add(self.text)
        outer.pack_start(scroll,True,True,0)
        self.status=Gtk.Label(xalign=0,wrap=True);self.status.set_no_show_all(True)
        outer.pack_start(self.status,False,False,0)
        grip=Gtk.EventBox();grip.set_visible_window(False);grip.add(Gtk.Label(label='◢',xalign=1))
        grip.set_halign(Gtk.Align.END);grip.set_tooltip_text('Arraste para redimensionar')
        outer.pack_end(grip,False,False,0);grip.connect('button-press-event',self.resize_press)
        self.apply_color()
        self.buffer.connect('changed',self.changed)
        self.text.connect('populate-popup',self.populate_popup)
        self.connect('key-press-event',self.key_press)
        self.connect('focus-out-event',lambda *_:self.flush() and False)
        self.connect('configure-event',self.configured)
        self.connect('window-state-event',self.state_changed)
        self.connect('delete-event',self.close_requested)
        self.connect('destroy',self.destroyed)
        self.move(note['x'],note['y']);self.show_all()
        # One normal GTK placement, outside the Shell process, after mapping.
        self.move(note['x'],note['y'])
        for widget in [outer,heading_row,header,title,self.close_button,self.text,scroll,self.status,grip,*grip.get_children()]:
            widget.get_style_context().add_provider(self.css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def value(self):return self.buffer.get_text(self.buffer.get_start_iter(),self.buffer.get_end_iter(),True)

    def apply_color(self):
        color=self.note['color']
        self.css.load_from_data(f'''
        window.postit {{background-color:{color};border-radius:10px;}}
        textview, textview text, label, eventbox, scrolledwindow {{background-color:transparent;color:#161616;}}
        textview {{font:15px Sans;caret-color:#161616;}}
        label.heading {{font:bold 12px Sans;}}
        button {{background:transparent;border:0;box-shadow:none;color:#161616;padding:0;min-width:18px;min-height:18px;}}
        button:hover {{background-color:rgba(0,0,0,0.08);border-radius:4px;}}
        label {{font:11px Sans;}}
        '''.encode())

    def error(self,error):self.status.set_text('Não foi salvo: '+str(error));self.status.show()

    def changed(self,*_):
        if self.loading:return
        self.dirty=self.value()!=self.saved
        # A committed transaction per text change survives an application crash.
        self.flush()
        if self.history_timer:GLib.source_remove(self.history_timer)
        self.history_timer=GLib.timeout_add(300,self.record)

    def flush(self):
        if not self.dirty:return True
        try:
            value=self.value();self.revision=self.app.store.text(self.note['id'],value,self.revision)
        except Exception as error:
            self.error(error);return False
        self.saved=value;self.dirty=False;self.status.hide();return True

    def record(self):
        if self.history_timer:GLib.source_remove(self.history_timer);self.history_timer=0
        value=self.value()
        if value!=self.history[self.index]:
            self.history=(self.history[:self.index+1]+[value])[-60:];self.index=len(self.history)-1
        return False

    def undo(self,redo=False):
        self.record();index=self.index+(1 if redo else -1)
        if not 0<=index<len(self.history):return
        self.index=index;self.loading=True;self.buffer.set_text(self.history[index]);self.loading=False
        self.dirty=self.value()!=self.saved;self.flush()

    def key_press(self,_widget,event):
        if event.state&Gdk.ModifierType.CONTROL_MASK:
            key=(Gdk.keyval_name(event.keyval) or '').lower()
            if key in ('z','y'):self.undo(key=='y' or bool(event.state&Gdk.ModifierType.SHIFT_MASK));return True
            if key=='s':self.flush();return True
            if key=='0':self.restore_size();return True
            if key=='n':self.app.new_card(self);return True
            if key=='h':
                if self.flush():self.hide()
                return True
        return False

    def header_press(self,_widget,event):
        if event.button==1:
            self.begin_move_drag(1,int(event.x_root),int(event.y_root),event.time);return True
        if event.button==3:
            menu=Gtk.Menu();self.add_options(menu);menu.show_all();menu.popup_at_pointer(event);return True
        return False

    def resize_press(self,_widget,event):
        if event.button==1:
            self.begin_resize_drag(Gdk.WindowEdge.SOUTH_EAST,1,int(event.x_root),int(event.y_root),event.time);return True
        return False

    def set_property_value(self,**values):
        try:self.app.store.properties(self.note['id'],**values)
        except Exception as error:self.error(error);return
        self.note.update(values);self.apply_color();self.set_keep_above(bool(self.note['above']))

    def populate_popup(self,_text,menu):
        menu.append(Gtk.SeparatorMenuItem());self.add_options(menu);menu.show_all()

    def add_options(self,menu):
        def item(title,callback):
            widget=Gtk.MenuItem(label=title);widget.connect('activate',lambda *_:callback());menu.append(widget)
        item('Nova nota · Ctrl+N',lambda:self.app.new_card(self))
        item('Restaurar tamanho · Ctrl+0',self.restore_size)
        colors=Gtk.Menu();parent=Gtk.MenuItem(label='Cor da nota');parent.set_submenu(colors);menu.append(parent)
        for name,color in zip(NAMES,COLORS):
            entry=Gtk.MenuItem(label=name);entry.connect('activate',lambda _,c=color:self.set_property_value(color=c));colors.append(entry)
        above=Gtk.CheckMenuItem(label='Sempre acima das outras janelas');above.set_active(bool(self.note['above']))
        above.connect('toggled',lambda widget:self.set_property_value(above=int(widget.get_active())));menu.append(above)
        item('Ocultar nota · Ctrl+H',lambda:self.hide() if self.flush() else None)
        item('Arquivar nota',self.archive)
        archived=Gtk.Menu();parent=Gtk.MenuItem(label='Restaurar nota arquivada');parent.set_submenu(archived);menu.append(parent)
        notes=self.app.store.all(True);parent.set_sensitive(bool(notes))
        for note in notes:
            entry=Gtk.MenuItem(label=(note['text'].splitlines() or ['Nota vazia'])[0][:45])
            entry.connect('activate',lambda _,n=note:self.app.restore(n));archived.append(entry)
        item('Encerrar post-its',self.app.safe_quit)

    def archive(self):
        if not self.flush():return
        try:self.app.store.properties(self.note['id'],archived=1)
        except Exception as error:self.error(error);return
        self.destroy()

    def close_requested(self,*_):
        if self.flush():self.hide()
        return True

    def expanded(self):
        window=self.get_window()
        return bool(window and window.get_state()&(Gdk.WindowState.MAXIMIZED|Gdk.WindowState.FULLSCREEN))

    def restore_size(self):
        self.pending_restore=True
        self.unmaximize();self.unfullscreen()
        if not self.expanded():
            self.pending_restore=False;self.resize(310,300)

    def state_changed(self,_window,event):
        expanded=event.new_window_state&(Gdk.WindowState.MAXIMIZED|Gdk.WindowState.FULLSCREEN)
        if self.pending_restore and not expanded:
            self.pending_restore=False;self.resize(310,300)
        return False

    def configured(self,*_):
        if self.geometry_timer:GLib.source_remove(self.geometry_timer)
        self.geometry_timer=GLib.timeout_add(400,self.save_geometry)
        return False

    def save_geometry(self):
        if self.geometry_timer:GLib.source_remove(self.geometry_timer);self.geometry_timer=0
        if self.expanded():return False
        x,y=self.get_position();width,height=self.get_size()
        try:self.app.store.properties(self.note['id'],x=x,y=y,width=width,height=height)
        except Exception as error:self.error(error)
        return False

    def destroyed(self,*_):
        self.alive=False
        for timer in [self.history_timer,self.geometry_timer]:
            if timer:GLib.source_remove(timer)
        self.history_timer=0;self.geometry_timer=0


"""GTK sticky card editing, interaction and geometry."""
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,GLib,Gdk,Gio,Pango
from storage import COLORS
from link_targets import target_at,link_at

NAMES=['Amarelo','Rosa','Verde','Azul','Lilás','Pêssego']


def editor_scroll(text):
    scroll=Gtk.ScrolledWindow();scroll.set_name('sticky-note-scroll')
    # Show the translucent scrollbar only when the content needs scrolling.
    scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC)
    scroll.set_overlay_scrolling(False)
    scroll.set_propagate_natural_height(False);scroll.set_propagate_natural_width(False)
    scroll.set_min_content_width(1);scroll.set_min_content_height(1)
    scroll.set_shadow_type(Gtk.ShadowType.NONE)
    scrollbar=scroll.get_vscrollbar();scrollbar.set_opacity(1.0)
    text.set_vscroll_policy(Gtk.ScrollablePolicy.MINIMUM)
    scroll.add(text)
    return scroll,scrollbar


def resize_grip(callback):
    grip=Gtk.EventBox();grip.set_visible_window(True);grip.set_above_child(True)
    grip.set_size_request(28,28)
    grip.set_halign(Gtk.Align.END);grip.set_valign(Gtk.Align.END)
    grip.set_margin_end(2);grip.set_margin_bottom(2)
    icon=Gtk.Label(label='◢');icon.set_halign(Gtk.Align.END);icon.set_valign(Gtk.Align.END)
    icon.set_margin_end(4);icon.set_margin_bottom(4);grip.add(icon)
    grip.set_tooltip_text('Arraste este canto para redimensionar')
    grip.get_accessible().set_name('Redimensionar nota')
    grip.connect('button-press-event',callback)
    grip.connect('realize',lambda widget:widget.get_window().set_cursor(
        Gdk.Cursor.new_from_name(widget.get_display(),'se-resize')))
    return grip


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
        self.get_style_context().add_provider(self.css,Gtk.STYLE_PROVIDER_PRIORITY_USER)
        outer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,margin=18)
        outer.set_margin_bottom(30)  # Keep the corner hit target clear of editable text.
        overlay=Gtk.Overlay();overlay.add(outer);self.add(overlay)
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
        self.text.set_name('sticky-note-text')
        self.buffer=self.text.get_buffer();self.buffer.set_text(self.saved)
        self.link_tag=self.buffer.create_tag('ctrl-link',weight=Pango.Weight.BOLD)
        self.hover_link=None
        self.link_cursor=Gdk.Cursor.new_from_name(display,'pointer')
        self.edit_cursor=Gdk.Cursor.new_from_name(display,'text')
        self.scroll,self.scrollbar=editor_scroll(self.text);scroll=self.scroll
        outer.pack_start(scroll,True,True,0)
        self.status=Gtk.Label(xalign=0,wrap=True);self.status.set_no_show_all(True)
        outer.pack_start(self.status,False,False,0)
        grip=resize_grip(self.resize_press)
        overlay.add_overlay(grip);overlay.set_overlay_pass_through(grip,False)
        self.apply_color()
        self.buffer.connect('changed',self.changed)
        self.text.connect('populate-popup',self.populate_popup)
        self.text.connect('button-press-event',self.text_press)
        self.text.add_events(Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.ENTER_NOTIFY_MASK|Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.text.connect('motion-notify-event',self.link_motion)
        self.text.connect('enter-notify-event',self.link_motion)
        self.text.connect('leave-notify-event',lambda *_:self.clear_link_hover())
        self.connect('key-release-event',self.link_key_release)
        self.text.set_tooltip_text('Ctrl+clique: abrir pasta, URL ou e-mail no aplicativo padrão')
        self.connect('key-press-event',self.key_press)
        self.connect('focus-out-event',self.focus_out)
        self.connect('configure-event',self.configured)
        self.connect('window-state-event',self.state_changed)
        self.connect('delete-event',self.close_requested)
        self.connect('destroy',self.destroyed)
        self.move(note['x'],note['y']);self.show_all()
        # One normal GTK placement, outside the Shell process, after mapping.
        self.move(note['x'],note['y'])
        for widget in [outer,heading_row,header,title,self.close_button,self.text,scroll,self.scrollbar,self.status,grip,*grip.get_children()]:
            widget.get_style_context().add_provider(self.css,Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def value(self):return self.buffer.get_text(self.buffer.get_start_iter(),self.buffer.get_end_iter(),True)

    def apply_color(self):
        color=self.note['color']
        self.css.load_from_data(f'''
        window.postit {{background-color:{color};border-radius:10px;}}
        textview, textview text, label, eventbox, scrolledwindow, viewport {{background-color:transparent;color:#161616;}}
        scrolledwindow#sticky-note-scroll, scrolledwindow#sticky-note-scroll viewport, scrolledwindow#sticky-note-scroll undershoot, scrolledwindow#sticky-note-scroll overshoot, scrolledwindow#sticky-note-scroll junction {{border:none;border-width:0;border-style:none;background-color:transparent;background-image:none;box-shadow:none;}}
        textview#sticky-note-text, textview#sticky-note-text.view, textview#sticky-note-text:focus, textview#sticky-note-text.view:focus, textview#sticky-note-text text {{border:none;border-width:0;border-style:none;border-color:transparent;background-color:transparent;background-image:none;box-shadow:none;outline:none;padding:0;}}
        scrolledwindow#sticky-note-scroll scrollbar, scrolledwindow#sticky-note-scroll scrollbar * {{opacity:1;background-color:transparent;background-image:none;border-color:transparent;box-shadow:none;}}
        scrolledwindow#sticky-note-scroll scrollbar slider {{background-color:rgba(22,22,22,0.20);border-radius:8px;}}
        scrolledwindow#sticky-note-scroll scrollbar slider:hover, scrolledwindow#sticky-note-scroll scrollbar slider:focus {{background-color:rgba(22,22,22,0.30);}}
        scrolledwindow#sticky-note-scroll scrollbar slider:active {{background-color:rgba(22,22,22,0.40);}}
        textview#sticky-note-text {{font:15px Sans;caret-color:#161616;}}
        label.heading {{font:bold 12px Sans;}}
        button {{background:transparent;border:0;box-shadow:none;color:#161616;padding:0;min-width:18px;min-height:18px;}}
        button:hover {{background-color:rgba(0,0,0,0.08);border-radius:4px;}}
        label {{font:11px Sans;}}
        '''.encode())

    def error(self,error):self.status.set_text('Não foi salvo: '+str(error));self.status.show()

    def changed(self,*_):
        if self.loading:return
        self.clear_link_hover()
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
        if Gdk.keyval_name(event.keyval) in ('Control_L','Control_R'):self.refresh_link_hover()
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

    def clear_link_hover(self):
        self.buffer.remove_tag(self.link_tag,self.buffer.get_start_iter(),self.buffer.get_end_iter())
        self.hover_link=None
        window=self.text.get_window(Gtk.TextWindowType.TEXT)
        if window:window.set_cursor(self.edit_cursor)
        return False

    def update_link_hover(self,window,x,y,control):
        link=None
        if control:
            kind=self.text.get_window_type(window)
            bx,by=self.text.window_to_buffer_coords(kind,int(x),int(y))
            found,where=self.text.get_iter_at_location(bx,by)
            if found:link=link_at(self.value(),where.get_offset())
        if link==self.hover_link:return False
        self.clear_link_hover()
        if link:
            self.buffer.apply_tag(self.link_tag,self.buffer.get_iter_at_offset(link[0]),self.buffer.get_iter_at_offset(link[1]))
            self.hover_link=link
            self.text.get_window(Gtk.TextWindowType.TEXT).set_cursor(self.link_cursor)
        return False

    def link_motion(self,_widget,event):
        return self.update_link_hover(event.window,event.x,event.y,bool(event.state&Gdk.ModifierType.CONTROL_MASK))

    def refresh_link_hover(self):
        window=self.text.get_window(Gtk.TextWindowType.TEXT)
        if window:
            pointer=self.get_display().get_default_seat().get_pointer()
            _child,x,y,_state=window.get_device_position(pointer)
            self.update_link_hover(window,x,y,True)

    def link_key_release(self,_widget,event):
        if Gdk.keyval_name(event.keyval) in ('Control_L','Control_R'):self.clear_link_hover()
        return False

    def focus_out(self,*_):
        self.clear_link_hover();self.flush()
        return False

    def text_press(self,_widget,event):
        if event.button!=1 or not event.state&Gdk.ModifierType.CONTROL_MASK:return False
        kind=self.text.get_window_type(event.window)
        x,y=self.text.window_to_buffer_coords(kind,int(event.x),int(event.y))
        found,where=self.text.get_iter_at_location(x,y)
        if not found:return False
        uri=target_at(self.value(),where.get_offset())
        if not uri:return False
        try:
            context=self.get_display().get_app_launch_context();context.set_timestamp(event.time)
            Gio.AppInfo.launch_default_for_uri(uri,context)
        except Exception:
            self.status.set_text('Não foi possível abrir o destino no aplicativo padrão.');self.status.show()
        return True

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


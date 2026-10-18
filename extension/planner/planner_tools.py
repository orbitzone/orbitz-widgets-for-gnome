"""Read-only archive viewer and recoverable backup restoration UI."""
from datetime import date
import hashlib
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
import store,timesheet as model
from timesheet_ui import Timesheet

def view_archive(window,identity,parent=None):
    latest=store.modify({'action':'get'});sheet=model.get_sheet(latest,identity)
    dialog=Gtk.Dialog(title='Consulta · TS - '+sheet['name'],transient_for=parent or window,modal=True)
    dialog.add_button('Fechar',Gtk.ResponseType.CLOSE);dialog.set_default_size(1050,650)
    dialog.data=latest;dialog.day=window.day;dialog.status=Gtk.Label(xalign=0)
    content=Gtk.Box(spacing=16,margin=16);dialog.get_content_area().pack_start(content,True,True,0)
    calendar=Gtk.Calendar();chosen=date.fromisoformat(dialog.day)
    calendar.select_month(chosen.month-1,chosen.year);calendar.select_day(chosen.day)
    left=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10);left.pack_start(calendar,False,False,0)
    left.pack_start(Gtk.Label(label='Consulta e exportação.\nPara editar, resgate a timesheet.',xalign=0),False,False,0);content.pack_start(left,False,False,0)
    page=Timesheet(dialog,identity,readonly=True);content.pack_start(page,True,True,0)
    dialog.render=page.render
    def selected(*_):
        year,month,day=calendar.get_date();dialog.day=date(year,month+1,day).isoformat();page.render()
    calendar.connect('day-selected',selected)
    def source(identity):
        task=next((t for t in latest['tasks'] if t['id']==identity),None)
        info=Gtk.MessageDialog(transient_for=dialog,modal=True,message_type=Gtk.MessageType.INFO,buttons=Gtk.ButtonsType.CLOSE,text='Tarefa original')
        info.format_secondary_text(task['text']+'\n'+task['date'] if task else 'A tarefa original foi removida; o lançamento permanece salvo.')
        info.run();info.destroy()
    dialog.open_source_task=source;page.render();dialog.show_all();dialog.run();dialog.destroy()

def open_backups(window,*_):
    dialog=Gtk.Dialog(title='Restaurar backup da agenda',transient_for=window,modal=True)
    dialog.add_buttons('Fechar',Gtk.ResponseType.CLOSE,'Restaurar selecionado',Gtk.ResponseType.OK)
    dialog.set_default_size(720,520);dialog.set_default_response(Gtk.ResponseType.CLOSE)
    box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,margin=18);dialog.get_content_area().add(box)
    box.add(Gtk.Label(label='A restauração substitui notas antigas, tarefas e todas as timesheets.\nAntes de restaurar, o estado atual também será guardado em uma cópia.',xalign=0,wrap=True))
    combo=Gtk.ComboBoxText();box.pack_start(combo,False,False,0)
    for name in store.list_backups():combo.append(name,name.removesuffix('.json'))
    scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC);box.pack_start(scroll,True,True,0)
    preview=Gtk.TextView(editable=False,cursor_visible=False,wrap_mode=Gtk.WrapMode.WORD_CHAR);scroll.add(preview)
    error=Gtk.Label(xalign=0,wrap=True);box.pack_end(error,False,False,0);selection={}
    def changed(*_):
        selection.clear();dialog.set_response_sensitive(Gtk.ResponseType.OK,False)
        name=combo.get_active_id()
        if not name:preview.get_buffer().set_text('Nenhuma cópia disponível.');return
        try:
            current=store.modify({'action':'get'});path=store.backup_file(name);raw=path.read_bytes();backup=store.read(path)
            a,b=store.summary(current),store.summary(backup)
            lines=['PRÉVIA · Atual → Cópia selecionada']
            for key,title in [('tasks','Tarefas'),('sheets','Timesheets'),('entries','Registros'),('active','Cronômetros em andamento')]:lines.append(f'{title}: {a[key]} → {b[key]}')
            lines.append('Horas: '+model.duration(a['minutes'])+' → '+model.duration(b['minutes']))
            lines.append(f"Caracteres em notas antigas: {a['notes']} → {b['notes']}")
            lines.append('\nTIMESHEETS DA CÓPIA')
            for sheet in backup['timesheets']:
                lines.append('TS - '+sheet['name']+(' [arquivada]' if sheet['archived'] else '')+f" · {len(sheet['timesheet'])} registros · "+model.duration(model.total(sheet['timesheet'])))
                for entry in sheet['timesheet'][:10]:lines.append(f"  {entry['date']} {entry['start']}–{entry['end']} · {entry['description']}")
            lines.append('\nTAREFAS DA CÓPIA')
            for task in backup['tasks'][:30]:lines.append(task['date']+' · '+task['text'])
            preview.get_buffer().set_text('\n'.join(lines))
            selection.update(name=name,expected=store.fingerprint(current),backup_hash=hashlib.sha256(raw).hexdigest())
            dialog.set_response_sensitive(Gtk.ResponseType.OK,True);error.set_text('')
        except Exception as failure:error.set_text(str(failure))
    combo.connect('changed',changed);combo.set_active(0);changed();dialog.show_all()
    while dialog.run()==Gtk.ResponseType.OK:
        if not selection:continue
        confirm=Gtk.MessageDialog(transient_for=dialog,modal=True,message_type=Gtk.MessageType.WARNING,buttons=Gtk.ButtonsType.OK_CANCEL,text='Restaurar a cópia selecionada?')
        confirm.set_default_response(Gtk.ResponseType.CANCEL)
        confirm.format_secondary_text('O histórico atual será substituído pelo conteúdo da prévia. Cronômetros presentes na cópia também serão restaurados. Uma cópia do estado atual ficará disponível para recuperação.')
        answer=confirm.run();confirm.destroy()
        if answer!=Gtk.ResponseType.OK:continue
        try:
            window.data=store.modify(dict(action='backup_restore',**selection));window.render();window.status.set_text('Backup restaurado · estado anterior preservado em uma cópia');break
        except Exception as failure:error.set_text(str(failure))
    dialog.destroy()

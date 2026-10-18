"""Review and register a completed task in a local timesheet."""
from datetime import date
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk
import store
import timesheet as timesheet_model

def register_task(window,task):
    window.refresh()
    current=next((t for t in window.data['tasks'] if t['id']==task['id']),None)
    if current is None or not current['done']:
        window.status.set_text('Esta tarefa precisa estar concluída para registrar horas.');return
    task=current
    recorded=[s for s in window.data['timesheets'] if any(e.get('source_task_id')==task['id'] for e in s['timesheet'])]
    choices=[s for s in window.data['timesheets'] if not s['archived'] and s not in recorded]
    if not choices:
        window.status.set_text('Esta tarefa já está nas timesheets disponíveis. Crie uma nova pelo + ou resgate uma arquivada.' if recorded else 'Crie uma timesheet pelo + ou resgate uma arquivada para registrar esta tarefa.')
        return
    dialog=Gtk.Dialog(title='Registrar tarefa na timesheet',transient_for=window,modal=True)
    dialog.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Registrar',Gtk.ResponseType.OK)
    dialog.set_default_size(500,280)
    box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10,margin=18);dialog.get_content_area().add(box)
    description=Gtk.Label(label=task['text'],xalign=0,wrap=True);description.set_max_width_chars(55);box.add(description)
    box.add(Gtk.Label(label='Data da tarefa: '+date.fromisoformat(task['date']).strftime('%d/%m/%Y'),xalign=0))
    if recorded:
        existing=Gtk.Label(label='Já registrada em: '+', '.join('TS - '+s['name'] for s in recorded),xalign=0,wrap=True)
        box.add(existing)
    box.add(Gtk.Label(label='Timesheet de destino',xalign=0))
    target=Gtk.ComboBoxText()
    for sheet in choices:target.append(sheet['id'],'TS - '+sheet['name'])
    box.add(target)
    grid=Gtk.Grid(column_spacing=12,row_spacing=6);box.add(grid);fields={}
    for col,(key,title) in enumerate((('start','Início · HH:MM'),('end','Fim · HH:MM'))):
        grid.attach(Gtk.Label(label=title,xalign=0),col,0,1,1)
        field=Gtk.Entry();field.set_max_length(5);field.set_width_chars(10);fields[key]=field;grid.attach(field,col,1,1,1)
    error=Gtk.Label(xalign=0,wrap=True);box.add(error)
    suggested={'start':'','end':''}
    def suggest(*_):
        sheet=next(s for s in choices if s['id']==target.get_active_id())
        last=max((e['end'] for e in sheet['timesheet'] if e['date']==task['date']),default='')
        start=task.get('time') or (last if last!='24:00' else '')
        from datetime import datetime
        original=task.get('external_source',{})
        end=original.get('end','')[11:16] if not original.get('all_day',True) and original.get('end','')[:10]==task['date'] else ''
        if not end:end=datetime.now().strftime('%H:%M') if task['date']==date.today().isoformat() else ''
        if end and start and end<=start:end=''
        for key,value in [('start',start),('end',end)]:
            if not fields[key].get_text() or fields[key].get_text()==suggested[key]:fields[key].set_text(value)
            suggested[key]=value
    target.connect('changed',suggest);target.set_active(0)
    dialog.set_default_response(Gtk.ResponseType.OK)
    for field in fields.values():field.set_activates_default(True)
    dialog.show_all();fields['start'].grab_focus()
    while dialog.run()==Gtk.ResponseType.OK:
        payload=dict(action='task_timesheet',task_id=task['id'],sheet_id=target.get_active_id(),
            start=fields['start'].get_text().strip(),end=fields['end'].get_text().strip(),
            expected_task={k:task[k] for k in ('text','date')})
        try:
            try:latest=store.modify(payload)
            except timesheet_model.OverlapError as failure:
                confirm=Gtk.MessageDialog(transient_for=dialog,modal=True,message_type=Gtk.MessageType.QUESTION,buttons=Gtk.ButtonsType.YES_NO,text='Horários sobrepostos')
                confirm.format_secondary_text(str(failure));answer=confirm.run();confirm.destroy()
                if answer!=Gtk.ResponseType.YES:continue
                latest=store.modify(dict(payload,allow_overlap=True))
            window.data=latest;window.render()
            page=window.sheet_pages[payload['sheet_id']];window.tabs.set_current_page(window.tabs.page_num(page))
            window.status.set_text('Tarefa registrada em '+target.get_active_text()+' · salvo e com backup');break
        except Exception as failure:error.set_text(str(failure))
    dialog.destroy()


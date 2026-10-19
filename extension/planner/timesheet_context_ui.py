"""Editable timesheet work context, independent of fiscal invoice recipients."""
import store

CONTEXT_FIELDS = [('client_name', 'Cliente / destinatário de trabalho (opcional)'),
    ('project_contract', 'Contrato / projeto (opcional)'),
    ('department_costcenter', 'Departamento / centro de custo (opcional)')]


def context_payload(name, values, identity=None):
    context = {key: values.get(key, '').strip() for key, _title in CONTEXT_FIELDS}
    payload = {'action': 'sheet_update' if identity else 'sheet_create', 'name': name.strip(), 'context': context}
    if identity:
        payload['sheet_id'] = identity
    return payload


def edit_context(window, sheet=None):
    from gi.repository import Gtk
    sheet = sheet or {}
    dialog = Gtk.Dialog(title='Contexto da timesheet' if sheet else 'Nova timesheet', transient_for=window, modal=True)
    dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Salvar', Gtk.ResponseType.OK)
    dialog.set_default_size(540, 420)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=18)
    dialog.get_content_area().add(box)
    fields = {}
    for key, title, value, limit in [('name', 'Nome da timesheet (obrigatório)', sheet.get('name', ''), 80),
            *[(key, title, sheet.get('context', {}).get(key, ''), 200) for key, title in CONTEXT_FIELDS]]:
        label = Gtk.Label(label=title, xalign=0, wrap=True)
        entry = Gtk.Entry(text=value, hexpand=True)
        entry.set_max_length(limit)
        entry.get_accessible().set_name(title)
        box.add(label);box.add(entry);fields[key] = entry
    box.add(Gtk.Label(label='Este contexto identifica o trabalho. Os dados fiscais do destinatário são revisados separadamente na invoice.',
        xalign=0, wrap=True))
    error = Gtk.Label(xalign=0, wrap=True)
    box.add(error)
    dialog.show_all();fields['name'].grab_focus()
    try:
        while dialog.run() == Gtk.ResponseType.OK:
            try:
                before = {value['id'] for value in window.data.get('timesheets', [])}
                window.data = store.modify(context_payload(fields['name'].get_text(),
                    {key: fields[key].get_text() for key, _title in CONTEXT_FIELDS}, sheet.get('id')))
                identity = sheet.get('id') or next(value['id'] for value in window.data['timesheets'] if value['id'] not in before)
                window.render();window.focus_sheet(identity)
                window.status.set_text('Contexto da timesheet salvo neste computador.')
                break
            except Exception as failure:
                error.set_text(str(failure))
    finally:
        dialog.destroy()

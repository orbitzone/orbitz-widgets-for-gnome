"""Workspace navigation and today's read-only overview, independent of storage."""
from datetime import date

AREAS = [('today', 'Hoje'), ('events', 'Agenda'), ('tasks', 'Tarefas'), ('hours', 'Horas'), ('invoices', 'Invoices')]


def context_text(sheet):
    context = sheet.get('context', {})
    values = [sheet['name']]
    for key, title in [('client_name', 'Cliente'), ('project_contract', 'Projeto/contrato'),
            ('department_costcenter', 'Departamento/centro de custo')]:
        if context.get(key):
            values.append(title + ': ' + context[key])
    return ' · '.join(values)


def today_text(data, events=(), today=None):
    today = today or date.today().isoformat()
    pending = [task for task in data.get('tasks', []) if not task.get('done')]
    due = [task for task in pending if task['date'] == today]
    overdue = sorted((task for task in pending if task['date'] < today), key=lambda task: task['date'])
    lines = [f'Hoje · {date.fromisoformat(today):%d/%m/%Y}', '',
        f'Compromissos na fonte selecionada (cache): {len(events)}']
    lines.extend('• ' + event.get('title', '') for event in events[:10])
    lines += ['', f'Tarefas pendentes: {len(pending)} · Hoje: {len(due)}']
    lines.extend('• ' + task['text'] for task in due[:10])
    lines += ['', f'Tarefas atrasadas: {len(overdue)}']
    lines.extend('• ' + task['date'] + ' · ' + task['text'] for task in overdue[:10])
    active = [sheet for sheet in data.get('timesheets', []) if sheet.get('timesheet_active')]
    lines += ['', f'Cronômetros em andamento: {len(active)}']
    for sheet in active:
        timer = sheet['timesheet_active']
        lines.append('• ' + sheet['name'] + ' · ' + timer['description'] + ' · desde ' + timer['started'])
    return '\n'.join(lines)


class AgendaMount:
    """External calendar UI still mounts its page through the small existing API."""
    def __init__(self, container):
        self.container = container

    def append_page(self, page, _label):
        self.container.pack_start(page, True, True, 0)
        return 0


def add_navigation(container, window):
    from gi.repository import Gtk, Pango
    title = Gtk.Label(label='Orbitz Workspace', xalign=0)
    title.get_style_context().add_class('title')
    subtitle = Gtk.Label(label='Agenda, tarefas, horas e faturamento', xalign=0, wrap=True)
    container.pack_start(title, False, False, 0)
    container.pack_start(subtitle, False, False, 0)
    stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.NONE)
    switcher = Gtk.StackSwitcher(stack=stack, halign=Gtk.Align.START)
    switcher.get_accessible().set_name('Áreas do Orbitz Workspace')
    nav_scroll = Gtk.ScrolledWindow()
    nav_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
    nav_scroll.add(switcher)
    container.pack_start(nav_scroll, False, False, 0)
    context = Gtk.Label(xalign=0, wrap=True, selectable=True)
    context.set_max_width_chars(70)
    context.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    container.pack_start(context, False, False, 0)
    container.pack_start(stack, True, True, 0)
    return stack, context


def flush_drafts(window, remove_source):
    for page in window.sheet_pages.values():
        if not page.readonly and not page.persist():
            return False
        if page.persist_timer:
            remove_source(page.persist_timer);page.persist_timer = 0
    return True


def quiesce(window, remove_source):
    # Drafts were flushed before inspect_backup; no write may follow its CAS token.
    window.restoring = True
    window.syncing_tabs = True
    for page in window.sheet_pages.values():
        page.readonly = True
        page.cleanup()
    if hasattr(window, 'external'):
        window.external.cleanup()
        window.external.executor.shutdown(wait=True, cancel_futures=True)
    if window.timer:
        remove_source(window.timer);window.timer = 0


def open_preferences(window):
    from gi.repository import Gtk
    import ui_state
    dialog = Gtk.Dialog(title='Preferências do Orbitz Workspace', transient_for=window, modal=True)
    dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Salvar', Gtk.ResponseType.OK)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=18)
    dialog.get_content_area().add(box)
    box.add(Gtk.Label(label='Área inicial do Workspace', xalign=0))
    choice = Gtk.ComboBoxText()
    for key, title in AREAS:choice.append(key, title)
    choice.set_active_id(ui_state.get('workspace-start-area','today'))
    box.add(choice);dialog.show_all()
    try:
        if dialog.run() == Gtk.ResponseType.OK:
            ui_state.set('workspace-start-area',choice.get_active_id() or 'today')
            window.status.set_text('Preferência de área inicial salva.')
    except Exception as failure:window.status.set_text(str(failure))
    finally:dialog.destroy()

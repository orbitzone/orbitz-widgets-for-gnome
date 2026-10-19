"""Calendar header actions, sharing the existing archive and backup callbacks."""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import planner_tools
import workspace_backup_ui
import workspace_ui


def add_header(container, window):
    header = Gtk.Box(spacing=8)
    window.heading = Gtk.Label(xalign=0, hexpand=True)
    header.pack_start(window.heading, True, True, 0)
    button = Gtk.MenuButton()
    button.add(Gtk.Image.new_from_icon_name('open-menu-symbolic', Gtk.IconSize.BUTTON))
    button.set_tooltip_text('Mais ações do Workspace')
    button.get_accessible().set_name('Mais ações do Workspace')
    menu = Gtk.Menu()
    actions = [
        ('Timesheets arquivadas', window.open_archived),
        ('Exportar backup completo…', lambda *_: workspace_backup_ui.export_backup(window)),
        ('Restaurar backup completo…', lambda *_: workspace_backup_ui.restore_backup(window)),
        ('Restaurar backup da agenda (legado)…', lambda *_: planner_tools.open_backups(window)),
        ('Preferências…', lambda *_: workspace_ui.open_preferences(window)),
    ]
    for label, callback in actions:
        item = Gtk.MenuItem(label=label)
        item.connect('activate', callback)
        menu.append(item)
        if label == 'Timesheets arquivadas':
            window.archived_button = item
    menu.show_all()
    button.set_popup(menu)
    header.pack_end(button, False, False, 0)
    container.pack_start(header, False, False, 0)
    return button


def update_archive_count(window):
    count = sum(bool(sheet['archived']) for sheet in window.data.get('timesheets', []))
    label = f'Timesheets arquivadas ({count})'
    window.archived_button.set_label(label)
    window.archived_button.get_accessible().set_name(label)

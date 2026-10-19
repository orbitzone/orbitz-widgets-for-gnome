"""Invoice UI workflow and menu contracts with synthetic data and no GTK session."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

PLANNER = Path(__file__).resolve().parents[1] / 'extension/planner'
sys.path.insert(0, str(PLANNER))
import invoice_ui


def values(language='pt'):
    return dict(issuer=dict(name='Emitente de teste', tax_id='00000000000'),
        client=dict(name='Cliente de teste', tax_id='00000000000000', address='Endereço sintético\nSem dados reais'),
        rate='120,50', currency='BRL', language=language, reference='INV-TESTE', issued_on='2026-10-18')


def data():
    return {'timesheets': [dict(id='sheet-a', name='Empresa de teste', archived=True,
        timesheet=[dict(description='Atividade sintética', date='2026-10-10', start='09:00', end='10:30')],
        timesheet_active={'description': 'Não faturar'})]}


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.archive = SimpleNamespace(ROOT=Path('/synthetic-managed-history'), possible_duplicates=Mock(return_value={'matches': [], 'warnings': [], 'incomplete': False}), record=Mock())
        isolated = patch.dict(sys.modules, {'invoice_history': self.archive})
        isolated.start()
        self.addCleanup(isolated.stop)

    def test_pt_en_review_export_then_profile_without_mutating_history(self):
        for language in ('pt', 'en'):
            original = data()
            before = deepcopy(original)
            session = invoice_ui.InvoiceSession(lambda: original)
            with patch.object(invoice_ui.invoice_profiles, 'save') as save:
                snapshot = session.prepare('sheet-a', values(language))
                save.assert_not_called()
                self.assertEqual((snapshot['minutes'], snapshot['hours'], snapshot['total']), (90, '01:30', '180.75'))
                self.assertEqual(snapshot['currency'], 'BRL')
                self.assertEqual(snapshot['language'], language)
                self.assertTrue(snapshot['warnings'])
                self.assertTrue(snapshot['period']['all_history'])
                writer = Mock(return_value=Path('/synthetic/invoice.pdf'))
                with patch.dict(sys.modules, {'invoice_pdf': SimpleNamespace(write=writer)}):
                    result, warning = session.export('/synthetic/invoice.pdf')
                self.assertEqual(result, Path('/synthetic/invoice.pdf'))
                self.assertEqual(warning, '')
                writer.assert_called_once_with(session.snapshot, '/synthetic/invoice.pdf', overwrite=False)
                save.assert_called_once_with('sheet-a', session.profile)
            self.assertEqual(original, before)

    def test_real_pdf_and_private_profile_round_trip_pt_en(self):
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(invoice_ui.invoice_profiles, 'PATH', Path(folder) / 'profiles.json'):
            for language in ('pt', 'en'):
                session = invoice_ui.InvoiceSession(data)
                session.prepare('sheet-a', values(language))
                destination = Path(folder) / (language + '.pdf')
                result, warning = session.export(destination)
                self.assertEqual(result, destination)
                self.assertEqual(warning, '')
                self.assertTrue(destination.read_bytes().startswith(b'%PDF-'))
                self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
                profile = invoice_ui.invoice_profiles.load('sheet-a')
                self.assertEqual(profile['language'], language)
                self.assertEqual(profile['currency'], 'BRL')
                self.assertEqual(profile['rate'], '120.50')
                self.assertEqual(profile['client']['name'], 'Cliente de teste')

    def test_invalidated_or_failed_review_never_saves_profile(self):
        session = invoice_ui.InvoiceSession(data)
        with patch.object(invoice_ui.invoice_profiles, 'save') as save:
            session.prepare('sheet-a', values())
            session.invalidate()  # Editing/cancelling a form does not persist anything.
            with self.assertRaisesRegex(ValueError, 'Revise'):
                session.export('/synthetic/invoice.pdf')
            with self.assertRaises(ValueError):
                session.prepare('sheet-a', dict(values(), rate='NaN'))
            self.assertIsNone(session.snapshot)
            save.assert_not_called()

    def test_pdf_failure_and_missing_dependency_do_not_save_profile(self):
        session = invoice_ui.InvoiceSession(data)
        session.prepare('sheet-a', values())
        with patch.object(invoice_ui.invoice_profiles, 'save') as save:
            with patch.dict(sys.modules, {'invoice_pdf': SimpleNamespace(write=Mock(side_effect=FileExistsError()))}):
                with self.assertRaises(FileExistsError):
                    session.export('/synthetic/existing.pdf')
            import builtins
            original_import = builtins.__import__
            def missing(name, *args, **kwargs):
                if name == 'invoice_pdf':
                    raise ImportError('synthetic missing dependency')
                return original_import(name, *args, **kwargs)
            with patch('builtins.__import__', side_effect=missing):
                with self.assertRaisesRegex(ValueError, 'ReportLab'):
                    session.export('/synthetic/invoice.pdf')
            with patch.dict(sys.modules, {'invoice_pdf': SimpleNamespace(write=Mock(side_effect=ImportError('reportlab')))}):
                with self.assertRaisesRegex(ValueError, 'ReportLab'):
                    session.export('/synthetic/invoice.pdf')
            save.assert_not_called()

    def test_review_is_fresh_but_export_is_frozen_and_profile_failure_is_distinct(self):
        original = data()
        session = invoice_ui.InvoiceSession(lambda: original)
        original['timesheets'][0]['timesheet'][0]['end'] = '11:00'
        snapshot = session.prepare('sheet-a', dict(values(), start='2026-10-10', end='2026-10-10'))
        self.assertEqual(snapshot['minutes'], 120)
        snapshot['minutes'] = 999
        original['timesheets'][0]['timesheet'][0]['end'] = '12:00'
        writer = Mock(return_value=Path('/synthetic/invoice.pdf'))
        with patch.dict(sys.modules, {'invoice_pdf': SimpleNamespace(write=writer)}), \
                patch.object(invoice_ui.invoice_profiles, 'save', side_effect=OSError()):
            result, warning = session.export('/synthetic/invoice.pdf', overwrite=True)
        self.assertEqual(result, Path('/synthetic/invoice.pdf'))
        self.assertIn('PDF foi salvo', warning)
        self.assertEqual(writer.call_args.args[0]['minutes'], 120)
        self.assertTrue(writer.call_args.kwargs['overwrite'])


class MenuTests(unittest.TestCase):
    def test_header_order_accessible_menu_and_original_callbacks(self):
        class Actor:
            def __init__(self, **props):
                self.children = []
                self.events = {}
                self.__dict__.update(props)
            def pack_start(self, child, *args): self.children.append(child)
            pack_end = pack_start
            def add(self, child): self.children.append(child)
            append = add
            def connect(self, event, callback): self.events[event] = callback
            def show_all(self): pass
            def get_accessible(self): return self
            def set_name(self, name): self.accessible_name = name
            def set_label(self, label): self.label = label
            def set_tooltip_text(self, text): self.tooltip = text
            def set_popup(self, popup): self.popup = popup
        gtk = SimpleNamespace(Box=Actor, Label=Actor, MenuButton=Actor, Menu=Actor, MenuItem=Actor,
            Image=SimpleNamespace(new_from_icon_name=lambda *args: Actor()), IconSize=SimpleNamespace(BUTTON=1))
        tools = SimpleNamespace(open_backups=Mock())
        backups = SimpleNamespace(export_backup=Mock(), restore_backup=Mock())
        preferences = SimpleNamespace(open_preferences=Mock())
        modules = {'gi': SimpleNamespace(require_version=lambda *args: None),
            'gi.repository': SimpleNamespace(Gtk=gtk), 'planner_tools': tools, 'workspace_backup_ui': backups, 'workspace_ui': preferences}
        spec = importlib.util.spec_from_file_location('test_planner_menu', PLANNER / 'planner_menu.py')
        menu_module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(menu_module)
        container = Actor()
        window = SimpleNamespace(open_archived=Mock())
        button = menu_module.add_header(container, window)
        self.assertEqual(container.children[0].children, [window.heading, button])
        self.assertEqual(button.accessible_name, 'Mais ações do Workspace')
        self.assertEqual([item.label for item in button.popup.children],
            ['Timesheets arquivadas', 'Exportar backup completo…', 'Restaurar backup completo…', 'Restaurar backup da agenda (legado)…', 'Preferências…'])
        for item in button.popup.children:
            item.events['activate'](item)
        backups.export_backup.assert_called_once_with(window)
        backups.restore_backup.assert_called_once_with(window)
        preferences.open_preferences.assert_called_once_with(window)
        tools.open_backups.assert_called_once_with(window)
        window.open_archived.assert_called_once()
        self.assertIs(window.archived_button, button.popup.children[0])
        window.data = {'timesheets': [{'archived': True}, {'archived': False}]}
        menu_module.update_archive_count(window)
        self.assertEqual(window.archived_button.label, 'Timesheets arquivadas (1)')
        self.assertEqual(window.archived_button.accessible_name, 'Timesheets arquivadas (1)')
        window.data['timesheets'][0]['archived'] = False
        menu_module.update_archive_count(window)
        self.assertEqual(window.archived_button.label, 'Timesheets arquivadas (0)')


if __name__ == '__main__':
    unittest.main()

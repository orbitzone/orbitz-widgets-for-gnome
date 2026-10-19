"""History UI contracts with synthetic metadata and isolated archive adapters."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

PLANNER = Path(__file__).resolve().parents[1] / 'extension/planner'
sys.path.insert(0, str(PLANNER))
from invoice_history_ui import HistorySession, group_records, describe, list_feedback
from invoice_ui import InvoiceSession


def record(identity='a' * 32, sheet='sheet-one', client='client-one', document='00000000000'):
    return dict(id=identity, client_key=client, issued_year=2026, issued_month=10,
        created_at='2026-10-19T12:00:00Z', snapshot=dict(sheet_id=sheet, sheet_name='Empresa de teste',
        client=dict(name='Mesmo nome de teste', tax_id=document), reference='INV-TESTE',
        issued_on='2026-10-19', period=dict(start='2025-01-01', end='2025-01-31', all_history=False),
        hours='01:30', total='180.75', currency='BRL', language='pt'))


class HistoryTests(unittest.TestCase):
    def test_stable_groups_keep_homonyms_and_multiple_invoices_per_issue_month(self):
        records = [record(), record('b' * 32), record('c' * 32, client='client-two', document='00000000000000'),
            record('d' * 32, sheet='sheet-two')]
        original = deepcopy(records)
        grouped = group_records(records)
        self.assertEqual(len(grouped), 2)  # Same company names, distinct timesheet identities.
        clients = grouped['sheet-one']['clients']
        self.assertEqual(len(clients), 2)
        self.assertNotEqual(clients['client-one']['label'], clients['client-two']['label'])
        self.assertEqual(len(clients['client-one']['months'][(2026, 10)]), 2)
        self.assertNotIn((2025, 1), clients['client-one']['months'])  # Services period != issue month.
        self.assertEqual(records, original)

    def test_headers_and_cancelled_delete_have_no_file_actions(self):
        archive = SimpleNamespace(list_records=Mock(return_value={'records': [record()], 'errors': []}),
            get_path=Mock(), export_copy=Mock(), delete=Mock())
        session = HistorySession(archive)
        session.reload()
        for selection in ('', None, 'company-heading'):
            self.assertIsNone(session.select(selection))
            with self.assertRaises(ValueError): session.path()
            with self.assertRaises(ValueError): session.export('/synthetic/copy.pdf')
        session.select('a' * 32)
        self.assertFalse(session.delete(confirmed=False))
        archive.delete.assert_not_called()
        archive.get_path.assert_not_called()
        archive.export_copy.assert_not_called()

    def test_actions_target_only_selected_record_and_reload_reports_corruption(self):
        archive = SimpleNamespace(list_records=Mock(return_value={'records': [record()],
            'errors': [{'id': 'bad', 'message': 'Registro inválido'}]}),
            get_path=Mock(return_value=Path('/synthetic/private.pdf')), export_copy=Mock(), delete=Mock())
        session = HistorySession(archive)
        result = session.reload()
        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(len(session.records), 1)
        session.select('a' * 32)
        self.assertEqual(session.path(), Path('/synthetic/private.pdf'))
        session.export('/synthetic/copy.pdf', overwrite=False)
        archive.export_copy.assert_called_once_with('a' * 32, '/synthetic/copy.pdf', overwrite=False)
        self.assertTrue(session.delete(confirmed=True))
        archive.delete.assert_called_once_with('a' * 32)
        self.assertIsNone(session.selected_id)
        archive.list_records.side_effect = OSError('synthetic list failure')
        with self.assertRaises(OSError): session.reload()
        self.assertEqual(session.records, {})
        self.assertIsNone(session.selected_id)

    def test_feedback_distinguishes_empty_partial_and_all_unreadable(self):
        self.assertIn('Nenhuma invoice guardada', list_feedback([], []))
        unreadable = list_feedback([], [{'message': 'Inválido'}])
        self.assertIn('Nenhuma invoice pôde ser exibida', unreadable)
        self.assertNotIn('disponíveis', unreadable)
        self.assertIn('válidas continuam disponíveis', list_feedback([record()], [{'message': 'Inválido'}]))
        self.assertIn('1 invoice(s)', list_feedback([record()], []))

    def test_details_distinguish_issue_date_from_services_period(self):
        text = describe(record())
        self.assertIn('Emissão: 2026-10-19', text)
        self.assertIn('Período dos serviços: 2025-01-01 a 2025-01-31', text)
        self.assertIn('Total: BRL 180.75', text)

    def test_export_archiving_and_profiles_are_independent_after_pdf_success(self):
        session = InvoiceSession(lambda: {})
        session.snapshot = {'synthetic': True}
        session.profile = {'synthetic': True}
        session.sheet_id = 'test-sheet'
        archive = SimpleNamespace(ROOT=Path('/synthetic-managed-history'), possible_duplicates=Mock(return_value={'matches': [], 'warnings': [], 'incomplete': False}), record=Mock(side_effect=OSError('synthetic archive failure')))
        writer = SimpleNamespace(write=Mock(return_value=Path('/synthetic/saved.pdf')))
        with patch.dict(sys.modules, {'invoice_history': archive, 'invoice_pdf': writer}), \
                patch('invoice_ui.invoice_profiles.save', side_effect=OSError('synthetic profile failure')) as save:
            path, warning = session.export('/synthetic/saved.pdf')
        self.assertEqual(path, Path('/synthetic/saved.pdf'))
        self.assertIn('histórico de invoices', warning)
        self.assertIn('próxima invoice', warning)
        archive.record.assert_called_once_with(session.snapshot, path)
        save.assert_called_once()

    def test_real_archive_adapter_round_trip_without_rendering_or_real_storage(self):
        import invoice_history
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(invoice_history, 'ROOT', Path(folder) / 'archive'), \
                patch('invoice_ui.invoice_profiles.save'):
            external = Path(folder) / 'external.pdf'
            pdf = b'%PDF-1.4\nsynthetic archive integration\n%%EOF\n'
            external.write_bytes(pdf)
            session = InvoiceSession(lambda: {'timesheets': [dict(id='test-sheet', name='Empresa sintética',
                timesheet=[dict(description='Serviço sintético', date='2026-09-01', start='09:00', end='10:00')])]})
            session.prepare('test-sheet', dict(issuer=dict(name='Emitente teste', tax_id='00000000000'),
                client=dict(name='Cliente teste', tax_id='00000000000000', address='Endereço sintético'),
                rate='100', currency='BRL', language='pt', reference='TESTE', issued_on='2026-10-19'))
            with patch.dict(sys.modules, {'invoice_pdf': SimpleNamespace(write=Mock(return_value=external))}):
                _, warning = session.export(external)
            self.assertEqual(warning, '')
            history = HistorySession(invoice_history)
            result = history.reload()
            self.assertEqual(len(result['records']), 1)
            self.assertEqual(result['errors'], [])
            saved = result['records'][0]
            self.assertEqual(len(group_records(result['records'])), 1)
            history.select(saved['id'])
            self.assertEqual(history.path().read_bytes(), pdf)
            target = Path(folder) / 'copy.pdf'
            history.export(target)
            self.assertEqual(target.read_bytes(), pdf)
            self.assertFalse(history.delete(confirmed=False))
            self.assertTrue(history.path().exists())
            history.delete(confirmed=True)
            self.assertEqual(history.reload()['records'], [])
            self.assertEqual(external.read_bytes(), pdf)
            self.assertEqual(target.read_bytes(), pdf)

    def test_managed_export_destinations_are_rejected_before_all_writes(self):
        import invoice_history
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(invoice_history, 'ROOT', Path(folder) / 'archive'):
            root = invoice_history.ROOT
            original = b'%PDF-1.4\noriginal immutable history\n%%EOF\n'
            external = Path(folder) / 'external.pdf'
            external.write_bytes(original)
            session = InvoiceSession(lambda: {'timesheets': [dict(id='test-sheet', name='Empresa sintética',
                timesheet=[dict(description='Teste', date='2026-09-01', start='09:00', end='10:00')])]})
            session.prepare('test-sheet', dict(issuer=dict(name='Teste', tax_id='00000000000'),
                client=dict(name='Teste', tax_id='00000000000000', address='Endereço sintético'),
                rate='100', currency='BRL', language='pt', reference='TESTE', issued_on='2026-10-19'))
            saved = invoice_history.record(session.snapshot, external)
            old_path = invoice_history.resolve_pdf(saved['id'])
            alias = Path(folder) / 'alias'
            alias.symlink_to(root, target_is_directory=True)
            link = Path(folder) / 'linked.pdf'
            link.symlink_to(old_path)
            targets = [old_path, root / 'new.pdf', alias / saved['id'] / 'invoice.pdf',
                root / '..' / 'outside.pdf', link]
            writer = Mock(side_effect=lambda *args, **kwargs: old_path.write_bytes(b'%PDF-corrupted'))
            with patch.dict(sys.modules, {'invoice_pdf': SimpleNamespace(write=writer)}), \
                    patch.object(invoice_history, 'record') as archive, patch('invoice_ui.invoice_profiles.save') as profiles:
                for target in targets:
                    with self.subTest(target=str(target)):
                        with self.assertRaisesRegex(ValueError, 'fora do histórico'):
                            session.export(target, overwrite=True)
                        self.assertEqual(old_path.read_bytes(), original)
                writer.assert_not_called()
                archive.assert_not_called()
                profiles.assert_not_called()
            self.assertEqual(invoice_history.get(saved['id'])['snapshot'], session.snapshot)

    def test_pdf_failure_never_archives_or_saves_profiles(self):
        session = InvoiceSession(lambda: {})
        session.snapshot = {'synthetic': True}
        session.profile = {'synthetic': True}
        session.sheet_id = 'test-sheet'
        archive = SimpleNamespace(ROOT=Path('/synthetic-managed-history'), possible_duplicates=Mock(return_value={'matches': [], 'warnings': [], 'incomplete': False}), record=Mock())
        writer = SimpleNamespace(write=Mock(side_effect=OSError('synthetic write failure')))
        with patch.dict(sys.modules, {'invoice_history': archive, 'invoice_pdf': writer}), \
                patch('invoice_ui.invoice_profiles.save') as save:
            with self.assertRaises(OSError): session.export('/synthetic/not-saved.pdf')
        archive.record.assert_not_called()
        save.assert_not_called()


if __name__ == '__main__':
    unittest.main()

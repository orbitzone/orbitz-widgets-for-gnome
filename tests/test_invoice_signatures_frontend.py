"""Manual signature flows: fixed portals, cancellation and immutable versions."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

PLANNER = Path(__file__).resolve().parents[1] / 'extension/planner'
sys.path.insert(0, str(PLANNER))
from invoice_signatures_ui import (SignatureSession, assist_sign, open_validator, version_label,
    SIGN_URL, VALIDATE_URL)
from ui_language import ui as language


class SignatureFlowTests(unittest.TestCase):
    def test_cancel_or_failed_download_never_opens_portal(self):
        launch = Mock()
        self.assertEqual(assist_sign(Mock(return_value=None), launch), (None, False))
        with self.assertRaises(OSError):
            assist_sign(Mock(side_effect=OSError('synthetic copy failure')), launch)
        launch.assert_not_called()

    def test_only_successful_copy_opens_fixed_sign_url_without_file_data(self):
        events = []
        path = Path('/synthetic/user-copy.pdf')
        def save():
            events.append('saved')
            return path
        def launch(url): events.append(url)
        self.assertEqual(assist_sign(save, launch), (path, True))
        self.assertEqual(events, ['saved', 'https://assinador.iti.br/'])
        self.assertEqual(SIGN_URL, 'https://assinador.iti.br/')
        path, opened = assist_sign(save, Mock(side_effect=OSError('synthetic browser failure')))
        self.assertEqual(path, Path('/synthetic/user-copy.pdf'))
        self.assertFalse(opened)
        self.assertEqual(assist_sign(save, Mock(return_value=False)), (path, False))

    def test_validator_never_changes_local_status_and_display_never_claims_validity(self):
        version = dict(id='b' * 32, created_at='2026-10-19T12:00:00Z', status='imported_pending_validation',
            status_label='untrusted label')
        original = deepcopy(version)
        launch = Mock()
        open_validator(launch)
        launch.assert_called_once_with('https://validar.iti.gov.br/')
        self.assertEqual(VALIDATE_URL, 'https://validar.iti.gov.br/')
        previous_locale=language.get_locale()
        self.addCleanup(language.refresh,previous_locale)
        for locale,pending in (('pt-BR','Importada — validação pendente'),
                ('en-US','Imported — validation pending')):
            with self.subTest(locale=locale):
                language.refresh(locale)
                label=version_label(version)
                self.assertIn(pending,label)
                self.assertNotIn('untrusted label',label)
                self.assertIn('bbbbbbbb',label)
                self.assertEqual(version,original)

    def test_import_confirmation_and_selection_route_only_exact_invoice_version(self):
        archive = SimpleNamespace(get_path=Mock(return_value=Path('/synthetic/original.pdf')), export_copy=Mock())
        signatures = SimpleNamespace(list_versions=Mock(return_value={'versions': [dict(id='b' * 32)], 'errors': []}),
            import_version=Mock(), resolve_pdf=Mock(return_value=Path('/synthetic/version.pdf')), export_copy=Mock())
        session = SignatureSession('a' * 32, archive, signatures)
        session.reload()
        self.assertFalse(session.select('heading'))
        with self.assertRaises(ValueError): session.path()
        with self.assertRaises(ValueError): session.export('/synthetic/no.pdf')
        session.import_pdf('/synthetic/import.pdf', confirmed=False)
        signatures.import_version.assert_not_called()
        session.import_pdf('/synthetic/import.pdf', confirmed=True)
        signatures.import_version.assert_called_once_with('a' * 32, '/synthetic/import.pdf')
        session.select('original')
        self.assertEqual(session.path(), Path('/synthetic/original.pdf'))
        session.export('/synthetic/original-copy.pdf', overwrite=False)
        archive.export_copy.assert_called_once_with('a' * 32, '/synthetic/original-copy.pdf', overwrite=False)
        session.select('b' * 32)
        self.assertEqual(session.path(), Path('/synthetic/version.pdf'))
        session.export('/synthetic/version-copy.pdf', overwrite=True)
        signatures.export_copy.assert_called_once_with('a' * 32, 'b' * 32, '/synthetic/version-copy.pdf', overwrite=True)

    def test_real_versions_preserve_bytes_original_and_guard_downloads(self):
        import invoice
        import invoice_history
        import invoice_signatures
        from invoice_history_ui import HistorySession
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(invoice_history, 'ROOT', Path(folder) / 'archive'):
            base = Path(folder)
            original = base / 'original.pdf'
            first = base / 'first.pdf'
            second = base / 'second.pdf'
            sources = {original: b'%PDF-1.4\noriginal synthetic\n%%EOF\n',
                first: b'%PDF-1.4\nfirst import no signature claim\n%%EOF\n',
                second: b'%PDF-1.4\nsecond import no signature claim\n%%EOF\n'}
            for path, raw in sources.items(): path.write_bytes(raw)
            snapshot = invoice.build_snapshot(dict(id='test-sheet', name='Teste', timesheet=[
                dict(description='Sintético', date='2026-10-01', start='10:00', end='11:00')]),
                issuer=dict(name='Teste', tax_id='00000000000'),
                client=dict(name='Teste', tax_id='00000000000000', address='Endereço sintético'),
                rate='100', reference='TESTE', issued_on='2026-10-19')
            saved = invoice_history.record(snapshot, original)
            original_path = invoice_history.get_path(saved['id'])
            original_metadata = (original_path.parent / 'metadata.json').read_bytes()
            session = SignatureSession(saved['id'])
            self.assertIsNone(session.import_pdf(first, confirmed=False))
            self.assertEqual(session.reload()['versions'], [])
            first_version = session.import_pdf(first, confirmed=True)
            second_version = session.import_pdf(second, confirmed=True)
            result = session.reload()
            self.assertEqual(len(result['versions']), 2)
            self.assertEqual(result['errors'], [])
            self.assertNotEqual(first_version['id'], second_version['id'])
            for version, source in [(first_version, first), (second_version, second)]:
                self.assertEqual(version['status'], 'imported_pending_validation')
                session.select(version['id'])
                self.assertEqual(session.path().read_bytes(), sources[source])
                copy = base / (version['id'] + '.pdf')
                session.export(copy)
                self.assertEqual(copy.read_bytes(), sources[source])
                self.assertEqual(copy.stat().st_mode & 0o777, 0o600)
                with self.assertRaises(ValueError): session.export(original_path, overwrite=True)
            self.assertEqual(original_path.read_bytes(), sources[original])
            self.assertEqual((original_path.parent / 'metadata.json').read_bytes(), original_metadata)
            history = HistorySession(invoice_history)
            history.reload()
            history.select(saved['id'])
            self.assertFalse(history.delete(confirmed=False))
            self.assertEqual(len(session.reload()['versions']), 2)
            history.delete(confirmed=True)
            self.assertFalse(original_path.exists())
            for path, raw in sources.items(): self.assertEqual(path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()

"""Visible domain exceptions preserve types/data and translate only owned text."""
import ast
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'extension/planner'))
from ui_language import ui
import invoice, invoice_profiles, invoice_history, invoice_pdf
import timesheet, store, workspace_backup, calendar_http, credential_vault
from calendar_events import CalendarError
from test_invoice_backend import PROFILE, snapshot


class DomainLocaleTests(unittest.TestCase):
    def setUp(self):
        previous = ui.get_locale()
        self.addCleanup(ui.refresh, previous)
        ui.refresh('en-US')

    def error(self, kind, function, expected):
        with self.assertRaises(kind) as result: function()
        self.assertIs(type(result.exception),kind)
        self.assertEqual(str(result.exception),expected)
        self.assertIsInstance(result.exception.args[0],str)
        return result.exception

    def test_invoice_visible_validation_preview_and_reissue_errors(self):
        self.error(ValueError,lambda:invoice.party({'name':'','tax_id':'00000000000'}), 'Name is required or too long.')
        self.error(ValueError,lambda:invoice.parse_rate('not-a-rate'), 'Use a positive rate without thousands separators, with up to two decimal places: 123,45 or 123.45.')
        self.error(ValueError,lambda:invoice.prepare({'timesheets':[]},'removed'), 'Timesheet not found. Refresh the workspace.')
        self.error(ValueError,lambda:invoice_history.get('invalid'), 'Invalid invoice record identity.')
        self.error(ValueError,lambda:invoice_pdf.write(snapshot(),Path('/tmp/not-used.txt')), 'Choose a file with a .pdf extension.')

    def test_snapshot_data_money_language_and_warnings_are_locale_independent(self):
        ui.refresh('pt-BR'); portuguese=snapshot()
        ui.refresh('en-US'); english=snapshot()
        self.assertEqual(english,portuguese)
        self.assertEqual(english['issuer'],PROFILE['issuer'])
        self.assertEqual(english['language'],'pt')
        self.assertEqual(invoice.format_money('123.45','pt'),'123,45')
        self.assertEqual(invoice.validate_snapshot(english),invoice.validate_snapshot(portuguese))

    def test_overlap_preserves_user_description_dates_and_exception_type(self):
        entry=dict(id='one',description='Data inválida. {name} ç',date='2026-10-21',start='09:00',end='10:00')
        other=dict(description='Other',date='2026-10-21',start='09:30',end='10:30')
        before=copy.deepcopy(entry)
        self.error(timesheet.OverlapError,lambda:timesheet.check_overlap([entry],other),
                   'Overlap with Data inválida. {name} ç (09:00–10:00) on 2026-10-21. Save anyway?')
        self.assertEqual(entry,before)
        self.error(ValueError,lambda:store.validate_task({'text':'','date':'2026-10-21'}),'Enter a task of up to 1000 characters.')
        ui.refresh('pt-BR')
        self.error(ValueError,lambda:timesheet.clock_minutes('invalid'),'Use o horário no formato HH:MM.')

    def test_backup_confirmation_and_symlink_errors_remain_distinct(self):
        self.error(ValueError,lambda:workspace_backup.restore_backup('not-used.zip'),
                   'Confirm restoration with the interface closed and operations stopped.')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);real=root/'real';real.mkdir();link=root/'link';link.symlink_to(real,target_is_directory=True)
            self.error(ValueError,lambda:workspace_backup._directory(link),'Symlinked data directory refused.')
            self.assertEqual(list(real.iterdir()),[])

    def test_provider_errors_translate_fixed_messages_without_remote_details(self):
        secret='REMOTE_SECRET_SENTINEL'
        failure=HTTPError('https://www.googleapis.com/calendar/v3/users/me/calendarList',403,'remote '+secret,{},io.BytesIO(secret.encode()))
        opener=Mock();opener.open.side_effect=failure
        with patch.object(calendar_http,'build_opener',return_value=opener):
            error=self.error(CalendarError,lambda:calendar_http.request_json('https://www.googleapis.com/calendar/v3/users/me/calendarList',host='www.googleapis.com',path_prefix='/calendar/v3/'),
                              'Google Calendar - calendar list (HTTP 403): Permission denied; check the granted read scopes.')
        self.assertNotIn(secret,str(error))
        self.error(CalendarError,lambda:credential_vault.ProviderVault()._attributes('google','invalid-identity'), 'Invalid credential identity.')

    def test_raw_os_failure_is_not_rewritten_or_translated(self):
        raw='SO não traduzido /tmp/user-file'
        with tempfile.TemporaryDirectory() as folder,patch.object(invoice_profiles.atomic_json,'write',side_effect=OSError(raw)):
            self.error(OSError,lambda:invoice_profiles.save('sheet',PROFILE,Path(folder)/'profiles.json'),raw)

    def test_existing_invoice_error_metadata_changes_language_but_args_do_not(self):
        error=self.error(ValueError,lambda:invoice.party({'name':'','tax_id':'00000000000'}),'Name is required or too long.')
        args=error.args
        self.assertIs(type(args[0]),str)
        display=ui.error_message(error)
        self.assertIsInstance(display,ui.Message)
        ui.refresh('pt-BR')
        self.assertEqual(str(display),'Nome obrigatório ou muito longo.')
        self.assertEqual(error.args,args)
        self.assertEqual(str(error),'Name is required or too long.')
        ui.refresh('en-US')
        self.assertEqual(str(display),args[0])

    def test_overlap_metadata_preserves_literal_user_text_across_language_switch(self):
        entry=dict(id='one',description='Data inválida. {name}',date='2026-10-21',start='09:00',end='10:00')
        other=dict(description='Other',date=entry['date'],start='09:30',end='10:30')
        with self.assertRaises(timesheet.OverlapError) as caught:timesheet.check_overlap([entry],other)
        error=caught.exception;args=error.args;display=ui.error_message(error)
        ui.refresh('pt-BR')
        self.assertEqual(str(display),'Sobreposição com Data inválida. {name} (09:00–10:00) em 2026-10-21. Salvar mesmo assim?')
        self.assertEqual(error.args,args)
        self.assertIs(type(error.args[0]),str)

    def test_http_error_metadata_is_live_and_compatibility_helper_stays_string(self):
        raw=HTTPError('url',400,'raw',{},io.BytesIO(b'{"error":"invalid_grant","error_description":"REMOTE_SECRET"}'))
        opener=Mock();opener.open.side_effect=raw
        with patch.object(calendar_http,'build_opener',return_value=opener),self.assertRaises(CalendarError) as caught:
            calendar_http.request_json('https://oauth2.googleapis.com/token',host='oauth2.googleapis.com',path_prefix='/token',form={'code':'synthetic'})
        error=caught.exception;args=error.args;display=ui.error_message(error)
        self.assertIs(type(args[0]),str)
        self.assertIn('token exchange (HTTP 400)',str(display))
        ui.refresh('pt-BR')
        self.assertIn('troca de token (HTTP 400)',str(display))
        self.assertIn('Código ou autorização recusado/expirado (invalid_grant).',str(display))
        self.assertNotIn('REMOTE_SECRET',str(display))
        self.assertEqual(error.args,args)
        ui.refresh('en-US')
        self.assertEqual(str(display),args[0])
        compatibility=calendar_http._token_error(HTTPError('url',400,'raw',{},io.BytesIO(b'{"error":"invalid_grant"}')))
        self.assertIs(type(compatibility),str)
        self.assertEqual(compatibility,'Code or authorization denied/expired (invalid_grant).')

    def test_external_error_with_same_text_has_no_live_metadata(self):
        error=ValueError('Name is required or too long.')
        self.assertFalse(hasattr(error,'orbitz_message'))
        display=ui.error_message(error)
        ui.refresh('pt-BR')
        self.assertIs(type(display),str)
        self.assertEqual(display,'Name is required or too long.')

    def test_all_domain_message_ids_are_in_both_canonical_catalogs(self):
        keys=set()
        for path in (ROOT/'extension/planner').glob('*.py'):
            if path.stem.endswith('_ui'):continue
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.startswith('domain.'):
                    keys.add(node.value)
        for locale in ('pt-BR','en-US'):
            catalog=json.loads((ROOT/'i18n'/(locale+'.json')).read_text())
            self.assertFalse(keys-catalog.keys(),(locale,keys-catalog.keys()))

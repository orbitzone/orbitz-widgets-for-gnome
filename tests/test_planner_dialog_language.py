"""Localized invoice/backup descriptors and stable GTK models, without any file operation."""
import ast
import json
import hashlib
from copy import deepcopy
from datetime import date
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'extension/planner'))
from ui_language import ui
from invoice_history_ui import describe_message,feedback_message
from invoice_signatures_ui import version_message
from invoice_period_ui import PeriodSelection
import workspace_backup_ui
from invoice_messages import warning_messages
try:
    import gi
    gi.require_version('Gtk','3.0')
    from gi.repository import Gtk
except (ImportError,ValueError):Gtk=None

class Owner:
    def __init__(self,**props):self.__dict__.update(props)
    def set_text(self,value):self.text=value
    def set_property(self,key,value):setattr(self,key,value)

class PlannerDialogLanguageTests(unittest.TestCase):
    def setUp(self):ui.refresh('pt-BR')
    def tearDown(self):ui.refresh('pt-BR')
    def test_invoice_details_keep_amounts_ids_and_pdf_locale_while_labels_update(self):
        record={'id':'USER-record','created_at':'2026-10-21T12:00:00Z','snapshot':{'reference':'USER Reference','sheet_name':'USER Sheet','client':{'name':'USER Cliente','tax_id':'USER tax'},'issued_on':'2026-10-21','period':{'all_history':False,'start':'2026-09-01','end':'2026-09-30'},'hours':'1.5','currency':'BRL','total':'180.75','language':'pt'}}
        before=deepcopy(record);details=Owner();feedback=Owner()
        ui.call(details,'set_text',describe_message(record));ui.call(feedback,'set_text',feedback_message([record],[{}]))
        ui.refresh('en-US')
        self.assertIn('Issue: 10/21/2026 · grouped by issue month',details.text)
        self.assertIn('Service period: 09/01/2026 to 09/30/2026',details.text)
        self.assertIn('Total: BRL 180.75',details.text)
        self.assertIn('USER Cliente · CPF/CNPJ USER tax',details.text)
        self.assertIn('Language: Português',details.text)
        self.assertIn('Valid invoices remain available',feedback.text)
        self.assertEqual(record,before)
    def test_period_summary_changes_locale_without_changing_boundaries(self):
        period=PeriodSelection('2026-10-21');period.set_mode('month');before=period.bounds();label=Owner()
        ui.call(label,'set_text',period.summary_message())
        ui.refresh('en-US')
        self.assertEqual(label.text,'Calendar month: 10/01/2026 to 10/31/2026, inclusive.')
        self.assertEqual(period.bounds(),before)
    def test_backup_scope_and_signature_status_do_not_gain_verification_claims(self):
        scope=Owner();status=Owner()
        ui.call(scope,'set_text',workspace_backup_ui.SCOPE_TEXT)
        ui.call(status,'set_text',version_message({'created_at':'USER timestamp','id':'USER-version'}))
        ui.refresh('en-US')
        self.assertIn('Does not include credentials, external calendars, Sticky Notes or GSettings.',scope.text)
        self.assertIn('Imported — validation pending',status.text)
        self.assertIn('USER-ver',status.text)
        self.assertNotIn('verified',status.text.lower())
        notice=ui.tr('workspace.dialogs.invoice_signatures_ui.confirm_import',reference='USER',id='USER',client='USER',start='USER',end='USER')
        self.assertIn('no cryptographic verification or automatic matching',notice)
        self.assertIn('The file may not be signed.',notice)
        self.assertIn('original and previous versions will be preserved',notice)
    def test_known_historical_warnings_translate_only_in_presentation_without_mutating_snapshot(self):
        known='Cronômetro ativo ignorado; somente registros concluídos entram na fatura.'
        unknown='USER warning with external details'
        snapshot={'warnings':[known,unknown,known+' USER suffix'],'client':{'name':known},'language':'pt','total':'180.75'}
        original=json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        digest=hashlib.sha256(original).hexdigest()
        label=Owner();client=Owner()
        ui.call(label,'set_text',ui.join('\n',warning_messages(snapshot['warnings'])))
        ui.call(client,'set_text',snapshot['client']['name'])
        ui.refresh('en-US')
        self.assertIn('Active timer ignored; only completed records are included in the invoice.',label.text)
        self.assertIn(unknown,label.text);self.assertIn(known+' USER suffix',label.text)
        self.assertEqual(client.text,known,'same text in a user field is never mapped')
        after=json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        self.assertEqual(after,original);self.assertEqual(hashlib.sha256(after).hexdigest(),digest)
        ui.refresh('pt-BR');self.assertEqual(label.text,'\n'.join(snapshot['warnings']))

    def test_invoice_combo_relabel_never_reloads_profiles_or_changes_drafts(self):
        source=Path(__file__).resolve().parents[1]/'extension/planner/invoice_ui.py'
        tree=ast.parse(source.read_text());open_dialog=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='open_invoice')
        callback=next(n for n in open_dialog.body if isinstance(n,ast.FunctionDef) and n.name=='change_sheet')
        choice=SimpleNamespace(_orbitz_language_updating=True)
        profiles=SimpleNamespace(load=Mock())
        namespace=dict(sheet_choice=choice,invoice_profiles=profiles)
        exec(compile(ast.Module(body=[callback],type_ignores=[]),str(source),'exec'),namespace)
        namespace['change_sheet']()
        profiles.load.assert_not_called()

    @unittest.skipIf(Gtk is None,'GTK model unavailable')
    def test_list_and_tree_model_cells_update_with_stable_ids_and_prune_cleared_rows(self):
        owner=Owner();model=Gtk.ListStore(str,str)
        row=ui.model_append(model,[version_message({'created_at':'USER time','id':'version-id'}),'version-id'],owner=owner)
        tree_owner=Owner();tree=Gtk.TreeStore(str,str)
        ui.model_clear(tree,tree_owner)
        heading=ui.model_append(tree,[ui.msg('workspace.dialogs.invoice_history_ui.issue_month',year='2026',month='10'),''],tree=True,owner=tree_owner)
        child=ui.model_append(tree,['USER Customer','USER-id'],parent=heading,tree=True,owner=tree_owner)
        ui.refresh('en-US')
        self.assertIn('Imported — validation pending',model[row][0]);self.assertEqual(model[row][1],'version-id')
        self.assertEqual(tree[heading][0],'Issue: 2026/10');self.assertEqual(tree[child][1],'USER-id');self.assertEqual(tree[child][0],'USER Customer')
        ui.model_clear(model,owner)
        current=ui.model_append(model,[ui.msg('workspace.dialogs.invoice_signatures_ui.original'),'original'],owner=owner)
        ui.refresh('pt-BR')
        self.assertEqual(model[current][0],'Original · PDF gerado da invoice');self.assertEqual(model[current][1],'original')
        self.assertEqual(len(owner._orbitz_language_rows),1)

if __name__=='__main__':unittest.main()

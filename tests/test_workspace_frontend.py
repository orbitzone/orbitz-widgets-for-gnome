"""Workspace orchestration with synthetic widgets/data; no GTK session."""
import ast
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

PLANNER=Path(__file__).resolve().parents[1]/'extension/planner'
sys.path.insert(0,str(PLANNER))
import workspace_ui
import workspace_backup_ui
import ui_language
ui = ui_language.ui
from day_activity import local_details,local_detail_messages
from timesheet_context_ui import context_payload
from invoice_ui import InvoiceSession, ReissueConfirmation
from invoice_history_ui import HistorySession


class Actor:
    def __init__(self,*args,**props):
        self.children=[];self.events={};self.visible=True;self.__dict__.update(props)
    def add(self,child):self.children.append(child)
    def pack_start(self,child,*args):self.add(child)
    pack_end=pack_start
    def get_children(self):return self.children
    def reorder_child(self,child,index):self.children.remove(child);self.children.insert(index,child)
    def connect(self,event,callback):self.events[event]=callback
    def emit(self,event,*args):
        if event in self.events:return self.events[event](self,*args)
    def set_text(self,text):self.text=text
    def set_label(self,text):self.label=text
    def set_property(self,name,value):setattr(self,name.replace('-','_'),value)
    def get_style_context(self):return SimpleNamespace(add_class=lambda *args:None)
    def get_accessible(self):return self
    def set_name(self,name):self.accessible_name=name
    def set_visible(self,value):self.visible=value
    def destroy_all_children(self):self.children=[]
    def destroy(self):self.emit('destroy')
    def __getattr__(self,name):
        if name.startswith('set_') or name in ('show','show_all','hide','clear_marks','mark_day','finish_marks'):
            return lambda *args,**kwargs:None
        raise AttributeError(name)


class Stack(Actor):
    def __init__(self,**props):super().__init__(**props);self.pages={};self.current=None;self.titles={}
    def add_titled(self,page,key,title):self.pages[key]=page;self.titles[key]=title;self.current=self.current or key
    def child_set_property(self,page,key,value):self.titles[page.page_id]=value
    def get_visible_child_name(self):return self.current
    def set_visible_child_name(self,key):
        self.current=key;self.emit('notify::visible-child-name')


class Notebook(Actor):
    def __init__(self,**props):super().__init__(**props);self.labels={};self.current=0
    def append_page(self,page,label):self.children.append(page);self.labels[page]=label;return len(self.children)-1
    def get_current_page(self):return self.current
    def get_n_pages(self):return len(self.children)
    def get_nth_page(self,index):return self.children[index] if self.children and -len(self.children)<=index<len(self.children) else None
    def page_num(self,page):return self.children.index(page) if page in self.children else -1
    def get_tab_label(self,page):return self.labels[page]
    def set_current_page(self,index):
        if 0<=index<len(self.children):self.current=index;self.emit('switch-page',self.children[index],index)
    def set_tab_reorderable(self,page,reorderable):
        self.reorderable=getattr(self,'reorderable',{});self.reorderable[page]=reorderable
    def remove_page(self,index):self.children.pop(index);self.current=0


class Calendar(Actor):
    def __init__(self):super().__init__();self.chosen=date.today()
    def get_date(self):return self.chosen.year,self.chosen.month-1,self.chosen.day
    def select_month(self,month,year):self.year,self.month=year,month+1
    def select_day(self,day):self.chosen=date(self.year,self.month,day);self.emit('day-selected')


class Page(Actor):
    def __init__(self,window,identity):super().__init__();self.sheet_id=identity;self.readonly=False;self.persist_timer=0;self.tick=0
    def render(self):pass
    def update_timer(self):pass


class WorkspaceTests(unittest.TestCase):
    def test_today_and_context_are_read_only_and_distinguish_overdue(self):
        data={'tasks':[dict(text='Hoje',date='2026-10-19',done=False),dict(text='Atrasada',date='2026-10-18',done=False),
            dict(text='Futura',date='2026-11-01',done=False),dict(text='Feita',date='2026-10-18',done=True)],
            'timesheets':[dict(name='Equipe',timesheet_active=dict(description='Trabalho',started='2026-10-19T10:00'))]}
        original=deepcopy(data)
        text=workspace_ui.today_text(data,[{'title':'Compromisso'}],today='2026-10-19')
        self.assertIn('Tarefas pendentes: 3 · Hoje: 1',text)
        self.assertIn('Tarefas atrasadas: 1',text)
        self.assertIn('Cronômetros em andamento: 1',text)
        self.assertIn('Compromisso',text)
        self.assertEqual(data,original)
        payload=context_payload(' Nome ',dict(client_name=' Cliente ',project_contract=' Contrato ',department_costcenter=' Centro '),'id')
        self.assertEqual(payload,dict(action='sheet_update',sheet_id='id',name='Nome',context=dict(client_name='Cliente',project_contract='Contrato',department_costcenter='Centro')))
        self.assertIn('Contrato',workspace_ui.context_text(dict(name='Nome',context=payload['context'])))

    def test_five_areas_and_legacy_navigation_route_to_correct_content(self):
        gtk=SimpleNamespace(ApplicationWindow=Actor,Box=Actor,Label=Actor,Button=Actor,ScrolledWindow=Actor,
            Stack=Stack,StackSwitcher=Actor,Notebook=Notebook,Orientation=SimpleNamespace(VERTICAL=1),
            PackType=SimpleNamespace(END=1),PolicyType=SimpleNamespace(NEVER=0,AUTOMATIC=1),
            Align=SimpleNamespace(START=0),StackTransitionType=SimpleNamespace(NONE=0))
        data={'tasks':[],'timesheets':[dict(id=key,name=key,archived=False,timesheet=[],context={'client_name':'Cliente'}) for key in ('one','two')]}
        def header(container,window):window.heading=Actor();return Actor()
        class External:
            def __init__(self,window,left,mount):self.page=Actor();mount.append_page(self.page,Actor())
            def render(self):pass
            def mark_days(self,details):pass
            def selected_cache(self):return None,{}
        history_content=Actor();refresh=Mock()
        namespace=dict(Gtk=gtk,Gio=SimpleNamespace(),GLib=SimpleNamespace(timeout_add_seconds=lambda *args:77,source_remove=Mock()),
            Pango=SimpleNamespace(WrapMode=SimpleNamespace(WORD_CHAR=0),EllipsizeMode=SimpleNamespace(END=0)),date=date,timedelta=timedelta,
            workspace_ui=workspace_ui,MonthCalendar=Calendar,ExternalCalendars=External,Timesheet=Page,
            ui=ui,
            planner_menu=SimpleNamespace(add_header=header,update_archive_count=Mock()),
            store=SimpleNamespace(modify=lambda request:deepcopy(data)),ui_state=SimpleNamespace(set=Mock()),
            local_details=local_details,local_detail_messages=local_detail_messages,
            invoice_history_ui=SimpleNamespace(create_history_content=Mock(return_value=(history_content,refresh))),
            invoice_ui=SimpleNamespace(open_invoice=Mock()))
        tree=ast.parse((PLANNER/'calendar-app.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CalendarWindow')
        exec(compile(ast.Module(body=[node],type_ignores=[]),'calendar-app.py','exec'),namespace)
        with patch.dict(sys.modules,{'gi.repository':SimpleNamespace(Gtk=gtk,Pango=namespace['Pango'])}):
            window=namespace['CalendarWindow'](object())
            self.assertEqual(list(window.workspace.pages),['today','events','tasks','hours','invoices'])
            self.assertEqual(window.tabs.get_n_pages(),2)  # Only timesheets remain in the hours notebook.
            self.assertEqual(list(window.tabs.reorderable.values()),[True,True])
            self.assertEqual(window.workspace.current,'today')
            window.focus_sheet('two')
            self.assertEqual(window.workspace.current,'hours')
            self.assertEqual(window.selected_sheet_id,'two')
            self.assertIn('Cliente',window.context_label.text)
            window.show_area('events')
            self.assertIn(window.external.page,window.workspace.pages['events'].children)
            window.show_area('invoices')
            self.assertIn(history_content,window.workspace.pages['invoices'].children)
            refresh.assert_called()
            generate=window.workspace.pages['invoices'].children[0]
            generate.events['clicked'](generate)
            namespace['invoice_ui'].open_invoice.assert_called_once_with(window)
            window.show_area('tasks')
            self.assertEqual(window.workspace.current,'tasks')
            window.show_area('today')
            window.select('2026-10-01')
            self.assertEqual(window.workspace.current,'today')
            window.day_selected()  # A calendar action from Hoje leads to the selected-day agenda.
            self.assertEqual(window.workspace.current,'events')
            current_page=window.workspace.current
            pages=dict(window.workspace.pages)
            before=deepcopy(window.data)
            try:
                ui.refresh('en-US')
                self.assertEqual(window.workspace.titles['today'],'Today')
                self.assertEqual(window.workspace.titles['tasks'],'Tasks')
                self.assertEqual(window.workspace.current,current_page)
                self.assertEqual(window.workspace.pages,pages)
                self.assertEqual(window.data,before)
                self.assertIn('Events in the selected source',window.today_label.text)
            finally:ui.refresh('pt-BR')
            window.data={'tasks':[],'timesheets':[]}
            window.sync_sheets()
            self.assertEqual(window.tabs.get_n_pages(),0)
            self.assertTrue(window.hours_empty.visible)
            self.assertTrue(any(getattr(child,'label','')=='+ Nova timesheet' for child in window.workspace.pages['hours'].children))

    def test_restore_flush_then_quiesce_prevents_old_draft_writeback(self):
        writes=[];removed=[]
        class Sheet:
            readonly=False;persist_timer=3
            def persist(self):writes.append('before-preview');return True
            def cleanup(self):
                if not self.readonly:writes.append('stale-write')
        page=Sheet();executor=SimpleNamespace(shutdown=Mock())
        window=SimpleNamespace(sheet_pages={'one':page},timer=5,external=SimpleNamespace(cleanup=Mock(),executor=executor),restoring=False,syncing_tabs=False)
        self.assertTrue(workspace_ui.flush_drafts(window,removed.append))
        workspace_ui.quiesce(window,removed.append)
        page.cleanup()  # Simulated widget destruction after restore must remain read-only.
        self.assertEqual(writes,['before-preview'])
        self.assertTrue(window.restoring);self.assertTrue(window.syncing_tabs)
        self.assertEqual(removed,[3,5])
        executor.shutdown.assert_called_once_with(wait=True,cancel_futures=True)
        backend=SimpleNamespace(restore_backup=Mock(return_value={'restored':True}))
        quiesce=Mock()
        preview={'token':'archive-and-current-data','current_active_timer':False}
        self.assertIsNone(workspace_backup_ui.apply_restore(backend,'synthetic.zip',preview,quiesce,confirmed=False))
        quiesce.assert_not_called();backend.restore_backup.assert_not_called()
        workspace_backup_ui.apply_restore(backend,'synthetic.zip',preview,quiesce,confirmed=True)
        quiesce.assert_called_once()
        backend.restore_backup.assert_called_once_with('synthetic.zip',confirmed=True,expected=preview['token'],quiescent=True)
        backend.restore_backup.reset_mock();quiesce.reset_mock()
        with self.assertRaises(ValueError):
            workspace_backup_ui.apply_restore(backend,'synthetic.zip',dict(preview,current_active_timer=True),quiesce,confirmed=True)
        quiesce.assert_not_called();backend.restore_backup.assert_not_called()
        quiesce.side_effect=OSError('synthetic shutdown failure')
        with self.assertRaises(OSError):workspace_backup_ui.apply_restore(backend,'synthetic.zip',preview,quiesce,confirmed=True)
        backend.restore_backup.assert_not_called()

    def test_context_prefill_saved_fiscal_profile_and_real_manual_payment(self):
        import invoice_profiles, invoice_history, invoice_payments
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(invoice_profiles,'PATH',Path(folder)/'profiles.json'), \
                patch.object(invoice_history,'ROOT',Path(folder)/'history'):
            context=dict(client_name='Cliente de trabalho',project_contract='Contrato de teste',department_costcenter='Centro de teste')
            profile=invoice_profiles.load('sheet',context=context)
            self.assertEqual(profile['client']['name'],'Cliente de trabalho')
            self.assertFalse(invoice_profiles.PATH.exists())
            profile.update(issuer=dict(name='Emitente teste',tax_id='00000000000'),
                client=dict(name='Destinatário fiscal salvo',tax_id='00000000000000',address='Endereço sintético'),rate='100')
            invoice_profiles.save('sheet',profile)
            self.assertEqual(invoice_profiles.load('sheet',context=dict(context,client_name='Outro cliente'))['client']['name'],'Destinatário fiscal salvo')
            sheet=dict(id='sheet',name='Timesheet',archived=False,context=context,timesheet=[
                dict(id='entry',description='Sintético',date='2026-10-01',start='10:00',end='11:00')])
            session=InvoiceSession(lambda:{'timesheets':[sheet]})
            snapshot=session.prepare('sheet',dict(profile,reference='TESTE',issued_on='2026-10-19'))
            self.assertEqual(snapshot['context'],context)
            self.assertEqual(snapshot['client']['name'],'Destinatário fiscal salvo')
            pdf=Path(folder)/'external.pdf';pdf.write_bytes(b'%PDF-1.4\nsynthetic payment test\n%%EOF\n')
            saved=invoice_history.record(snapshot,pdf)
            managed=invoice_history.get_path(saved['id'])
            metadata=(managed.parent/'metadata.json').read_bytes();raw=managed.read_bytes()
            history=HistorySession(invoice_history,invoice_payments);history.reload();history.select(saved['id'])
            self.assertEqual(history.payment()['status'],'not_reported')
            history.report_paid(True,confirmed=True)
            self.assertEqual(history.payment()['status'],'reported_paid')
            self.assertEqual((managed.parent/'metadata.json').read_bytes(),metadata)
            self.assertEqual(managed.read_bytes(),raw)
            matches=session.duplicate_check()['matches']
            self.assertEqual(matches[0]['minutes'],60)
            self.assertEqual(matches[0]['id'],saved['id'])

    def test_duplicate_warning_requires_explicit_reissue_and_payment_is_separate(self):
        session=InvoiceSession(lambda:{})
        session.snapshot={'synthetic':True};session.profile={};session.sheet_id='sheet'
        archive=SimpleNamespace(ROOT=Path('/synthetic-managed'),possible_duplicates=Mock(return_value=dict(matches=[dict(id='old',reference='R',minutes=60,basis='entries')],warnings=[],incomplete=False)),record=Mock())
        writer=Mock(return_value=Path('/synthetic/out.pdf'))
        with patch.dict(sys.modules,{'invoice_history':archive,'invoice_pdf':SimpleNamespace(write=writer)}),patch('invoice_ui.invoice_profiles.save'):
            with self.assertRaises(ReissueConfirmation):session.export('/synthetic/out.pdf')
            writer.assert_not_called();archive.record.assert_not_called()
            session.export('/synthetic/out.pdf',confirmed_reissue=True)
            writer.assert_called_once()
        payments=SimpleNamespace(get=Mock(return_value={'status':'not_reported','updated_at':None}),set_paid=Mock())
        history=HistorySession(archive=SimpleNamespace(),payments=payments)
        history.records={'record':{}};history.selected_id='record'
        self.assertEqual(history.payment()['status'],'not_reported')
        history.report_paid(True,confirmed=False);payments.set_paid.assert_not_called()
        history.report_paid(True,confirmed=True);payments.set_paid.assert_called_once_with('record',True)


if __name__=='__main__':unittest.main()

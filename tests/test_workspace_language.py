"""Live labels/models use the real catalog without rebuilding editable timesheet rows."""
import ast
from copy import deepcopy
from datetime import date,datetime,timedelta
import calendar
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'extension/planner'))
from ui_language import ui
import workspace_ui
import timesheet_context_ui
import timesheet as model
from day_activity import day_messages,local_detail_messages

class Actor:
    instances=[]
    def __init__(self,**props):self.__dict__.update(props);self.children=[];self.events={};self.text=props.get('text','');self.__class__.instances.append(self)
    @classmethod
    def new_from_icon_name(cls,*args):return cls()
    def get_style_context(self):return self
    def add_class(self,*args):pass
    def get_accessible(self):return self
    def set_name(self,value):self.accessible_name=value
    def set_tooltip_text(self,value):self.tooltip=value
    def set_markup(self,value):self.markup=value
    def set_property(self,key,value):setattr(self,key.replace('-','_'),value)
    def set_text(self,value):self.text=value
    def set_label(self,value):self.label=value
    def grab_focus(self):self.focused=True
    def get_text(self):return self.text
    def attach(self,child,*args):self.children.append(child)
    def add(self,child):self.children.append(child)
    def get_children(self):return self.children
    def destroy(self):pass
    def connect(self,event,fn):self.events[event]=fn
    def __getattr__(self,name):
        if name.startswith('set_') or name=='show_all':return lambda *args:None
        raise AttributeError(name)

class Model:
    def __init__(self,owner):self.rows=[];self.owner=owner
    def get_iter_first(self):return 0 if self.rows else None
    def get_value(self,i,col):return self.rows[i][col]
    def iter_next(self,i):return i+1 if i+1<len(self.rows) else None
    def set_value(self,i,col,value):
        self.rows[i][col]=value
        if self.owner.on_changed:self.owner.on_changed()

class Combo:
    def __init__(self):self.model=Model(self);self.active='day';self.on_changed=None
    def append(self,identity,label):self.model.rows.append([label,identity])
    def get_model(self):return self.model
    def get_active_id(self):return self.active

class WorkspaceLanguageTests(unittest.TestCase):
    def setUp(self):ui.refresh('pt-BR');Actor.instances=[]
    def tearDown(self):ui.refresh('pt-BR')
    def test_today_context_and_dates_preserve_user_text_and_data(self):
        data={'tasks':[dict(text='USER Hoje',date='2026-10-21',done=False)],'timesheets':[dict(name='USER Equipe',timesheet_active=dict(description='USER Trabalho',started='2026-10-21T10:30'))]}
        before=deepcopy(data);label=Actor();context=Actor()
        ui.call(label,'set_text',workspace_ui.today_message(data,[{'title':'USER Compromisso'}],today='2026-10-21'))
        ui.call(context,'set_text',workspace_ui.context_message(dict(name='USER Sheet',context={'client_name':'USER Cliente'})))
        self.assertIn('Hoje · 21/10/2026',label.text)
        ui.refresh('en-US')
        self.assertIn('Today · 10/21/2026',label.text)
        self.assertIn('Pending tasks: 1 · Today: 1',label.text)
        self.assertIn('USER Trabalho · since 10/21/2026 10:30',label.text)
        self.assertEqual(context.text,'USER Sheet · Client: USER Cliente')
        self.assertEqual(data,before)
    def test_timesheet_headers_summary_recovery_and_inline_drafts_update_in_place(self):
        tree=ast.parse((ROOT/'extension/planner/timesheet_ui.py').read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));cls.bases=[]
        gtk=SimpleNamespace(Label=Actor,Entry=Actor,Button=Actor,Box=Actor,EntryCompletion=Actor,ListStore=lambda *args:[],IconSize=SimpleNamespace(BUTTON=1))
        namespace=dict(ui=ui,Gtk=gtk,date=date,datetime=datetime,context_message=workspace_ui.context_message,model=model)
        exec(compile(ast.Module(body=[cls],type_ignores=[]),'timesheet_ui.py','exec'),namespace)
        page=object.__new__(namespace['Timesheet'])
        sheet=dict(name='USER Sheet',context={'client_name':'USER Cliente'},timesheet=[dict(id='row',date='2026-10-21',description='USER saved',start='10:00',end='11:00')])
        page.sheet_data=lambda:sheet;page.window=SimpleNamespace(day='2026-10-21');page.day='2026-10-21';page.switch_day=lambda day:None
        page.readonly=False;page.editing=None;page.rows=Actor();page.period=Combo();page.summary=Actor();page.context_label=Actor();page.editor_label=Actor();page.undo=Actor();page.timer_button=Actor();page.active_label=Actor()
        page.inline_drafts={'row':{'values':dict(description='USER draft',start='10:05',end='11:30')},'removed':{'values':dict(description='USER removed')}}
        page.fields={'description':Actor(text='USER unsaved form')}
        page.render();before=deepcopy(sheet);drafts=deepcopy(page.inline_drafts)
        fields=dict(page.inline_widgets['row']);actors=list(page.rows.children);count=len(Actor.instances)
        self.assertEqual(fields['description'].text,'USER draft')
        self.assertTrue(any(getattr(a,'label','')=='21/10' for a in actors))
        ui.refresh('en-US')
        self.assertEqual(len(Actor.instances),count)
        self.assertEqual(page.rows.children,actors)
        self.assertEqual(page.inline_widgets['row'],fields)
        self.assertEqual(fields['description'].text,'USER draft')
        self.assertEqual(page.fields['description'].text,'USER unsaved form')
        self.assertTrue(any(getattr(a,'label','')=='Description' for a in actors))
        self.assertTrue(any(getattr(a,'label','')=='10/21' for a in actors))
        self.assertTrue(any(getattr(a,'label','')=='Recover draft of deleted row: USER removed' for a in actors))
        self.assertIn('Day: 01h 00min',page.summary.text)
        self.assertEqual(page.editor_label.text,'New activity · 10/21/2026')
        self.assertEqual(sheet,before);self.assertEqual(page.inline_drafts,drafts)
    def test_context_dialog_updates_labels_and_accessibility_without_changing_fields(self):
        case=self
        sheet=dict(id='USER id',name='USER Sheet',context=dict(client_name='USER Cliente',project_contract='USER Contrato'))
        before=deepcopy(sheet)
        class Dialog(Actor):
            def __init__(self,**props):super().__init__(**props);self.content=Actor()
            def get_content_area(self):return self.content
            def add_button(self,label,response):return Actor(label=label)
            def run(self):
                fields=[actor for actor in Actor.instances if actor.text in ('USER Sheet','USER Cliente','USER Contrato')]
                identities=list(fields);values=[field.text for field in fields]
                ui.refresh('en-US')
                case.assertEqual(self.title,'Timesheet context')
                case.assertTrue(any(getattr(actor,'label','')=='Timesheet name (required)' for actor in Actor.instances))
                case.assertTrue(any(getattr(actor,'accessible_name','')=='Client / work recipient (optional)' for actor in fields))
                case.assertEqual(fields,identities);case.assertEqual([field.text for field in fields],values)
                case.assertTrue(next(field for field in fields if field.text=='USER Sheet').focused)
                return 0
        gtk=SimpleNamespace(Dialog=Dialog,Box=Actor,Label=Actor,Entry=Actor,Orientation=SimpleNamespace(VERTICAL=1),ResponseType=SimpleNamespace(CANCEL=0,OK=1))
        with patch.dict(sys.modules,{'gi.repository':SimpleNamespace(Gtk=gtk)}),patch.object(timesheet_context_ui.store,'modify',Mock()) as write:
            timesheet_context_ui.edit_context(SimpleNamespace(),sheet)
            write.assert_not_called()
        self.assertEqual(sheet,before)

    def test_month_weekdays_and_activity_tooltips_switch_without_redraw(self):
        tree=ast.parse((ROOT/'extension/planner/month_calendar.py').read_text())
        months=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MONTHS' for t in n.targets))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='redraw')
        namespace=dict(ui=ui,Gtk=SimpleNamespace(Label=Actor,Button=Actor),date=date,timedelta=timedelta,day_messages=day_messages)
        exec(compile(ast.Module(body=[months,method],type_ignores=[]),'month_calendar.py','exec'),namespace)
        data={'tasks':[dict(date='2026-10-21',text='USER task',done=False)],'timesheets':[dict(name='USER Sheet',archived=False,timesheet=[dict(date='2026-10-21')])]}
        details=local_detail_messages(data,date(2026,10,21))
        page=SimpleNamespace(year=2026,month=10,chosen=date(2026,10,21),marks={21},holidays={21:['USER Holiday']},details={21:details},grid=Actor(),title=Actor(),click=lambda day:None)
        namespace['redraw'](page);actors=list(page.grid.children);count=len(Actor.instances)
        button=page.buttons[21]
        self.assertIn('Data selecionada',button.tooltip)
        ui.refresh('en-US')
        self.assertEqual(page.title.text,'October 2026')
        self.assertEqual(page.grid.children,actors);self.assertEqual(len(Actor.instances),count)
        self.assertIn('Selected date',button.tooltip);self.assertIn('Holiday: USER Holiday',button.tooltip)
        self.assertIn('Local hours: USER Sheet',button.accessible_name)
        self.assertTrue(any(getattr(actor,'label','')=='Sun' for actor in actors))
        self.assertEqual(page.chosen,date(2026,10,21))

    def test_combo_labels_keep_identity_and_suppress_table_rebuild(self):
        combo=Combo();writes=[];renders=[]
        ui.combo_append(combo,'day',ui.msg('workspace.live.period_day'))
        ui.combo_append(combo,'month',ui.msg('workspace.live.period_month'))
        combo.active='month'
        tree=ast.parse((ROOT/'extension/planner/timesheet_ui.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='period_changed')
        namespace=dict(ui=ui,ui_state=SimpleNamespace(set=lambda *args:writes.append(args)))
        exec(compile(ast.Module(body=[method],type_ignores=[]),'timesheet_ui.py','exec'),namespace)
        page=SimpleNamespace(period=combo,readonly=False,sheet_id='user-id',render=lambda:renders.append(1))
        combo.on_changed=lambda:namespace['period_changed'](page)
        ui.refresh('en-US')
        self.assertEqual(combo.active,'month');self.assertEqual(combo.model.rows,[['Selected day','day'],['Selected month','month']])
        self.assertEqual(writes,[]);self.assertEqual(renders,[])

if __name__=='__main__':unittest.main()

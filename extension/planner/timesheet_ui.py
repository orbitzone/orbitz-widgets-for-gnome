"""Three-field timesheet editor embedded in the calendar."""
from datetime import date,datetime
from pathlib import Path
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,GLib,Pango,Gdk
import store
import ui_state
from workspace_ui import context_text
import timesheet as model

class Timesheet(Gtk.Box):
    def __init__(self,window,sheet_id,readonly=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL,spacing=10,margin=12)
        self.readonly=readonly;self.persist_timer=0;self.inline_widgets={}
        self.sheet_id=sheet_id
        self.window=window;self.day=None;self.drafts={};self.editing=None;self.loading=False;self.dirty=False
        self.context_label=Gtk.Label(xalign=0,wrap=True,selectable=True)
        self.context_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.context_label.set_max_width_chars(70);self.pack_start(self.context_label,False,False,0)
        self.period=Gtk.ComboBoxText()
        for key,title in [('day','Dia selecionado'),('week','Semana (segunda a domingo)'),('month','Mês selecionado')]:self.period.append(key,title)
        self.period.set_active_id(ui_state.get('period:'+sheet_id,'day'));self.period.connect('changed',self.period_changed)
        toolbar=Gtk.Box(spacing=8);self.pack_start(toolbar,False,False,0);toolbar.pack_start(self.period,True,True,0)
        export=Gtk.Button(label='Exportar CSV');export.connect('clicked',self.export);toolbar.pack_end(export,False,False,0)
        archive=Gtk.Button.new_from_icon_name('folder-symbolic',Gtk.IconSize.BUTTON);archive.set_tooltip_text('Arquivar esta timesheet')
        archive.connect('clicked',lambda *_:self.window.archive_sheet(self));toolbar.pack_end(archive,False,False,0)
        rename=Gtk.Button.new_from_icon_name('document-edit-symbolic',Gtk.IconSize.BUTTON);rename.set_tooltip_text('Editar contexto da timesheet');rename.connect('clicked',lambda *_:self.window.rename_sheet(self));toolbar.pack_end(rename,False,False,0)
        self.timer_button=Gtk.Button(label='Iniciar atividade agora');self.timer_button.connect('clicked',self.timer_click);self.pack_start(self.timer_button,False,False,0)
        self.active_label=Gtk.Label(xalign=0,wrap=True);self.pack_start(self.active_label,False,False,0)
        self.summary=Gtk.Label(xalign=0,wrap=True)
        scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC);self.pack_start(scroll,True,True,0)
        self.rows=Gtk.Grid(column_spacing=10,row_spacing=8);scroll.add(self.rows)
        self.pack_start(self.summary,False,False,0)
        self.editor_label=Gtk.Label(xalign=0);self.pack_start(self.editor_label,False,False,0)
        editor=Gtk.Grid(column_spacing=8,row_spacing=6);self.pack_start(editor,False,False,0);self.fields={}
        for col,(key,title) in enumerate([('description','Descrição'),('start','Início · HH:MM'),('end','Fim · HH:MM')]):
            editor.attach(Gtk.Label(label=title,xalign=0),col,0,1,1)
            field=Gtk.Entry();field.set_max_length(1000 if col==0 else 5);field.set_width_chars(24 if col==0 else 7)
            field.set_hexpand(col==0);field.connect('changed',self.changed);field.connect('activate',lambda *_:self.save())
            self.fields[key]=field;editor.attach(field,col,1,1,1)
        editor.set_focus_chain(list(self.fields.values()))
        actions=Gtk.Box(spacing=8);self.pack_start(actions,False,False,0)
        save=Gtk.Button(label='Salvar e nova linha ↵');save.connect('clicked',lambda *_:self.save());actions.pack_start(save,False,False,0)
        cancel=Gtk.Button(label='Limpar / cancelar edição');cancel.connect('clicked',lambda *_:self.reset());actions.pack_start(cancel,False,False,0)
        self.undo=Gtk.Button(label='Desfazer exclusão');self.undo.connect('clicked',lambda *_:self.commit({'action':'timesheet_undo'}));actions.pack_end(self.undo,False,False,0)
        self.message=Gtk.Label(xalign=0,wrap=True);self.pack_start(self.message,False,False,0)
        self.pack_start(Gtk.Label(label='Tab: próximo campo · Enter: salvar e continuar · Horários em minutos',xalign=0,wrap=True),False,False,0)
        if readonly:
            for actor in [archive,rename,self.timer_button,self.editor_label,editor,actions]:
                actor.set_no_show_all(True);actor.hide()
        try:
            saved=ui_state.get('draft:'+sheet_id,{}) if not readonly else {}
            self.drafts=saved.get('days',{});self.inline_drafts=saved.get('rows',{})
        except Exception as error:
            self.drafts={};self.inline_drafts={};self.message.set_text(str(error))
        self.tick=0;self.connect('destroy',self.cleanup)

    def period_changed(self,*_):
        try:
            if not self.readonly:ui_state.set('period:'+self.sheet_id,self.period.get_active_id())
        except Exception as error:self.message.set_text(str(error))
        self.render()

    def schedule_persist(self):
        if self.readonly:return
        if self.persist_timer:GLib.source_remove(self.persist_timer)
        self.persist_timer=GLib.timeout_add(350,self.persist_idle)

    def persist_idle(self):
        self.persist_timer=0;self.persist();return False

    def persist(self):
        if self.readonly:return True
        try:
            if self.day:
                if self.dirty:self.drafts[self.day]=self.snapshot()
                else:self.drafts.pop(self.day,None)
            days={k:v for k,v in self.drafts.items() if v[2]}
            ui_state.set('draft:'+self.sheet_id,{'days':days,'rows':self.inline_drafts} if days or self.inline_drafts else None)
            if self.has_draft():self.message.set_text('Rascunho salvo · ainda não incluído nos totais')
            return True
        except Exception as error:self.message.set_text('Não foi possível salvar o rascunho: '+str(error));return False

    def inline_changed(self,entry,fields):
        values={k:f.get_text() for k,f in fields.items()}
        if len(values)!=3:return
        if values=={k:entry[k] for k in values}:self.inline_drafts.pop(entry['id'],None)
        else:
            expected=self.inline_drafts.get(entry['id'],{}).get('expected',dict(entry))
            self.inline_drafts[entry['id']]={'values':values,'expected':expected}
        self.message.set_text('Rascunho da linha · Enter salva · Esc cancela');self.schedule_persist()

    def recover_row(self,identity):
        draft=self.inline_drafts[identity]
        if self.dirty and not self.ask('Substituir o preenchimento atual?','O rascunho da linha será recuperado como uma nova atividade.'):return
        self.window.select(draft['expected']['date']);self.editing=None;self.fill(draft['values']);self.dirty=True
        self.inline_drafts.pop(identity,None);self.persist();self.render()

    def inline_save(self,entry,fields):
        draft=self.inline_drafts.get(entry['id'])
        if not draft:return
        payload=dict(action='timesheet',id=entry['id'],expected=draft['expected'],date=entry['date'],**{k:f.get_text().strip() for k,f in fields.items()})
        if self.commit(payload):
            self.inline_drafts.pop(entry['id'],None);self.persist();self.render()

    def inline_key(self,event,entry):
        if event.keyval==Gdk.KEY_Escape:
            self.inline_drafts.pop(entry['id'],None);self.persist();self.render();return True
        return False

    def sheet_data(self):return model.get_sheet(self.window.data,self.sheet_id)

    def has_draft(self):return self.dirty or any(snapshot[2] for snapshot in self.drafts.values()) or bool(self.inline_drafts)

    def changed(self,*_):
        if not self.loading:self.dirty=True;self.message.set_text('Rascunho em edição');self.schedule_persist()

    def snapshot(self):return ({k:v.get_text() for k,v in self.fields.items()},self.editing,self.dirty)

    def switch_day(self,day):
        if day==self.day:return
        if self.day:self.drafts[self.day]=self.snapshot()
        self.day=day
        if day in self.drafts:
            values,self.editing,self.dirty=self.drafts[day];self.fill(values)
        else:self.reset()
        if self.dirty:self.message.set_text('Rascunho recuperado · Enter para registrar')

    def fill(self,values):
        self.loading=True
        for key,field in self.fields.items():field.set_text(values.get(key,''))
        self.loading=False

    def reset(self,start=None):
        self.editing=None;self.dirty=False
        entries=[e for e in self.sheet_data().get('timesheet',[]) if e['date']==self.day]
        last=max((e['end'] for e in entries),default='') if start is None else start
        self.fill({'start':'' if last=='24:00' else last})
        self.message.set_text('');self.drafts.pop(self.day,None)
        self.editor_label.set_text('Nova atividade · '+(self.day or ''))
        self.schedule_persist()

    def render(self):
        self.context_label.set_text(context_text(self.sheet_data()))
        self.switch_day(self.window.day)
        self.editor_label.set_text(('Editar atividade' if self.editing else 'Nova atividade')+' · '+date.fromisoformat(self.day).strftime('%d/%m/%Y'))
        entries=self.sheet_data().get('timesheet',[])
        self.inline_widgets={}
        for child in self.rows.get_children():child.destroy()
        start,end=model.bounds(self.day,self.period.get_active_id() or 'day')
        selected=model.entries_for(entries,start,end)
        columns=['Data','Descrição','Início','Fim','Horas','']
        for col,title in enumerate(columns):self.rows.attach(Gtk.Label(label=title,xalign=0),col,0,1,1)
        for row,e in enumerate(selected,1):
            values=[date.fromisoformat(e['date']).strftime('%d/%m'),e['description'],e['start'],e['end'],model.duration(model.activity_minutes(e))]
            row_fields={}
            draft=self.inline_drafts.get(e['id'])
            for col,value in enumerate(values):
                if col in (1,2,3) and not self.readonly:
                    key={1:'description',2:'start',3:'end'}[col]
                    cell=Gtk.Entry(text=(draft['values'].get(key,value) if draft else value))
                    cell.set_width_chars(20 if col==1 else 5);cell.set_max_length(1000 if col==1 else 5)
                    cell.set_hexpand(col==1);row_fields[key]=cell
                    cell.connect('changed',lambda _,entry=e,fields=row_fields:self.inline_changed(entry,fields))
                    cell.connect('activate',lambda _,entry=e,fields=row_fields:self.inline_save(entry,fields))
                    cell.connect('key-press-event',lambda _,event,entry=e:self.inline_key(event,entry))
                    cell.set_tooltip_text('Editar aqui · Enter salva · Esc cancela')
                else:cell=Gtk.Label(label=value,xalign=0)
                self.rows.attach(cell,col,row,1,1)
            self.inline_widgets[e['id']]=row_fields
            action_box=Gtk.Box(spacing=4)
            if e.get('source_task_id'):
                link=Gtk.Button.new_from_icon_name('go-jump-symbolic',Gtk.IconSize.BUTTON);link.set_tooltip_text('Abrir tarefa original')
                link.connect('clicked',lambda _,identity=e['source_task_id']:self.window.open_source_task(identity));action_box.add(link)
            if not self.readonly:
                remove=Gtk.Button.new_from_icon_name('edit-delete-symbolic',Gtk.IconSize.BUTTON);remove.set_tooltip_text('Excluir atividade')
                remove.connect('clicked',lambda _,entry=e:self.delete(entry));action_box.add(remove)
            self.rows.attach(action_box,5,row,1,1)
        orphan_ids=[identity for identity in self.inline_drafts if not any(e['id']==identity for e in entries)] if not self.readonly else []
        for position,identity in enumerate(orphan_ids,len(selected)+1):
            recover=Gtk.Button(label='Recuperar rascunho de linha removida: '+self.inline_drafts[identity]['values'].get('description',''))
            recover.connect('clicked',lambda _,i=identity:self.recover_row(i));self.rows.attach(recover,0,position,6,1)
        if not selected and not orphan_ids:self.rows.attach(Gtk.Label(label='Nenhuma atividade neste período.',xalign=0),0,1,6,1)
        self.rows.show_all()
        parts=[]
        for period,title in [('day','Dia'),('week','Semana'),('month','Mês')]:
            a,b=model.bounds(self.day,period);parts.append(title+': '+model.duration(model.total(model.entries_for(entries,a,b))))
        text=' · '.join(parts)+'\nTotal do período: '+model.duration(model.total(selected))
        if model.has_overlaps(selected):text+='\n⚠ Há sobreposições; o total soma os intervalos registrados.'
        self.summary.set_text(text);self.undo.set_sensitive(bool(self.sheet_data().get('timesheet_trash')))
        completion=Gtk.EntryCompletion();choices=Gtk.ListStore(str)
        for description in sorted({e['description'] for e in entries},key=str.casefold):choices.append([description])
        completion.set_model(choices);completion.set_text_column(0);completion.set_minimum_key_length(1);completion.set_inline_completion(True)
        self.fields['description'].set_completion(completion)
        self.update_timer()

    def ask(self,title,text):
        dialog=Gtk.MessageDialog(transient_for=self.window,modal=True,message_type=Gtk.MessageType.QUESTION,buttons=Gtk.ButtonsType.YES_NO,text=title)
        dialog.format_secondary_text(text);result=dialog.run();dialog.destroy();return result==Gtk.ResponseType.YES

    def commit(self,payload):
        if self.readonly:return False
        payload=dict(payload,sheet_id=self.sheet_id)
        try:
            try:latest=store.modify(payload)
            except model.OverlapError as error:
                if not self.ask('Horários sobrepostos',str(error)):return False
                latest=store.modify(dict(payload,allow_overlap=True))
            self.window.data=latest;self.window.render();self.window.status.set_text('Salvo · backup automático atualizado')
            self.message.set_text('Salvo neste computador');return True
        except Exception as error:self.message.set_text('Não foi salvo: '+str(error));return False

    def save(self):
        payload=dict(action='timesheet',date=self.day,**{k:v.get_text().strip() for k,v in self.fields.items()})
        if self.editing:payload.update(id=self.editing['id'],expected=self.editing)
        if self.commit(payload):
            self.reset(payload['end']);self.message.set_text('Salvo · próxima linha pronta');self.fields['description'].grab_focus()

    def edit(self,entry):
        if self.dirty and not self.ask('Descartar o preenchimento atual?','O registro salvo permanece no histórico.'):return
        self.window.select(entry['date']);self.editing=dict(entry);self.fill(entry);self.dirty=False
        self.editor_label.set_text('Editar atividade · '+entry['date']);self.fields['description'].grab_focus()

    def delete(self,entry):
        if self.ask('Excluir atividade?',entry['description']+'\nVocê poderá desfazer esta exclusão.'):
            if self.commit({'action':'timesheet_delete','id':entry['id']}) and self.editing and self.editing['id']==entry['id']:self.reset()

    def update_timer(self):
        active=self.sheet_data().get('timesheet_active');self.timer_button.set_label('Encerrar atividade' if active else 'Iniciar atividade agora')
        if active:
            started=datetime.fromisoformat(active['started']);minutes=max(0,int((datetime.now()-started).total_seconds()//60))
            self.active_label.set_text(active['description']+' · desde '+started.strftime('%d/%m %H:%M')+' · '+model.duration(minutes)+'\nEm andamento · início salvo; continua mesmo com a janela fechada.')
        else:self.active_label.set_text('')
        return True

    def timer_click(self,*_):
        if self.sheet_data().get('timesheet_active'):
            self.commit({'action':'timesheet_stop'});return
        dialog=Gtk.Dialog(title='Iniciar atividade agora',transient_for=self.window,modal=True)
        dialog.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Iniciar',Gtk.ResponseType.OK)
        box=dialog.get_content_area();box.set_margin_start(16);box.set_margin_end(16);box.set_spacing(8)
        box.add(Gtk.Label(label='Descrição',xalign=0));field=Gtk.Entry(text=self.fields['description'].get_text());field.set_max_length(1000)
        completion=Gtk.EntryCompletion();completion.set_model(self.fields['description'].get_completion().get_model());completion.set_text_column(0);completion.set_minimum_key_length(1)
        field.set_completion(completion);box.add(field)
        info=Gtk.Label(xalign=0,wrap=True);box.add(info);dialog.show_all()
        while dialog.run()==Gtk.ResponseType.OK:
            if self.commit({'action':'timesheet_start','description':field.get_text()}):break
            info.set_text(self.message.get_text())
        dialog.destroy()

    def export(self,*_):
        dialog=Gtk.Dialog(title='Exportar timesheet',transient_for=self.window,modal=True)
        dialog.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Escolher arquivo',Gtk.ResponseType.OK)
        box=dialog.get_content_area();box.set_spacing(8);box.set_margin_start(16);box.set_margin_end(16)
        a,b=model.bounds(self.day,self.period.get_active_id() or 'day');fields=[]
        for title,value in [('De · AAAA-MM-DD',a),('Até · AAAA-MM-DD',b)]:
            box.add(Gtk.Label(label=title,xalign=0));field=Gtk.Entry(text=value);box.add(field);fields.append(field)
        error=Gtk.Label(xalign=0);box.add(error);dialog.show_all()
        while dialog.run()==Gtk.ResponseType.OK:
            try:
                start,end=[date.fromisoformat(f.get_text().strip()).isoformat() for f in fields]
                if end<start:raise ValueError('O fim do período deve ser igual ou posterior ao início.')
                content=model.csv_text(model.get_sheet(store.modify({'action':'get'}),self.sheet_id)['timesheet'],start,end)
                chooser=Gtk.FileChooserDialog(title='Salvar CSV',transient_for=self.window,action=Gtk.FileChooserAction.SAVE)
                chooser.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Salvar',Gtk.ResponseType.OK);chooser.set_do_overwrite_confirmation(True)
                safe_name=''.join(c if c.isalnum() or c in '-_' else '_' for c in self.sheet_data()['name'])
                chooser.set_current_name(f'timesheet-{safe_name}-{start}-{end}.csv')
                try:
                    if chooser.run()==Gtk.ResponseType.OK:
                        Path(chooser.get_filename()).write_text(content,encoding='utf-8-sig');self.message.set_text('CSV exportado');break
                finally:chooser.destroy()
            except Exception as failure:error.set_text(str(failure))
        dialog.destroy()

    def can_close(self,*_):
        return not self.persist() if not self.readonly else False

    def cleanup(self,*_):
        if self.persist_timer:GLib.source_remove(self.persist_timer);self.persist_timer=0
        if not self.readonly:self.persist()
        if self.tick:GLib.source_remove(self.tick);self.tick=0

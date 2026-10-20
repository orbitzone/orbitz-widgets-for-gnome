"""Multi-account calendar chooser, Apple connection UI and external events."""
from datetime import date,datetime,timezone,timedelta
import threading,hashlib,re
from concurrent.futures import ThreadPoolExecutor
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,GLib,Pango
import apple_client as apple
import external_store as remote
import store,ui_state
import ics_client
from calendar_selector import CalendarSelector,below
import provider_connection_ui
from day_activity import external_activity, local_activity

class ExternalCalendars:
    def __init__(self,window,left,tabs):
        self.executor=ThreadPoolExecutor(max_workers=3)
        self.window=window;self.alive=True;self.busy=set();self.cancel_events=[];self.accounts=[];self.loading=False;self.sync_cancels={}
        self.controls=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6)
        left.pack_start(self.controls,False,False,0);left.reorder_child(self.controls,0)
        self.selector=CalendarSelector()
        self.controls.pack_start(self.selector,False,False,0)
        menu_row=Gtk.Box(spacing=4);self.controls.pack_start(menu_row,False,False,0)
        connect=Gtk.MenuButton();connect_content=Gtk.Box(spacing=6)
        connect_content.pack_start(Gtk.Label(label='Integrar calendário'),True,True,0)
        connect_content.pack_end(Gtk.Image.new_from_icon_name('pan-down-symbolic',Gtk.IconSize.MENU),False,False,0)
        connect.add(connect_content);menu_row.pack_start(connect,True,True,0)
        menu,menu_rows=below(connect)
        for label,callback in [('Apple / iCloud…',self.connect_apple),('Google Calendar…',self.connect_google),('Calendly…',self.connect_calendly),('Assinatura por link (.ics)…',self.connect_subscription),('Gerenciar conexões…',self.manage)]:
            item=Gtk.Button(label=label);item.set_relief(Gtk.ReliefStyle.NONE)
            def activate(_button,action=callback):menu.popdown();action()
            item.connect('clicked',activate);menu_rows.pack_start(item,False,False,0)
        menu_rows.show_all()
        refresh=Gtk.Button.new_from_icon_name('view-refresh-symbolic',Gtk.IconSize.MENU);refresh.set_tooltip_text('Atualizar eventos do calendário selecionado')
        refresh.connect('clicked',lambda *_:self.sync(True));menu_row.pack_end(refresh,False,False,0)
        cancel=Gtk.Button.new_from_icon_name('process-stop-symbolic',Gtk.IconSize.MENU);cancel.set_tooltip_text('Cancelar sincronização em andamento')
        cancel.get_accessible().set_name('Cancelar sincronização');cancel.connect('clicked',self.cancel_sync);menu_row.pack_end(cancel,False,False,0)
        self.status=Gtk.Label(xalign=0,wrap=True);self.status.set_max_width_chars(28);self.controls.pack_start(self.status,False,False,0)
        self.page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10,margin=12);self.page.page_id='events'
        self.title=Gtk.Label(xalign=0,wrap=True);self.page.pack_start(self.title,False,False,0)
        scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);self.page.pack_start(scroll,True,True,0)
        self.rows=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);scroll.add(self.rows)
        tabs.append_page(self.page,Gtk.Label(label='Eventos'))
        self.selector.connect('changed',self.selection_changed)
        window.calendar.connect('month-changed',lambda *_:self.sync())
        self.populate()
        self.timer=GLib.timeout_add_seconds(300,self.periodic)
        GLib.idle_add(self.initial)

    def initial(self):
        if self.alive:self.selection_changed()
        return False
    def periodic(self):
        if self.alive:self.sync()
        return self.alive
    def run(self,work,done):
        def worker():
            result=None;error=None
            try:result=work()
            except Exception as failure:error=failure
            def deliver():
                if self.alive:done(result,error)
                return False
            GLib.idle_add(deliver)
        self.executor.submit(worker)

    def populate(self,select=None):
        previous=select if select is not None else (self.selector.get_active_id() or ui_state.get('external-source','local'))
        try:
            remote.ensure_default_calendar()
            self.accounts=remote.read()['accounts']
        except Exception as error:self.accounts=[];self.status.set_text(str(error))
        self.loading=True;self.selector.remove_all();self.selector.append('local','Somente agenda local')
        ids=[]
        for account in self.accounts:
            if not account.get('enabled',True):continue
            for calendar in account['calendars']:
                identity=account['id']+'|'+calendar['id'];ids.append(identity)
                self.selector.append(identity,self.source_label(account,calendar))
        self.selector.set_active_id(previous if previous in ids else 'local');self.loading=False

    def context(self):
        identity=self.selector.get_active_id()
        for account in self.accounts:
            if not account.get('enabled',True):continue
            for calendar in account['calendars']:
                if identity==account['id']+'|'+calendar['id']:
                    year,month,_=self.window.calendar.get_date()
                    return account,calendar,f'{year:04d}-{month+1:02d}'
        return None
    def selected_cache(self):
        context=self.context()
        if not context:return None,{}
        account,calendar,month=context
        return context,remote.read()['cache'].get(remote.cache_key(account['id'],calendar['id'],month),{})

    def selection_changed(self,*_):
        if self.loading or not self.alive:return
        try:ui_state.set('external-source',self.selector.get_active_id())
        except Exception as error:self.status.set_text(str(error))
        self.render();self.window.mark_days();self.sync()

    def sync(self,force=False):
        if not self.alive:return
        year,month,_=self.window.calendar.get_date();month=f'{year:04d}-{month+1:02d}'
        selected=self.context()
        if selected:self.sync_context(selected,force)
        else:self.status.set_text('');self.render()
        for account in self.accounts:
            if not account.get('enabled',True):continue
            for calendar in account['calendars']:
                context=(account,calendar,month)
                if context!=selected:self.sync_context(context,force)

    def connect_google(self,*_):
        provider_connection_ui.connect_provider(self,'google')

    def connect_calendly(self,*_):
        provider_connection_ui.connect_provider(self,'calendly')

    def cancel_sync(self,*_,account_id=None):
        matched=0
        for owner,cancel in list(self.sync_cancels.values()):
            if account_id is None or owner==account_id:cancel.set();matched+=1
        if account_id is None:self.status.set_text('Interrompendo sincronização; último cache disponível mantido.' if matched else 'Nenhuma sincronização em andamento.')

    def sync_context(self,context,force=False):
        if not self.alive:return
        account,calendar,month=context
        if not account.get('enabled',True):return
        key=remote.cache_key(account['id'],calendar['id'],month)
        try:
            cache=remote.read()['cache'].get(key,{})
            if not force and cache.get('updated') and (datetime.now(timezone.utc)-datetime.fromisoformat(cache['updated'])).total_seconds()<300:
                if self.context()==context:self.cache_status(cache);self.render()
                return
        except Exception as error:
            if self.context()==context:self.status.set_text(str(error))
            return
        if key in self.busy:return
        self.busy.add(key)
        cancelled=threading.Event();self.cancel_events.append(cancelled);self.sync_cancels[key]=(account['id'],cancelled)
        if self.context()==context:self.status.set_text('Atualizando eventos…');self.render()
        def work():
            if cancelled.is_set():return
            current=next((a for a in remote.read()['accounts'] if a['id']==account['id']),None)
            if current is None or not current.get('enabled',True):return
            if account['provider'] in ('google','calendly'):
                import calendar_accounts
                events=calendar_accounts.events(account,calendar,month,cancel_event=cancelled)
            elif account['provider']=='ics':events=ics_client.events(calendar['url'],account['id'],calendar['id'],month)
            else:
                password=remote.Vault().get(account['id'])
                try:events=apple.AppleClient(account['email'],password).events(calendar,account['id'],month)
                finally:password=None
            if not cancelled.is_set() and self.alive:remote.put_cache(account['id'],calendar,month,events,datetime.now(timezone.utc).isoformat())
        def done(result,error):
            self.busy.discard(key);self.sync_cancels.pop(key,None)
            if cancelled in self.cancel_events:self.cancel_events.remove(cancelled)
            if cancelled.is_set():
                if self.context()==context:self.status.set_text('Sincronização interrompida; último cache disponível mantido.')
                return
            if self.context()!=context:self.window.mark_days();return
            if error:self.status.set_text(str(error)+'\nOs eventos já baixados foram preservados.')
            else:
                _,cache=self.selected_cache();self.cache_status(cache)
            self.render();self.window.mark_days()
        self.run(work,done)
    def cache_status(self,cache):
        if cache.get('updated'):
            stamp=datetime.fromisoformat(cache['updated']).astimezone(apple.ZONE).strftime('%d/%m %H:%M')
            self.status.set_text('Atualizado em '+stamp)
        else:self.status.set_text('Ainda não atualizado para este mês.')

    @staticmethod
    def is_holiday(event):
        # Observances (e.g. Teachers' Day) must not become public holidays.
        description=event.get('description','').split('\n')[0].strip().casefold()
        categories=event.get('categories','').casefold()
        if 'comemorativa' in description or 'observance' in description:return False
        return description.startswith(('feriado','public holiday','national holiday')) or bool(re.search(r'\b(holiday|feriado)\b',categories)) or event.get('title','').casefold().startswith('feriado')

    def day_context(self,day,data=None):
        data=remote.read() if data is None else data
        return external_activity(self.accounts,data.get('cache',{}),remote.cache_key,
            self.selector.get_active_id(),day,self.is_holiday,self.source_label)

    def mark_days(self,details=None):
        holidays={};details=dict(details or {})
        try:
            year,month,_=self.window.calendar.get_date()
            day=date(year,month+1,1);data=remote.read()
            while day.month==month+1 and day.year==year:
                events,others,holiday_text=self.day_context(day,data)
                if events or others:self.window.calendar.mark_day(day.day)
                if events:details.setdefault(day.day,[]).extend('Evento: '+e['title'] for e in events if not self.is_holiday(e))
                if holiday_text:holidays[day.day]=holiday_text
                day+=timedelta(days=1)
        except Exception as error:self.status.set_text(str(error))
        self.window.calendar.finish_marks(holidays,details)

    def render(self):
        if not self.alive:return
        for child in self.rows.get_children():child.destroy()
        try:
            context,cache=self.selected_cache()
            if not context:
                self.title.set_text('Calendários externos')
                self.rows.pack_start(Gtk.Label(label='Use “Integrar calendário” para conectar uma fonte.\nDepois, selecione um calendário para consultar os eventos e criar tarefas.',xalign=0,wrap=True),False,False,0)
            else:
                account,calendar,month=context;self.title.set_text(self.source_label(account,calendar)+' · '+date.fromisoformat(self.window.day).strftime('%d/%m/%Y'))
                events,_,_=self.day_context(date.fromisoformat(self.window.day))
                for event in events:
                    card=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6,margin_top=8,margin_bottom=8)
                    clock='Dia inteiro' if event['all_day'] else datetime.fromisoformat(event['start']).strftime('%H:%M')+' – '+datetime.fromisoformat(event['end']).strftime('%H:%M')
                    title=Gtk.Label(label=clock+' · '+event['title'],xalign=0,wrap=True);title.set_max_width_chars(65);card.pack_start(title,False,False,0)
                    if event.get('location'):card.pack_start(Gtk.Label(label=event['location'],xalign=0,wrap=True),False,False,0)
                    existing=next((t for t in self.window.data['tasks'] if t.get('external_source',{}).get('key')==event['key']),None)
                    action=Gtk.Button(label='Tarefa já criada' if existing else 'Criar tarefa')
                    action.set_sensitive(not existing);action.connect('clicked',lambda _,e=event,a=account,c=calendar:self.import_task(e,a,c));card.pack_start(action,False,False,0)
                    self.rows.pack_start(card,False,False,0)
                if not events:
                    text='Atualizando eventos deste mês…' if remote.cache_key(account['id'],calendar['id'],month) in self.busy else 'Nenhum evento nesta fonte neste dia.'
                    self.rows.pack_start(Gtk.Label(label=text,xalign=0,wrap=True),False,False,0)
            day=date.fromisoformat(self.window.day)
            _,other_holidays,_=self.day_context(day)
            for event,source in other_holidays:
                self.rows.pack_start(Gtk.Label(label='Feriado · '+event['title']+'\nFonte: '+source,xalign=0,wrap=True),False,False,0)
            tasks,sheets=local_activity(self.window.data,day)
            if tasks:
                text='Tarefas locais pendentes: '+str(len(tasks))+'\n'+'\n'.join(t['text'] for t in tasks)
                self.rows.pack_start(Gtk.Label(label=text,xalign=0,wrap=True),False,False,0)
                action=Gtk.Button(label='Abrir Tarefas');action.connect('clicked',lambda *_:self.window.show_area('tasks'))
                self.rows.pack_start(action,False,False,0)
            for sheet,entries in sheets:
                self.rows.pack_start(Gtk.Label(label='Horas locais · '+sheet['name']+' · '+str(len(entries))+' registro(s)',xalign=0,wrap=True),False,False,0)
                action=Gtk.Button(label='Abrir Horas · '+sheet['name'])
                action.connect('clicked',lambda _,identity=sheet['id']:self.window.focus_sheet(identity))
                self.rows.pack_start(action,False,False,0)
        except Exception as error:self.rows.pack_start(Gtk.Label(label=str(error),xalign=0,wrap=True),False,False,0)
        self.rows.show_all()

    def import_task(self,event,account,calendar):
        dialog=Gtk.Dialog(title='Criar tarefa a partir do evento',transient_for=self.window,modal=True)
        dialog.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Criar tarefa',Gtk.ResponseType.OK)
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10,margin=18);dialog.get_content_area().add(box)
        box.pack_start(Gtk.Label(label=self.source_label(account,calendar),xalign=0),False,False,0)
        fields={}
        for key,title,value in [('text','Tarefa',event['title']),('date','Data · AAAA-MM-DD',event['start'][:10]),('time','Horário · HH:MM · opcional','' if event['all_day'] else event['start'][11:16]),('reminder','Avisar quantos minutos antes?','10')]:
            box.add(Gtk.Label(label=title,xalign=0));field=Gtk.Entry(text=value);fields[key]=field;box.add(field)
        error=Gtk.Label(xalign=0,wrap=True);box.add(error);dialog.show_all()
        while dialog.run()==Gtk.ResponseType.OK:
            try:
                raw=fields['reminder'].get_text().strip()
                if not raw.isdigit():raise ValueError('Informe um número inteiro de minutos.')
                source=dict(key=event['key'],provider=account['provider'],account_id=account['id'],calendar_id=calendar['id'],calendar_name=self.source_label(account,calendar),uid=event['uid'],occurrence=event['occurrence'],start=event['start'],end=event['end'],all_day=event['all_day'])
                payload=dict(action='external_task',source=source,text=fields['text'].get_text(),date=fields['date'].get_text().strip(),time=fields['time'].get_text().strip(),reminder=int(raw))
                self.window.data=store.modify(payload);self.window.select(payload['date']);self.window.show_area('tasks');self.window.status.set_text('Tarefa criada a partir do evento · salva localmente');break
            except Exception as failure:error.set_text(str(failure))
        dialog.destroy()

    @staticmethod
    def source_label(account,calendar):
        return calendar['name'] if account['provider']=='ics' else account['label']+' · '+calendar['name']

    def connect_subscription(self,*_):
        dialog=Gtk.Dialog(title='Adicionar assinatura de calendário',transient_for=self.window,modal=True)
        dialog.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Adicionar',Gtk.ResponseType.OK)
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10,margin=18);dialog.get_content_area().add(box)
        fields={}
        for key,title,placeholder in [('name','Nome','Ex.: Feriados do Brasil'),('url','Endereço da assinatura','https://… ou webcal://…')]:
            box.add(Gtk.Label(label=title,xalign=0));field=Gtk.Entry();field.set_placeholder_text(placeholder);fields[key]=field;box.add(field)
        status=Gtk.Label(xalign=0,wrap=True);box.add(status);dialog.set_default_size(560,240);dialog.show_all()
        busy=[False];cancelled=threading.Event();self.cancel_events.append(cancelled);success=[None]
        while True:
            response=dialog.run()
            if response==Gtk.ResponseType.ACCEPT:break
            if response!=Gtk.ResponseType.OK:cancelled.set();break
            if busy[0]:continue
            try:account=ics_client.account(fields['name'].get_text(),fields['url'].get_text())
            except Exception as error:status.set_text(str(error));continue
            month=self.context()[2] if self.context() else f'{self.window.calendar.get_date()[0]:04d}-{self.window.calendar.get_date()[1]+1:02d}'
            busy[0]=True;dialog.set_response_sensitive(Gtk.ResponseType.OK,False);status.set_text('Verificando assinatura…')
            def work(account=account,month=month):
                calendar=account['calendars'][0];events=ics_client.events(calendar['url'],account['id'],calendar['id'],month)
                if cancelled.is_set():return None
                remote.add_account(account)
                remote.put_cache(account['id'],calendar,month,events,datetime.now(timezone.utc).isoformat())
                if cancelled.is_set():remote.remove_account(account['id']);return None
                return account
            def done(account,error):
                busy[0]=False
                if cancelled.is_set():
                    if account:remote.remove_account(account['id'])
                    return
                if error:status.set_text(str(error));dialog.set_response_sensitive(Gtk.ResponseType.OK,True)
                elif account:success[0]=account;dialog.response(Gtk.ResponseType.ACCEPT)
            self.run(work,done)
        dialog.destroy()
        if success[0]:
            account=success[0];self.populate(account['id']+'|'+account['calendars'][0]['id']);self.selection_changed()
            self.window.show_area('events')

    def connect_apple(self,*_):
        dialog=Gtk.Dialog(title='Conectar Apple / iCloud',transient_for=self.window,modal=True)
        dialog.add_buttons('Cancelar',Gtk.ResponseType.CANCEL,'Conectar',Gtk.ResponseType.OK);dialog.set_default_size(510,350)
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10,margin=18);dialog.get_content_area().add(box)
        box.add(Gtk.Label(label='Use uma senha específica de aplicativo gerada na sua conta Apple.\nA conexão consulta eventos; seus calendários Apple não serão alterados.',xalign=0,wrap=True))
        box.add(Gtk.LinkButton(uri='https://support.apple.com/pt-br/102654',label='Como gerar a senha específica de app'))
        fields={}
        for key,title,placeholder in [('label','Nome da conexão','Ex.: Apple pessoal'),('email','E-mail da conta Apple','voce@icloud.com'),('password','Senha específica de aplicativo','xxxx-xxxx-xxxx-xxxx')]:
            box.add(Gtk.Label(label=title,xalign=0));field=Gtk.Entry();field.set_placeholder_text(placeholder)
            field.set_visibility(key!='password');field.set_max_length(200);fields[key]=field;box.add(field)
        status=Gtk.Label(xalign=0,wrap=True);box.add(status);dialog.show_all()
        cancelled=threading.Event();self.cancel_events.append(cancelled);running=[False];success=[None]
        while True:
            response=dialog.run()
            if response==Gtk.ResponseType.ACCEPT:break
            if response!=Gtk.ResponseType.OK:
                cancelled.set();break
            if running[0]:continue
            label=fields['label'].get_text().strip();email=fields['email'].get_text().strip();password=fields['password'].get_text().strip()
            if not label or not email or '@' not in email or not password:status.set_text('Preencha o nome, o e-mail e a senha específica de aplicativo.');continue
            if any(a.get('email','').casefold()==email.casefold() for a in self.accounts):status.set_text('Esta conta já está conectada. Use Gerenciar conexões para desconectar e reconectar.');continue
            running[0]=True;dialog.set_response_sensitive(Gtk.ResponseType.OK,False);status.set_text('Conectando ao iCloud… Isso pode levar alguns segundos.')
            identity='apple-'+hashlib.sha256(email.casefold().encode()).hexdigest()
            def work(email=email,password=password,label=label,identity=identity):
                calendars=apple.AppleClient(email,password).discover()
                if cancelled.is_set():return None
                vault=remote.Vault();vault.put(identity,password)
                try:
                    if cancelled.is_set():vault.delete(identity);return None
                    account=dict(id=identity,provider='icloud',label=label,email=email,calendars=calendars)
                    remote.add_account(account)
                    if cancelled.is_set():remote.remove_account(identity);vault.delete(identity);return None
                    return account
                except Exception:
                    try:vault.delete(identity)
                    except Exception:pass
                    raise
            def done(account,error):
                running[0]=False
                if cancelled.is_set():
                    if account:self.run(lambda:(remote.remove_account(account['id']),remote.Vault().delete(account['id'])),lambda *_:None)
                    return
                if error:status.set_text(str(error));dialog.set_response_sensitive(Gtk.ResponseType.OK,True)
                elif account:
                    success[0]=account;dialog.response(Gtk.ResponseType.ACCEPT)
            self.run(work,done)
            password=None
        fields['password'].set_text('');dialog.destroy()
        if success[0]:
            account=success[0];self.populate(account['id']+'|'+account['calendars'][0]['id']);self.selection_changed()
            self.window.show_area('events')

    def set_builtin_enabled(self,account,enabled):
        if not enabled:self.cancel_sync(account_id=account['id'])
        remote.set_builtin_enabled(account['id'],enabled)
        self.populate();self.selection_changed()

    def disconnect_account(self,account):
        if remote.is_builtin(account):
            self.set_builtin_enabled(account,False);return
        self.cancel_sync(account_id=account['id'])
        if account['provider'] in ('google','calendly'):
            import calendar_accounts
            calendar_accounts.disconnect(account)
        else:
            if account['provider']=='icloud':remote.Vault().delete(account['id'])
            remote.remove_account(account['id'])

    def manage(self,*_):
        dialog=Gtk.Dialog(title='Conexões de calendário',transient_for=self.window,modal=True)
        dialog.add_button('Fechar',Gtk.ResponseType.CLOSE);dialog.set_default_size(540,320)
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,margin=16);dialog.get_content_area().add(box)
        status=Gtk.Label(xalign=0,wrap=True);dialog.get_content_area().pack_end(status,False,False,8)
        def populate():
            for child in box.get_children():child.destroy()
            remote.ensure_default_calendar()
            accounts=remote.read()['accounts']
            for account in accounts:
                row=Gtk.Box(spacing=10);box.add(row)
                builtin=remote.is_builtin(account)
                description=('Fonte pública · Ativada' if account.get('enabled',True) else 'Fonte pública · Desativada') if builtin else account.get('email',{'google':'Google Calendar','calendly':'Calendly','ics':'Assinatura por link'}.get(account['provider'],'iCloud'))
                title=Gtk.Label(label=('Brasil · Datas comemorativas' if builtin else account['label'])+'\n'+description,xalign=0,wrap=True)
                title.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);title.set_max_width_chars(40);row.pack_start(title,True,True,0)
                if builtin:
                    toggle=Gtk.Button(label='Desativar' if account.get('enabled',True) else 'Ativar')
                    toggle.connect('clicked',lambda _,a=account:change_enabled(a));row.pack_end(toggle,False,False,0)
                else:
                    remove=Gtk.Button(label='Desconectar');remove.connect('clicked',lambda _,a=account:disconnect(a));row.pack_end(remove,False,False,0)
            if not accounts:box.add(Gtk.Label(label='Nenhuma conta conectada.',xalign=0))
            box.show_all()
        def change_enabled(account):
            try:
                enabled=not account.get('enabled',True)
                self.set_builtin_enabled(account,enabled)
                status.set_text('Fonte pública ativada.' if enabled else 'Fonte pública desativada; cache e atividades locais preservados.')
                populate()
            except Exception as error:status.set_text(str(error))
        def disconnect(account):
            confirm=Gtk.MessageDialog(transient_for=dialog,modal=True,message_type=Gtk.MessageType.QUESTION,buttons=Gtk.ButtonsType.OK_CANCEL,text='Desconectar '+account['label']+'?')
            confirm.format_secondary_text('Os eventos baixados desta conexão serão removidos. Tarefas criadas e registros de horas permanecerão salvos.')
            answer=confirm.run();confirm.destroy()
            if answer!=Gtk.ResponseType.OK:return
            status.set_text('Desconectando…')
            def work():
                self.disconnect_account(account)
            def done(result,error):
                if not dialog.get_visible():return
                status.set_text(str(error) if error else 'Conexão removida.');self.populate();self.selection_changed();populate()
            self.run(work,done)
        populate();dialog.show_all();dialog.run();dialog.destroy()

    def cleanup(self):
        self.alive=False
        self.executor.shutdown(wait=False,cancel_futures=True)
        for cancel in self.cancel_events:cancel.set()
        if self.timer:GLib.source_remove(self.timer);self.timer=0

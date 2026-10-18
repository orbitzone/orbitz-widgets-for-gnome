/* Local calendar, task dialogs, sticky note and reminders for GNOME Shell 42. */
const {Clutter,Gio,GLib,St,Pango,Shell}=imports.gi;
const Main=imports.ui.main;
const ModalDialog=imports.ui.modalDialog;
let placement=null,windowSignal=0;
const placementTimers=new Set();
let root=null,storeFile=null,monitor=null,timer=0,refreshTimer=0,generation=0;
let data={notes:'',tasks:[]},agenda=null,alerts=null;
const dialogs=new Set(),stickies=new Set(),announced=new Set();
const pad=n=>String(n).padStart(2,'0');
var dayKey=date=>`${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}`;
var taskStamp=task=>[task.date,task.time,task.reminder].join('|');
var dueTasks=(tasks,now=new Date())=>tasks.filter(task=>{
    if(task.done||!task.time||task.dismissed===taskStamp(task))return false;
    const start=new Date(`${task.date}T${task.time}:00`).getTime();
    const minutes=Number(task.reminder??10);
    return Number.isFinite(start)&&now.getTime()>=start-minutes*60000&&now.getTime()<start+(minutes===0?60000:0);
});
function label(text,style=''){
    const actor=new St.Label({text,style});actor.clutter_text.set_line_wrap(true);actor.clutter_text.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);return actor;
}
function button(text,action,style=''){
    const actor=new St.Button({label:text,reactive:true,can_focus:true,style:`padding:8px 12px;border-radius:7px;background-color:#344457;color:#edf1f5;${style}`});
    actor.connect('clicked',action);return actor;
}
function dialog(title,width=780){
    const modal=new ModalDialog.ModalDialog({styleClass:null});
    modal.dialogLayout.set_style(`background-color:#20262e;color:#edf1f5;border-radius:16px;padding:22px;width:${Math.min(width,Math.max(400,Main.layoutManager.primaryMonitor.width-100))}px;`);
    modal.contentLayout.set_style('spacing:14px;');modal.contentLayout.add_child(label(title,'font-size:21px;font-weight:bold;'));
    modal._plannerAlive=true;dialogs.add(modal);
    modal.connect('destroy',()=>{modal._plannerAlive=false;dialogs.delete(modal);if(agenda===modal)agenda=null;});return modal;
}
function field(box,title,value='',hint=''){
    box.add_child(label(title,'color:#b5c4d3;font-size:12px;'));
    const entry=new St.Entry({text:String(value),hint_text:hint,can_focus:true,x_expand:true,style:'background-color:#141b23;color:#f1f4f7;border-radius:7px;padding:10px;'});
    box.add_child(entry);return entry;
}
async function request(payload){
    const epoch=generation;
    const proc=Gio.Subprocess.new(['/usr/bin/python3',GLib.build_filenamev([root,'planner','store.py'])],Gio.SubprocessFlags.STDIN_PIPE|Gio.SubprocessFlags.STDOUT_PIPE|Gio.SubprocessFlags.STDERR_PIPE);
    const [stdout]=await proc.communicate_utf8_async(JSON.stringify(payload),null);
    const result=JSON.parse(stdout);
    if(!proc.get_successful()||!result.ok)throw Error(result.error||'Não foi possível salvar.');
    if(epoch===generation&&root){data=result.data;updateStickies();updateAlerts();}
    return result.data;
}
function problem(error){Main.notifyError('Agenda e notas',String(error.message||error));}
const noteColors=[['Amarelo','#ffe293'],['Rosa','#ffd6df'],['Verde','#d9edb5'],['Azul','#cce7ff'],['Lilás','#e5d7fa'],['Pêssego','#ffdbb5']];
var styleSticky=function(container){
    const color=noteColors.some(item=>item[1]===data.note_color)?data.note_color:'#ffe293';
    container.set_style(`padding:18px;background-color:${color};color:#000000;border-radius:10px;`);
};
function updateStickies(){
    for(const card of stickies){
        styleSticky(card.container);
        // Bounded plain text keeps desktop layout independent of note size.
        const lines=data.notes.split('\n');
        const preview=lines.slice(0,9).join('\n').slice(0,700);
        card.preview.set_text(preview || 'Clique para escrever sua primeira nota…');
        const pending=data.tasks.filter(task=>!task.done).length;
        card.footer.set_text(`${pending} tarefa${pending===1?'':'s'} pendente${pending===1?'':'s'} · Clique para editar`);
    }
}
var openNote=function(container=null){
    if(!root)return;
    if(!container)container=[...stickies][0]?.container;
    if(container){
        const [x,y]=container.get_transformed_position();
        const [width,height]=container.get_transformed_size();
        if([x,y,width,height].every(Number.isFinite)&&width>0&&height>0)
            placement={x:Math.round(x),y:Math.round(y),width:Math.round(width),height:Math.round(height)};
    }
    // Existing editor windows also follow the current widget position.
    for(const actor of global.get_window_actors())positionEditor(actor.meta_window);
    try{
        const proc=Gio.Subprocess.new(['/usr/bin/python3',GLib.build_filenamev([root,'planner','editor.py'])],Gio.SubprocessFlags.NONE);
        proc.wait_async(null,(process,result)=>{try{process.wait_finish(result);if(!process.get_successful())Main.notifyError('Notas rápidas','Não foi possível abrir o editor.');}catch(error){logError(error,'Editor de notas');}});
    }catch(error){problem(error);}
};
var createSticky=function(container,bindClick){
    styleSticky(container);
    const header=new St.BoxLayout({style:'spacing:8px;margin-bottom:12px;',x_expand:true});
    const title=label('NOTAS RÁPIDAS','font-size:12px;font-weight:bold;color:#000000;');
    title.x_expand=true;header.add_child(title);container.add_child(header);
    const palette=new St.BoxLayout({visible:false,style:'spacing:7px;margin-bottom:12px;'});
    const picker=new St.Button({reactive:true,can_focus:true,accessible_name:'Trocar cor do post-it',style:'padding:2px;color:#000000;'});
    picker.set_child(new St.Icon({icon_name:'applications-graphics-symbolic',icon_size:18,style:'color:#000000;'}));
    header.add_child(picker);container.add_child(palette);
    bindClick(picker,()=>{palette.visible=!palette.visible;});
    for(const [name,color] of noteColors){
        const swatch=new St.Button({reactive:true,can_focus:true,accessible_name:name,style:`width:27px;height:27px;background-color:${color};border:1px solid rgba(0,0,0,0.3);border-radius:14px;`});
        palette.add_child(swatch);bindClick(swatch,async()=>{palette.hide();try{await request({action:'note_color',color});}catch(error){problem(error);}});
    }
    const preview=label('Carregando…','font-size:15px;color:#000000;');
    preview.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
    const edit=new St.Button({reactive:true,can_focus:true,x_expand:true,height:205,child:preview,
        accessible_name:'Editar nota rápida',style:'padding:0;text-align:left;'});
    preview.x_align=Clutter.ActorAlign.START;preview.y_align=Clutter.ActorAlign.START;
    container.add_child(edit);bindClick(edit,()=>openNote(container));
    const footer=label('Clique para editar','font-size:10px;color:#3d3420;margin-top:12px;');container.add_child(footer);
    const card={container,preview,footer};stickies.add(card);
    edit.connect('destroy',()=>stickies.delete(card));updateStickies();
};

function taskEditor(day,task,refresh){
    const modal=dialog(task?'Editar tarefa':'Nova tarefa',570);
    const title=field(modal.contentLayout,'Tarefa',task?.text||'','O que você precisa fazer?');
    const dates=new St.BoxLayout({style:'spacing:14px;'});modal.contentLayout.add_child(dates);
    const left=new St.BoxLayout({vertical:true,x_expand:true,style:'spacing:6px;'}),right=new St.BoxLayout({vertical:true,x_expand:true,style:'spacing:6px;'});dates.add_child(left);dates.add_child(right);
    const date=field(left,'Dia · AAAA-MM-DD',task?.date||day);
    const time=field(right,'Horário · HH:MM',task?.time||'','Sem horário = dia inteiro');
    const reminder=field(modal.contentLayout,'Exibir alerta quantos minutos antes?',task?.reminder??10);
    const choices=new St.BoxLayout({style:'spacing:6px;'});modal.contentLayout.add_child(choices);
    for(const minutes of [0,5,10,15,30,60])choices.add_child(button(minutes===0?'Na hora':`${minutes} min`,()=>reminder.set_text(String(minutes)),'padding:6px 9px;'));
    const status=label('O aviso fica visível até o horário da tarefa ou até ser dispensado.\nSem horário, a tarefa aparece só no calendário.','font-size:12px;color:#b5c4d3;');modal.contentLayout.add_child(status);
    let saving=false;
    const save=async()=>{
        if(saving)return;
        const value=reminder.get_text().trim();
        if(!/^\d+$/.test(value)){status.text='Informe os minutos de antecedência, de 0 a 10080.';return;}
        saving=true;status.text='Salvando…';
        try{
            await request({action:'task',id:task?.id,text:title.get_text(),date:date.get_text().trim(),time:time.get_text().trim(),reminder:Number(value)});
            if(modal._plannerAlive)modal.close();refresh();
        }catch(error){if(modal._plannerAlive)status.text=error.message;}finally{saving=false;}
    };
    const buttons=[{label:'Cancelar',key:Clutter.KEY_Escape,action:()=>modal.close()}];
    if(task)buttons.push({label:'Excluir',action:async()=>{
        if(saving)return;saving=true;
        try{await request({action:'delete',id:task.id});if(modal._plannerAlive)modal.close();refresh();}
        catch(error){if(modal._plannerAlive)status.text=error.message;}finally{saving=false;}
    }});
    buttons.push({label:'Salvar tarefa',default:true,action:save});modal.setButtons(buttons);modal.setInitialKeyFocus(title);modal.open();
}
var openCalendar=function(initialDay=null){
    if(agenda){agenda.close();return;}
    const modal=dialog('Calendário e tarefas');agenda=modal;
    let selectedDay=initialDay||dayKey(new Date());let month=new Date(`${selectedDay}T12:00:00`);month.setDate(1);
    const body=new St.BoxLayout({vertical:true,style:'spacing:12px;'});modal.contentLayout.add_child(body);
    let renderVersion=0;
    const draw=()=>{
        if(!modal._plannerAlive)return;body.destroy_all_children();
        const layout=new St.BoxLayout({style:'spacing:22px;'});body.add_child(layout);
        const calendar=new St.BoxLayout({vertical:true,style:'spacing:6px;width:320px;'});layout.add_child(calendar);
        const nav=new St.BoxLayout({style:'spacing:7px;'});calendar.add_child(nav);
        nav.add_child(button('‹',()=>{month.setMonth(month.getMonth()-1);draw();}));
        const monthTitle=label(month.toLocaleDateString('pt-BR',{month:'long',year:'numeric'}),'font-weight:bold;font-size:15px;');monthTitle.x_expand=true;monthTitle.y_align=Clutter.ActorAlign.CENTER;nav.add_child(monthTitle);
        nav.add_child(button('›',()=>{month.setMonth(month.getMonth()+1);draw();}));
        const weekdays=new St.BoxLayout();calendar.add_child(weekdays);
        for(const name of ['D','S','T','Q','Q','S','S'])weekdays.add_child(label(name,'width:44px;text-align:center;color:#aabacb;font-size:12px;'));
        const year=month.getFullYear(),index=month.getMonth(),days=new Date(year,index+1,0).getDate(),offset=month.getDay();
        const marked=new Set(data.tasks.filter(t=>!t.done).map(t=>t.date));let row;
        for(let slot=0;slot<Math.ceil((offset+days)/7)*7;slot++){
            if(slot%7===0){row=new St.BoxLayout({style:'spacing:2px;'});calendar.add_child(row);}
            const day=slot-offset+1;
            if(day<1||day>days){row.add_child(new St.Widget({style:'width:42px;height:38px;'}));continue;}
            const key=dayKey(new Date(year,index,day));
            row.add_child(button(`${day}${marked.has(key)?' •':''}`,()=>{selectedDay=key;draw();},`padding:4px 0;width:42px;height:30px;font-size:12px;background-color:${key===selectedDay?'#3679a7':key===dayKey(new Date())?'#405a45':'#293442'};`));
        }
        calendar.add_child(button('Hoje',()=>{selectedDay=dayKey(new Date());month=new Date();month.setDate(1);draw();},'margin-top:6px;'));
        const tasks=new St.BoxLayout({vertical:true,x_expand:true,style:'spacing:9px;width:365px;'});layout.add_child(tasks);
        tasks.add_child(label(new Date(`${selectedDay}T12:00:00`).toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long'}),'font-size:16px;font-weight:bold;'));
        tasks.add_child(button('+ Adicionar tarefa',()=>taskEditor(selectedDay,null,refresh)));
        const scroll=new St.ScrollView({style:'max-height:300px;min-height:200px;',hscrollbar_policy:St.PolicyType.NEVER,vscrollbar_policy:St.PolicyType.AUTOMATIC});tasks.add_child(scroll);
        const list=new St.BoxLayout({vertical:true,style:'spacing:8px;'});scroll.add_actor(list);
        const items=data.tasks.filter(t=>t.date===selectedDay).sort((a,b)=>Number(a.done)-Number(b.done)||(a.time||'').localeCompare(b.time||''));
        if(!items.length)list.add_child(label('Nenhuma tarefa para este dia.','color:#aabacb;margin-top:18px;'));
        for(const task of items){
            const card=new St.BoxLayout({style:'spacing:8px;padding:9px;background-color:#293442;border-radius:8px;'});list.add_child(card);
            card.add_child(button(task.done?'✓':'○',async()=>{try{await request({action:'toggle',id:task.id});draw();}catch(error){problem(error);}},'padding:6px;'));
            const details=new St.BoxLayout({vertical:true,x_expand:true,style:'spacing:5px;'});
            const title=label(task.text,`font-size:14px;color:${task.done?'#94a99d':'#edf1f5'};`);title.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);details.add_child(title);
            details.add_child(label(task.time?`${task.time} · aviso ${task.reminder===0?'na hora':task.reminder+' min antes'}`:'Dia inteiro · sem alerta','font-size:11px;color:#aabacb;'));
            const edit=new St.Button({reactive:true,can_focus:true,child:details,x_expand:true,accessible_name:'Editar tarefa: '+task.text});edit.connect('clicked',()=>taskEditor(selectedDay,task,refresh));card.add_child(edit);
        }
    };
    const refresh=async()=>{
        const version=++renderVersion;
        try{await request({action:'get'});if(version===renderVersion)draw();}
        catch(error){if(modal._plannerAlive){body.destroy_all_children();body.add_child(label(error.message,'color:#ffab91;'));}}
    };
    modal._plannerRefresh=refresh;modal._plannerRedraw=draw;modal.setButtons([{label:'Fechar',key:Clutter.KEY_Escape,action:()=>modal.close()}]);draw();modal.open();refresh();
};
function updateAlerts(){
    if(!root)return;
    const due=dueTasks(data.tasks);
    if(!due.length){alerts?.destroy();alerts=null;return;}
    if(!alerts){alerts=new St.BoxLayout({vertical:true,reactive:true,style:'spacing:8px;width:345px;'});Main.layoutManager.addChrome(alerts);}
    alerts.destroy_all_children();
    const screen=Main.layoutManager.primaryMonitor;alerts.set_position(screen.x+screen.width-370,screen.y+60);
    for(const task of due.slice(0,4)){
        const card=new St.BoxLayout({vertical:true,style:'background-color:#fff0b6;color:#392b0f;border:1px solid #cba84e;border-radius:12px;padding:14px;spacing:8px;'});alerts.add_child(card);
        card.add_child(label(`TAREFA ÀS ${task.time}`,'font-weight:bold;font-size:12px;color:#73541d;'));
        card.add_child(label(task.text,'font-size:16px;color:#392b0f;'));
        const actions=new St.BoxLayout({style:'spacing:8px;'});card.add_child(actions);
        actions.add_child(button('Abrir agenda',()=>openCalendar(task.date)));
        actions.add_child(button('Dispensar',async()=>{try{await request({action:'dismiss',id:task.id,stamp:taskStamp(task)});}catch(error){problem(error);}}));
        const key=task.id+'|'+taskStamp(task);
        if(!announced.has(key)){announced.add(key);Main.notify('Tarefa às '+task.time,task.text);}
    }
    if(due.length>4)alerts.add_child(label(`+ ${due.length-4} tarefas na agenda`,'color:#ffffff;background-color:#293442;padding:8px;'));
    if(announced.size>4000)announced.clear();
}
function positionEditor(window){return false;}

var enable=function(extensionPath){
    if(root)return;root=extensionPath;generation++;
    const directory=GLib.build_filenamev([GLib.get_user_data_dir(),'orbitz-widgets']);GLib.mkdir_with_parents(directory,448);
    storeFile=Gio.File.new_for_path(GLib.build_filenamev([directory,'notes.json']));
    const refresh=()=>request({action:'get'}).then(()=>{if(agenda?._plannerAlive)agenda._plannerRedraw();}).catch(error=>logError(error,'Agenda local'));
    monitor=Gio.File.new_for_path(directory).monitor_directory(Gio.FileMonitorFlags.NONE,null);
    monitor.connect('changed',(_monitor,file,other)=>{
        if(file?.get_basename()!=='notes.json'&&other?.get_basename()!=='notes.json')return;
        if(refreshTimer)GLib.source_remove(refreshTimer);
        refreshTimer=GLib.timeout_add(GLib.PRIORITY_DEFAULT,200,()=>{refreshTimer=0;refresh();return GLib.SOURCE_REMOVE;});
    });
    timer=GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,10,()=>{updateAlerts();return GLib.SOURCE_CONTINUE;});refresh();
};
var disable=function(){
    if(windowSignal){global.display.disconnect(windowSignal);windowSignal=0;}
    for(const id of placementTimers)GLib.source_remove(id);placementTimers.clear();placement=null;
    generation++;root=null;monitor?.cancel();monitor=null;
    if(timer)GLib.source_remove(timer);timer=0;if(refreshTimer)GLib.source_remove(refreshTimer);refreshTimer=0;
    for(const modal of [...dialogs])modal.destroy();dialogs.clear();agenda=null;
    alerts?.destroy();alerts=null;stickies.clear();announced.clear();data={notes:'',tasks:[]};
};

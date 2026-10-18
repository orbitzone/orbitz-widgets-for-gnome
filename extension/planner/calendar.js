/* Calendar reminders run in GNOME Shell, including while the agenda is closed. */
const {Clutter,Gio,GLib,St,Pango}=imports.gi;
const Main=imports.ui.main;
const Me=imports.misc.extensionUtils.getCurrentExtension();
const Reminders=Me.imports.planner.reminders;
let root=null,monitor=null,timer=0,refreshTimer=0,generation=0,anchorProvider=null;
let data={tasks:[]},external={accounts:[],cache:{}},ledger={},alerts=null,signature='';
let directory=null;
const cards=new Map();
const pad=n=>String(n).padStart(2,'0');
var dayKey=date=>`${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}`;
var taskStamp=Reminders.stamp;
var dueTasks=(tasks,now=new Date())=>tasks.filter(t=>Reminders.collect({tasks:[t]},{},now.getTime()).length);
function jsonFile(name,fallback){
    try{
        const [ok,bytes]=Gio.File.new_for_path(GLib.build_filenamev([directory,name])).load_contents(null);
        return ok?JSON.parse(new TextDecoder().decode(bytes)):fallback;
    }catch(error){return fallback;}
}
function saveLedger(){
    try{
        const cutoff=Date.now()-7*86400000;
        for(const [key,value] of Object.entries(ledger))if(value.time<cutoff)delete ledger[key];
        const file=Gio.File.new_for_path(GLib.build_filenamev([directory,'reminder-state.json']));
        file.replace_contents(JSON.stringify(ledger),null,false,Gio.FileCreateFlags.PRIVATE|Gio.FileCreateFlags.REPLACE_DESTINATION,null);
    }catch(error){logError(error,'Estado dos lembretes');}
}
function label(text,style=''){
    const actor=new St.Label({text,style});actor.clutter_text.set_line_wrap(true);actor.clutter_text.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);return actor;
}
function button(text,action){
    const actor=new St.Button({label:text,reactive:true,can_focus:true,style:'padding:6px 10px;border-radius:7px;background-color:#344457;color:#edf1f5;'});
    actor.connect('clicked',action);return actor;
}
async function request(payload){
    const epoch=generation;
    const proc=Gio.Subprocess.new(['/usr/bin/python3',GLib.build_filenamev([root,'planner','store.py'])],Gio.SubprocessFlags.STDIN_PIPE|Gio.SubprocessFlags.STDOUT_PIPE|Gio.SubprocessFlags.STDERR_PIPE);
    const [stdout]=await proc.communicate_utf8_async(JSON.stringify(payload),null);
    const result=JSON.parse(stdout);
    if(!proc.get_successful()||!result.ok)throw Error(result.error||'Não foi possível salvar.');
    if(epoch===generation&&root){data=result.data;updateAlerts();}
    return result.data;
}
function problem(error){Main.notifyError('Agenda',String(error.message||error));}
var openCalendar=function(initialDay=null){
    if(!root)return;
    try{
        const argv=['/usr/bin/env','GDK_BACKEND=x11','/usr/bin/python3',GLib.build_filenamev([root,'planner','calendar-app.py'])];
        if(typeof initialDay==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(initialDay))argv.push(initialDay);
        const proc=Gio.Subprocess.new(argv,Gio.SubprocessFlags.NONE);
        proc.wait_async(null,(process,result)=>{try{process.wait_finish(result);if(!process.get_successful())problem(Error('Não foi possível abrir o calendário.'));}catch(error){logError(error,'Calendário');}});
    }catch(error){problem(error);}
};
function sound(){
    try{
        const executable=GLib.find_program_in_path('canberra-gtk-play');
        if(executable)Gio.Subprocess.new([executable,'--id','alarm-clock-elapsed','--description','Lembrete da agenda'],Gio.SubprocessFlags.STDOUT_SILENCE|Gio.SubprocessFlags.STDERR_SILENCE);
    }catch(error){logError(error,'Som do lembrete');}
}
function clearCards(){alerts?.destroy();alerts=null;cards.clear();signature='';}
function positionCards(){
    if(!alerts)return;
    let anchor=null;
    try{anchor=anchorProvider?.();}catch(error){/* Widgets can be rebuilding. */}
    const monitors=Main.layoutManager.monitors||[];
    const screen=(anchor&&monitors.find(m=>anchor.x>=m.x&&anchor.x<m.x+m.width&&anchor.y>=m.y&&anchor.y<m.y+m.height))||Main.layoutManager.primaryMonitor;
    if(!screen)return;
    const width=Math.min(345,screen.width-24);alerts.width=width;
    const height=alerts.height||220;
    let x=anchor?anchor.x:screen.x+screen.width-width-20;
    let y=anchor?anchor.y+anchor.height+10:screen.y+60;
    if(y+height>screen.y+screen.height-12&&anchor)y=anchor.y-height-10;
    x=Math.max(screen.x+12,Math.min(x,screen.x+screen.width-width-12));
    y=Math.max(screen.y+12,Math.min(y,screen.y+screen.height-height-12));
    alerts.set_position(Math.round(x),Math.round(y));
}
async function dismiss(item){
    try{
        if(item.type==='task')await request({action:'dismiss',id:item.id,stamp:item.stamp});
        ledger[item.key]={time:Date.now(),dismissed:true};saveLedger();updateAlerts();
    }catch(error){problem(error);}
}
function updateAlerts(){
    if(!root)return;
    if(Main.sessionMode?.isLocked){clearCards();return;}
    const now=Date.now();
    const due=Reminders.collect(data,external,now).filter(item=>!ledger[item.key]?.dismissed);
    if(!due.length){clearCards();return;}
    const shown=due.slice(0,3),next=shown.map(i=>i.key).join('|')+'|'+due.length;
    if(next!==signature){
        clearCards();signature=next;
        alerts=new St.BoxLayout({vertical:true,reactive:true,style:'spacing:8px;width:345px;'});
        Main.layoutManager.addChrome(alerts);
        for(const item of shown){
            const card=new St.BoxLayout({vertical:true,reactive:true,style:'background-color:rgba(24,29,36,0.97);color:#ffffff;border:1px solid #e5b94b;border-radius:12px;padding:14px;spacing:7px;'});
            alerts.add_child(card);
            card.add_child(label(`${item.type==='task'?'TAREFA':'EVENTO'} ÀS ${item.time}`,'font-size:11px;font-weight:bold;color:#f6c453;'));
            card.add_child(label(item.title,'font-size:16px;font-weight:bold;color:#ffffff;'));
            const remaining=label(Reminders.countdown(item.start-now),'font-size:15px;color:#ffffff;');card.add_child(remaining);cards.set(item.key,remaining);
            card.add_child(label(item.source,'font-size:11px;color:#bcc5d0;'));
            const actions=new St.BoxLayout({style:'spacing:8px;'});card.add_child(actions);
            actions.add_child(button('Abrir agenda',()=>openCalendar(item.day)));
            actions.add_child(button('Dispensar',()=>dismiss(item)));
        }
        if(due.length>3)alerts.add_child(label(`+ ${due.length-3} lembretes na agenda`,'color:#ffffff;background-color:#293442;padding:8px;'));
        alerts.connect('notify::height',positionCards);
    }
    let play=false;
    for(const item of shown){
        cards.get(item.key)?.set_text(Reminders.countdown(item.start-now));
        if(!ledger[item.key]){
            ledger[item.key]={time:now,dismissed:false};
            Main.notify(item.title,Reminders.countdown(item.start-now)+' · '+item.source);play=true;
        }
    }
    if(play){saveLedger();sound();}
    positionCards();
}
function refreshFiles(){
    if(!root)return;
    const fresh=jsonFile('notes.json',null);if(fresh)data=fresh;
    external=jsonFile('external-calendars.json',{accounts:[],cache:{}});
    updateAlerts();
}
var enable=function(extensionPath,provider=null){
    if(root)return;root=extensionPath;generation++;anchorProvider=provider;
    directory=GLib.build_filenamev([GLib.get_user_data_dir(),'orbitz-widgets']);GLib.mkdir_with_parents(directory,448);
    ledger=jsonFile('reminder-state.json',{});
    monitor=Gio.File.new_for_path(directory).monitor_directory(Gio.FileMonitorFlags.NONE,null);
    monitor.connect('changed',(_monitor,file,other)=>{
        const names=['notes.json','external-calendars.json'];
        if(!names.includes(file?.get_basename())&&!names.includes(other?.get_basename()))return;
        if(refreshTimer)GLib.source_remove(refreshTimer);
        refreshTimer=GLib.timeout_add(GLib.PRIORITY_DEFAULT,200,()=>{refreshTimer=0;refreshFiles();return GLib.SOURCE_REMOVE;});
    });
    timer=GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT,1,()=>{updateAlerts();return GLib.SOURCE_CONTINUE;});refreshFiles();
};
var disable=function(){
    generation++;root=null;anchorProvider=null;monitor?.cancel();monitor=null;
    if(timer)GLib.source_remove(timer);timer=0;if(refreshTimer)GLib.source_remove(refreshTimer);refreshTimer=0;
    clearCards();data={tasks:[]};external={accounts:[],cache:{}};ledger={};
};

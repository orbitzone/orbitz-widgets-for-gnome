const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const path = require('path');
const source = fs.readFileSync(path.join(__dirname, '../extension/terminalLaunch.js'), 'utf8');
const events = [];
let fail = false, id = 0;
const proc = {};
const context = {Gio: {
    AppInfoCreateFlags: {SUPPORTS_STARTUP_NOTIFICATION: 1}, SubprocessFlags: {NONE: 0},
    AppInfo: {create_from_commandline(cmd, name, flags) {assert.equal(cmd, '/usr/bin/tilix'); assert.equal(flags, 1); return {terminal: true};}},
    SubprocessLauncher: class {
        constructor(options) {assert.equal(options.flags, 0);}
        setenv(key, value, overwrite) {events.push(['env', key, value, overwrite]);}
        spawnv(argv) {events.push(['argv', argv]); if (fail) throw new Error('spawn failed'); return proc;}
    },
}, global: {create_app_launch_context(time, workspace) {
    assert.equal(time, 0); assert.equal(workspace, -1);
    return {get_startup_notify_id(info, files) {assert(info.terminal); assert.equal(files.length, 0); return `launch-${++id}`;},
        launch_failed(value) {events.push(['failed', value]);}};
}}};
vm.createContext(context); vm.runInContext(source, context);
const launch = context.create(context);
const argv = ['/usr/bin/python3', '/synthetic/path with spaces/action.py', '--action', 'refresh'];
const owner = {_networkModalGrab: {id: 7}};
owner._closeNetworkDialog = function() {
    events.push(['closeDialog', this._networkModalGrab]);
    this._networkModalGrab = null;
};
owner._openNetworkDialog = function() {
    events.push(['openDialog']);
    this._networkModalGrab = {id: 10};
};
assert.strictEqual(launch(argv, owner), proc);
assert.deepEqual(events[0], ['env', 'DESKTOP_STARTUP_ID', 'launch-1', true]);
assert.deepEqual(events[1], ['env', 'XDG_ACTIVATION_TOKEN', 'launch-1', true]);
assert.deepEqual(events[2], ['closeDialog', {id: 7}]);
assert.deepEqual(events[3], ['argv', argv]); // No command re-parsing, concatenation or shell.
assert.strictEqual(owner._networkModalGrab, null);
launch(argv);
assert.deepEqual(events[4], ['env', 'DESKTOP_STARTUP_ID', 'launch-2', true]);
assert.deepEqual(events[5], ['env', 'XDG_ACTIVATION_TOKEN', 'launch-2', true]); // Every click gets a fresh context.
assert.deepEqual(events[6], ['argv', argv]);
fail = true;
const failingOwner = {...owner, _networkModalGrab: {id: 9}};
assert.throws(() => launch(argv, failingOwner), /spawn failed/);
assert.deepEqual(events[7], ['env', 'DESKTOP_STARTUP_ID', 'launch-3', true]);
assert.deepEqual(events[8], ['env', 'XDG_ACTIVATION_TOKEN', 'launch-3', true]);
assert.deepEqual(events[9], ['closeDialog', {id: 9}]);
assert.deepEqual(events[10], ['argv', argv]);
assert.deepEqual(events[11], ['failed', 'launch-3']);
assert.deepEqual(events[12], ['openDialog']);
assert.deepEqual(failingOwner._networkModalGrab, {id: 10}); // Modal panel is restored after spawn failure.
console.log('OK: terminal activation context, argv preservation, fresh IDs and failed-launch cleanup.');
// Real panel callbacks must use the activation launcher, never an untracked spawn.
class Actor {
    constructor(props={}) {Object.assign(this,props);this.children=[];this.signals={};this.clutter_text={set_line_wrap(){},set_ellipsize(){}};}
    add_child(child){this.children.push(child);}
    set_child(child){this.children=[child];}
    destroy_all_children(){this.children=[];}
    connect(name,callback){this.signals[name]=callback;}
    set_policy(){}
    get_preferred_height(){return [100,100];}
}
const launched=[];
const panels={St:{BoxLayout:Actor,Label:Actor,Button:Actor,Icon:Actor,PolicyType:{NEVER:0}},
    Pango:{EllipsizeMode:{NONE:0,END:1}},Clutter:{ActorAlign:{CENTER:0}},
    Main:{layoutManager:{findMonitorForActor:()=>({width:1200,height:900})}},
    GLib:{shell_parse_argv:()=>[true,['python3','/synthetic/cpu-ram-widget.py']],
        path_get_dirname:()=>'/synthetic',build_filenamev:parts=>parts.join('/')},
    launchTerminalAction:(argv,owner)=>{launched.push(Array.from(argv));assert.strictEqual(owner,host);},getData:()=>'',
};
vm.createContext(panels);
const methods=require('./helpers/command_panels').load(panels);
const host=Object.assign({_updatesRows:new Actor(),_updatesActions:new Actor(),_updatesHeading:{},_updatesNote:{},
    _updatesScroll:new Actor(),_networkRefreshButton:{},_networkRefreshStatus:{},
    _attachActionTooltip(){},_hardwareMode:'ram'},methods);
host._renderPressure=()=>{};host._attachActionTooltip=()=>{};
const action={id:'monitor',name:'Teste',command:'not executed',effect:'Teste'};
function clickAction(){
    const walk=actor=>actor.signals.clicked ? [actor] : actor.children.flatMap(walk);
    const buttons=walk(host._updatesActions);
    assert.equal(buttons.length,1);buttons[0].signals.clicked();
}
host._renderUpdates({text:'Teste',reboot:false,index_updated:'',error:'',items:[],omitted:0,notices:[],actions:[action]});clickAction();
host._renderProcesses({summary:'Teste',notices:[],cpu_rows:[],memory_rows:[],actions:[action]});clickAction();
host._renderHardware({mode:'ram',title:'RAM',note:'',cards:[],firmware_action:true});clickAction();
host._renderStorage({text:'SSD',error:'',omitted:0,unmounted:[],disks:[],items:[{files:[],content_error:'',more:false,mount:'/',device:'/dev/test',disk:'/dev/test',total:100,available:50,percent:50,inodes:1}]});clickAction();
assert.deepEqual(launched,[['python3','/synthetic/cpu-ram-widget.py','--action','monitor'],
    ['python3','/synthetic/cpu-ram-widget.py','--action','monitor'],
    ['/usr/bin/python3','/synthetic/hardware-details.py','--read-firmware'],
    ['/usr/bin/python3','/synthetic/limpeza-linux.py','--launch']]);
console.log('OK: updates, processes, RAM firmware and cleanup callbacks use terminal activation.');

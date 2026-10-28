const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const source = fs.readFileSync(path.join(__dirname, '../extension/extension.js'), 'utf8');
class Actor {
    constructor(props = {}) { Object.assign(this, props); this.events = {}; this.children = []; }
    set_child(child) { this.children = [child]; }
    add_child(child) { this.children.push(child); }
    show() { this.visible = true; } hide() { this.visible = false; }
    set_position(x,y) { this.x=x; this.y=y; }
    connect(name, callback) { this.events[name] = callback; }
    destroy() { this.destroyed = true; }
}
let postitCloses = 0;
let postitsLaunched = 0;
let created = 0, destroyed = 0, settingsRead = 0, stopped = 0, fail = -1, failValidation = false;
const timers = new Map();
const settings = {
    disconnectObject() {}, connectObject() {},
    get_value() { return {deep_unpack: () => ({})}; }, set_value() {},
};
const loggedErrors = [];
const context = {
    Calendar: {enable() {}, disable() {}},
    Meta: {WindowType:{DESKTOP:1}},
    widgetsEnabled: false, dragWidgets: new Set(), widgetDragController: null, activeCommandRuns: new Set(), pendingStops: new Set(),
    metricLabels: new Set(), networkClickLabels: new Set(), metricRestart: null, networkClickTimer: null,
    WIDGETDATA: null, DIGITAL_CLOCK: 'Digital_Clock', ANALOG_CLOCK: 'Analog_Clock',
    Me: {path:'/extension', settings: null, imports: {settings: {SettingsImport: {validateWidgets() { if (failValidation) throw Error('bad config'); }}}}},
    ExtensionUtils: {getSettings() { settingsRead++; return settings; }},
    Utils: {unpackData() { return [[{Widget_Type:'Widget_Box'}, {Element_Type:'Digital_Clock'}],[{Widget_Type:'Widget_Box'}],[{Widget_Type:'Widget_Box'}]]; }},
    Main: {panel: {height:28, addToStatusArea() {}}, layoutManager: {addChrome(actor, params) { actor.inputTracked = params; }, primaryMonitor: {x:0,y:0,width:1920,height:1080}, disconnectObject() {}, connectObject() {}, _backgroundGroup: {add_child() {}}}, notifyError() {}},
    PanelMenu: {Button: Actor}, St: {Button: Actor, Label: Actor, Icon: Actor}, Clutter: {ActorAlign: {CENTER:0}},
    Gio: {icon_new_for_string: value => value, SubprocessFlags: {NONE: 0},
        Subprocess: {new() {postitsLaunched++;throw Error('widget lifecycle must not launch any desktop app');}},
        DBus: {session: {call() {postitCloses++;throw Error('widget lifecycle must not send application quit actions');}}}},
    GLib: {build_filenamev: parts => parts.join('/'), get_user_data_dir: () => '/user-data', Variant: class {}, PRIORITY_DEFAULT:0, SOURCE_CONTINUE: true, SOURCE_REMOVE:false,
        timeout_add(priority, delay, fn) { const id = timers.size + 1; timers.set(id,fn); return id; },
        source_remove(id) { timers.delete(id); }},
    DesktopWidget: class extends Actor {
        constructor(index) { super(); if (index === fail) throw Error('failed widget'); created++; }
        updateComponents() {} updateClocks() {} setPositionFromSettings() {}
        destroy() { destroyed++; super.destroy(); }
    },
    stopMetrics() { stopped++; }, stopCommandRun(run) { run.cancelled = true; return Promise.resolve(); },
    logError(error, label) { loggedErrors.push([error, label]); }, debugLog() {}, global: {get_window_actors: () => [], workspace_manager: {get_active_workspace: () => 0, connectObject() {}}, display: {get_n_monitors: () => 1, connectObject() {}}, window_group: {add_child() {}, get_children: () => [{meta_window:{get_window_type:()=>0}}], set_child_below_sibling(actor,sibling){actor.below=sibling}, set_child_above_sibling(){}}},
};
context.Language = require('./helpers/ui_language').create(context,'pt-BR');
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('class AzClock {')) + 'this.Controller = AzClock;', context);
(async () => {
    const controller = new context.Controller();
    controller.enable();
    assert.equal(controller._controller.inputTracked.affectsStruts, false);
    assert.equal(controller._controller.inputTracked.trackFullscreen, false);
    assert.equal(typeof controller._controller.events.clicked, "function");
    assert.equal(controller._controller.visible, true); assert(controller._controller.style.includes('background-color: transparent')); assert.equal(controller._controllerIcon.icon_size, 24); assert.equal(controller._controller.width, 40);
    assert.equal(controller._controller.x, 1868); assert.equal(controller._controller.y, 36);
    assert.equal(created, 0); assert.equal(settingsRead, 2); // UI locale configuration and layout settings are read separately.
    assert.equal(timers.size, 0);
    assert.equal(controller._controllerIcon.gicon, '/extension/media/controls/widgets-white.svg');
    const coveringWindow = {get_window_type: () => 0, showing_on_its_workspace: () => true,
        located_on_workspace: () => true, get_frame_rect: () => ({x:1800,y:0,width:120,height:100})};
    controller._controllerWindows.add(coveringWindow);
    controller._stackControllerBehindWindows(); assert.equal(controller._controller.visible, false);
    coveringWindow.showing_on_its_workspace = () => false;
    controller._stackControllerBehindWindows(); assert.equal(controller._controller.visible, true);
    coveringWindow.showing_on_its_workspace = () => true;
    coveringWindow.get_window_type = () => 1;
    controller._stackControllerBehindWindows(); assert.equal(controller._controller.visible, true);
    coveringWindow.get_window_type = () => 0;
    coveringWindow.get_gtk_application_id = () => 'com.rastersoft.ding';
    controller._stackControllerBehindWindows(); assert.equal(controller._controller.visible, true);
    coveringWindow.get_gtk_application_id = () => 'org.example.Application';
    controller._stackControllerBehindWindows(); assert.equal(controller._controller.visible, false);
    coveringWindow.customJS_ding = {_keepAtBottom: true};
    controller._stackControllerBehindWindows(); assert.equal(controller._controller.visible, true);
    controller._controllerWindows.clear();
    const primary=context.Main.layoutManager.primaryMonitor;
    const second={x:-1280,y:0,width:1280,height:1024};
    context.Main.layoutManager.monitors=[primary,second];
    const originalGet=settings.get_value;
    settings.get_value=()=>({deep_unpack:()=>[[{Location_X:'-900',Location_Y:'50'}],[{Location_X:'-600',Location_Y:'200'}],[{Location_X:'40',Location_Y:'30'}]]});
    controller._positionController(); assert.equal(controller._controller.x,-52); assert.equal(controller._controller.y,8);
    settings.get_value=()=>({deep_unpack:()=>[[{Location_X:'0',Location_Y:'100',Box_AnchorPoint:'2'}]]});
    assert.strictEqual(controller._controllerMonitor(),second);
    settings.get_value=originalGet; controller._positionController();
    controller._controller.events.clicked();
    assert.equal(created, 3); assert.equal(controller.widgets.length, 3); assert(timers.size > 0);
    assert.equal(postitsLaunched, 0, 'starting widgets leaves independent apps alone');
    assert.equal(controller._controllerIcon.gicon, '/extension/media/controls/widgets-white.svg');
    const run = {}; context.activeCommandRuns.add(run);
    let release; const pending = new Promise(resolve => { release = resolve; }); context.pendingStops.add(pending);
    const stopping = controller._stopWidgets();
    assert.equal(controller._controllerButton.reactive, false);
    controller._startWidgets(); assert.equal(created, 3);
    release(); await stopping; context.pendingStops.delete(pending);
    assert.equal(destroyed, 3); assert.equal(controller.widgets.length, 0); assert(run.cancelled);
    assert.equal(context.widgetsEnabled, false); assert.equal(context.WIDGETDATA, null); assert.equal(timers.size, 0);
    assert.equal(controller._controllerIcon.gicon, '/extension/media/controls/widgets-white.svg');
    controller._startWidgets(); assert.equal(created, 6);
    assert.equal(postitsLaunched, 0);
    await controller._stopWidgets(); assert.equal(destroyed, 6);
    controller._startWidgets();
    controller.widgets[0]._onInitializationError(Error('delayed initialization'));
    await controller._stopping; assert.equal(created, 9); assert.equal(destroyed, 9);
    assert.equal(postitsLaunched, 0, 'asynchronous initialization never launches notes');
    assert.equal(postitCloses, 0, 'asynchronous rollback does not close independent apps');
    fail = 1;
    controller._startWidgets();
    await controller._stopping;
    assert.equal(created, 10); assert.equal(destroyed, 10); assert.equal(controller.widgets.length, 0);
    assert.equal(controller._running, false);
    assert.equal(postitsLaunched, 0, 'synchronous initialization never launches notes');
    assert.equal(postitCloses, 0, 'synchronous rollback does not close independent apps');
    fail = -1; failValidation = true;
    controller._startWidgets(); await controller._stopping; assert.equal(created, 10);
    assert.equal(postitsLaunched, 0, 'invalid configuration does not launch independent apps');
    controller.disable(); await controller._stopping;
    assert.equal(controller._controllerButton, null);
    assert(stopped > 0); assert.equal(postitCloses, 0);assert.equal(postitsLaunched,0);
    assert.equal(typeof controller._openPostits,'undefined');assert.equal(typeof controller._closePostits,'undefined');
    console.log('OK: startup/stop lifecycle, independent apps untouched across success, rollback and disable, monitor selection, and widget construction rollback.');
})().catch(error => { console.error(error); process.exitCode = 1; });

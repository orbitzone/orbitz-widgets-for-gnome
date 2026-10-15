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
let created = 0, destroyed = 0, settingsRead = 0, stopped = 0, fail = -1, failValidation = false;
const timers = new Map();
const settings = {
    disconnectObject() {}, connectObject() {},
    get_value() { return {deep_unpack: () => ({})}; }, set_value() {},
};
const context = {
    widgetsEnabled: false, activeCommandRuns: new Set(), pendingStops: new Set(),
    metricLabels: new Set(), networkClickLabels: new Set(), metricRestart: null, networkClickTimer: null,
    WIDGETDATA: null, DIGITAL_CLOCK: 'Digital_Clock', ANALOG_CLOCK: 'Analog_Clock',
    Me: {path:'/extension', settings: null, imports: {settings: {SettingsImport: {validateWidgets() { if (failValidation) throw Error('bad config'); }}}}},
    ExtensionUtils: {getSettings() { settingsRead++; return settings; }},
    Utils: {unpackData() { return [[{Widget_Type:'Widget_Box'}, {Element_Type:'Digital_Clock'}],[{Widget_Type:'Widget_Box'}],[{Widget_Type:'Widget_Box'}]]; }},
    Main: {panel: {height:28, addToStatusArea() {}}, layoutManager: {addChrome() {}, primaryMonitor: {x:0,y:0,width:1920,height:1080}, disconnectObject() {}, connectObject() {}, _backgroundGroup: {add_child() {}}}, notifyError() {}},
    PanelMenu: {Button: Actor}, St: {Button: Actor, Label: Actor, Icon: Actor}, Clutter: {ActorAlign: {CENTER:0}},
    Gio: {icon_new_for_string: value => value},
    GLib: {build_filenamev: parts => parts.join('/'), Variant: class {}, PRIORITY_DEFAULT:0, SOURCE_CONTINUE: true, SOURCE_REMOVE:false,
        timeout_add(priority, delay, fn) { const id = timers.size + 1; timers.set(id,fn); return id; },
        source_remove(id) { timers.delete(id); }},
    DesktopWidget: class extends Actor {
        constructor(index) { super(); if (index === fail) throw Error('failed widget'); created++; }
        updateComponents() {} updateClocks() {} setPositionFromSettings() {}
        destroy() { destroyed++; super.destroy(); }
    },
    stopMetrics() { stopped++; }, stopCommandRun(run) { run.cancelled = true; return Promise.resolve(); },
    logError() {}, debugLog() {}, global: {display: {get_n_monitors: () => 1}},
};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('class AzClock {')) + 'this.Controller = AzClock;', context);
(async () => {
    const controller = new context.Controller();
    controller.enable();
    assert.equal(controller._controller.visible, true); assert(controller._controller.style.includes('background-color: transparent')); assert.equal(controller._controllerIcon.icon_size, 24); assert.equal(controller._controller.width, 40);
    assert.equal(controller._controller.x, 1868); assert.equal(controller._controller.y, 36);
    assert.equal(created, 0); assert.equal(settingsRead, 1); assert.equal(timers.size, 0);
    assert.equal(controller._controllerIcon.gicon, '/extension/media/controls/widgets-white.svg');
    const primary=context.Main.layoutManager.primaryMonitor;
    const second={x:-1280,y:0,width:1280,height:1024};
    context.Main.layoutManager.monitors=[primary,second];
    const originalGet=settings.get_value;
    settings.get_value=()=>({deep_unpack:()=>[[{Location_X:'-900',Location_Y:'50'}],[{Location_X:'-600',Location_Y:'200'}],[{Location_X:'40',Location_Y:'30'}]]});
    controller._positionController(); assert.equal(controller._controller.x,-52); assert.equal(controller._controller.y,8);
    settings.get_value=()=>({deep_unpack:()=>[[{Location_X:'0',Location_Y:'100',Box_AnchorPoint:'2'}]]});
    assert.strictEqual(controller._controllerMonitor(),second);
    settings.get_value=originalGet; controller._positionController();
    controller._startWidgets();
    assert.equal(created, 3); assert.equal(controller.widgets.length, 3); assert(timers.size > 0);
    assert.equal(controller._controllerIcon.gicon, '/extension/media/controls/widgets-active.svg');
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
    await controller._stopWidgets(); assert.equal(destroyed, 6);
    controller._startWidgets();
    controller.widgets[0]._onInitializationError(Error('delayed initialization'));
    await controller._stopping; assert.equal(created, 9); assert.equal(destroyed, 9);
    fail = 1;
    controller._startWidgets();
    await controller._stopping;
    assert.equal(created, 10); assert.equal(destroyed, 10); assert.equal(controller.widgets.length, 0);
    assert.equal(controller._running, false);
    fail = -1; failValidation = true;
    controller._startWidgets(); await controller._stopping; assert.equal(created, 10);
    controller.disable(); await controller._stopping;
    assert.equal(controller._controllerButton, null);
    assert(stopped > 0);
    console.log('OK: startup without widgets/collectors/timers, metadata-only monitor selection; Play/Stop; repeated cycles; cancelled runs; rollback on widget/config failure.');
})().catch(error => { console.error(error); process.exitCode = 1; });

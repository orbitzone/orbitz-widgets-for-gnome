const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const source = fs.readFileSync(path.join(__dirname, '../extension/extension.js'), 'utf8');
class Actor {
    constructor(props = {}) { Object.assign(this, props); this.children = []; this.events = {}; this.clutter_text = {set_ellipsize() {}}; }
    add_child(child) { this.children.push(child); }
    set_child(child) { this.children = [child]; }
    destroy_all_children() { this.children = []; }
    connect(name, handler) { this.events[name] = handler; }
    get_preferred_height() { return [100, 100]; }
    set_policy() {}
}
const command = 'python3 /synthetic/cpu-ram-widget.py';
const calls = [], rendered = [];
const context = vm.createContext({
    TextEncoder, TextDecoder, Pango: {SCALE: 1024, EllipsizeMode: {END: 0}},
    Clutter: {ModifierType: {BUTTON1_MASK: 1, SUPER_MASK: 2, MOD4_MASK: 2, CONTROL_MASK: 4}},
    activeWidgetDrag: null, desktopPointerBlocked: () => false, metricMode: () => 'cpu', getData: () => command,
    Main: {layoutManager: {findMonitorForActor: () => null, primaryMonitor: {width: 1280, height: 900}}},
    St: {BoxLayout: Actor, Label: Actor, Button: Actor, PolicyType: {NEVER: 0, AUTOMATIC: 1}},
    Gio: {Cancellable: class {}, SubprocessFlags: {STDOUT_PIPE: 1, STDERR_PIPE: 2},
        Subprocess: {new(argv) { calls.push(argv); return {get_successful: () => true}; }}},
    GLib: {shell_parse_argv: () => [true, ['python3', '/synthetic/cpu-ram-widget.py']],
        timeout_add: () => 1, source_remove() {}, PRIORITY_DEFAULT: 0,
        DateTime: {new_now_local: () => ({format: () => '12:00'})}},
    stopCommandRun() {}, logError(error) { throw error; },
});
const body = (start, end) => source.slice(source.indexOf(start), source.indexOf(end));
vm.runInContext('this.Click = class {' + body('    _storageTarget(pointer)', '    async _ejectExternalDevice') +
    body('    _checkNetworkClick(pointer)', '    _closeNetworkDialog()') + '}', context);
vm.runInContext('this.Refresh = class {' + body('    async _refreshNetworkDialog()', '    _openNetworkDialog()') + '}', context);
const methods = require('./helpers/command_panels').load(context);
const text = 'CPU ███ 30%\n\nRAM ██ 20%\n\n! SSD ███ 93%';
let line = 0;
const host = Object.assign(new context.Click(), methods, {
    _networkGeneration: 0, _updatesHeading: {}, _updatesNote: {}, _updatesScroll: new Actor(),
    _updatesRows: new Actor(), _updatesActions: new Actor(), _networkRefreshButton: {}, _networkRefreshStatus: {},
    get_transformed_position: () => [0, 0], get_transformed_size: () => [400, 200], get_paint_visibility: () => true,
    clutter_text: {transform_stage_point: () => [true, 0, line * 15], get_text: () => text,
        get_layout: () => ({xy_to_index: () => [true, new TextEncoder().encode(text.split('\n').slice(0, line).join('\n') + (line ? '\n' : '')).length, 0]})},
    _attachActionTooltip: () => () => {},
    _openNetworkDialog() { this._networkDialog ||= {}; this._networkDialog.visible = true; },
});
context.readCommandOutput = async () => {
    if (host._hardwareMode) return ['AZCLOCK_HARDWARE:' + JSON.stringify({mode: host._hardwareMode,
        title: host._hardwareMode.toUpperCase(), note: '', cards: [{title: 'Sintético', lines: ['Informação']}], firmware_action: false})];
    return ['AZCLOCK_STORAGE:' + JSON.stringify({text: 'SSD', error: '', omitted: 0, items: [], unmounted: [], disks: []})];
};
(async () => {
    for (const [row, mode] of [[0, 'cpu'], [2, 'ram'], [4, null], [2, 'ram'], [0, 'cpu']]) {
        if (host._networkDialog) host._networkDialog.visible = false;
        line = row;
        host._checkNetworkClick([10, row * 15, 1]);
        host._checkNetworkClick([10, row * 15, 0]);
        assert.equal(host._networkDialog.visible, true);
        assert.equal(host._hardwareMode, mode);
        await context.Refresh.prototype._refreshNetworkDialog.call(host);
        assert(host._networkRefreshStatus.text.startsWith('Consultado às'), host._networkRefreshStatus.text);
        const argv = calls.at(-1);
        assert.equal(argv.includes('--hardware'), mode !== null);
        if (mode) assert.equal(argv[argv.indexOf('--hardware') + 1], mode);
        assert.equal(argv.at(-1), '--details');
        rendered.push(host._updatesHeading.text);
    }
    assert.deepEqual(rendered, ['CPU', 'RAM', 'SSD · armazenamento e saúde', 'RAM', 'CPU']);
    console.log('OK: real hit testing, press/release and CPU→RAM→SSD→RAM→CPU refresh/render; mode resets and injected storage dependencies.');
})().catch(error => {console.error(error); process.exitCode = 1;});

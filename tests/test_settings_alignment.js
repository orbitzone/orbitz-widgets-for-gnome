const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
class ComboRow {
    constructor(values) { Object.assign(this, values); }
    connect(name, handler) { this.change = handler; }
}
class StringList { constructor() { this.items = []; } append(value) { this.items.push(value); } }
const settings = {TimeZoneDialog: {}, WidgetsData: {}, timeZoneCatalog: {TimeZoneCatalog: {}}};
const Me = {metadata: {}, imports: {utils: {}, settings, worldClock: {WorldClock: {isTimeFormat: () => false}}}};
const gi = {Adw: {PreferencesPage: class {}, ComboRow}, Gtk: {StringList}, Gdk: {}, GLib: {},
    GObject: {registerClass: (...args) => args.at(-1), ParamSpec: {int() {}}, ParamFlags: {}}};
const imports = {gi, misc: {extensionUtils: {getCurrentExtension: () => Me}}, gettext: {domain: () => ({gettext: text => 'tr:' + text})}};
const load = name => {
    const context = vm.createContext({imports});
    vm.runInContext(fs.readFileSync(path.join(__dirname, '../extension/settings', name + '.js'), 'utf8'), context);
    return context[name];
};
settings.SubPage = {SubPage: load('SubPage')};
for (const name of ['TextLabelSubPage', 'DigitalClockSubPage']) {
    const Class = load(name);
    assert(!Object.hasOwn(Class.prototype, 'createComboRow'));
    for (const [value, selected] of [['Start', 0], ['Center', 1], ['End', 2], ['unknown', 0]]) {
        let saved;
        const host = {getClockElementData: () => value, setClockElementData: (...args) => {saved = args;}};
        const row = Class.prototype.createComboRow.call(host, 'Alignment', 'Text_Align');
        assert.equal(row.selected, selected);
        assert.deepEqual(row.model.items, ['tr:Start', 'tr:Center', 'tr:End']);
        row.change({selected_item: {string: 'tr:End'}});
        assert.deepEqual(saved, ['Text_Align', 'tr:End']);
    }
}
console.log('OK: text and digital pages inherit identical alignment selection, translation and persistence.');

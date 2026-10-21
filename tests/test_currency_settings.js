const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Row {
    constructor(props = {}) { this.handlers = {}; Object.assign(this, props); }
    add_suffix(widget) { this.suffix = widget; }
    connect(name, callback) { this.handlers[name] = callback; }
    add(row) { (this.rows ??= []).push(row); }
}
class DropDown extends Row {
    set selected(value) { this._selected = value; this.handlers['notify::selected']?.(); }
    get selected() { return this._selected ?? 0; }
}
class SwitchRow extends Row {
    set active(value) { this._active = value; this.handlers['notify::active']?.(); }
    get active() { return this._active ?? false; }
}
class StringList {
    static new(items) { const list = new StringList(); list.items = items; return list; }
}
const saved = [];
const gi = {
    Adw: {PreferencesGroup: Row, ActionRow: Row, SwitchRow},
    Gio: {
        SubprocessFlags: {STDOUT_PIPE: 1, STDERR_SILENCE: 2},
        Subprocess: {new: () => {
            const proc = {
            communicate_utf8_async: (_input, _cancel, callback) => callback(proc, {}),
            communicate_utf8_finish: () => [true, JSON.stringify({EUR: 'Euro', USD: 'US Dollar'})],
            get_successful: () => true,
            };
            return proc;
        }},
    },
    GLib: {
        build_filenamev: parts => parts.join('/'),
        get_user_data_dir: () => '/user-data',
        shell_quote: value => `'${value}'`,
        shell_parse_argv: command => [true, command.match(/'[^']*'|\S+/g).map(token => token.replace(/^'|'$/g, ''))],
    },
    GObject: {registerClass: (_metadata, klass) => klass},
    Gtk: {DropDown, StringList},
};
const Me = {metadata: {}, imports: {settings: {TextLabelSubPage: {TextLabelSubPage: class {}}}}};
const imports = {
    gi,
    misc: {extensionUtils: {getCurrentExtension: () => Me}},
    gettext: {domain: () => ({gettext: value => value})},
};
const context = vm.createContext({imports, Object, JSON, Error});
vm.runInContext(fs.readFileSync('extension/settings/CommandLabelSubPage.js', 'utf8'), context);
const Page = context.CommandLabelSubPage;
const host = {
    textGroupAdd: row => (host.groups ??= []).push(row),
    setClockElementData: (...args) => saved.push(args),
};
Page.prototype._addCurrencyControls.call(host,
    "/usr/bin/python3 '/user-data/orbitz-widgets/collectors/currency-widget.py' --quote USD");
const group = host.groups[0];
const pickerRow = group.rows[0];
const picker = pickerRow.suffix;
const direction = group.rows[1];
assert.equal(picker.sensitive, true);
assert.deepEqual(Array.from(picker.model.items), ['EUR · Euro', 'USD · US Dollar']);
assert.deepEqual(saved.at(-1), ['Text_Command', '/usr/bin/python3 \'/user-data/orbitz-widgets/collectors/currency-widget.py\' --quote USD']);
picker.selected = 0;
assert.deepEqual(saved.at(-1), ['Text_Command', '/usr/bin/python3 \'/user-data/orbitz-widgets/collectors/currency-widget.py\' --quote EUR']);
direction.active = true;
assert.deepEqual(saved.at(-1), ['Text_Command', '/usr/bin/python3 \'/user-data/orbitz-widgets/collectors/currency-widget.py\' --quote EUR --reverse']);
assert.equal(pickerRow.title, 'Convert to BRL');
console.log('OK: currency settings load the async catalog and persist selected quote/direction in the runtime command.');

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const digitalClockSource = fs.readFileSync(path.join(__dirname, '../extension/settings/DigitalClockSubPage.js'), 'utf8');
assert.match(digitalClockSource, /const\s*\{[^}]*\bGLib\b[^}]*\}\s*=\s*imports\.gi;/,
    'digital clock settings must import GLib before creating the world-clock selector');

class Actor {
    constructor(props = {}) { this.children = []; this.handlers = {}; Object.assign(this, props); }
    _init(props = {}) { Object.assign(this, props); }
    connect(signal, callback) { this.handlers ??= {}; this.handlers[signal] = callback; }
    add_suffix(child) { this.children ??= []; this.children.push(child); }
    add_prefix(child) { this.children ??= []; this.children.push(child); }
    add_controller() {}
    get_root() { return this; }
}
class Button extends Actor {
    click() { this.handlers.clicked(); }
}
class DragController extends Actor {}
class Image extends Actor {}
class ContentProvider {}

const buttons = [];
let openedSettings = null;
const widgetSettingsPage = class {
    constructor(settings, homePage, params) { openedSettings = {settings, homePage, params}; }
    connect() {}
    present() { openedSettings.presented = true; }
};
const widgetData = [[{Name: 'Digital Clock Widget'}]];
const Me = {metadata: {'gettext-domain': 'azclock'}, imports: {settings: {
    AboutPage: {}, DialogWindow: {DialogWindow: class {}}, WidgetsData: {WidgetsData: {data: widgetData}},
    WidgetSettingsPage: {WidgetSettingsPage: widgetSettingsPage},
}, utils: {}}};
const Gtk = {
    Button: class extends Button { constructor(props) { super(props); buttons.push(this); } },
    Image, Label: Actor, DragSource: DragController, DropTargetAsync: DragController,
    Align: {CENTER: 0, END: 1}, StateFlags: {NORMAL: 0},
};
const GObject = {
    registerClass: (...args) => args.at(-1),
    ParamSpec: {int: () => ({})}, ParamFlags: {READWRITE: 1}, TYPE_UINT: 1,
};
Me.imports.uiLanguage={Language:require('./helpers/ui_language').create({})};
const context = vm.createContext({imports: {
    misc: {extensionUtils: {getCurrentExtension: () => Me}},
    gi: {Adw: {PreferencesPage: Actor, ActionRow: Actor}, Gtk, Gdk: {DragAction: {MOVE: 1}, ContentProvider},
        Gio: {icon_new_for_string: value => value}, GLib: {MAXINT32: 2147483647, markup_escape_text: value => value}, GObject},
    gettext: {domain: () => ({gettext: value => value})},
}});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../extension/prefs.js'), 'utf8'), context);

const homePage = {settings: {}};
const row = Object.create(context.WidgetRow.prototype);
row._init(homePage, {title: 'Digital Clock Widget', widget_index: 0});
const configureButton = buttons.find(button => button.label === 'Configure');
assert(configureButton, 'Configure must be an explicit button');
configureButton.click();
assert(openedSettings?.presented, 'Configure click must present widget settings');
assert.equal(openedSettings.params.widget_index, 0);
assert.equal(openedSettings.params.title, 'Digital Clock Widget');
console.log('OK: Configure button opens the selected widget settings page.');

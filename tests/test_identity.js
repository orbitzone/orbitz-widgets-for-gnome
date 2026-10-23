const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const root = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(root, name), 'utf8');
const metadata = JSON.parse(read('extension/metadata.json'));
assert.equal(metadata.name, 'Orbitz Widgets for GNOME');
assert.equal(metadata.uuid, 'orbitz-widgets@orbitzone.github.io');
assert.equal(metadata.url, 'https://github.com/orbitzone/orbitz-widgets-for-gnome');
assert.equal(metadata['settings-schema'], 'org.gnome.shell.extensions.orbitz-widgets');
assert.equal(metadata['gettext-domain'], 'azclock');
assert.equal(metadata.version, 1);
assert.equal(metadata['version-name'], '1.0');
assert(!metadata.donations);
const legacy = read('extension/schemas/org.gnome.shell.extensions.azclock.gschema.xml');
const current = read('extension/schemas/org.gnome.shell.extensions.orbitz-widgets.gschema.xml');
assert.equal(current, legacy.replace('id="org.gnome.shell.extensions.azclock" path="/org/gnome/shell/extensions/azclock/"',
    'id="org.gnome.shell.extensions.orbitz-widgets" path="/org/gnome/shell/extensions/orbitz-widgets/"'));
class Actor {
    constructor(props = {}) { this.children = []; this.events = {}; Object.assign(this, props); }
    _init(props) { Object.assign(this, props); }
    add(child) { this.children.push(child); }
    append(child) { this.children.push(child); }
    add_suffix(child) { this.children.push(child); }
    connect(name, handler) { this.events[name] = handler; }
    get_root() { return this; }
}
const opened = [];
const Me = {path: '/synthetic/orbitz-extension', metadata, imports: {settings: {SettingsImport: {}}}};
const Gtk = {Box: Actor, Image: Actor, Label: Actor, Button: Actor,
    Orientation: {VERTICAL: 1}, Align: {FILL: 0, CENTER: 1, END: 2}, Justification: {CENTER: 1}, AccessibleRole: {IMG: 1},
    show_uri(_root, uri) { opened.push(uri); }};
const context = vm.createContext({imports: {
    misc: {extensionUtils: {getCurrentExtension: () => Me}, config: {PACKAGE_VERSION: '42-test'}},
    gi: {Adw: {PreferencesPage: Actor, PreferencesGroup: Actor, ActionRow: Actor}, Gtk, Gdk: {}, Gio: {File: {new_for_path: value => ({path: value})}, FileIcon: class {constructor(props) {Object.assign(this, props);}}},
        GLib: {build_filenamev: parts => parts.join('/'), get_os_info: () => 'Synthetic OS', getenv: () => 'x11'}, GObject: {registerClass: (...args) => args.at(-1)}},
    gettext: {domain: () => ({gettext: value => value})},
}});
Me.imports.uiLanguage={Language:require('./helpers/ui_language').create(context,'pt-BR')};
vm.runInContext(read('extension/settings/AboutPage.js'), context);
const page = new context.AboutPage();
page._init();
const flatten = actor => [actor, ...actor.children.flatMap(flatten)];
const actors = flatten(page);
assert(actors.some(actor => actor.label === metadata.name));
assert(actors.some(actor => actor.title === 'Versão do Orbitz'));
assert(actors.some(actor => actor.title === 'Configurações do Orbitz'));
assert(actors.some(actor => actor.title === 'Felipe Santiago · orbitzone'));
for (const [title, uri] of [['Orbitz no GitHub', metadata.url], ['Felipe Santiago · orbitzone', 'https://github.com/orbitzone'],
    ['Base original: azclock · Andrew Zaech', 'https://gitlab.com/AndrewZaech/azclock']]) {
    actors.find(actor => actor.title === title).events.activated();
    assert.equal(opened.at(-1), uri);
}
assert(actors.some(actor => actor.title === 'Créditos'));
const license = actors.find(actor => actor.label?.includes('GNU General Public License'));
assert(license.label.includes('https://github.com/orbitzone/orbitz-widgets-for-gnome/blob/main/LICENSE'));
assert(license.label.includes('This program comes with absolutely no warranty.'));
assert(flatten(actors.find(actor => actor.title === 'Créditos')).includes(license));
assert(!license.label.includes('version 2 or later'));
assert(!actors.some(actor => /PayPal|Desktop Clock/.test(actor.title || actor.label || '')));
const image = actors.find(actor => actor.pixel_size === 100);
assert.equal(image.gicon.file.path, '/synthetic/orbitz-extension/media/orbitz-logo.svg');
assert.equal(image.margin_bottom, 5);
assert.equal(image.icon_name, undefined);
assert.equal(actors.find(actor => actor.title === 'Versão do Orbitz').children[0].label, '1.0');
const svg = read('extension/media/orbitz-logo.svg');
assert(svg.includes('viewBox="0 0 128 128"'));
assert(svg.includes('<title id="orbitz-title">Orbitz</title>'));
assert(svg.includes('<desc id="orbitz-desc">'));
assert(!/<(?:image|script|foreignObject)\b/.test(svg));
assert(!/azclock|https?:\/\/(?!www.w3.org)/i.test(svg));
const cached = {...metadata};
delete metadata['version-name'];
const fallback = new context.AboutPage(); fallback._init();
assert.equal(flatten(fallback).find(actor => actor.title === 'Versão do Orbitz').children[0].label, '1.0');
Object.assign(metadata, cached);
assert.deepEqual(actors.filter(actor => ['Salvar', 'Carregar'].includes(actor.label)).map(actor => actor.label).sort(), ['Carregar', 'Salvar']);
console.log('OK: Orbitz metadata/schema identity, unchanged legacy keys/defaults, About author/project/upstream/license links and settings controls.');

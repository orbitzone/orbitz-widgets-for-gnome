// Explicit UI messages only: user/provider strings never enter the catalog.
const {Gio, GLib} = imports.gi;
const Me = imports.misc.extensionUtils.getCurrentExtension();
let settings = null, signal = 0, locale = 'pt-BR', catalogs = null;
const bindings = new Set(), listeners = new Set();
function normalize(value) { return value === 'en-US' ? 'en-US' : 'pt-BR'; }
function directory() {
    const candidates = [GLib.getenv('ORBITZ_I18N_DIR'), GLib.build_filenamev([Me.path, '..', 'i18n']),
        GLib.build_filenamev([GLib.get_user_data_dir(), 'orbitz-widgets', 'i18n']), GLib.build_filenamev([Me.path, 'i18n'])];
    return candidates.find(path => path && GLib.file_test(GLib.build_filenamev([path, 'pt-BR.json']), GLib.FileTest.IS_REGULAR));
}
function load() {
    if (catalogs) return catalogs;
    catalogs = {'pt-BR': {}, 'en-US': {}};
    const root = directory();
    if (root) for (const language of Object.keys(catalogs)) {
        try { catalogs[language] = JSON.parse(new TextDecoder().decode(GLib.file_get_contents(GLib.build_filenamev([root, language + '.json']))[1])); }
        catch (error) { logError(error, 'Orbitz UI catalog'); }
    }
    return catalogs;
}
function tr(key, values = {}) {
    const all = load(), template = all[locale]?.[key] ?? all['pt-BR'][key] ?? key;
    return template.replace(/\{([A-Za-z_][A-Za-z0-9_]*)\}/g, (match, name) => Object.prototype.hasOwnProperty.call(values, name) ? String(text(values[name])) : match);
}
function msg(key, values = {}) { return {orbitzMessage: true, key, values}; }
function error(value) { const result = new Error(text(value)); if (value?.orbitzMessage || value?.orbitzParts || value?.orbitzFormat) result.orbitzMessage = value; return result; }
function join(...parts) { return {orbitzParts: parts}; }
function number(value, options = {}) { return {orbitzFormat: 'number', value, options}; }
function date(value, options = {}) { return {orbitzFormat: 'date', value, options}; }
function text(value) {
    if (value?.orbitzFormat === 'number') return Number(value.value).toLocaleString(locale, value.options);
    if (value?.orbitzFormat === 'date') return new Date(value.value).toLocaleString(locale, value.options);
    return value?.orbitzParts ? value.orbitzParts.map(text).join('') : value?.orbitzMessage ? tr(value.key, value.values) : value;
}
function slot(property) { return ['text', 'label', 'markup', 'set_text', 'set_label', 'set_markup'].includes(property) ? '@content' : property; }
function bind(owner, property, value, method = false) {
    for (const item of bindings) if (item.owner.deref() === owner && slot(item.property) === slot(property)) bindings.delete(item);
    if (!value?.orbitzMessage && !value?.orbitzParts && !value?.orbitzFormat) return;
    const reference = new WeakRef(owner);
    bindings.add({owner: reference, property, value, method});
}
function set(owner, property, value) { bind(owner, property, value); owner[property] = text(value); return owner; }
function call(owner, method, value, ...args) {
    bind(owner, method, value, true); owner[method](text(value), ...args); return owner;
}
function widget(Constructor, properties = {}) {
    const plain = Object.fromEntries(Object.entries(properties).map(([key, value]) => [key, text(value)]));
    const owner = new Constructor(plain);
    for (const [property, value] of Object.entries(properties)) bind(owner, property, value);
    return owner;
}
function properties(owner, values) {
    const plain = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, text(value)]));
    if (Object.values(values).some(value => value?.orbitzMessage || value?.orbitzParts || value?.orbitzFormat)) GLib.idle_add(GLib.PRIORITY_DEFAULT_IDLE, () => {
        for (const [property, value] of Object.entries(values)) bind(owner, property, value);
        return GLib.SOURCE_REMOVE;
    });
    return plain;
}
function refresh() {
    for (const item of bindings) {
        const owner = item.owner.deref();
        if (!owner) { bindings.delete(item); continue; }
        try { if (item.method) owner[item.property](text(item.value)); else owner[item.property] = text(item.value); }
        catch (error) { bindings.delete(item); }
    }
    for (const callback of listeners) callback(locale);
}
function items(owner, StringList, messages) {
    const reference = new WeakRef(owner);
    const update = () => {
        const target = reference.deref();if (!target) return;
        const selected = target.selected;
        target.orbitzLanguageUpdating = true;
        target.model = StringList.new(messages.map(text));
        target.selected = selected;
        target.orbitzLanguageUpdating = false;
    };
    update();
    const unwatch = watch(update);
    owner.connect('unrealize', unwatch);
    return owner;
}
function configure(value) {
    if (settings === value) return;
    if (settings && signal) settings.disconnect(signal);
    settings = value;locale = normalize(settings.get_string('ui-language'));
    signal = settings.connect('changed::ui-language', () => { locale = normalize(settings.get_string('ui-language'));refresh(); });
}
function watch(callback) { listeners.add(callback);return () => listeners.delete(callback); }
function button(dialog, label, response) { return set(dialog.add_button(text(label), response), 'label', label); }
function spawn(argv, flags) {
    const launcher = new Gio.SubprocessLauncher({flags});
    launcher.setenv('ORBITZ_LOCALE', locale, true);
    const root = directory();if (root) launcher.setenv('ORBITZ_I18N_DIR', root, true);
    return launcher.spawnv(argv);
}
var Language = {normalize, tr, msg, join, number, date, text, error, widget, set, call, properties, items, configure, watch, button, spawn, directory, getLocale: () => locale};

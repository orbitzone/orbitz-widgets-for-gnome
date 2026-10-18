// Real GObject registrations representing both identities in one process; no GUI.
const {GObject, GLib, Gio} = imports.gi;
const root = ARGV[0];
const files = ['extension/extension.js', 'extension/prefs.js'];
const directory = Gio.File.new_for_path(root + '/extension/settings');
const entries = directory.enumerate_children('standard::name', Gio.FileQueryInfoFlags.NONE, null);
let entry;
while ((entry = entries.next_file(null))) {
    if (entry.get_name().endsWith('.js')) files.push('extension/settings/' + entry.get_name());
}
entries.close(null);
const names = new Set();
let count = 0;
for (const file of files) {
    const [, bytes] = GLib.file_get_contents(root + '/' + file);
    const source = new TextDecoder().decode(bytes);
    const starts = [...source.matchAll(/var (\w+) = GObject\.registerClass\(/g)];
    for (let i = 0; i < starts.length; i++) {
        const block = source.slice(starts[i].index, starts[i + 1]?.index);
        const legacyName = block.match(/class (\w+) extends /)?.[1];
        const orbitzName = block.match(/GTypeName:\s*'([^']+)'/)?.[1];
        if (!legacyName || !orbitzName?.startsWith('OrbitzWidgets') || names.has(orbitzName))
            throw Error(`Missing/duplicate identity at ${file}:${starts[i][1]}`);
        names.add(orbitzName);
        const make = () => new Function('GObject', `return class ${legacyName} extends GObject.Object {}`)(GObject);
        const legacy = GObject.registerClass(make());
        let collided = false;
        try { GObject.registerClass(make()); } catch (error) { collided = /already registered/.test(error.message); }
        if (!collided) throw Error('Legacy collision not reproduced: ' + legacyName);
        const orbitz = GObject.registerClass({GTypeName: orbitzName}, make());
        if (!GObject.type_from_name(orbitzName) || legacy.$gtype === orbitz.$gtype)
            throw Error('Distinct GType not registered: ' + orbitzName);
        count++;
    }
}
if (count !== 20) throw Error('Unexpected registered class coverage: ' + count);
print(`OK: ${count} legacy/Orbitz class pairs coexist as distinct real GTypes; implicit duplicate collision reproduced for each.`);

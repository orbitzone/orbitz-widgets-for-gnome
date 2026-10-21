/* eslint-disable jsdoc/require-jsdoc */
let catalogCache = null;

function parse(content) {
    const entries = new Map();
    for (const rawLine of String(content || '').split(/\r?\n/)) {
        const line = rawLine.trim();
        if (!line || line.startsWith('#')) continue;
        const [countries = '', , identifier = '', comment = ''] = line.split('\t');
        if (!identifier || !identifier.includes('/')) continue;
        const parts = identifier.split('/');
        const region = parts.slice(0, -1).join(' / ').replaceAll('_', ' ');
        const fallbackCity = parts.slice(1).join(' / ');
        const city = (comment && !/[(),:]/.test(comment) ? comment : fallbackCity).replaceAll('_', ' ').trim();
        entries.set(identifier, {identifier, city, region, countries});
    }
    entries.set('UTC', {identifier: 'UTC', city: 'UTC', region: 'UTC', countries: ''});
    return [...entries.values()].sort((a, b) => a.city.localeCompare(b.city) || a.identifier.localeCompare(b.identifier));
}

function search(entries, query) {
    const normalized = String(query || '').normalize().toLocaleLowerCase();
    if (!normalized) return [];
    return entries.filter(entry => [entry.city, entry.region, entry.identifier,
        entry.identifier.replaceAll('_', ' ').replaceAll('/', ' '), entry.countries]
        .some(value => value.normalize().toLocaleLowerCase().includes(normalized)));
}

function load(GLib) {
    if (catalogCache) return catalogCache;
    for (const path of ['/usr/share/zoneinfo/zone.tab', '/usr/share/zoneinfo/zone1970.tab']) {
        try {
            const [, bytes] = GLib.file_get_contents(path);
            const entries = parse(new TextDecoder().decode(bytes));
            if (entries.length > 1) {
                catalogCache = entries;
                return catalogCache;
            }
        } catch (error) { /* Try the alternate tzdata catalog path. */ }
    }
    catalogCache = parse('');
    return catalogCache;
}

function displayName(GLib, entry) {
    const zone = GLib.TimeZone.new(entry.identifier);
    const interval = zone.find_interval(GLib.TimeType.UNIVERSAL, Math.floor(Date.now() / 1000));
    const offset = zone.get_offset(interval);
    const hours = Math.trunc(Math.abs(offset) / 3600);
    const minutes = Math.trunc((Math.abs(offset) % 3600) / 60);
    const formattedOffset = `${offset < 0 ? '-' : '+'}${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    return `${entry.city} · ${entry.region} · ${entry.identifier} · UTC${formattedOffset}`;
}

function createDropDown(GLib, Gtk, selectedIdentifier) {
    const entries = load(GLib);
    const strings = new Gtk.StringList();
    entries.forEach(entry => strings.append(displayName(GLib, entry)));
    const selected = Math.max(0, entries.findIndex(entry => entry.identifier === selectedIdentifier));
    const dropdown = new Gtk.DropDown({model: strings, selected, enable_search: true});
    dropdown.orbitzTimeZones = entries;
    return dropdown;
}

var TimeZoneCatalog = {createDropDown, displayName, load, parse, search};

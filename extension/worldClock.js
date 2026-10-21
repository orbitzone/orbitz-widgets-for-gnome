/* eslint-disable jsdoc/require-jsdoc */
function format(GLib, identifier, pattern = '%H:%M') {
    if (!identifier || !pattern) return '';
    try {
        const zone = GLib.TimeZone.new(identifier);
        if (!zone || zone.get_identifier() !== identifier) return '';
        const now = GLib.DateTime.new_now(zone);
        return now ? (now.format(pattern) || '') : '';
    } catch (error) {
        return '';
    }
}

function isTimeFormat(pattern) {
    return /%[HIk lMS]/.test(String(pattern || ''));
}

var WorldClock = {format, isTimeFormat};

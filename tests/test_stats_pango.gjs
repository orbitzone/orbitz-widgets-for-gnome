// Run with GJS: real Pango geometry without a window or a Shell session.
const {GLib, Pango, PangoCairo} = imports.gi;
const [, bytes] = GLib.file_get_contents(ARGV[0] + '/extension/extension.js');
const source = new TextDecoder().decode(bytes);
const method = source.slice(source.indexOf('    _storageTarget(pointer) {') + '    _storageTarget'.length,
    source.indexOf('    async _ejectExternalDevice(device)'));
const target = new Function('Pango', 'return function' + method)(Pango);
const layout = Pango.Layout.new(PangoCairo.FontMap.get_default().create_context());
layout.set_font_description(Pango.FontDescription.from_string('Cantarell 8'));
layout.set_alignment(Pango.Alignment.CENTER);
const rows = ['  CPU    █░░░░░░░   11%', '  RAM    ████░░░░   45%', '  SSD    ███████░   90%', '  EXT    ██░░░░░░   20%'];
for (const count of [3, 4]) {
layout.set_markup('<span font_family="monospace" size="7680" line_height="1.5">' + rows.slice(0, count).join('\n') + '</span>', -1);
for (const width of [-1, 220, 440]) {
    layout.set_width(width < 0 ? -1 : width * Pango.SCALE);
    const host = {clutter_text: {transform_stage_point: (x, y) => [true, x, y],
        get_layout: () => layout, get_text: () => layout.get_text()}};
    const iter = layout.get_iter();
    let row = 0;
    do {
        const [, rect] = iter.get_line_extents();
        const y = (rect.y + rect.height / 2) / Pango.SCALE;
        for (const x of [rect.x / Pango.SCALE + 1, (rect.x + rect.width / 2) / Pango.SCALE,
            (rect.x + rect.width - 1) / Pango.SCALE]) {
            const actual = target.call(host, [x, y]);
            const expected = ['cpu', 'ram', 'ssd', 'external:0'][row];
            if (actual !== expected) throw Error(`width=${width} row=${row} x=${x}: ${actual} != ${expected}`);
        }
        row++;
    } while (iter.next_line());
    if (row !== count) throw Error(`Unexpected row count: ${row}`);
}
}
print('OK: historical markup size7680/line_height1.5/bar8; real centered Pango CPU/RAM/SSD hits with/without EXT at label/bar/end, natural/220/440 widths.');

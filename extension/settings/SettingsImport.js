const Language = imports.misc.extensionUtils.getCurrentExtension().imports.uiLanguage.Language;
const {Gio, GLib} = imports.gi;

function validateWidgets(data) {
    if (!Array.isArray(data) || data.length > 100)
        throw Language.error(Language.msg('settings.validation.widgets_limit'));
    const commands = [];
    let elements = 0;
    for (const widget of data) {
        if (!Array.isArray(widget) || !widget.length || widget.length > 100)
            throw Language.error(Language.msg('settings.validation.widget'));
        elements += widget.length;
        if (elements > 300)
            throw Language.error(Language.msg('settings.validation.elements_limit'));
        for (const element of widget) {
            if (!element || typeof element !== 'object' || Array.isArray(element) || Object.keys(element).length > 150 ||
                Object.entries(element).some(([key, value]) => key.length > 128 || typeof value !== 'string' || value.length > 8192))
                throw Language.error(Language.msg('settings.validation.fields'));
            for (const [key, value] of Object.entries(element)) {
                if ((key === 'Clock_Size' || key === 'Text_Size' || /(?:Padding|Margin|BorderWidth|Spacing)/.test(key)) &&
                    (!Number.isFinite(Number(value)) || Math.abs(Number(value)) > (key === 'Clock_Size' ? 2048 : 512)))
                    throw Language.error(Language.msg('settings.validation.dimension', {key}));
            }
            if (element.Text_Command)
                commands.push(element.Text_Command);
            const maxPollingInterval = (element.Text_Command || '').includes('/currency-widget.py') ? 14400000 : 3600000;
            if (element.Element_Type === 'Command_Label' && (!Number.isFinite(Number(element.Text_PollingInterval)) ||
                Number(element.Text_PollingInterval) < 250 || Number(element.Text_PollingInterval) > maxPollingInterval))
                throw Language.error(Language.msg('settings.validation.polling'));
        }
        if (widget[0].Widget_Type !== 'Widget_Box')
            throw Language.error(Language.msg('settings.validation.widget_type'));
        if (widget.slice(1).some(element => !['Digital_Clock', 'Analog_Clock', 'Text_Label', 'Command_Label'].includes(element.Element_Type)))
            throw Language.error(Language.msg('settings.validation.element_type'));
    }
    return commands;
}

function parse(text, settings) {
    if (new TextEncoder().encode(text).length > 1048576)
        throw Language.error(Language.msg('settings.validation.size'));
    let values;
    if (text.trim().startsWith('{')) {
        const data = JSON.parse(text);
        if (data.format !== 'orbitz-settings-v1' || !data.values || typeof data.values !== 'object' || Array.isArray(data.values))
            throw Language.error(Language.msg('settings.validation.format'));
        values = data.values;
    } else {
        const file = new GLib.KeyFile();
        file.load_from_data(text, new TextEncoder().encode(text).length, GLib.KeyFileFlags.NONE);
        const groups = file.get_groups()[0];
        if (groups.length !== 1 || groups[0] !== '/')
            throw Language.error(Language.msg('settings.validation.sections'));
        values = {};
        for (const key of file.get_keys('/')[0])
            values[key] = file.get_value('/', key);
    }
    const parsed = {};
    const schema = settings.settings_schema;
    for (const [key, value] of Object.entries(values)) {
        if (!schema.has_key(key) || typeof value !== 'string')
            throw Language.error(Language.msg('settings.validation.key', {key}));
        if (key === 'changed-data')
            continue;
        const schemaKey = schema.get_key(key);
        const variant = GLib.Variant.parse(schemaKey.get_value_type(), value, null, null);
        if (!schemaKey.range_check(variant))
            throw Language.error(Language.msg('settings.validation.range', {key}));
        parsed[key] = variant;
    }
    if (!parsed['widget-data'])
        throw Language.error(Language.msg('settings.validation.no_widgets'));
    const commands = validateWidgets(parsed['widget-data'].deep_unpack());
    return {values: parsed, commands};
}

function read(path) {
    const file = Gio.File.new_for_path(path);
    const info = file.query_info('standard::type,standard::size', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, null);
    if (info.get_file_type() !== Gio.FileType.REGULAR || info.get_size() > 1048576)
        throw Language.error(Language.msg('settings.validation.regular_file'));
    const stream = file.read(null);
    try {
        const bytes = stream.read_bytes(1048577, null).get_data();
        if (bytes.length > 1048576)
            throw Language.error(Language.msg('settings.validation.file_size'));
        return new TextDecoder('utf-8', {fatal: true}).decode(bytes);
    } finally { stream.close(null); }
}

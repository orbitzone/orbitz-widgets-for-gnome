const {Gio, GLib} = imports.gi;

function validateWidgets(data) {
    if (!Array.isArray(data) || data.length > 100)
        throw new Error('Configuração deve conter até 100 widgets.');
    const commands = [];
    let elements = 0;
    for (const widget of data) {
        if (!Array.isArray(widget) || !widget.length || widget.length > 100)
            throw new Error('Widget inválido.');
        elements += widget.length;
        if (elements > 300)
            throw new Error('Configuração excede 300 elementos.');
        for (const element of widget) {
            if (!element || typeof element !== 'object' || Array.isArray(element) || Object.keys(element).length > 150 ||
                Object.entries(element).some(([key, value]) => key.length > 128 || typeof value !== 'string' || value.length > 8192))
                throw new Error('Campos de widget inválidos.');
            for (const [key, value] of Object.entries(element)) {
                if ((key === 'Clock_Size' || key === 'Text_Size' || /(?:Padding|Margin|BorderWidth|Spacing)/.test(key)) &&
                    (!Number.isFinite(Number(value)) || Math.abs(Number(value)) > (key === 'Clock_Size' ? 2048 : 512)))
                    throw new Error('Dimensão inválida: ' + key);
            }
            if (element.Text_Command)
                commands.push(element.Text_Command);
            if (element.Element_Type === 'Command_Label' && (!Number.isFinite(Number(element.Text_PollingInterval)) ||
                Number(element.Text_PollingInterval) < 250 || Number(element.Text_PollingInterval) > 3600000))
                throw new Error('Intervalo de comando inválido.');
        }
        if (widget[0].Widget_Type !== 'Widget_Box')
            throw new Error('Tipo de widget inválido.');
        if (widget.slice(1).some(element => !['Digital_Clock', 'Analog_Clock', 'Text_Label', 'Command_Label'].includes(element.Element_Type)))
            throw new Error('Tipo de elemento inválido.');
    }
    return commands;
}

function parse(text, settings) {
    if (new TextEncoder().encode(text).length > 1048576)
        throw new Error('Arquivo de configuração excede 1 MiB.');
    let values;
    if (text.trim().startsWith('{')) {
        const data = JSON.parse(text);
        if (data.format !== 'orbitz-settings-v1' || !data.values || typeof data.values !== 'object' || Array.isArray(data.values))
            throw new Error('Formato inválido.');
        values = data.values;
    } else {
        const file = new GLib.KeyFile();
        file.load_from_data(text, new TextEncoder().encode(text).length, GLib.KeyFileFlags.NONE);
        const groups = file.get_groups()[0];
        if (groups.length !== 1 || groups[0] !== '/')
            throw new Error('Seções de configuração inválidas.');
        values = {};
        for (const key of file.get_keys('/')[0])
            values[key] = file.get_value('/', key);
    }
    const parsed = {};
    const schema = settings.settings_schema;
    for (const [key, value] of Object.entries(values)) {
        if (!schema.has_key(key) || typeof value !== 'string')
            throw new Error('Chave desconhecida ou inválida: ' + key);
        if (key === 'changed-data')
            continue;
        const schemaKey = schema.get_key(key);
        const variant = GLib.Variant.parse(schemaKey.get_value_type(), value, null, null);
        if (!schemaKey.range_check(variant))
            throw new Error('Valor fora do intervalo: ' + key);
        parsed[key] = variant;
    }
    if (!parsed['widget-data'])
        throw new Error('Configuração não contém widgets.');
    const commands = validateWidgets(parsed['widget-data'].deep_unpack());
    return {values: parsed, commands};
}

function read(path) {
    const file = Gio.File.new_for_path(path);
    const info = file.query_info('standard::type,standard::size', Gio.FileQueryInfoFlags.NOFOLLOW_SYMLINKS, null);
    if (info.get_file_type() !== Gio.FileType.REGULAR || info.get_size() > 1048576)
        throw new Error('Selecione um arquivo regular de até 1 MiB.');
    const stream = file.read(null);
    try {
        const bytes = stream.read_bytes(1048577, null).get_data();
        if (bytes.length > 1048576)
            throw new Error('Arquivo excede 1 MiB.');
        return new TextDecoder('utf-8', {fatal: true}).decode(bytes);
    } finally { stream.close(null); }
}

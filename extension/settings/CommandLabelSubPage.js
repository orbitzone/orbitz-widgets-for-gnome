const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const {Adw, Gio, GLib, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Gettext.gettext;

const Settings = Me.imports.settings;
const {TextLabelSubPage} = Settings.TextLabelSubPage;

var CommandLabelSubPage = GObject.registerClass({GTypeName: 'OrbitzWidgetsCommandLabelSubPage'},
class AzClockCommandLabelSubPage extends TextLabelSubPage {
    _init(settings, params) {
        super._init(settings, params);

        this.removeTextRow();

        const commandExpanderRow = new Adw.ExpanderRow({
            title: _('Command'),
            expanded: true,
            enable_expansion: true,
        });

        const commandEntry = new Gtk.Entry({
            valign: Gtk.Align.FILL,
            vexpand: true,
            halign: Gtk.Align.FILL,
            hexpand: true,
            text: this.getClockElementData('Text_Command') || '',
        });
        commandEntry.connect('changed', () => {
            this.setClockElementData('Text_Command', commandEntry.get_text());
        });
        const commandRow = new Adw.ActionRow({
            activatable: false,
            selectable: false,
        });

        commandRow.set_child(commandEntry);
        commandExpanderRow.add_row(commandRow);
        this.textGroupAdd(commandExpanderRow);

        const command = this.getClockElementData('Text_Command') || '';
        const isCurrency = command.includes('currency-widget.py');
        const pollingIntervalRow = this.createSpinRow(_('Polling Interval (ms)'), 'Text_PollingInterval', 250,
            isCurrency ? 14400000 : 3600000);
        this.textGroupAdd(pollingIntervalRow);
        if (isCurrency) {
            commandEntry.sensitive = false;
            commandEntry.tooltip_text = _('Use the controls below to configure this converter.');
            this._addCurrencyControls(command);
            pollingIntervalRow.sensitive = false;
            pollingIntervalRow.subtitle = _('Updates automatically every four hours; use the widget to refresh manually.');
            if (this.getClockElementData('Text_PollingInterval') !== '14400000')
                this.setClockElementData('Text_PollingInterval', '14400000');
        }
        if (command.startsWith('playerctl -p spotify,chromium metadata')) {
            pollingIntervalRow.sensitive = false;
            pollingIntervalRow.subtitle = 'Atualização por eventos de mídia';
        } else if (command.includes('/firewall-widget.py')) {
            pollingIntervalRow.sensitive = false;
            pollingIntervalRow.subtitle = 'Atualização manual na modal';
        }
    }

    _addCurrencyControls(command) {
        const group = new Adw.PreferencesGroup({title: _('Currency converter')});
        this.textGroupAdd(group);

        const parsed = GLib.shell_parse_argv(command);
        const argv = parsed[0] ? parsed[1] : [];
        let quote = 'USD';
        let reverse = false;
        for (let i = 0; i < argv.length; i++) {
            if (argv[i] === '--quote' && /^[A-Z]{3}$/.test(argv[i + 1] || '')) quote = argv[++i];
            else if (argv[i] === '--reverse') reverse = true;
        }

        const picker = new Gtk.DropDown({enable_search: true, sensitive: false});
        const pickerRow = new Adw.ActionRow({title: _('Convert BRL to'), subtitle: _('Loading supported currencies…')});
        pickerRow.add_suffix(picker);
        group.add(pickerRow);

        const directionRow = new Adw.SwitchRow({
            title: _('Reverse conversion'),
            subtitle: _('Convert the selected currency back to BRL.'),
            active: reverse,
        });
        group.add(directionRow);

        const script = GLib.build_filenamev([GLib.get_user_data_dir(), 'orbitz-widgets', 'collectors', 'currency-widget.py']);
        let choices = [];
        let loaded = false;
        const updateCommand = () => {
            if (!loaded || !choices[picker.selected]) return;
            const code = choices[picker.selected].code;
            const next = ['/usr/bin/python3', GLib.shell_quote(script), '--quote', code];
            if (directionRow.active) next.push('--reverse');
            this.setClockElementData('Text_Command', next.join(' '));
            pickerRow.title = directionRow.active ? _('Convert to BRL') : _('Convert BRL to');
            pickerRow.subtitle = choices[picker.selected].name;
        };
        picker.connect('notify::selected', updateCommand);
        directionRow.connect('notify::active', updateCommand);

        try {
            const proc = Gio.Subprocess.new(['/usr/bin/python3', script, '--catalog-json'],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE);
            proc.communicate_utf8_async(null, null, (source, result) => {
                try {
                    const [success, output] = source.communicate_utf8_finish(result);
                    if (!success || !source.get_successful())
                        throw new Error('Currency catalog process failed');
                    const catalog = JSON.parse(output);
                    if (!catalog || Array.isArray(catalog) || typeof catalog !== 'object')
                        throw new Error('Invalid currency catalog');
                    choices = Object.entries(catalog).filter(([code, name]) => /^[A-Z]{3}$/.test(code) &&
                        typeof name === 'string' && name.length <= 160).map(([code, name]) => ({code, name}))
                        .sort((a, b) => a.name.localeCompare(b.name));
                    if (!choices.length) throw new Error('Empty currency catalog');
                    picker.model = Gtk.StringList.new(choices.map(item => `${item.code} · ${item.name}`));
                    const index = choices.findIndex(item => item.code === quote);
                    picker.selected = Math.max(0, index >= 0 ? index : choices.findIndex(item => item.code === 'USD'));
                    picker.sensitive = true;
                    loaded = true;
                    updateCommand();
                } catch (error) {
                    pickerRow.subtitle = _('Could not load the currency list. Check the connection and reopen Settings.');
                }
            });
        } catch (error) {
            pickerRow.subtitle = _('Currency converter is not installed yet. Update Orbitz and reopen Settings.');
        }
    }
});

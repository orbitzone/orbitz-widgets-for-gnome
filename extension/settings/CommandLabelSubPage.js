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

    setClockElementData(elementType, newValue) {
        const guard = this._currencyIdentityGuard;
        if (guard && !guard.current()) return;
        super.setClockElementData(elementType, newValue);
        // Accept edits made by this live page (for example Name) without
        // accepting external changes that could have moved/replaced its target.
        if (guard) guard.acceptOwnChange();
    }

    _addCurrencyControls(command) {
        const group = new Adw.PreferencesGroup({title: _('Currency converter')});
        this.textGroupAdd(group);
        let argv = [];
        try { const parsed = GLib.shell_parse_argv(command); if (parsed[0]) argv = parsed[1]; } catch (error) { /* Keep defaults for a damaged command. */ }
        const value = flag => argv[argv.indexOf(flag) + 1];
        const crypto = argv.includes('--mode') && value('--mode') === 'crypto';
        const remembered = {fiat: argv.includes('--quote') && /^[A-Z]{3}$/.test(value('--quote')) ? value('--quote') : 'USD',
            crypto: argv.includes('--asset') && /^[a-z0-9-]+$/.test(value('--asset')) ? value('--asset') : 'btc-bitcoin'};
        const category = new Gtk.DropDown({model: Gtk.StringList.new(['Fiat', 'Crypto']), selected: crypto ? 1 : 0});
        const categoryRow = new Adw.ActionRow({title: _('Category')});
        categoryRow.add_suffix(category);group.add(categoryRow);
        const picker = new Gtk.DropDown({enable_search: true, sensitive: false});
        const pickerRow = new Adw.ActionRow({title: _('Asset'), subtitle: _('Loading supported currencies…')});
        pickerRow.add_suffix(picker);group.add(pickerRow);
        // Adw.SwitchRow requires libadwaita 1.4; GNOME 42 ships 1.1.
        const direction = new Gtk.Switch({active: argv.includes('--reverse'), valign: Gtk.Align.CENTER, sensitive: false});
        const directionRow = new Adw.ActionRow({title: _('Reverse conversion'), activatable_widget: direction});
        directionRow.add_suffix(direction);group.add(directionRow);
        const script = GLib.build_filenamev([GLib.get_user_data_dir(), 'orbitz-widgets', 'collectors', 'currency-widget.py']);
        let choices = [], loaded = false, generation = 0, alive = true;
        const widgetIndex = this.widget_index, elementIndex = this.element_index;
        const snapshot = () => JSON.stringify(this._settings.get_value('widget-data').deep_unpack());
        let targetState = snapshot();
        const current = () => alive && this.widget_index === widgetIndex && this.element_index === elementIndex && snapshot() === targetState;
        this._currencyIdentityGuard = {current, acceptOwnChange: () => { targetState = snapshot(); }};
        this.connect('unrealize', () => { alive = false; generation++; });
        const mode = () => category.selected === 1 ? 'crypto' : 'fiat';
        const updateCommand = (persist = true) => {
            if (!current() || !loaded || !choices[picker.selected]) return;
            direction.sensitive = true;
            const selected = choices[picker.selected];remembered[mode()] = selected.id;
            const next = ['/usr/bin/python3', GLib.shell_quote(script)];
            if (mode() === 'crypto') next.push('--mode', 'crypto', '--asset', selected.id);
            else next.push('--quote', selected.id);
            if (direction.active) next.push('--reverse');
            if (persist) {
                this.setClockElementData('Text_Command', next.join(' '));
                targetState = snapshot();
            }
            const base = mode() === 'crypto' ? 'USD' : 'BRL';
            pickerRow.title = direction.active ? `${selected.symbol} → ${base}` : `${base} → ${selected.symbol}`;
            pickerRow.subtitle = selected.name;
            directionRow.subtitle = mode() === 'crypto' ? _('Reverse between USD and the selected crypto asset.') : _('Convert the selected currency back to BRL.');
        };
        const loadCatalog = (persist = false) => {
            if (!current()) return;
            const request = ++generation, requestedMode = mode();
            loaded = false;picker.sensitive = false;direction.sensitive = false;
            pickerRow.subtitle = _('Loading supported currencies…');
            categoryRow.subtitle = requestedMode === 'crypto' ? 'Powered by CoinPaprika' : _('Fiat reference rates');
            const args = ['/usr/bin/python3', script];
            if (requestedMode === 'crypto') args.push('--mode', 'crypto');
            args.push('--catalog-json');
            try {
                const proc = Gio.Subprocess.new(args, Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE);
                proc.communicate_utf8_async(null, null, (source, result) => {
                    try {
                        const [success, output] = source.communicate_utf8_finish(result);
                        if (request !== generation || !alive) return;
                        if (!current()) {
                            pickerRow.subtitle = _('Settings changed. Reopen this configuration to select an asset.');
                            return;
                        }
                        if (!success || !source.get_successful()) throw new Error('Catalog process failed');
                        const catalog = JSON.parse(output);
                        if (requestedMode === 'crypto') {
                            if (!Array.isArray(catalog.assets) || catalog.assets.length > 5000) throw new Error('Invalid crypto catalog');
                            choices = catalog.assets.filter(item => item && typeof item.id === 'string' && /^[a-z0-9-]{1,100}$/.test(item.id) &&
                                typeof item.symbol === 'string' && /^[A-Za-z0-9]{1,20}$/.test(item.symbol) && typeof item.name === 'string' && item.name.length <= 160)
                                .map(item => ({id: item.id, symbol: item.symbol, name: item.name}));
                        } else {
                            if (!catalog || Array.isArray(catalog) || typeof catalog !== 'object') throw new Error('Invalid fiat catalog');
                            choices = Object.entries(catalog).filter(([code, name]) => /^[A-Z]{3}$/.test(code) && typeof name === 'string' && name.length <= 160)
                                .map(([code, name]) => ({id: code, symbol: code, name}));
                        }
                        choices.sort((a, b) => a.name.localeCompare(b.name));
                        if (!choices.length) throw new Error('Empty catalog');
                        picker.model = Gtk.StringList.new(choices.map(item => `${item.symbol} · ${item.name} (${item.id})`));
                        const index = choices.findIndex(item => item.id === remembered[requestedMode]);
                        picker.selected = index < 0 ? Gtk.INVALID_LIST_POSITION : index;
                        picker.sensitive = true;loaded = true;
                        if (index < 0) {
                            direction.sensitive = false;
                            pickerRow.title = `${_('Unavailable asset')}: ${remembered[requestedMode]}`;
                            pickerRow.subtitle = _('The configured asset is unavailable. Select another asset to change it.');
                            return;
                        }
                        direction.sensitive = true;updateCommand(persist);
                    } catch (error) {
                        if (request === generation) pickerRow.subtitle = _('Could not load the asset list. Check the connection and reopen Settings.');
                    }
                });
            } catch (error) { pickerRow.subtitle = _('Currency converter is not installed yet. Update Orbitz and reopen Settings.'); }
        };
        picker.connect('notify::selected', () => updateCommand());
        direction.connect('notify::active', () => updateCommand());
        category.connect('notify::selected', () => loadCatalog(true));
        loadCatalog();
    }
});

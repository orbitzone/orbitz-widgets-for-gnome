// Fiat/crypto currency converter modal; selected pair and direction live in Text_Command.
var create = ({Language, Clutter, Gio, GLib, Main, Me, Pango, St, Utils, global, getData, getWidgetData, readCommandOutput, stopCommandRun}) => ({
    _buildCurrencyDialog() {
        this._networkBackdrop = Language.widget(St.Widget, {reactive: true, visible: false});
        this._networkBackdrop.add_constraint(new Clutter.BindConstraint({source: global.stage, coordinate: Clutter.BindCoordinate.ALL}));
        this._networkBackdrop.connect('button-press-event', (_actor, event) => {
            if (this._networkDialog?.contains(event.get_source()))
                return Clutter.EVENT_PROPAGATE;
            this._closeNetworkDialog();
            return Clutter.EVENT_STOP;
        });
        Main.uiGroup.add_child(this._networkBackdrop);

        this._networkDialog = Language.widget(St.BoxLayout, {vertical: true, reactive: true,
            style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 8px; padding: 16px; spacing: 12px; width: 390px;'});
        const header = Language.widget(St.BoxLayout, {style: 'spacing: 12px;'});
        header.add_child(Language.widget(St.Label, {text: Language.msg('panels.currency.title'), style: 'font-weight: bold; font-size: 18px;', x_expand: true}));
        const closeButton = Language.widget(St.Button, {reactive: true, can_focus: true, accessible_name: Language.msg('panels.currency.close'),
            style: 'background-color: transparent; color: white; padding: 4px;'});
        closeButton.set_child(Language.widget(St.Icon, {icon_name: 'window-close-symbolic', icon_size: 16}));
        closeButton.connect('clicked', () => this._closeNetworkDialog());
        header.add_child(closeButton);
        this._networkDialog.add_child(header);

        this._currencyRateLabel = Language.widget(St.Label, {text: this.text || Language.msg('panels.currency.loading'),
            style: 'font-size: 24px; font-weight: bold; padding: 12px 4px;', x_align: Clutter.ActorAlign.CENTER});
        this._currencyRateLabel.clutter_text.set_line_wrap(true);
        this._currencyRateLabel.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
        this._networkDialog.add_child(this._currencyRateLabel);
        this._currencySourceLabel = Language.widget(St.Label, {text: '', style: 'font-size: 11px; color: #c8c8c8;'});
        this._networkDialog.add_child(this._currencySourceLabel);

        this._currencyQuote = null;
        this._networkDialog.add_child(Language.widget(St.Label, {text: Language.msg('panels.currency.amount'), style: 'font-weight: bold;'}));
        this._currencyAmountEntry = Language.widget(St.Entry, {text: '1', hint_text: Language.msg('panels.currency.hint'),
            can_focus: true, x_expand: true, accessible_name: Language.msg('panels.currency.amount'),
            style: 'background-color: #343434; color: white; padding: 10px; border-radius: 4px;'});
        this._currencyAmountEntry.clutter_text.set_max_length(60);
        this._currencyAmountEntry.clutter_text.connect('text-changed', () => this._updateCurrencyCalculation());
        this._networkDialog.add_child(this._currencyAmountEntry);
        this._currencyTotalLabel = Language.widget(St.Label, {text: Language.msg('panels.currency.waiting'),
            style: 'font-size: 20px; font-weight: bold; padding: 4px;'});
        this._currencyTotalLabel.clutter_text.set_line_wrap(true);
        this._currencyTotalLabel.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
        this._networkDialog.add_child(this._currencyTotalLabel);

        const controls = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
        this._currencyDirectionButton = Language.widget(St.Button, {reactive: true, can_focus: true,
            style: 'background-color: #343434; color: white; padding: 8px 12px;', x_expand: true});
        this._currencyDirectionButton.connect('clicked', () => this._toggleCurrencyDirection());
        controls.add_child(this._currencyDirectionButton);
        this._networkRefreshButton = Language.widget(St.Button, {reactive: true, can_focus: true,
            label: Language.msg('panels.currency.refresh'), accessible_name: Language.msg('panels.currency.refresh_accessible'),
            style: 'background-color: #315d80; color: white; padding: 8px 12px;'});
        this._networkRefreshButton.connect('clicked', () => this._refreshCurrencyDialog());
        controls.add_child(this._networkRefreshButton);
        this._networkDialog.add_child(controls);
        this._networkRefreshStatus = Language.widget(St.Label, {text: '', style: 'font-size: 12px; color: #c8c8c8;'});
        this._networkDialog.add_child(this._networkRefreshStatus);
        this._networkBackdrop.add_child(this._networkDialog);
        this._updateCurrencyDirectionButton(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
    },

    // Exact decimal multiplication; only fiat totals are rounded to cents.
    _currencyProduct(amount, rate, fullPrecision = false) {
        const decimal = text => {
            const [mantissa, exponent = '0'] = text.toLowerCase().split('e');
            const [whole, fraction = ''] = mantissa.split('.');
            const scale = fraction.length - Number(exponent);
            if (Math.abs(scale) > 1000) throw Language.error(Language.msg('panels.currency.limit'));
            return [BigInt(whole + fraction), scale];
        };
        const [a, sa] = decimal(amount), [b, sb] = decimal(rate);
        let cents = a * b;
        if (fullPrecision) {
            const scale = sa + sb;
            let digits = cents.toString();
            if (scale <= 0) digits += '0'.repeat(-scale);
            else digits = digits.padStart(scale + 1, '0');
            const whole = scale > 0 ? digits.slice(0, -scale) : digits;
            const fraction = scale > 0 ? digits.slice(-scale).replace(/0+$/, '') : '';
            return whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (fraction ? ',' + fraction : '');
        }
        const scale = sa + sb - 2;
        if (scale > 0) {
            const divisor = 10n ** BigInt(scale);
            cents = (cents + divisor / 2n) / divisor;
        } else cents *= 10n ** BigInt(-scale);
        const digits = cents.toString().padStart(3, '0');
        return digits.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + digits.slice(-2);
    },

    _updateCurrencyCalculation() {
        if (!this._currencyTotalLabel) return;
        if (!this._currencyQuote) {
            Language.set(this._currencyTotalLabel, 'text', Language.msg('panels.currency.wait_valid'));
            return;
        }
        const raw = this._currencyAmountEntry.get_text().trim();
        // Brazilian grouping/decimal syntax, also accept an ungrouped decimal point.
        const valid = /^(?:[0-9]+(?:[,.][0-9]+)?|[0-9]{1,3}(?:\.[0-9]{3})+(?:,[0-9]+)?)$/.test(raw);
        if (!valid || raw.length > 60) {
            Language.set(this._currencyTotalLabel, 'text', raw ? Language.msg('panels.currency.invalid_amount') : Language.msg('panels.currency.enter_amount'));
            return;
        }
        const amount = raw.includes(',') || /^[0-9]{1,3}(?:\.[0-9]{3})+$/.test(raw)
            ? raw.replace(/\./g, '').replace(',', '.') : raw;
        try {
            const item = this._currencyQuote;
            Language.set(this._currencyAmountEntry, 'accessible_name', Language.msg('panels.currency.amount_in', {base: item.base}));
            Language.set(this._currencyTotalLabel, 'text', Language.msg('panels.currency.total', {amount: this._currencyProduct(amount, item.rate, Boolean(item.asset)), quote: item.quote}));
        } catch (error) { Language.set(this._currencyTotalLabel, 'text', Language.msg('panels.currency.limit')); }
    },

    _currencyCommandInfo(command) {
        try {
            const [ok, argv] = GLib.shell_parse_argv(command);
            if (!ok || !argv.some(arg => arg.endsWith('/currency-widget.py')))
                return null;
            const quoteIndex = argv.indexOf('--quote');
            const quote = quoteIndex >= 0 ? argv[quoteIndex + 1] : 'USD';
            const crypto = argv[argv.indexOf('--mode') + 1] === 'crypto' && argv.includes('--mode');
            const assetIndex = argv.indexOf('--asset');
            const asset = assetIndex >= 0 ? argv[assetIndex + 1] : 'btc-bitcoin';
            return {argv, quote: crypto ? asset : quote, base: crypto ? 'USD' : 'BRL', crypto, reverse: argv.includes('--reverse')};
        } catch (error) { return null; }
    },

    _updateCurrencyDirectionButton(command) {
        const info = this._currencyCommandInfo(command);
        if (!info || !this._currencyDirectionButton)
            return;
        const item = this._currencyQuote;
        const symbol = !info.crypto ? info.quote : item?.asset === info.quote
            ? (item.base === 'USD' ? item.quote : item.base) : info.quote.split('-')[0].toUpperCase();
        const from = info.reverse ? symbol : info.base;
        const to = info.reverse ? info.base : symbol;
        if (this._currencySourceLabel) Language.set(this._currencySourceLabel, 'text', info.crypto ? 'Powered by CoinPaprika' : '');
        Language.set(this._currencyDirectionButton, 'label', Language.msg('panels.currency.reverse', {from, to}));
        Language.set(this._currencyDirectionButton, 'accessible_name', Language.msg('panels.currency.reverse_accessible', {from, to}));
    },

    _toggleCurrencyDirection() {
        const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
        const info = this._currencyCommandInfo(command);
        if (!info)
            return;
        const args = info.argv.filter(arg => arg !== '--reverse');
        if (!info.reverse)
            args.push('--reverse');
        const updatedCommand = args.map(arg => GLib.shell_quote(arg)).join(' ');
        Me.settings.set_value('changed-data', new GLib.Variant('a{ss}', {
            WidgetIndex: String(this.widgetIndex),
            ElementIndex: String(this.elementIndex),
            ElementType: 'Text_Command',
        }));
        Utils.setData(getWidgetData(), this.widgetIndex, this.elementIndex, 'Text_Command', updatedCommand);
        this._updateCurrencyDirectionButton(updatedCommand);
        this._refreshCurrencyDialog(updatedCommand);
    },

    async _refreshCurrencyDialog(commandOverride = null) {
        if (this._networkDestroyed || !this._networkDialog?.visible)
            return;
        if (this._networkRefreshRun) {
            this._currencyQuote = null;
            this._updateCurrencyCalculation();
            this._networkRefreshPending = true;
            this._currencyPendingCommand = commandOverride || getData(this.widgetIndex, this.elementIndex, 'Text_Command');
            return;
        }
        this._currencyQuote = null;
        this._updateCurrencyCalculation();
        const command = commandOverride || getData(this.widgetIndex, this.elementIndex, 'Text_Command');
        const info = this._currencyCommandInfo(command);
        if (!info) {
            Language.set(this._networkRefreshStatus, 'text', Language.msg('panels.currency.config_error'));
            return;
        }
        const widgetIndex = this.widgetIndex, elementIndex = this.elementIndex;
        const currentCommand = () => {
            try {
                return this.widgetIndex === widgetIndex && this.elementIndex === elementIndex &&
                    getData(widgetIndex, elementIndex, 'Text_Command') === command;
            } catch (error) { return false; }
        };
        const discardStale = () => {
            if (currentCommand()) return false;
            if (!this._networkRefreshPending) {
                Language.set(this._currencyRateLabel, 'text', Language.msg('panels.currency.config_changed'));
                Language.set(this._networkRefreshStatus, 'text', Language.msg('panels.currency.config_prompt'));
            }
            return true;
        };
        const run = {generation: this._networkGeneration, cancellable: new Gio.Cancellable(), proc: null};
        this._networkRefreshRun = run;
        this._networkRefreshButton.reactive = false;
        Language.set(this._networkRefreshButton, 'label', Language.msg('panels.currency.query_button'));
        Language.set(this._networkRefreshButton, 'accessible_name', Language.msg('panels.currency.query_accessible'));
        Language.set(this._networkRefreshStatus, 'text', '');
        Language.set(this._currencyRateLabel, 'text', Language.msg('panels.currency.query'));
        let proc, timedOut = false;
        try {
            proc = Language.spawn(['/usr/bin/setsid', ...info.argv, ...(!info.argv.includes('--quote-json') ? ['--quote-json'] : [])],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
            run.proc = proc;
            this._networkRefreshProcess = proc;
            this._networkRefreshTimeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 30000, () => {
                this._networkRefreshTimeout = null;
                timedOut = true;
                stopCommandRun(run);
                return GLib.SOURCE_REMOVE;
            });
            const [stdout, stderr] = await readCommandOutput(run);
            if (this._networkDestroyed || run.cancelled || run.generation !== this._networkGeneration)
                return;
            if (discardStale()) return;
            if (!proc.get_successful() || stderr)
                throw Language.error(stderr.trim() || Language.msg('panels.currency.refresh_error'));
            if (this._networkRefreshPending) return;
            const item = JSON.parse(stdout.trim());
            if (typeof item.error === 'string') throw new Error(item.error);
            if (typeof item.rate !== 'string' || !/^(?:[0-9]+(?:\.[0-9]+)?)(?:[eE][+-]?[0-9]+)?$/.test(item.rate) ||
                !Number.isFinite(Number(item.rate)) || Number(item.rate) <= 0 ||
                !/^[A-Z0-9]{1,20}$/.test(item.base) || !/^[A-Z0-9]{1,20}$/.test(item.quote) ||
                (info.crypto ? item.asset !== info.quote || !Number.isFinite(Date.parse(item.updated_at)) :
                    item.base !== (info.reverse ? info.quote : info.base) || item.quote !== (info.reverse ? info.base : info.quote)))
                throw Language.error(Language.msg('panels.error.currency'));
            const response = `1 ${item.base} → ${this._currencyProduct('1', item.rate)} ${item.quote}`;
            this._currencyQuote = item;
            this._updateCurrencyDirectionButton(command);
            this._updateCurrencyCalculation();
            if (info.crypto && this._currencySourceLabel)
                Language.set(this._currencySourceLabel, 'text', `Powered by CoinPaprika · ${item.updated_at}`);
            Language.set(this._currencyRateLabel, 'text', response);
            Language.set(this, 'text', response);
            this.clutter_text.set_markup(GLib.markup_escape_text(response, -1));
            Language.set(this._networkRefreshStatus, 'text', Language.msg('panels.currency.updated', {time: GLib.DateTime.new_now_local().format('%H:%M')}));
        } catch (error) {
            if (!this._networkDestroyed && (!run.cancelled || timedOut) && run.generation === this._networkGeneration) {
                if (discardStale()) return;
                Language.set(this._networkRefreshStatus, 'text', timedOut ? Language.msg('panels.currency.timeout') :
                    error.orbitzMessage || error.message || Language.msg('panels.currency.refresh_error'));
                {
                    this._currencyQuote = null;
                    this._updateCurrencyCalculation();
                    Language.set(this, 'text', Language.join(Language.msg('panels.currency.unavailable_prefix'), this._networkRefreshStatus.text));
                    Language.set(this._currencyRateLabel, 'text', Language.join(Language.msg('panels.currency.unavailable_prefix'), timedOut ? Language.msg('panels.currency.timeout') : error.orbitzMessage || error.message || Language.msg('panels.currency.refresh_error')));
                    this.clutter_text.set_markup(GLib.markup_escape_text(this.text, -1));
                    if (this._currencySourceLabel) Language.set(this._currencySourceLabel, 'text', info.crypto ? 'Powered by CoinPaprika' : '');
                }
            }
        } finally {
            if (this._networkRefreshTimeout) {
                GLib.source_remove(this._networkRefreshTimeout);
                this._networkRefreshTimeout = null;
            }
            this._networkRefreshProcess = null;
            this._networkRefreshRun = null;
            const pending = this._networkRefreshPending;
            this._networkRefreshPending = false;
            const pendingCommand = this._currencyPendingCommand;
            this._currencyPendingCommand = null;
            if (!this._networkDestroyed) {
                this._networkRefreshButton.reactive = true;
                Language.set(this._networkRefreshButton, 'label', Language.msg('panels.currency.refresh'));
                Language.set(this._networkRefreshButton, 'accessible_name', Language.msg('panels.currency.refresh_accessible'));
                if (pending && this._networkDialog?.visible)
                    this._refreshCurrencyDialog(pendingCommand);
            }
        }
    },
});

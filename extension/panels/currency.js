// Fiat currency converter modal; selected pair and direction live in Text_Command.
var create = ({Clutter, Gio, GLib, Main, Me, Pango, St, Utils, global, getData, getWidgetData, readCommandOutput, stopCommandRun}) => ({
    _buildCurrencyDialog() {
        this._networkBackdrop = new St.Widget({reactive: true, visible: false});
        this._networkBackdrop.add_constraint(new Clutter.BindConstraint({source: global.stage, coordinate: Clutter.BindCoordinate.ALL}));
        this._networkBackdrop.connect('button-press-event', (_actor, event) => {
            if (this._networkDialog?.contains(event.get_source()))
                return Clutter.EVENT_PROPAGATE;
            this._closeNetworkDialog();
            return Clutter.EVENT_STOP;
        });
        Main.uiGroup.add_child(this._networkBackdrop);

        this._networkDialog = new St.BoxLayout({vertical: true, reactive: true,
            style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 8px; padding: 16px; spacing: 12px; width: 390px;'});
        const header = new St.BoxLayout({style: 'spacing: 12px;'});
        header.add_child(new St.Label({text: 'Cotação de moedas', style: 'font-weight: bold; font-size: 18px;', x_expand: true}));
        const closeButton = new St.Button({reactive: true, can_focus: true, accessible_name: 'Fechar cotação',
            style: 'background-color: transparent; color: white; padding: 4px;'});
        closeButton.set_child(new St.Icon({icon_name: 'window-close-symbolic', icon_size: 16}));
        closeButton.connect('clicked', () => this._closeNetworkDialog());
        header.add_child(closeButton);
        this._networkDialog.add_child(header);

        this._currencyRateLabel = new St.Label({text: this.text || 'Carregando cotação…',
            style: 'font-size: 24px; font-weight: bold; padding: 12px 4px;', x_align: Clutter.ActorAlign.CENTER});
        this._currencyRateLabel.clutter_text.set_line_wrap(true);
        this._currencyRateLabel.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
        this._networkDialog.add_child(this._currencyRateLabel);

        const controls = new St.BoxLayout({style: 'spacing: 8px;'});
        this._currencyDirectionButton = new St.Button({reactive: true, can_focus: true,
            style: 'background-color: #343434; color: white; padding: 8px 12px;', x_expand: true});
        this._currencyDirectionButton.connect('clicked', () => this._toggleCurrencyDirection());
        controls.add_child(this._currencyDirectionButton);
        this._networkRefreshButton = new St.Button({reactive: true, can_focus: true,
            label: 'Atualizar agora', accessible_name: 'Atualizar cotação agora',
            style: 'background-color: #315d80; color: white; padding: 8px 12px;'});
        this._networkRefreshButton.connect('clicked', () => this._refreshCurrencyDialog());
        controls.add_child(this._networkRefreshButton);
        this._networkDialog.add_child(controls);
        this._networkRefreshStatus = new St.Label({text: '', style: 'font-size: 12px; color: #c8c8c8;'});
        this._networkDialog.add_child(this._networkRefreshStatus);
        this._networkBackdrop.add_child(this._networkDialog);
        this._updateCurrencyDirectionButton(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
    },

    _currencyCommandInfo(command) {
        try {
            const [ok, argv] = GLib.shell_parse_argv(command);
            if (!ok || !argv.some(arg => arg.endsWith('/currency-widget.py')))
                return null;
            const quoteIndex = argv.indexOf('--quote');
            const quote = quoteIndex >= 0 ? argv[quoteIndex + 1] : 'USD';
            return {argv, quote, reverse: argv.includes('--reverse')};
        } catch (error) { return null; }
    },

    _updateCurrencyDirectionButton(command) {
        const info = this._currencyCommandInfo(command);
        if (!info || !this._currencyDirectionButton)
            return;
        const from = info.reverse ? info.quote : 'BRL';
        const to = info.reverse ? 'BRL' : info.quote;
        this._currencyDirectionButton.label = `Inverter: ${from} → ${to}`;
        this._currencyDirectionButton.accessible_name = `Inverter conversão atual ${from} para ${to}`;
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
            this._networkRefreshPending = true;
            this._currencyPendingCommand = commandOverride || getData(this.widgetIndex, this.elementIndex, 'Text_Command');
            return;
        }
        const command = commandOverride || getData(this.widgetIndex, this.elementIndex, 'Text_Command');
        const info = this._currencyCommandInfo(command);
        if (!info) {
            this._networkRefreshStatus.text = 'Não foi possível ler a configuração da cotação.';
            return;
        }
        const run = {generation: this._networkGeneration, cancellable: new Gio.Cancellable(), proc: null};
        this._networkRefreshRun = run;
        this._networkRefreshButton.reactive = false;
        this._networkRefreshButton.label = 'Consultando…';
        this._networkRefreshButton.accessible_name = 'Consultando cotação';
        this._networkRefreshStatus.text = '';
        this._currencyRateLabel.text = 'Consultando cotação…';
        let proc, timedOut = false;
        try {
            proc = Gio.Subprocess.new(['/usr/bin/setsid', ...info.argv],
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
            if (!proc.get_successful() || stderr)
                throw new Error(stderr.trim() || 'Não foi possível atualizar a cotação.');
            const response = stdout.trim();
            if (!response)
                throw new Error('A consulta não retornou uma cotação.');
            this._currencyRateLabel.text = response;
            this.text = response;
            this.clutter_text.set_markup(GLib.markup_escape_text(response, -1));
            this._networkRefreshStatus.text = response.startsWith('Cotação indisponível ·')
                ? 'A consulta falhou. Tente novamente.'
                : `Atualizado às ${GLib.DateTime.new_now_local().format('%H:%M')}`;
        } catch (error) {
            if (!this._networkDestroyed && (!run.cancelled || timedOut) && run.generation === this._networkGeneration)
                this._networkRefreshStatus.text = timedOut ? 'A consulta demorou demais. Tente novamente.' :
                    error.message || 'Não foi possível atualizar a cotação.';
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
                this._networkRefreshButton.label = 'Atualizar agora';
                this._networkRefreshButton.accessible_name = 'Atualizar cotação agora';
                if (pending && this._networkDialog?.visible)
                    this._refreshCurrencyDialog(pendingCommand);
            }
        }
    },
});

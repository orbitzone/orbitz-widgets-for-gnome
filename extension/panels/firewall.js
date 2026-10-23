// Firewall panel methods; state and lifecycle belong to CommandLabel.
var create = ({Language, Clutter, Gio, GLib, Main, Pango, St, getData, readCommandOutput, stopCommandRun, global}) => ({
    _buildFirewallDialog() {
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
            style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 8px; padding: 12px; spacing: 10px;'});
        this._firewallHeading = Language.widget(St.Label, {text: Language.msg('panels.firewall.title'), style: 'font-weight: bold; font-size: 18px;'});
        this._networkDialog.add_child(this._firewallHeading);
        const note = Language.widget(St.Label, {text: Language.msg('panels.firewall.note'), style: 'font-size: 12px; color: #c8c8c8;'});
        note.clutter_text.set_line_wrap(true);
        this._networkDialog.add_child(note);
        const scroll = Language.widget(St.ScrollView, {style: 'width: 720px; height: 300px;', reactive: true});
        scroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this._firewallRows = Language.widget(St.BoxLayout, {vertical: true, style: 'spacing: 8px;'});
        scroll.add_actor(this._firewallRows);
        this._networkDialog.add_child(scroll);
        const footer = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
        this._networkRefreshButton = Language.widget(St.Button, {reactive: true, can_focus: true, accessible_name: Language.msg('panels.firewall.refresh'), style: 'background-color: transparent; color: white; padding: 6px;'});
        this._networkRefreshButton.set_child(Language.widget(St.Icon, {icon_name: 'view-refresh-symbolic', icon_size: 18, style: 'color: white;'}));
        this._networkRefreshButton.connect('clicked', () => this._refreshNetworkDialog());
        footer.add_child(this._networkRefreshButton);
        this._networkRefreshStatus = Language.widget(St.Label, {text: '', style: 'font-size: 12px; color: #c8c8c8;'});
        footer.add_child(this._networkRefreshStatus);
        this._networkDialog.add_child(footer);
        this._networkBackdrop.add_child(this._networkDialog);
    },

    _renderFirewall(data) {
        this._cancelFirewallInspection();
        if (typeof data.text !== 'string' || data.text.length > 128 || typeof data.scope !== 'string' || data.scope.length > 4096 || typeof data.updated !== 'string' || !Array.isArray(data.groups) || data.groups.length > 50)
            throw Language.error(Language.msg('panels.error.firewall'));
        for (const row of data.groups) {
            if (!row || !['source', 'destination', 'protocol', 'ports', 'last', 'kind', 'interface'].every(key => typeof row[key] === 'string' && row[key].length <= 512) || !Number.isInteger(row.count) || row.count < 1 || (data.pattern_mode && (typeof row.reason !== 'string' || row.reason.length > 4096)))
                throw Language.error(Language.msg('panels.error.firewall_event'));
        }
        this._firewallData = data;
        Language.set(this._firewallHeading, 'text', data.text + ' · Firewall');
        this._firewallRows.destroy_all_children();
        const scope = Language.widget(St.Label, {text: data.scope, style: 'font-size: 11px; color: #c8c8c8;'});
        scope.clutter_text.set_line_wrap(true);
        scope.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
        this._firewallRows.add_child(scope);
        if (!data.groups.length)
            this._firewallRows.add_child(Language.widget(St.Label, {text: Language.msg('panels.firewall.empty'), style: 'color: #8bd5a1; padding: 8px;'}));
        for (const item of data.groups) {
            const box = Language.widget(St.BoxLayout, {vertical: true, style: 'padding: 8px; spacing: 4px; border-bottom: 1px solid #444;'});
            const escape = value => GLib.markup_escape_text(String(value), -1);
            if (data.pattern_mode && typeof item.reason === 'string') {
                const evidence = Language.widget(St.Label, {text: item.reason, style: 'font-size: 12px; color: #ffd479;'});
                evidence.clutter_text.set_line_wrap(true);
                evidence.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
                box.add_child(evidence);
            }
            const sourceColor = item.source_remote === true || item.kind === 'Origem externa' ? '#ff9e64' : '#82cfff';
            const title = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
            const source = Language.widget(St.Button, {label: item.source, reactive: true, can_focus: true, style: `color: ${sourceColor}; padding: 0px; font-family: monospace;`});
            source.connect('clicked', () => this._inspectFirewall('ip', item.source));
            title.add_child(source);
            title.add_child(Language.widget(St.Label, {text: '→'}));
            const destination = Language.widget(St.Button, {label: item.destination, reactive: true, can_focus: true, style: 'color: #82cfff; padding: 0px; font-family: monospace;'});
            destination.connect('clicked', () => this._inspectFirewall('ip', item.destination));
            title.add_child(destination);
            title.add_child(Language.widget(St.Label, {text: Language.msg('panels.firewall.count', {count: item.count})}));
            box.add_child(title);
            box.add_child(Language.widget(St.Label, {text: Language.msg('panels.firewall.kind', {kind: item.kind, local: item.local ? Language.msg('panels.firewall.local') : '', protocol: item.protocol, interface: item.interface || '—'}), style: 'color: #c8c8c8; font-size: 12px;'}));
            let ports = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
            ports.add_child(Language.widget(St.Label, {text: Language.msg('panels.firewall.ports'), style: 'font-size: 12px;'}));
            const portValues = item.ports.split(', ').slice(0, 30);
            for (let i = 0; i < portValues.length; i++) {
                const value = portValues[i];
                if (i > 0 && i % 8 === 0) {
                    box.add_child(ports);
                    ports = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
                }
                if (/^\d+$/.test(value) && Number(value) > 0 && Number(value) <= 65535) {
                    const port = Language.widget(St.Button, {label: value, reactive: true, can_focus: true, style: 'color: #ffd479; padding: 0px;'});
                    port.connect('clicked', () => this._inspectFirewall('port', value));
                    ports.add_child(port);
                } else {
                    ports.add_child(Language.widget(St.Label, {text: value, style: 'color: #ffd479;'}));
                }
            }
            box.add_child(ports);
            box.add_child(Language.widget(St.Label, {text: Language.msg('panels.firewall.times', {first: item.first || item.last, last: item.last}), style: 'color: #aaa; font-size: 11px;'}));
            this._firewallRows.add_child(box);
        }
    },

    _cancelFirewallInspection() {
        const run = this._firewallInspection;
        if (!run)
            return;
        if (run.timeout) {
            GLib.source_remove(run.timeout);
            run.timeout = null;
        }
        stopCommandRun(run);
        this._firewallInspection = null;
    },

    async _inspectFirewall(kind, target) {
        if (this._networkDestroyed || !this._networkDialog?.visible)
            return;
        this._cancelFirewallInspection();
        const run = {proc: null, cancellable: new Gio.Cancellable(), generation: this._networkGeneration, timeout: null};
        this._firewallInspection = run;
        const connections = Boolean(this._networkConnectionsBox);
        const rows = connections ? this._networkConnectionsBox : this._firewallRows;
        if (connections) this._networkInspecting = true;
        rows.destroy_all_children();
        const toolbar = Language.widget(St.BoxLayout, {style: 'spacing: 12px;'});
        const button = (text, action) => {
            const actor = Language.widget(St.Button, {label: text, reactive: true, can_focus: true, style: 'color: #82cfff; padding: 6px;'});
            actor.connect('clicked', action);
            toolbar.add_child(actor);
        };
        button(Language.msg('panels.firewall.back'), () => {
            if (connections) {
                this._cancelFirewallInspection();
                this._networkInspecting = false;
                this._networkConnectionSignature = null;
                this._updateNetworkTooltip();
            } else {
                this._renderFirewall(this._firewallData);
            }
        });
        button(Language.msg('panels.firewall.copy'), () => St.Clipboard.get_default().set_text(St.ClipboardType.CLIPBOARD, target));
        rows.add_child(toolbar);
        const label = Language.widget(St.Label, {text: Language.msg('panels.firewall.loading'), style: `width: ${connections ? 480 : 680}px; font-family: monospace; font-size: 12px; padding: 8px;`});
        label.clutter_text.set_line_wrap(true);
        label.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
        rows.add_child(label);
        try {
            const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
            let [, argv] = GLib.shell_parse_argv(command);
            if (connections) {
                const script = argv.find(arg => arg.endsWith('/seguranca-widget.py'));
                if (!script) throw Language.error(Language.msg('panels.error.connections_command'));
                argv = ['/usr/bin/python3', GLib.build_filenamev([GLib.path_get_dirname(script), 'conexoes-inspect.py'])];
            }
            const prefix = connections ? 'AZCLOCK_CONNECTION_INSPECT:' : 'AZCLOCK_FIREWALL:';
            const flag = kind === 'dns' ? '--dns' : (kind === 'port' ? '--inspect-port' : '--inspect-ip');
            run.proc = Language.spawn(['/usr/bin/setsid', ...argv, flag, target], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
            run.timeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 15000, () => {
                run.timeout = null;
                run.timedOut = true;
                stopCommandRun(run);
                return GLib.SOURCE_REMOVE;
            });
            const [stdout, stderr] = await readCommandOutput(run);
            if (this._firewallInspection !== run || run.cancelled || this._networkDestroyed || run.generation !== this._networkGeneration)
                return;
            if (!run.proc.get_successful() || !stdout.startsWith(prefix))
                throw Language.error(stderr.trim().slice(0, 300) || Language.msg('panels.error.inspect'));
            const data = JSON.parse(stdout.slice(prefix.length));
            if (typeof data.inspect !== 'string')
                throw Language.error(Language.msg('panels.error.response'));
            const escaped = GLib.markup_escape_text(data.inspect, -1);
            const selected = GLib.markup_escape_text(target, -1);
            const color = kind === 'port' ? '#ffd479' : (data.remote === true ? '#ff9e64' : '#82cfff');
            Language.set(label, 'text', '');
            label.clutter_text.set_markup(escaped.split(selected).join(`<span foreground="${color}">${selected}</span>`));
            if (kind === 'ip') {
                const notice = Language.widget(St.Label, {text: Language.msg('panels.firewall.privacy'), style: 'font-size: 12px; color: #ffd479;'});
                notice.clutter_text.set_line_wrap(true);
                rows.add_child(notice);
                button(Language.msg('panels.firewall.dns'), () => this._inspectFirewall('dns', target));
                if (data.remote === true)
                    button(Language.msg('panels.firewall.rdap'), () => {
                        try {
                            Gio.AppInfo.launch_default_for_uri(`https://rdap.org/ip/${encodeURIComponent(target).replace(/%3A/gi, ':')}`, null);
                        } catch (error) {
                            Language.set(label, 'text', Language.msg('panels.firewall.external_error'));
                        }
                    });
            }
        } catch (error) {
            if (this._firewallInspection === run && !this._networkDestroyed && run.generation === this._networkGeneration)
                Language.set(label, 'text', run.timedOut ? Language.msg('panels.firewall.timeout') : error.orbitzMessage || error.message);
        } finally {
            if (run.timeout)
                GLib.source_remove(run.timeout);
            if (this._firewallInspection === run)
                this._firewallInspection = null;
        }
    }
});

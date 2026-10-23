// Docker panel methods; state and lifecycle belong to CommandLabel.
var create = ({Language, Clutter, Gio, GLib, Main, St, global}) => ({
    _buildDockerDialog() {
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
        this._dockerHeading = Language.widget(St.Label, {text: Language.msg('panels.docker.title'), style: 'font-weight: bold; font-size: 18px;'});
        this._networkDialog.add_child(this._dockerHeading);
        const note = Language.widget(St.Label, {text: Language.msg('panels.docker.note'), style: 'font-size: 12px; color: #c8c8c8;'});
        note.clutter_text.set_line_wrap(true);
        this._networkDialog.add_child(note);
        const scroll = Language.widget(St.ScrollView, {style: 'width: 720px; height: 300px;', reactive: true});
        scroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this._dockerRows = Language.widget(St.BoxLayout, {vertical: true, style: 'spacing: 8px;'});
        scroll.add_actor(this._dockerRows);
        this._networkDialog.add_child(scroll);
        const footer = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
        this._networkRefreshButton = Language.widget(St.Button, {reactive: true, can_focus: true, accessible_name: Language.msg('panels.docker.refresh'), style: 'background-color: transparent; color: white; padding: 6px;'});
        this._networkRefreshButton.set_child(Language.widget(St.Icon, {icon_name: 'view-refresh-symbolic', icon_size: 18, style: 'color: white;'}));
        this._networkRefreshButton.connect('clicked', () => this._refreshNetworkDialog());
        footer.add_child(this._networkRefreshButton);
        this._networkRefreshStatus = Language.widget(St.Label, {text: '', style: 'font-size: 12px; color: #c8c8c8;'});
        footer.add_child(this._networkRefreshStatus);
        this._networkDialog.add_child(footer);
        this._networkBackdrop.add_child(this._networkDialog);
    },

    _validDockerUrl(url) {
        try {
            const uri = GLib.Uri.parse(url, GLib.UriFlags.NONE);
            return ['http', 'https'].includes(uri.get_scheme()) && !!uri.get_host() &&
                !uri.get_userinfo() && uri.get_port() >= 1 && uri.get_port() <= 65535 &&
                !uri.get_query() && !uri.get_fragment();
        } catch (error) { return false; }
    },

    _renderDocker(data) {
        if (typeof data.text !== 'string' || data.text.length > 128 || !Array.isArray(data.items) || data.items.length > 100 ||
            data.items.some(item => !item || !['name', 'ports', 'url'].every(key => typeof item[key] === 'string') ||
                item.name.length > 128 || item.ports.length > 256 || item.url.length > 512 ||
                (item.url && !this._validDockerUrl(item.url))))
            throw Language.error(Language.msg('panels.error.docker'));
        Language.set(this._dockerHeading, 'text', Language.msg('panels.docker.heading', {summary: data.text}));
        this._dockerRows.destroy_all_children();
        if (!data.items.length)
            this._dockerRows.add_child(Language.widget(St.Label, {text: data.error || Language.msg('panels.docker.empty'), style: 'padding: 8px;'}));
        if (Number.isInteger(data.skipped_containers) && data.skipped_containers > 0)
            this._dockerRows.add_child(Language.widget(St.Label, {text: Language.msg('panels.docker.skipped', {count: data.skipped_containers})}));
        if (Number.isInteger(data.omitted) && data.omitted > 0)
            this._dockerRows.add_child(Language.widget(St.Label, {text: Language.msg('panels.docker.omitted', {count: data.omitted})}));
        for (const item of data.items) {
            const row = Language.widget(St.BoxLayout, {style: 'spacing: 12px; padding: 8px;'});
            const service = Language.widget(St.Button, {label: item.name, reactive: !!item.url, can_focus: !!item.url,
                style: 'color: #82cfff;', accessible_name: item.url ? Language.msg('panels.docker.open', {name: item.name, url: item.url}) : item.name});
            service.connect('clicked', () => {
                try { Gio.AppInfo.launch_default_for_uri(item.url, null); }
                catch (error) { Language.set(this._networkRefreshStatus, 'text', Language.msg('panels.browser_error')); }
            });
            row.add_child(service);
            row.add_child(Language.widget(St.Label, {text: item.ports, style: 'color: #ffd479;'}));
            this._dockerRows.add_child(row);
        }
    }
});

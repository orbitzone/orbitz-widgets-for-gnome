// Common panel methods; state and lifecycle belong to CommandLabel.
var create = ({Language, Clutter, Main, Pango, St, global}) => ({
    _buildUpdatesDialog(compact = false) {
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
        this._updatesHeading = Language.widget(St.Label, {text: Language.msg('panels.common.title'), style: 'font-weight: bold; font-size: 18px;'});
        this._networkDialog.add_child(this._updatesHeading);
        const note = Language.widget(St.Label, {text: Language.msg('panels.common.note'), style: 'font-size: 12px; color: #c8c8c8;'});
        note.clutter_text.set_line_wrap(true);
        this._updatesNote = note;
        this._networkDialog.add_child(note);
        this._updatesRows = Language.widget(St.BoxLayout, {vertical: true, style: 'spacing: 10px; width: 720px;'});
        if (compact) {
            this._networkDialog.add_child(this._updatesRows);
        } else {
            const scroll = Language.widget(St.ScrollView, {style: 'width: 720px; height: 300px;', reactive: true});
            this._updatesScroll = scroll;
            scroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
            scroll.add_actor(this._updatesRows);
            this._networkDialog.add_child(scroll);
        }
        this._updatesActions = Language.widget(St.BoxLayout, {vertical: true, style: 'spacing: 8px;'});
        this._networkDialog.add_child(this._updatesActions);
        const footer = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
        this._networkRefreshButton = Language.widget(St.Button, {reactive: true, can_focus: true, label: Language.msg('panels.common.reread'), accessible_name: Language.msg('panels.common.reread_accessible'), style: 'background-color: transparent; color: white; padding: 6px;'});
        this._networkRefreshButton.connect('clicked', () => this._refreshNetworkDialog());
        footer.add_child(this._networkRefreshButton);
        this._networkRefreshStatus = Language.widget(St.Label, {text: '', style: 'font-size: 12px; color: #c8c8c8;'});
        footer.add_child(this._networkRefreshStatus);
        this._networkDialog.add_child(footer);
        this._networkBackdrop.add_child(this._networkDialog);
    },

    _attachActionTooltip(button, command) {
        const tooltip = Language.widget(St.Label, {text: command, visible: false, reactive: false,
            style: 'max-width: 620px; padding: 10px 12px; border-radius: 6px; background-color: #101820; color: #e5f3ff; border: 1px solid #6088a8; font-family: monospace; font-size: 12px;'});
        tooltip.clutter_text.set_line_wrap(true);
        tooltip.clutter_text.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);
        tooltip.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
        Main.uiGroup.add_child(tooltip);
        const hide = () => tooltip.hide();
        const show = () => {
            if (!this._networkDialog.visible) return;
            tooltip.show();
            const [x, y] = button.get_transformed_position();
            const [width, height] = tooltip.get_preferred_size().slice(2);
            const monitor = Main.layoutManager.findMonitorForActor(button) || Main.layoutManager.primaryMonitor;
            tooltip.set_position(Math.max(monitor.x + 8, Math.min(x, monitor.x + monitor.width - width - 8)),
                y - height - 8 >= monitor.y ? y - height - 8 : y + button.height + 8);
        };
        button.track_hover = true;
        button.connect('notify::hover', () => button.hover ? show() : hide());
        button.connect('key-focus-in', show);
        button.connect('key-focus-out', hide);
        if (button instanceof St.Button)
            button.connect('clicked', hide);
        const dialog = this._networkDialog;
        const visibilitySignal = dialog.connect('notify::visible', hide);
        button.connect('destroy', () => {
            dialog.disconnect(visibilitySignal);
            tooltip.destroy();
        });
        return show;
    }
});

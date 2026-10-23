// Network panel methods; state and lifecycle belong to CommandLabel.
var create = ({Language, Pango, St}) => ({
    _buildTrafficDialog() {
        this._buildUpdatesDialog(true);
        this._trafficDialog = true;
        Language.set(this._updatesHeading, 'text', Language.msg('panels.network.title'));
        Language.set(this._updatesNote, 'text', Language.msg('panels.network.note'));
        this._networkRefreshButton.set_child(Language.widget(St.Label, {text: Language.msg('panels.network.quality')}));
        Language.set(this._networkRefreshButton, 'accessible_name', Language.msg('panels.network.quality_accessible'));
        this._attachActionTooltip(this._networkRefreshButton, Language.msg('panels.network.quality_help'));
            const speedColumn = Language.widget(St.BoxLayout, {
                vertical: true,
                style: 'spacing: 10px; padding: 10px; background-color: #292929; border-radius: 6px;',
            });
            speedColumn.add_child(Language.widget(St.Label, {text: Language.msg('panels.network.speed_title'), style: 'font-weight: bold; color: #ededed;'}));
            this._speedtestButton = Language.widget(St.Button, {
                label: Language.msg('panels.network.speed'), reactive: true, can_focus: true,
                style: 'background-color: #315d85; color: white; border-radius: 6px; padding: 10px;',
            });
            this._speedtestButton.connect('clicked', () => this._startSpeedtest());
            speedColumn.add_child(this._speedtestButton);
            this._speedtestResult = Language.widget(St.Label, {text: '', visible: false, style: 'font-size: 15px;'});
            speedColumn.add_child(this._speedtestResult);
            this._speedtestStatus = Language.widget(St.Label, {text: '', visible: false, style: 'font-size: 12px; color: #c8c8c8;'});
            this._speedtestStatus.clutter_text.set_line_wrap(true);
            this._speedtestStatus.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
            speedColumn.add_child(this._speedtestStatus);
        this._networkDialog.add_child(speedColumn);
        this._attachActionTooltip(this._speedtestButton, Language.msg('panels.network.speed_help'));
    },

    _renderQuality(data) {
        if (!data || !Array.isArray(data.items) || data.items.length !== 2 || data.items.some(item =>
            !item || ['name', 'target', 'error'].some(key => typeof item[key] !== 'string' || item[key].length > 256) ||
            ['loss', 'latency', 'jitter'].some(key => item[key] !== null && (!Number.isFinite(item[key]) || item[key] < 0)) ||
            (item.loss !== null && item.loss > 100))) throw Language.error(Language.msg('panels.error.quality'));
        this._updatesRows.destroy_all_children();
        const columns = Language.widget(St.BoxLayout, {style: 'spacing: 12px;'});
        for (const [index, item] of data.items.entries()) {
            const bad = item.loss !== null && item.loss >= 20;
            const attention = item.loss > 0 || item.latency > (index === 0 ? 20 : 100);
            const color = item.error ? '#aaaaaa' : bad ? '#ff6b6b' : attention ? '#ffd479' : '#9fdf9f';
            const card = Language.widget(St.Button, {reactive: true, can_focus: true, style: 'padding: 12px; width: 326px; background-color: #292929; border-radius: 6px;'});
            const content = Language.widget(St.BoxLayout, {vertical: true, style: 'spacing: 8px;'});
            content.add_child(Language.widget(St.Label, {text: item.name, style: `font-weight: bold; color: ${color};`}));
            content.add_child(Language.widget(St.Label, {text: item.error ? Language.msg('panels.unavailable') : item.latency === null ? Language.msg('panels.network.no_icmp') : `${item.latency.toFixed(1)} ms`, style: `font-size: 22px; color: ${color};`}));
            content.add_child(Language.widget(St.Label, {text: item.loss === null ? Language.msg('panels.network.loss_na') : Language.msg('panels.network.loss', {loss: item.loss.toFixed(0)})}));
            card.set_child(content);
            this._attachActionTooltip(card, Language.msg('panels.network.detail', {target: item.target || Language.msg('panels.network.gateway_unknown'), error: item.error || Language.msg('panels.network.sample'), jitter: item.jitter === null ? Language.msg('panels.na') : item.jitter.toFixed(1) + ' ms'}));
            columns.add_child(card);
        }
        this._updatesRows.add_child(columns);
    }
});

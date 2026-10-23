// Resources panel methods; state and lifecycle belong to CommandLabel.
var create = ({Language, Clutter, Gio, GLib, Pango, St, getData, launchTerminalAction}) => ({
    _renderPressure(data) {
        const averagesValid = values => Array.isArray(values) && values.length === 3 &&
            values.every(value => Number.isFinite(value) && value >= 0 && value <= 100);
        if (!data || typeof data.text !== 'string' || data.text.length > 160 ||
            !Array.isArray(data.items) || data.items.length !== 3 ||
            data.items.some((item, index) => !item || item.resource !== ['cpu', 'memory', 'io'][index] ||
                typeof item.name !== 'string' || item.name.length > 40 ||
                typeof item.suggestion !== 'string' || item.suggestion.length > 256 ||
                !['normal', 'attention', 'high', 'unavailable'].includes(item.level) ||
                (item.level === 'unavailable') !== (item.averages === null) ||
                (item.averages !== null && !averagesValid(item.averages)) ||
                (item.full !== null && !averagesValid(item.full))))
            throw Language.error(Language.msg('panels.error.pressure'));
        const columns = Language.widget(St.BoxLayout, {style: 'spacing: 12px;'});
        for (const item of data.items) {
            const color = {normal: '#9fdf9f', attention: '#ffd479', high: '#ff6b6b', unavailable: '#aaaaaa'}[item.level];
            const column = Language.widget(St.BoxLayout, {vertical: true,
                style: 'width: 220px; padding: 8px; spacing: 8px; background-color: #292929; border-radius: 6px;'});
            column.add_child(Language.widget(St.Label, {text: item.name, style: `font-weight: bold; color: ${color};`}));
            const text = item.averages === null ? Language.msg('panels.unavailable') :
                item.averages.map((value, index) => `${[10, 60, 300][index]} s: ${value.toFixed(1)}%`).join('\n');
            column.add_child(Language.widget(St.Label, {text, style: `color: ${color};`}));
            if (item.full !== null)
                column.add_child(Language.widget(St.Label, {text: Language.msg('panels.resources.full', {value: item.full[0].toFixed(1)})}));
            const note = Language.widget(St.Label, {text: item.level === 'normal' ? Language.msg('panels.resources.normal') : item.suggestion});
            note.clutter_text.set_line_wrap(true);
            note.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
            column.add_child(note);
            columns.add_child(column);
        }
        this._updatesRows.add_child(columns);
    },

    _buildServicesDialog() {
        this._buildUpdatesDialog(true);
        Language.set(this._updatesHeading, 'text', Language.msg('panels.services.title'));
        Language.set(this._updatesNote, 'text', Language.msg('panels.services.note'));
        this._networkRefreshButton.set_child(Language.widget(St.Label, {text: Language.msg('panels.refresh')}));
    },

    _renderServices(data) {
        if (!data || typeof data.text !== 'string' || data.text.length > 160 ||
            !Array.isArray(data.groups) || data.groups.length !== 2 || data.groups.some((group, index) =>
                !group || group.scope !== ['system', 'user'][index] || !Number.isSafeInteger(group.count) || group.count < 0 ||
                typeof group.error !== 'string' || group.error.length > 256 || !Array.isArray(group.items) || group.items.length > 6 || group.items.length > group.count ||
                group.items.some(item => !item || ['name', 'description', 'result', 'status', 'changed'].some(key =>
                    typeof item[key] !== 'string' || item[key].length > 256))))
            throw Language.error(Language.msg('panels.error.services'));
        this._updatesRows.destroy_all_children();
        const columns = Language.widget(St.BoxLayout, {style: 'spacing: 12px;'});
        for (const group of data.groups) {
            const card = Language.widget(St.BoxLayout, {vertical: true, style: 'width: 338px; padding: 8px; spacing: 8px; background-color: #292929; border-radius: 6px;'});
            card.add_child(Language.widget(St.Label, {text: Language.msg('panels.services.count', {scope: group.scope === 'system' ? Language.msg('panels.services.system') : Language.msg('panels.services.session'), count: group.count}),
                style: `font-weight: bold; color: ${group.count ? '#ffd479' : group.error ? '#aaaaaa' : '#9fdf9f'};`}));
            if (group.error || !group.count) {
                const note = Language.widget(St.Label, {text: group.error || Language.msg('panels.services.empty'), style: 'color: #c8c8c8;'});
                note.clutter_text.set_line_wrap(true);
                card.add_child(note);
            }
            for (const item of group.items) {
                const button = Language.widget(St.Button, {reactive: true, can_focus: true, accessible_name: item.name + ': ' + item.description,
                    style: 'padding: 6px; color: #ffd479;'});
                const label = Language.widget(St.Label, {text: item.name});
                label.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
                button.set_child(label);
                this._attachActionTooltip(button, Language.msg('panels.services.detail', {description: item.description, name: item.name, result: item.result || Language.msg('panels.not_available'), status: item.status || Language.msg('panels.na'), changed: item.changed || Language.msg('panels.services.time_na')}));
                card.add_child(button);
            }
            if (group.count > group.items.length)
                card.add_child(Language.widget(St.Label, {text: Language.msg('panels.services.more', {count: group.count - group.items.length})}));
            columns.add_child(card);
        }
        this._updatesRows.add_child(columns);
    },

    _buildProcessesDialog() {
        this._buildUpdatesDialog(true);
        this._processesDialog = true;
        Language.set(this._updatesHeading, 'text', Language.msg('panels.processes.title'));
        Language.set(this._updatesNote, 'text', Language.msg('panels.processes.note'));
        this._updatesNote.reactive = true;
        this._attachActionTooltip(this._updatesNote, Language.msg('panels.processes.help'));
        this._networkRefreshButton.set_child(Language.widget(St.Label, {text: Language.msg('panels.refresh')}));
        Language.set(this._networkRefreshButton, 'accessible_name', Language.msg('panels.processes.refresh'));
    },

    _renderProcesses(data) {
        const validRows = rows => Array.isArray(rows) && rows.length <= 7 && rows.every(r => r &&
            Number.isInteger(r.pid) && r.pid > 0 && typeof r.name === 'string' && r.name.length <= 80 &&
            Number.isFinite(r.cpu) && r.cpu >= 0 && Number.isFinite(r.memory) && r.memory >= 0);
        if (!data || typeof data.summary !== 'string' || data.summary.length > 2048 ||
            !Array.isArray(data.notices) || data.notices.length > 20 || data.notices.some(n => typeof n !== 'string' || n.length > 2048) ||
            !validRows(data.cpu_rows) || !validRows(data.memory_rows) ||
            !Array.isArray(data.actions) || data.actions.length > 8 || data.actions.some(a => !a ||
                !['monitor', 'startup', 'balanced', 'performance'].includes(a.id) ||
                ['name', 'command', 'effect'].some(k => typeof a[k] !== 'string' || a[k].length > 2048)))
            throw Language.error(Language.msg('panels.error.processes'));
        this._updatesRows.destroy_all_children();
        this._updatesActions.destroy_all_children();
        this._renderPressure(data.pressure);
        const overview = Language.widget(St.BoxLayout, {style: 'spacing: 10px;'});
        const badge = (icon, text, tooltip, color) => {
            const button = Language.widget(St.Button, {reactive: true, can_focus: true,
                accessible_name: Language.join(text, ': ', tooltip),
                style: `padding: 7px 12px; background-color: #292929; border-radius: 6px; color: ${color};`});
            const content = Language.widget(St.BoxLayout, {style: 'spacing: 6px;'});
            content.add_child(Language.widget(St.Icon, {icon_name: icon, icon_size: 16}));
            content.add_child(Language.widget(St.Label, {text}));
            button.set_child(content);
            this._attachActionTooltip(button, tooltip);
            return button;
        };
        overview.add_child(badge('computer-symbolic', Language.msg('panels.processes.summary'), data.summary, '#82cfff'));
        overview.add_child(badge('dialog-information-symbolic', Language.msg('panels.processes.notices'), data.notices.join('\n\n'), '#c8c8c8'));
        this._updatesRows.add_child(overview);
        const rankings = Language.widget(St.BoxLayout, {style: 'spacing: 12px;'});
        for (const [title, rows, memory] of [[Language.msg('panels.processes.cpu'), data.cpu_rows, false], [Language.msg('panels.processes.ram'), data.memory_rows, true]]) {
            const card = Language.widget(St.BoxLayout, {vertical: true,
                style: 'width: 338px; padding: 8px; spacing: 6px; background-color: #292929; border-radius: 6px;'});
            card.add_child(Language.widget(St.Label, {text: title, style: 'font-weight: bold; color: #82cfff;'}));
            for (const process of rows.slice(0, 3)) {
                const line = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
                const name = Language.widget(St.Label, {text: process.name, x_expand: true, style: 'width: 225px;'});
                name.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
                line.add_child(name);
                line.add_child(Language.widget(St.Label, {text: memory ? `${process.memory} MiB` : `${process.cpu.toFixed(1)}%`,
                    style: 'color: #ededed;'}));
                const button = Language.widget(St.Button, {reactive: true, can_focus: true,
                    accessible_name: `${process.name}, PID ${process.pid}, CPU ${process.cpu.toFixed(1)}%, RAM ${process.memory} MiB`});
                button.set_child(line);
                this._attachActionTooltip(button, Language.msg('panels.processes.detail', {pid: process.pid, cpu: process.cpu.toFixed(1), memory: process.memory}));
                card.add_child(button);
            }
            if (!rows.length) card.add_child(Language.widget(St.Label, {text: Language.msg('panels.processes.empty'), style: 'color: #aaaaaa;'}));
            rankings.add_child(card);
        }
        this._updatesRows.add_child(rankings);
        let row;
        for (const [index, action] of data.actions.entries()) {
            if (index % 4 === 0) {
                row = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
                this._updatesActions.add_child(row);
            }
            const button = Language.widget(St.Button, {reactive: true, can_focus: true,
                accessible_name: action.name + ': ' + action.effect + ' ' + action.command,
                height: 38, y_align: Clutter.ActorAlign.CENTER,
                style: 'width: 156px; min-height: 22px; padding: 8px; border-radius: 6px; background-color: #315d80; color: white;'});
            const label = Language.widget(St.Label, {text: action.name, x_align: Clutter.ActorAlign.CENTER, y_align: Clutter.ActorAlign.CENTER});
            label.clutter_text.set_line_wrap(true);
            button.set_child(label);
            this._attachActionTooltip(button, action.effect + '\n\n' + action.command);
            button.connect('clicked', () => {
                try {
                    const [, argv] = GLib.shell_parse_argv(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
                    launchTerminalAction([...argv, '--action', action.id], this);
                    Language.set(this._networkRefreshStatus, 'text', Language.msg('panels.processes.opened'));
                } catch (error) {
                    Language.set(this._networkRefreshStatus, 'text', Language.msg('panels.processes.error'));
                }
            });
            row.add_child(button);
        }
    }
});

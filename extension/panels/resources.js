// Resources panel methods; state and lifecycle belong to CommandLabel.
var create = ({Clutter, Gio, GLib, Pango, St, getData}) => ({
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
            throw new Error('Resposta de pressão inválida.');
        const columns = new St.BoxLayout({style: 'spacing: 12px;'});
        for (const item of data.items) {
            const color = {normal: '#9fdf9f', attention: '#ffd479', high: '#ff6b6b', unavailable: '#aaaaaa'}[item.level];
            const column = new St.BoxLayout({vertical: true,
                style: 'width: 220px; padding: 8px; spacing: 8px; background-color: #292929; border-radius: 6px;'});
            column.add_child(new St.Label({text: item.name, style: `font-weight: bold; color: ${color};`}));
            const text = item.averages === null ? 'Leitura indisponível' :
                item.averages.map((value, index) => `${[10, 60, 300][index]} s: ${value.toFixed(1)}%`).join('\n');
            column.add_child(new St.Label({text, style: `color: ${color};`}));
            if (item.full !== null)
                column.add_child(new St.Label({text: `Espera total · 10 s: ${item.full[0].toFixed(1)}%`}));
            const note = new St.Label({text: item.level === 'normal' ? 'Sem pressão relevante na média de 10 s.' : item.suggestion});
            note.clutter_text.set_line_wrap(true);
            note.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
            column.add_child(note);
            columns.add_child(column);
        }
        this._updatesRows.add_child(columns);
    },

    _buildServicesDialog() {
        this._buildUpdatesDialog(true);
        this._updatesHeading.text = 'Serviços · falhas registradas';
        this._updatesNote.text = 'Somente leitura · passe o mouse nos serviços para ver os detalhes';
        this._networkRefreshButton.set_child(new St.Label({text: 'Atualizar'}));
    },

    _renderServices(data) {
        if (!data || typeof data.text !== 'string' || data.text.length > 160 ||
            !Array.isArray(data.groups) || data.groups.length !== 2 || data.groups.some((group, index) =>
                !group || group.scope !== ['system', 'user'][index] || !Number.isSafeInteger(group.count) || group.count < 0 ||
                typeof group.error !== 'string' || group.error.length > 256 || !Array.isArray(group.items) || group.items.length > 6 || group.items.length > group.count ||
                group.items.some(item => !item || ['name', 'description', 'result', 'status', 'changed'].some(key =>
                    typeof item[key] !== 'string' || item[key].length > 256))))
            throw new Error('Resposta de serviços inválida.');
        this._updatesRows.destroy_all_children();
        const columns = new St.BoxLayout({style: 'spacing: 12px;'});
        for (const group of data.groups) {
            const card = new St.BoxLayout({vertical: true, style: 'width: 338px; padding: 8px; spacing: 8px; background-color: #292929; border-radius: 6px;'});
            card.add_child(new St.Label({text: `${group.scope === 'system' ? 'Sistema' : 'Sua sessão'} · ${group.count}`,
                style: `font-weight: bold; color: ${group.count ? '#ffd479' : group.error ? '#aaaaaa' : '#9fdf9f'};`}));
            if (group.error || !group.count) {
                const note = new St.Label({text: group.error || 'Nenhum serviço com falha', style: 'color: #c8c8c8;'});
                note.clutter_text.set_line_wrap(true);
                card.add_child(note);
            }
            for (const item of group.items) {
                const button = new St.Button({reactive: true, can_focus: true, accessible_name: item.name + ': ' + item.description,
                    style: 'padding: 6px; color: #ffd479;'});
                const label = new St.Label({text: item.name});
                label.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
                button.set_child(label);
                this._attachActionTooltip(button, `${item.description}\n${item.name}\nResultado: ${item.result || 'Indisponível'} · Código: ${item.status || 'N/D'}\nMudança de estado: ${item.changed || 'Horário indisponível'}\nPode ser uma falha antiga ou de um componente opcional. O resultado não determina a causa raiz.`);
                card.add_child(button);
            }
            if (group.count > group.items.length)
                card.add_child(new St.Label({text: `+ ${group.count - group.items.length} serviços · consulte o systemctl`}));
            columns.add_child(card);
        }
        this._updatesRows.add_child(columns);
    },

    _buildProcessesDialog() {
        this._buildUpdatesDialog(true);
        this._processesDialog = true;
        this._updatesHeading.text = 'Processos · desempenho';
        this._updatesNote.text = 'Pressão de recursos · médias de 10 s / 1 min / 5 min';
        this._updatesNote.reactive = true;
        this._attachActionTooltip(this._updatesNote, 'PSI mede o tempo de espera por recursos, não o uso. Atenção ≥ 5%; alta ≥ 20% na média de 10 s. Limites indicativos, não diagnóstico de falha.');
        this._networkRefreshButton.set_child(new St.Label({text: 'Atualizar'}));
        this._networkRefreshButton.accessible_name = 'Atualizar diagnóstico e processos';
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
            throw new Error('Resposta de processos inválida.');
        this._updatesRows.destroy_all_children();
        this._updatesActions.destroy_all_children();
        this._renderPressure(data.pressure);
        const overview = new St.BoxLayout({style: 'spacing: 10px;'});
        const badge = (icon, text, tooltip, color) => {
            const button = new St.Button({reactive: true, can_focus: true,
                accessible_name: text + ': ' + tooltip,
                style: `padding: 7px 12px; background-color: #292929; border-radius: 6px; color: ${color};`});
            const content = new St.BoxLayout({style: 'spacing: 6px;'});
            content.add_child(new St.Icon({icon_name: icon, icon_size: 16}));
            content.add_child(new St.Label({text}));
            button.set_child(content);
            this._attachActionTooltip(button, tooltip);
            return button;
        };
        overview.add_child(badge('computer-symbolic', 'Resumo do sistema', data.summary, '#82cfff'));
        overview.add_child(badge('dialog-information-symbolic', 'Observações', data.notices.join('\n\n'), '#c8c8c8'));
        this._updatesRows.add_child(overview);
        const rankings = new St.BoxLayout({style: 'spacing: 12px;'});
        for (const [title, rows, memory] of [['CPU · maiores consumos', data.cpu_rows, false], ['RAM · maiores consumos', data.memory_rows, true]]) {
            const card = new St.BoxLayout({vertical: true,
                style: 'width: 338px; padding: 8px; spacing: 6px; background-color: #292929; border-radius: 6px;'});
            card.add_child(new St.Label({text: title, style: 'font-weight: bold; color: #82cfff;'}));
            for (const process of rows.slice(0, 3)) {
                const line = new St.BoxLayout({style: 'spacing: 8px;'});
                const name = new St.Label({text: process.name, x_expand: true, style: 'width: 225px;'});
                name.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
                line.add_child(name);
                line.add_child(new St.Label({text: memory ? `${process.memory} MiB` : `${process.cpu.toFixed(1)}%`,
                    style: 'color: #ededed;'}));
                const button = new St.Button({reactive: true, can_focus: true,
                    accessible_name: `${process.name}, PID ${process.pid}, CPU ${process.cpu.toFixed(1)}%, RAM ${process.memory} MiB`});
                button.set_child(line);
                this._attachActionTooltip(button, `PID ${process.pid} · CPU ${process.cpu.toFixed(1)}% · RAM ${process.memory} MiB\nCPU pode superar 100% ao usar vários núcleos.`);
                card.add_child(button);
            }
            if (!rows.length) card.add_child(new St.Label({text: 'Nenhum processo nesta amostra', style: 'color: #aaaaaa;'}));
            rankings.add_child(card);
        }
        this._updatesRows.add_child(rankings);
        let row;
        for (const [index, action] of data.actions.entries()) {
            if (index % 4 === 0) {
                row = new St.BoxLayout({style: 'spacing: 8px;'});
                this._updatesActions.add_child(row);
            }
            const button = new St.Button({reactive: true, can_focus: true,
                accessible_name: action.name + ': ' + action.effect + ' ' + action.command,
                height: 38, y_align: Clutter.ActorAlign.CENTER,
                style: 'width: 156px; min-height: 22px; padding: 8px; border-radius: 6px; background-color: #315d80; color: white;'});
            const label = new St.Label({text: action.name, x_align: Clutter.ActorAlign.CENTER, y_align: Clutter.ActorAlign.CENTER});
            label.clutter_text.set_line_wrap(true);
            button.set_child(label);
            this._attachActionTooltip(button, action.effect + '\n\n' + action.command);
            button.connect('clicked', () => {
                try {
                    const [, argv] = GLib.shell_parse_argv(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
                    Gio.Subprocess.new([...argv, '--action', action.id], Gio.SubprocessFlags.NONE);
                    this._networkRefreshStatus.text = 'Confira o comando e confirme com Enter no terminal.';
                } catch (error) {
                    this._networkRefreshStatus.text = 'Não foi possível abrir a ação.';
                }
            });
            row.add_child(button);
        }
    }
});

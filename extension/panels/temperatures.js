// Temperatures panel methods; state and lifecycle belong to CommandLabel.
var create = ({Language, Clutter, Main, Pango, St, global}) => ({
    _buildTemperaturesDialog() {
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
            style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 10px; padding: 16px; spacing: 12px;'});
        this._temperatureHeading = Language.widget(St.Label, {text: Language.msg('panels.temperatures.title'), style: 'font-size: 18px; font-weight: bold;'});
        this._networkDialog.add_child(this._temperatureHeading);
        this._networkDialog.add_child(Language.widget(St.Label, {text: Language.msg('panels.temperatures.note'), style: 'font-size: 12px; color: #b9c5cf;'}));
        this._temperatureRows = Language.widget(St.BoxLayout, {style: 'spacing: 12px;'});
        this._networkDialog.add_child(this._temperatureRows);
        const footer = Language.widget(St.BoxLayout, {style: 'spacing: 12px;'});
        this._networkRefreshButton = Language.widget(St.Button, {label: Language.msg('panels.refresh'), reactive: true, can_focus: true,
            accessible_name: Language.msg('panels.temperatures.refresh'), style: 'padding: 8px 12px; border-radius: 6px; background-color: #315d80; color: white;'});
        this._networkRefreshButton.connect('clicked', () => this._refreshNetworkDialog());
        footer.add_child(this._networkRefreshButton);
        this._networkRefreshStatus = Language.widget(St.Label, {text: '', style: 'font-size: 12px; color: #b9c5cf;', y_align: Clutter.ActorAlign.CENTER});
        footer.add_child(this._networkRefreshStatus);
        this._networkDialog.add_child(footer);
        this._networkBackdrop.add_child(this._networkDialog);
    },

    _temperatureCategory(item) {
        const code = item.name.split(' · ').pop();
        if (item.group.startsWith('coretemp') || code === 'x86_pkg_temp') return 'CPU';
        if (item.group.startsWith('NVIDIA') || item.group.startsWith('amdgpu')) return 'GPU';
        if (item.group.startsWith('nvme')) return 'Armazenamento';
        if (!item.group.startsWith('applesmc')) return 'Outros sensores';
        if (code === 'TCGC' || code.startsWith('TG')) return 'GPU';
        if (code.startsWith('TC')) return 'CPU';
        if (/^TH0[A-Ca-c]$/.test(code)) return 'Armazenamento';
        if (code === 'TM0P') return 'Memória RAM';
        if (['TPCD', 'TTLD', 'TTRD', 'TW0P'].includes(code)) return 'Placa e conectividade';
        if (/^Th[0-9]H$/.test(code)) return 'Dissipação';
        if (['Ts0P', 'Ts1P', 'Ts0S', 'Ts1S'].includes(code)) return 'Gabinete';
        if (code === 'TA0V') return 'Ambiente';
        return 'Outros sensores';
    },

    _temperatureColumns(items) {
        const groups = new Map();
        for (const item of items) {
            const title = this._temperatureCategory(item);
            if (!groups.has(title)) groups.set(title, []);
            groups.get(title).push(item);
        }
        const columns = [[], [], [], []];
        const heights = [0, 0, 0, 0];
        const critical = new Set(['CPU', 'GPU', 'Memória RAM', 'Armazenamento']);
        const segments = [...groups].map(([title, sensors]) => ({title,
            items: sensors.sort((a, b) => a.name.localeCompare(b.name, undefined, {numeric: true}))}));
        segments.sort((a, b) => b.items.length - a.items.length);
        for (const segment of segments) {
            const start = critical.has(segment.title) ? 0 : 2;
            const index = heights[start] <= heights[start + 1] ? start : start + 1;
            columns[index].push(segment);
            heights[index] += 36 + segment.items.length * 34;
        }
        return columns;
    },

    _renderTemperatures(data) {
        if (!data || !Array.isArray(data.items) || data.items.length > 256 || !Number.isInteger(data.omitted) || data.omitted < 0)
            throw Language.error(Language.msg('panels.error.sensors'));
        // Unavailable records never enter component state or acquire actors/signals.
        const available = data.items.filter(x => x && typeof x === 'object' &&
            Number.isFinite(x.value) && x.value >= -20 && x.value <= 250);
        if (available.some(x => typeof x.group !== 'string' || x.group.length > 128 || typeof x.name !== 'string' || x.name.length > 100 ||
            (x.description !== undefined && (typeof x.description !== 'string' || x.description.length > 512))))
            throw Language.error(Language.msg('panels.error.sensors'));
        data = {items: available.map(x => ({group: x.group, name: x.name, value: x.value, description: x.description})), omitted: data.omitted};
        this._temperatureData = data;
        const monitor = Main.layoutManager.findMonitorForActor(this) || Main.layoutManager.primaryMonitor;
        const columns = this._temperatureColumns(data.items);
        Language.set(this._temperatureHeading, 'text', Language.msg('panels.temperatures.heading', {count: data.items.length, extra: data.omitted ? Language.msg('panels.temperatures.omitted', {count: data.omitted}) : ''}));
        this._temperatureRows.destroy_all_children();
        for (const [index, segments] of columns.entries()) {
            const column = Language.widget(St.BoxLayout, {vertical: true, style: 'spacing: 0px; width: 220px;'});
            column.add_child(Language.widget(St.Label, {text: index < 2 ? Language.msg('panels.temperatures.critical') : Language.msg('panels.temperatures.auxiliary'),
                style: `font-size: 11px; color: ${index < 2 ? '#8bd5ca' : '#b9c5cf'}; padding: 0px 4px 8px;`}));
            for (const segment of segments) {
                column.add_child(Language.widget(St.Label, {text: ({"CPU": Language.msg('panels.temperatures.category_cpu'), "GPU": Language.msg('panels.temperatures.category_gpu'), "Armazenamento": Language.msg('panels.temperatures.category_storage'), "Outros sensores": Language.msg('panels.temperatures.category_other'), "Memória RAM": Language.msg('panels.temperatures.category_ram'), "Placa e conectividade": Language.msg('panels.temperatures.category_board'), "Dissipação": Language.msg('panels.temperatures.category_cooling'), "Gabinete": Language.msg('panels.temperatures.category_chassis'), "Ambiente": Language.msg('panels.temperatures.category_ambient')})[segment.title],
                    style: 'font-size: 12px; font-weight: bold; color: #b9d5e8; padding: 8px 4px 6px;'}));
                for (const item of segment.items) {
                const hot = item.value > 80;
                const card = Language.widget(St.BoxLayout, {vertical: true,
                    style: 'height: 24px; padding: 3px 8px; margin-bottom: 4px; border-radius: 5px; background-color: #293039;'});
                const line = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
                const name = Language.widget(St.Label, {text: item.name, x_expand: true, style: 'font-size: 13px; color: #e6edf3;'});
                name.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
                line.add_child(name);
                const help = Language.widget(St.Button, {label: '?', reactive: true, can_focus: true,
                    accessible_name: Language.msg('panels.temperatures.description', {name: item.name}),
                    style: 'font-size: 12px; padding: 0px 4px; border-radius: 8px; background-color: #405268; color: #dcecff;'});
                const showHelp = this._attachActionTooltip(help, Language.msg('panels.temperatures.help', {description: item.description || Language.msg('panels.temperatures.fallback', {name: item.name}), group: item.group}));
                help.connect('clicked', showHelp);
                line.add_child(help);
                line.add_child(Language.widget(St.Label, {text: `${item.value.toFixed(1)} °C`,
                    style: `font-size: 14px; font-weight: bold; color: ${hot ? '#ff5c5c' : '#8bd5ca'};`}));
                card.add_child(line);
                Language.set(card, 'accessible_name', Language.msg('panels.temperatures.accessible', {group: item.group, name: item.name, value: item.value}));
                column.add_child(card);
                }
                column.add_child(Language.widget(St.Widget, {style: 'height: 6px;'}));
            }
            this._temperatureRows.add_child(column);
        }
        if (!data.items.length)
            this._temperatureRows.add_child(Language.widget(St.Label, {text: Language.msg('panels.temperatures.empty'), style: 'padding: 16px; color: #b9c5cf;'}));
        const [, width] = this._networkDialog.get_preferred_width(-1);
        const [, height] = this._networkDialog.get_preferred_height(width);
        this._networkDialog.set_position(monitor.x + Math.max(8, (monitor.width - width) / 2), monitor.y + Math.max(8, (monitor.height - height) / 2));
    }
});

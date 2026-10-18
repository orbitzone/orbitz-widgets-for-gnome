// Storage panel methods; state and lifecycle belong to CommandLabel.
var create = ({Gio, GLib, Main, Pango, St, getData}) => ({
    _buildStorageDialog() {
        this._storageDialog = true;
        this._buildUpdatesDialog();
        this._updatesHeading.text = 'Armazenamento · espaço e saúde';
        this._updatesNote.text = 'Espaço disponível por volume · SMART quando acessível · detalhes nos tooltips';
        this._networkRefreshButton.set_child(new St.Label({text: 'Atualizar'}));
    },

    _renderHardware(data, page = 0) {
        if (!data || data.mode !== this._hardwareMode || typeof data.title !== 'string' || data.title.length > 160 ||
            typeof data.note !== 'string' || data.note.length > 512 || typeof data.firmware_action !== 'boolean' ||
            !Array.isArray(data.cards) || data.cards.length > 80 || data.cards.some(card => !card ||
                typeof card.title !== 'string' || card.title.length > 256 || !Array.isArray(card.lines) ||
                card.lines.length > 16 || card.lines.some(line => typeof line !== 'string' || line.length > 512)))
            throw new Error('Inventário de hardware inválido.');
        this._updatesHeading.text = data.title;
        this._updatesNote.text = 'Passe o mouse no ? para ver explicações e detalhes completos.';
        this._networkRefreshButton.label = 'Atualizar';
        const monitor = Main.layoutManager.findMonitorForActor(this) || Main.layoutManager.primaryMonitor;
        const available = Math.max(240, monitor.width - 80);
        const columns = Math.max(1, Math.min(3, Math.floor(available / 250)));
        const width = Math.min(900, available);
        const cardWidth = Math.floor((width - (columns - 1) * 10) / columns) - 20;
        const rowCount = monitor.height >= 850 ? 2 : 1;
        const perPage = columns * rowCount;
        const pages = Math.max(1, Math.ceil(data.cards.length / perPage));
        page = Math.max(0, Math.min(pages - 1, page));
        this._updatesScroll.set_policy(St.PolicyType.NEVER, St.PolicyType.NEVER);
        this._updatesRows.style = `spacing: 10px; width: ${width}px;`;
        this._updatesRows.destroy_all_children();
        this._updatesActions.destroy_all_children();
        let row;
        const explanatory = /^(O total utilizável|Slots vazios|Leitura:|Confirme o limite|A presença da extensão|Use “|Tipo DDR, velocidades)/;
        for (const [index, card] of data.cards.slice(page * perPage, (page + 1) * perPage).entries()) {
            if (index % columns === 0) {
                row = new St.BoxLayout({style: 'spacing: 10px;'});
                this._updatesRows.add_child(row);
            }
            const box = new St.BoxLayout({vertical: true, style: `width: ${cardWidth}px; padding: 10px; spacing: 6px; background-color: #292929; border-radius: 6px;`});
            const heading = new St.BoxLayout({style: 'spacing: 8px;'});
            const title = new St.Label({text: card.title, x_expand: true, style: 'font-weight: bold; color: #82cfff;'});
            title.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
            heading.add_child(title);
            const help = new St.Button({label: '?', reactive: true, can_focus: true,
                accessible_name: `Mais informações: ${card.title}`,
                style: 'padding: 0px 5px; border-radius: 5px; background-color: #40566c; color: #cde9ff;'});
            heading.add_child(help);
            box.add_child(heading);
            const extra = card.title === 'Topologia' ? '\nNúcleos físicos são unidades de processamento. Threads são os processadores lógicos apresentados ao Linux.'
                : card.title === 'Virtualização' ? '\nVT-x/AMD-V são recursos do processador. KVM depende do suporte do kernel, firmware e permissões da conta.'
                : data.mode === 'ram' ? '\nValores informados pelo Linux ou pelo firmware. Para upgrades, confirme compatibilidade e acesso aos slots no manual do equipamento.'
                : '\nIdentificação do processador informada pelo sistema.';
            const showHelp = this._attachActionTooltip(help, card.title + '\n\n' + card.lines.join('\n') + extra);
            help.connect('clicked', showHelp);
            const lines = card.lines.filter(text => !explanatory.test(text));
            if (!lines.length) lines.push('Leitura do firmware necessária');
            for (const text of lines) {
                const compact = text.replace('Processadores lógicos:', 'Threads:').replace('Threads por núcleo:', 'Threads/núcleo:')
                    .replace('Extensão anunciada:', 'Extensão:').replace('Velocidade declarada:', 'Vel. declarada:').replace('Velocidade configurada:', 'Vel. configurada:');
                const label = new St.Label({text: compact, style: 'font-size: 13px;'});
                label.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
                box.add_child(label);
            }
            row.add_child(box);
        }
        const [, height] = this._updatesRows.get_preferred_height(width);
        this._updatesScroll.style = `width: ${width}px; height: ${Math.ceil(height)}px;`;
        if (pages > 1) {
            const navigation = new St.BoxLayout({style: 'spacing: 12px;'});
            for (const [label, next, enabled] of [['← Anterior', page - 1, page > 0], ['Próxima →', page + 1, page + 1 < pages]]) {
                const button = new St.Button({label, reactive: enabled, can_focus: enabled, style: 'padding: 6px; color: #82cfff;'});
                button.connect('clicked', () => this._renderHardware(data, next));
                navigation.add_child(button);
            }
            navigation.add_child(new St.Label({text: `${page + 1} / ${pages}`}));
            this._updatesActions.add_child(navigation);
        }
        if (data.firmware_action) {
            const button = new St.Button({label: 'Ler módulos de RAM · autorizar no terminal', reactive: true, can_focus: true,
                style: 'padding: 10px; background-color: #315d80; border-radius: 6px;'});
            button.connect('clicked', () => {
                try {
                    const [, argv] = GLib.shell_parse_argv(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
                    const script = argv.find(arg => arg.endsWith('/cpu-ram-widget.py'));
                    if (!script) throw new Error('Comando de hardware desconhecido.');
                    Gio.Subprocess.new(['/usr/bin/python3', GLib.build_filenamev([GLib.path_get_dirname(script), 'hardware-details.py']), '--read-firmware'], Gio.SubprocessFlags.NONE);
                    this._networkRefreshStatus.text = 'Autorize no terminal e clique em Atualizar após a leitura.';
                } catch (error) { this._networkRefreshStatus.text = 'Não foi possível abrir a leitura do firmware.'; }
            });
            this._updatesActions.add_child(button);
        }
    },

    _renderStorage(data) {
        const numeric = value => Number.isFinite(value) && value >= 0;
        if (!data || typeof data.text !== 'string' || data.text.length > 160 || typeof data.error !== 'string' || data.error.length > 256 ||
            !Number.isInteger(data.omitted) || data.omitted < 0 || !Array.isArray(data.items) || data.items.length > 12 ||
            !Array.isArray(data.unmounted) || data.unmounted.length > 12 || data.unmounted.some(item => !item ||
                ['device', 'disk', 'fstype'].some(key => typeof item[key] !== 'string' || item[key].length > 512) ||
                !numeric(item.total) || ['available', 'used'].some(key => item[key] !== null && (!numeric(item[key]) || item[key] > item.total))) ||
            !Array.isArray(data.disks) || data.disks.length > 16 || data.items.some(item => !item ||
                ['device', 'disk', 'mount'].some(key => typeof item[key] !== 'string' || item[key].length > 512) ||
                !Array.isArray(item.files) || item.files.length > 30 || item.files.some(name => typeof name !== 'string' || name.length > 162) ||
                typeof item.content_error !== 'string' || item.content_error.length > 256 || typeof item.more !== 'boolean' ||
                !['total', 'available', 'percent'].every(key => numeric(item[key])) || item.percent > 100 ||
                (item.inodes !== null && (!numeric(item.inodes) || item.inodes > 100))) ||
            data.disks.some(disk => !disk || typeof disk.name !== 'string' || disk.name.length > 512 ||
                typeof disk.model !== 'string' || disk.model.length > 100 || !disk.health ||
                !['ok', 'alert', 'unavailable'].includes(disk.health.state) ||
                typeof disk.health.note !== 'string' || disk.health.note.length > 256 ||
                ['temperature', 'wear'].some(key => disk.health[key] !== null && !numeric(disk.health[key]))))
            throw new Error('Resposta de armazenamento inválida.');
        this._updatesNote.text = 'Espaço disponível por volume · SMART quando acessível · detalhes nos tooltips';
        this._networkRefreshButton.label = 'Atualizar';
        this._updatesScroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this._updatesRows.style = 'spacing: 10px; width: 720px;';
        this._updatesRows.destroy_all_children();
        const volumes = [...data.items, ...data.unmounted.map(item => ({...item, unmounted: true}))];
        if (this._updatesScroll) this._updatesScroll.style = `width: 720px; height: ${Math.min(420, Math.max(160, Math.ceil(volumes.length / 3) * (this._storageExternal ? 360 : 180) + (data.error ? 30 : 0)))}px;`;
        this._updatesHeading.text = this._storageExternal ? `${this._storageDevice?.label || 'EXT'} · ${this._storageDevice?.name || ''} · volumes e conteúdo` : 'SSD · armazenamento e saúde';
        const size = bytes => `${(bytes / 1073741824).toFixed(1)} GiB`;
        let row;
        for (const [index, item] of volumes.entries()) {
            if (index % 3 === 0) { row = new St.BoxLayout({style: 'spacing: 10px;'}); this._updatesRows.add_child(row); }
            if (item.unmounted) {
                const card = new St.Button({reactive: true, can_focus: true, style: 'width: 210px; padding: 10px; background-color: #292929; border-radius: 6px;'});
                const content = new St.BoxLayout({vertical: true, style: 'spacing: 6px;'});
                content.add_child(new St.Label({text: item.device.split('/').pop(), style: 'font-weight: bold;'}));
                content.add_child(new St.Label({text: 'Não montada', style: 'color: #aaaaaa; font-size: 18px;'}));
                content.add_child(new St.Label({text: `Capacidade: ${size(item.total)}`}));
                content.add_child(new St.Label({text: `Formato: ${item.fstype.toUpperCase()}`}));
                content.add_child(new St.Label({text: item.available === null ? 'Livre: indisponível' : `Livre: ${size(item.available)}`}));
                content.add_child(new St.Label({text: item.used === null ? 'Usado: indisponível' : `Usado: ${size(item.used)}`}));
                card.set_child(content);
                this._attachActionTooltip(card, `${item.device}\nPartição não montada. Capacidade é o tamanho da partição. Espaço livre/usado só aparece quando informado pelo sistema; sem leitura não é possível inferir o consumo. Nenhuma montagem ou reparo é executado.`);
                row.add_child(card);
                continue;
            }
            const alert = item.percent >= 95 || item.inodes >= 95;
            const color = alert ? '#ff6b6b' : item.percent >= 90 || item.inodes >= 90 ? '#ffd479' : '#9fdf9f';
            const card = new St.Button({reactive: true, can_focus: true, style: 'width: 210px; padding: 10px; background-color: #292929; border-radius: 6px;'});
            const content = new St.BoxLayout({vertical: true, style: 'spacing: 6px;'});
            const title = new St.Label({text: item.mount, style: 'font-weight: bold;'});
            title.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
            content.add_child(title);
            content.add_child(new St.Label({text: `${size(item.available)} livres`,  style: `color: ${color}; font-size: 18px;`}));
            content.add_child(new St.Label({text: `Capacidade: ${size(item.total)}`, style: 'color: #c8c8c8;'}));
            const blocks = Math.round(item.percent / 10);
            content.add_child(new St.Label({text: '━'.repeat(blocks) + '┄'.repeat(10 - blocks) + ` ${item.percent.toFixed(0)}%`, style: `color: ${color};`}));
            const disk = data.disks.find(disk => disk.name === item.disk);
            const health = disk?.health;
            content.add_child(new St.Label({text: health?.state === 'ok' ? 'SMART: sem alerta' : health?.state === 'alert' ? 'SMART: atenção' : 'SMART: indisponível',
                style: `color: ${health?.state === 'alert' ? '#ff6b6b' : '#aaaaaa'};`}));
            if (this._storageExternal) {
                for (const filename of (item.files || []).slice(0, 6)) {
                    const file = new St.Label({text: filename});
                    file.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
                    content.add_child(file);
                }
                content.add_child(new St.Label({text: item.content_error || (!item.files?.length ? 'Volume vazio' : item.files.length > 6 || item.more ? 'Mais itens no tooltip' : '')}));
            }
            card.set_child(content);
            this._attachActionTooltip(card, `${this._storageExternal ? (item.files || []).join('\n') + (item.more ? '\nLista limitada aos primeiros 30 itens.' : '') + '\n' : ''}${item.mount}\n${item.device} · ${disk?.model || item.disk}\nCapacidade: ${size(item.total)} · Uso: ${item.percent}%\nInodes usados: ${item.inodes === null ? 'N/D' : item.inodes + '%'}\n${health?.note || 'Saúde não consultada.'}\nTemperatura: ${health?.temperature == null ? 'N/D' : health.temperature + ' °C'} · Vida útil consumida: ${health?.wear == null ? 'N/D' : health.wear + '%'}\nEspaço: atenção ≥ 90%, crítico ≥ 95%. SMART sem alerta não garante ausência de falhas.`);
            row.add_child(card);
        }
        this._updatesActions.destroy_all_children();
        if (!this._storageExternal && data.items.some(item => item.mount === '/')) {
            const cleanup = new St.Button({label: 'Limpar caches do Linux · /', reactive: true, can_focus: true,
                style: 'padding: 10px; border-radius: 6px; background-color: #315d80; color: white;'});
            this._attachActionTooltip(cleanup, 'Abre análise no terminal: miniaturas e cache do pip antigos (30 dias), e pacotes baixados do APT. Mostra o espaço estimado e pede confirmação antes de apagar.');
            cleanup.connect('clicked', () => {
                try {
                    const [, argv] = GLib.shell_parse_argv(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
                    const script = argv.find(arg => arg.endsWith('/cpu-ram-widget.py') || arg.endsWith('/armazenamento-widget.py'));
                    if (!script) throw new Error('Comando de armazenamento desconhecido.');
                    const helper = GLib.build_filenamev([GLib.path_get_dirname(script), 'limpeza-linux.py']);
                    Gio.Subprocess.new(['/usr/bin/python3', helper, '--launch'], Gio.SubprocessFlags.NONE);
                    this._networkRefreshStatus.text = 'Analise e confirme no terminal. Após concluir, clique em Atualizar.';
                } catch (error) {
                    this._networkRefreshStatus.text = 'Não foi possível abrir a limpeza.';
                }
            });
            this._updatesActions.add_child(cleanup);
        }
        if (data.error || !volumes.length || data.omitted)
            this._updatesRows.add_child(new St.Label({text: data.error || (!volumes.length ? 'Nenhum volume disponível.' : `+ ${data.omitted} volumes não exibidos`)}));
    }
});

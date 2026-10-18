// Network panel methods; state and lifecycle belong to CommandLabel.
var create = ({Pango, St}) => ({
    _buildTrafficDialog() {
        this._buildUpdatesDialog(true);
        this._trafficDialog = true;
        this._updatesHeading.text = 'Rede · velocidade e qualidade';
        this._updatesNote.text = 'Qualidade: 5 pings por destino · testes somente nesta modal';
        this._networkRefreshButton.set_child(new St.Label({text: 'Testar qualidade'}));
        this._networkRefreshButton.accessible_name = 'Testar qualidade da conexão';
        this._attachActionTooltip(this._networkRefreshButton, 'Envia 5 pacotes ICMP ao gateway IPv4 e a 1.1.1.1 (Cloudflare). Uma amostra curta; ausência de resposta pode ser bloqueio de ICMP, não queda da internet.');
            const speedColumn = new St.BoxLayout({
                vertical: true,
                style: 'spacing: 10px; padding: 10px; background-color: #292929; border-radius: 6px;',
            });
            speedColumn.add_child(new St.Label({text: 'Velocidade da internet', style: 'font-weight: bold; color: #ededed;'}));
            this._speedtestButton = new St.Button({
                label: 'Testar velocidade', reactive: true, can_focus: true,
                style: 'background-color: #315d85; color: white; border-radius: 6px; padding: 10px;',
            });
            this._speedtestButton.connect('clicked', () => this._startSpeedtest());
            speedColumn.add_child(this._speedtestButton);
            this._speedtestResult = new St.Label({text: '', visible: false, style: 'font-size: 15px;'});
            speedColumn.add_child(this._speedtestResult);
            this._speedtestStatus = new St.Label({text: '', visible: false, style: 'font-size: 12px; color: #c8c8c8;'});
            this._speedtestStatus.clutter_text.set_line_wrap(true);
            this._speedtestStatus.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
            speedColumn.add_child(this._speedtestStatus);
        this._networkDialog.add_child(speedColumn);
        this._attachActionTooltip(this._speedtestButton, 'Executa o Speedtest da Ookla. Transmite dados e pode consumir bastante banda. Latência e perda podem aumentar durante o teste.');
    },

    _renderQuality(data) {
        if (!data || !Array.isArray(data.items) || data.items.length !== 2 || data.items.some(item =>
            !item || ['name', 'target', 'error'].some(key => typeof item[key] !== 'string' || item[key].length > 256) ||
            ['loss', 'latency', 'jitter'].some(key => item[key] !== null && (!Number.isFinite(item[key]) || item[key] < 0)) ||
            (item.loss !== null && item.loss > 100))) throw new Error('Resposta de qualidade inválida.');
        this._updatesRows.destroy_all_children();
        const columns = new St.BoxLayout({style: 'spacing: 12px;'});
        for (const [index, item] of data.items.entries()) {
            const bad = item.loss !== null && item.loss >= 20;
            const attention = item.loss > 0 || item.latency > (index === 0 ? 20 : 100);
            const color = item.error ? '#aaaaaa' : bad ? '#ff6b6b' : attention ? '#ffd479' : '#9fdf9f';
            const card = new St.Button({reactive: true, can_focus: true, style: 'padding: 12px; width: 326px; background-color: #292929; border-radius: 6px;'});
            const content = new St.BoxLayout({vertical: true, style: 'spacing: 8px;'});
            content.add_child(new St.Label({text: item.name, style: `font-weight: bold; color: ${color};`}));
            content.add_child(new St.Label({text: item.error ? 'Leitura indisponível' : item.latency === null ? 'Sem resposta ICMP' : `${item.latency.toFixed(1)} ms`, style: `font-size: 22px; color: ${color};`}));
            content.add_child(new St.Label({text: item.loss === null ? 'Perda: N/D' : `Perda: ${item.loss.toFixed(0)}% · 5 pacotes`}));
            card.set_child(content);
            this._attachActionTooltip(card, `${item.target || 'Gateway não identificado'}\n${item.error || 'Latência média; perda na amostra de 5 pacotes.'}\nVariação (mdev): ${item.jitter === null ? 'N/D' : item.jitter.toFixed(1) + ' ms'}\nCores indicativas: perda > 0% ou latência > 20 ms no roteador / 100 ms na internet; vermelho com perda ≥ 20%. ICMP pode ser limitado pelo destino. Não identifica sozinho a causa de lentidão.`);
            columns.add_child(card);
        }
        this._updatesRows.add_child(columns);
    }
});

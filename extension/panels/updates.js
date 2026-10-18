// Updates panel methods; state and lifecycle belong to CommandLabel.
var create = ({Clutter, Gio, GLib, Pango, St, getData}) => ({
    _renderUpdates(data) {
        if (typeof data.text !== 'string' || data.text.length > 128 || typeof data.reboot !== 'boolean' ||
            typeof data.index_updated !== 'string' || data.index_updated.length > 64 ||
            typeof data.error !== 'string' || data.error.length > 256 || !Array.isArray(data.items) || data.items.length > 100 ||
            !Number.isInteger(data.omitted) || data.omitted < 0 ||
            !Array.isArray(data.notices) || data.notices.length > 20 || data.notices.some(x => typeof x !== 'string' || x.length > 2048) ||
            !Array.isArray(data.actions) || data.actions.length > 20 || data.actions.some(x => !x ||
                typeof x.id !== 'string' || !/^[a-z0-9-]{1,40}$/.test(x.id) || typeof x.name !== 'string' || x.name.length > 80 ||
                typeof x.command !== 'string' || x.command.length > 2048) ||
            data.items.some(item => !item || !['name', 'installed', 'version', 'source'].every(k => typeof item[k] === 'string' && item[k].length <= 512)))
            throw new Error('Resposta de atualizações inválida.');
        this._updatesHeading.text = data.text;
        this._updatesRows.destroy_all_children();
        const add = (text, color = '#c8c8c8') => {
            const label = new St.Label({text, style: `padding: 4px; color: ${color};`});
            label.clutter_text.set_line_wrap(true);
            this._updatesRows.add_child(label);
        };
        add(data.reboot ? 'Reinicialização pendente.' : 'Sem indicação de reinicialização pendente.');
        add('Índice APT mais antigo: ' + data.index_updated);
        for (const notice of data.notices) add(notice);
        if (data.error) add(data.error);
        if (data.omitted) add(`${data.omitted} pacotes adicionais.`);
        for (const source of ['APT', 'Snap', 'Flatpak']) {
            const items = data.items.filter(item => item.source === source);
            add(source + ' · ' + items.length, 'white');
            for (const item of items)
                add((item.security ? '[Segurança] ' : '') + item.name + ' · ' + item.installed + ' → ' + item.version, item.security ? '#ffd479' : '#82cfff');
        }
        this._updatesActions.destroy_all_children();
        this._updatesActions.add_child(new St.Label({text: 'Ações · confirme com Enter no terminal',
            style: 'font-size: 12px; color: #c8c8c8;'}));
        let row;
        for (const [index, action] of data.actions.entries()) {
            if (index % 4 === 0) {
                row = new St.BoxLayout({style: 'spacing: 8px;', x_expand: true});
                this._updatesActions.add_child(row);
            }
            const button = new St.Button({reactive: true, can_focus: true,
                accessible_name: action.name + ': ' + action.command, x_expand: true,
                height: 38, y_align: Clutter.ActorAlign.CENTER,
                style: 'width: 156px; min-height: 22px; padding: 8px; border-radius: 6px; background-color: #315d80; color: white;'});
            const label = new St.Label({text: action.name, x_align: Clutter.ActorAlign.CENTER, y_align: Clutter.ActorAlign.CENTER});
            label.clutter_text.set_line_wrap(true);
            label.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
            button.set_child(label);
            this._attachActionTooltip(button, action.command);
            button.connect('clicked', () => {
                try {
                    const [, argv] = GLib.shell_parse_argv(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
                    Gio.Subprocess.new([...argv, '--action', action.id], Gio.SubprocessFlags.NONE);
                    this._networkRefreshStatus.text = 'Comando aberto no terminal; releia a lista após concluir.';
                } catch (error) { this._networkRefreshStatus.text = 'Não foi possível abrir o terminal.'; }
            });
            row.add_child(button);
        }
    }
});

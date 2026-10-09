const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const {Adw, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Gettext.gettext;

const Settings = Me.imports.settings;
const {TextLabelSubPage} = Settings.TextLabelSubPage;

var CommandLabelSubPage = GObject.registerClass(
class AzClockCommandLabelSubPage extends TextLabelSubPage {
    _init(settings, params) {
        super._init(settings, params);

        this.removeTextRow();

        const commandExpanderRow = new Adw.ExpanderRow({
            title: _('Command'),
            expanded: true,
            enable_expansion: true,
        });

        const commandEntry = new Gtk.Entry({
            valign: Gtk.Align.FILL,
            vexpand: true,
            halign: Gtk.Align.FILL,
            hexpand: true,
            text: this.getClockElementData('Text_Command') || '',
        });
        commandEntry.connect('changed', () => {
            this.setClockElementData('Text_Command', commandEntry.get_text());
        });
        const commandRow = new Adw.ActionRow({
            activatable: false,
            selectable: false,
        });

        commandRow.set_child(commandEntry);
        commandExpanderRow.add_row(commandRow);
        this.textGroupAdd(commandExpanderRow);

        const pollingIntervalRow = this.createSpinRow(_('Polling Interval (ms)'), 'Text_PollingInterval', 250, 20000);
        this.textGroupAdd(pollingIntervalRow);
    }
});

const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const {Adw, GLib, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Gettext.gettext;

const Settings = Me.imports.settings;
const {SubPage} = Settings.SubPage;

var WidgetSubPage = GObject.registerClass({GTypeName: 'OrbitzWidgetsWidgetSubPage'},
class AzClockWidgetClockSubPage extends SubPage {
    _init(settings, params) {
        super._init(settings, params);

        const generalGroup = new Adw.PreferencesGroup();
        this.add(generalGroup);

        this._addGroupingControls(generalGroup);
        const grouped = !!this.getClockElementData('Parent_Id');
        const xLocationRow = this.createSpinRow(_('Location X'), 'Location_X', 0, 10000);
        generalGroup.add(xLocationRow);

        const yLocationRow = this.createSpinRow(_('Location Y'), 'Location_Y', 0, 10000);
        generalGroup.add(yLocationRow);

        const boxAnchorPoint = this.createComboRow(_('Anchor Point'), 'Box_AnchorPoint');
        generalGroup.add(boxAnchorPoint);
        this._groupPositionRows = [xLocationRow, yLocationRow, boxAnchorPoint];
        for (const row of this._groupPositionRows) row.sensitive = !grouped;

        const boxWidthRow = this.createSpinRow('Widget width (px; 0 = default)', 'Box_Width', 0, 2000);
        generalGroup.add(boxWidthRow);

        const boxSpacingRow = this.createSpinRow(_('Widget Spacing'), 'Box_Spacing', 0, 500);
        generalGroup.add(boxSpacingRow);

        const boxPaddingRow = this.createSpinRow(_('Widget Padding'), 'Box_Padding', 0, 500);
        generalGroup.add(boxPaddingRow);

        const verticalLayoutSwitch = new Gtk.Switch({
            valign: Gtk.Align.CENTER,
            active: this.getClockElementData('Box_VerticalLayout', 'bool'),
        });
        const verticalLayoutRow = new Adw.ActionRow({
            title: _('Vertical Layout'),
            activatable_widget: verticalLayoutSwitch,
        });
        verticalLayoutSwitch.connect('notify::active', widget => {
            this.setClockElementData('Box_VerticalLayout', widget.get_active());
        });
        verticalLayoutRow.add_suffix(verticalLayoutSwitch);
        generalGroup.add(verticalLayoutRow);

        const borderEnabled = this.getClockElementData('Box_BorderEnabled', 'bool');

        const borderOptionsRow = new Adw.ExpanderRow({
            title: _('Enable Border'),
            show_enable_switch: true,
            enable_expansion: borderEnabled,
        });
        generalGroup.add(borderOptionsRow);
        borderOptionsRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData('Box_BorderEnabled', widget.enable_expansion);
        });

        const borderWidthRow = this.createSpinRow(_('Border Width'), 'Box_BorderWidth', 0, 15);
        borderOptionsRow.add_row(borderWidthRow);
        const borderColorRow = this.createColorRow(_('Border Color'), 'Box_BorderColor');
        borderOptionsRow.add_row(borderColorRow);

        const backgroundEnabled = this.getClockElementData('Box_BackgroundEnabled', 'bool');

        const widgetBackgroundRow = new Adw.ExpanderRow({
            title: _('Enable Background'),
            show_enable_switch: true,
            enable_expansion: backgroundEnabled,
        });
        generalGroup.add(widgetBackgroundRow);

        widgetBackgroundRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData('Box_BackgroundEnabled', widget.enable_expansion);
        });

        const widgetBackgroundColorRow = this.createColorRow(_('Background Color'), 'Box_BackgroundColor');
        widgetBackgroundRow.add_row(widgetBackgroundColorRow);
        const borderRadiusRow = this.createSpinRow(_('Background Radius'), 'Box_BorderRadius', 0, 999);
        widgetBackgroundRow.add_row(borderRadiusRow);
    }

    _addGroupingControls(group) {
        const data = this._settings.get_value('widget-data').deep_unpack();
        const current = data[this.widget_index][0];
        const candidates = data.map((widget,index) => ({meta:widget[0],index})).filter(item =>
            item.index !== this.widget_index && item.meta.Box_IsGroup === 'true' && !item.meta.Parent_Id);
        const model = new Gtk.StringList(); model.append('Desktop · sem pai');
        for (const item of candidates) model.append(item.meta.Name);
        const combo = new Adw.ComboRow({title: 'Widget pai · mover para', model,
            selected: Math.max(0, candidates.findIndex(item => item.meta.Widget_Id === current.Parent_Id) + 1),
            sensitive: current.Box_IsGroup !== 'true'});
        combo.connect('notify::selected', () => {
            this.setClockElementData('Parent_Id', combo.selected ? candidates[combo.selected - 1].meta.Widget_Id : '');
            for (const row of this._groupPositionRows || []) row.sensitive = combo.selected === 0;
            toggle.sensitive = combo.selected === 0;
        });
        group.add(combo);
        const toggle = new Gtk.Switch({active: current.Box_IsGroup === 'true', valign: Gtk.Align.CENTER, sensitive: !current.Parent_Id});
        const row = new Adw.ActionRow({title:'Usar como widget pai', subtitle:'Um nível de agrupamento; os filhos mantêm seus comandos e modais.'});
        row.add_suffix(toggle); group.add(row);
        toggle.connect('notify::active', () => {
            if (!current.Widget_Id) { current.Widget_Id = GLib.uuid_string_random(); this.setClockElementData('Widget_Id', current.Widget_Id); }
            if (toggle.active) this.setClockElementData('Box_IsGroup', 'true');
            else {
                const updated = this._settings.get_value('widget-data').deep_unpack();
                updated[this.widget_index][0].Box_IsGroup = 'false';
                for (const widget of updated) if (widget[0].Parent_Id === current.Widget_Id) widget[0].Parent_Id = '';
                this._settings.set_value('changed-data', new GLib.Variant('a{ss}', {}));
                this._settings.set_value('widget-data', new GLib.Variant('aaa{ss}', updated));
                Me.imports.settings.WidgetsData.WidgetsData.data = updated;
            }
            combo.sensitive = !toggle.active;
        });
        group.add(this.createSpinRow('Colunas dos subwidgets', 'Group_Columns', 1, 4));
    }

    createComboRow(title, setting) {
        const value = this.getClockElementData(setting);
        const stringList = new Gtk.StringList();
        stringList.append(_('Top Left'));
        stringList.append(_('Bottom Left'));
        stringList.append(_('Top Right'));
        stringList.append(_('Bottom Right'));

        const comboRow = new Adw.ComboRow({
            title: _(title),
            model: stringList,
            selected: value,
        });
        comboRow.connect('notify::selected', widget => {
            this.setClockElementData(setting, widget.selected);
        });
        return comboRow;
    }
});

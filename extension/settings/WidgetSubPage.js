const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();
const Language = Me.imports.uiLanguage.Language;

const {Adw, GLib, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Language.tr;

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
        const xLocationRow = this.createSpinRow(Language.msg('settings.location_x'), 'Location_X', 0, 10000);
        generalGroup.add(xLocationRow);

        const yLocationRow = this.createSpinRow(Language.msg('settings.location_y'), 'Location_Y', 0, 10000);
        generalGroup.add(yLocationRow);

        const boxAnchorPoint = this.createComboRow(Language.msg('settings.anchor_point'), 'Box_AnchorPoint');
        generalGroup.add(boxAnchorPoint);
        this._groupPositionRows = [xLocationRow, yLocationRow, boxAnchorPoint];
        for (const row of this._groupPositionRows) row.sensitive = !grouped;

        const boxWidthRow = this.createSpinRow(Language.msg('settings.widget_width'), 'Box_Width', 0, 2000);
        generalGroup.add(boxWidthRow);

        const boxSpacingRow = this.createSpinRow(Language.msg('settings.widget_spacing'), 'Box_Spacing', 0, 500);
        generalGroup.add(boxSpacingRow);

        const boxPaddingRow = this.createSpinRow(Language.msg('settings.widget_padding'), 'Box_Padding', 0, 500);
        generalGroup.add(boxPaddingRow);

        const verticalLayoutSwitch = Language.widget(Gtk.Switch, {
            valign: Gtk.Align.CENTER,
            active: this.getClockElementData('Box_VerticalLayout', 'bool'),
        });
        const verticalLayoutRow = Language.widget(Adw.ActionRow, {
            title: Language.msg('settings.vertical_layout'),
            activatable_widget: verticalLayoutSwitch,
        });
        verticalLayoutSwitch.connect('notify::active', widget => {
            this.setClockElementData('Box_VerticalLayout', widget.get_active());
        });
        verticalLayoutRow.add_suffix(verticalLayoutSwitch);
        generalGroup.add(verticalLayoutRow);

        const borderEnabled = this.getClockElementData('Box_BorderEnabled', 'bool');

        const borderOptionsRow = Language.widget(Adw.ExpanderRow, {
            title: Language.msg('settings.enable_border'),
            show_enable_switch: true,
            enable_expansion: borderEnabled,
        });
        generalGroup.add(borderOptionsRow);
        borderOptionsRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData('Box_BorderEnabled', widget.enable_expansion);
        });

        const borderWidthRow = this.createSpinRow(Language.msg('settings.border_width'), 'Box_BorderWidth', 0, 15);
        borderOptionsRow.add_row(borderWidthRow);
        const borderColorRow = this.createColorRow(Language.msg('settings.border_color'), 'Box_BorderColor');
        borderOptionsRow.add_row(borderColorRow);

        const backgroundEnabled = this.getClockElementData('Box_BackgroundEnabled', 'bool');

        const widgetBackgroundRow = Language.widget(Adw.ExpanderRow, {
            title: Language.msg('settings.enable_background'),
            show_enable_switch: true,
            enable_expansion: backgroundEnabled,
        });
        generalGroup.add(widgetBackgroundRow);

        widgetBackgroundRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData('Box_BackgroundEnabled', widget.enable_expansion);
        });

        const widgetBackgroundColorRow = this.createColorRow(Language.msg('settings.background_color'), 'Box_BackgroundColor');
        widgetBackgroundRow.add_row(widgetBackgroundColorRow);
        const borderRadiusRow = this.createSpinRow(Language.msg('settings.background_radius'), 'Box_BorderRadius', 0, 999);
        widgetBackgroundRow.add_row(borderRadiusRow);
    }

    _addGroupingControls(group) {
        const data = this._settings.get_value('widget-data').deep_unpack();
        const current = data[this.widget_index][0];
        const candidates = data.map((widget,index) => ({meta:widget[0],index})).filter(item =>
            item.index !== this.widget_index && item.meta.Box_IsGroup === 'true' && !item.meta.Parent_Id);

        const combo = Language.widget(Adw.ComboRow, {title: Language.msg('settings.parent_move'),
            selected: Math.max(0, candidates.findIndex(item => item.meta.Widget_Id === current.Parent_Id) + 1),
            sensitive: current.Box_IsGroup !== 'true'});
        Language.items(combo, Gtk.StringList, [Language.msg('settings.desktop_without_parent'), ...candidates.map(item => item.meta.Name)]);
        combo.connect('notify::selected', () => {
            if (combo.orbitzLanguageUpdating) return;
            this.setClockElementData('Parent_Id', combo.selected ? candidates[combo.selected - 1].meta.Widget_Id : '');
            for (const row of this._groupPositionRows || []) row.sensitive = combo.selected === 0;
            toggle.sensitive = combo.selected === 0;
        });
        group.add(combo);
        const toggle = Language.widget(Gtk.Switch, {active: current.Box_IsGroup === 'true', valign: Gtk.Align.CENTER, sensitive: !current.Parent_Id});
        const row = Language.widget(Adw.ActionRow, {title:Language.msg('settings.use_as_parent'), subtitle:Language.msg('settings.grouping_note')});
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
        group.add(this.createSpinRow(Language.msg('settings.subwidget_columns'), 'Group_Columns', 1, 4));
    }

    createComboRow(title, setting) {
        const value = this.getClockElementData(setting);
        const comboRow = Language.widget(Adw.ComboRow, {
            title,
            selected: value,
        });
        Language.items(comboRow, Gtk.StringList, ['settings.top_left', 'settings.bottom_left', 'settings.top_right', 'settings.bottom_right'].map(key => Language.msg(key)));
        comboRow.connect('notify::selected', widget => {
            if (widget.orbitzLanguageUpdating) return;
            this.setClockElementData(setting, widget.selected);
        });
        return comboRow;
    }
});

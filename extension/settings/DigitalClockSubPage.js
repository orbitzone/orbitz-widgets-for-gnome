const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();
const Language = Me.imports.uiLanguage.Language;

const {Adw, GLib, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Language.tr;

const Settings = Me.imports.settings;
const {SubPage} = Settings.SubPage;
const {TimeZoneCatalog} = Settings.timeZoneCatalog;
const WorldClock = Me.imports.worldClock.WorldClock;

var DigitalClockSubPage = GObject.registerClass({GTypeName: 'OrbitzWidgetsDigitalClockSubPage'},
class AzClockDigitalClockSubPage extends SubPage {
    _init(settings, params) {
        super._init(settings, params);

        const format = this.getClockElementData('Text_DateFormat') || '';
        if (WorldClock.isTimeFormat(format)) {
            const worldClockGroup = Language.widget(Adw.PreferencesGroup, {title: Language.msg('settings.world_clock')});
            this.add(worldClockGroup);

            const worldClockEnabled = this.getClockElementData('WorldClockEnabled', 'bool');
            const worldClockRow = Language.widget(Adw.ExpanderRow, {
                title: Language.msg('settings.show_an_additional_clock'),
                show_enable_switch: true,
                enable_expansion: worldClockEnabled,
                expanded: worldClockEnabled,
            });
            worldClockRow.connect('notify::enable-expansion', widget => {
                this.setClockElementData('WorldClockEnabled', widget.enable_expansion);
                worldTimeZoneRow.sensitive = widget.enable_expansion;
                worldTimeZoneSelector.sensitive = widget.enable_expansion;
            });
            worldClockGroup.add(worldClockRow);

            const worldTimeZoneRow = Language.widget(Adw.ActionRow, {title: Language.msg('settings.time_zone')});
            worldClockRow.add_row(worldTimeZoneRow);
            const worldTimeZoneSelector = TimeZoneCatalog.createDropDown(GLib, Gtk,
                this.getClockElementData('WorldClockTimeZone') || 'America/New_York');
            worldTimeZoneSelector.set_size_request(390, -1);
            worldTimeZoneSelector.sensitive = worldClockEnabled;
            worldTimeZoneSelector.connect('notify::selected', widget => {
                const selected = widget.orbitzTimeZones[widget.selected];
                if (!selected) return;
                this.setClockElementData('WorldClockTimeZone', selected.identifier);
                this.setClockElementData('WorldClockLabel', `${selected.city} • ${selected.region}`);
            });
            worldTimeZoneRow.add_suffix(worldTimeZoneSelector);
        }
        const timeZoneGroup = new Adw.PreferencesGroup();
        this.add(timeZoneGroup);

        const timeZoneRow = this.createTimeZoneRow();
        timeZoneGroup.add(timeZoneRow);

        const dateFormatGroup = new Adw.PreferencesGroup();
        this.add(dateFormatGroup);

        const dateFormatExpanderRow = Language.widget(Adw.ExpanderRow, {
            title: Language.msg('settings.date_time_format'),
            expanded: true,
            enable_expansion: true,
        });

        const dateFormatEntry = Language.widget(Gtk.Entry, {
            valign: Gtk.Align.FILL,
            vexpand: true,
            halign: Gtk.Align.FILL,
            hexpand: true,
            text: this.getClockElementData('Text_DateFormat'),
        });
        dateFormatEntry.connect('changed', () => {
            this.setClockElementData('Text_DateFormat', dateFormatEntry.get_text());
        });
        const dateFormatRow = Language.widget(Adw.ActionRow, {
            activatable: false,
            selectable: false,
        });

        const linksBox = Language.widget(Gtk.Box, {
            css_classes: ['linked'],
        });

        const linkButton = Language.widget(Gtk.LinkButton, {
            label: Language.msg('settings.format_guide'),
            uri: 'https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes',
            css_classes: ['caption'],
            valign: Gtk.Align.CENTER,
        });
        linksBox.append(linkButton);

        const linkButton2 = Language.widget(Gtk.LinkButton, {
            label: Language.msg('settings.markup_guide'),
            uri: 'https://docs.gtk.org/Pango/pango_markup.html',
            css_classes: ['caption'],
            valign: Gtk.Align.CENTER,
        });
        linksBox.append(linkButton2);

        dateFormatRow.set_child(dateFormatEntry);

        dateFormatExpanderRow.add_action(linksBox);
        dateFormatExpanderRow.add_row(dateFormatRow);

        dateFormatGroup.add(dateFormatExpanderRow);

        const generalGroup = new Adw.PreferencesGroup();
        this.add(generalGroup);

        const textAlignmentXRow = this.createComboRow(Language.msg('settings.alignment_x'), 'Text_AlignmentX');
        generalGroup.add(textAlignmentXRow);

        const textAlignmentYRow = this.createComboRow(Language.msg('settings.alignment_y'), 'Text_AlignmentY');
        generalGroup.add(textAlignmentYRow);

        const lineAlignmentRow = this.createComboRow(Language.msg('settings.line_alignment'), 'Text_LineAlignment');
        generalGroup.add(lineAlignmentRow);

        const marginsExpanderRow = Language.widget(Adw.ExpanderRow, {
            title: Language.msg('settings.margins'),
        });
        generalGroup.add(marginsExpanderRow);

        const marginTopRow = this.createSpinRow(Language.msg('settings.top'), 'Element_Margin_Top', 0, 200);
        marginsExpanderRow.add_row(marginTopRow);
        const marginRightRow = this.createSpinRow(Language.msg('settings.right'), 'Element_Margin_Right', 0, 200);
        marginsExpanderRow.add_row(marginRightRow);
        const marginBottomRow = this.createSpinRow(Language.msg('settings.bottom'), 'Element_Margin_Bottom', 0, 200);
        marginsExpanderRow.add_row(marginBottomRow);
        const marginLeftRow = this.createSpinRow(Language.msg('settings.left'), 'Element_Margin_Left', 0, 200);
        marginsExpanderRow.add_row(marginLeftRow);

        const paddingExpanderRow = Language.widget(Adw.ExpanderRow, {
            title: Language.msg('settings.padding'),
        });
        generalGroup.add(paddingExpanderRow);

        const paddingTopRow = this.createSpinRow(Language.msg('settings.top'), 'Element_Padding_Top', 0, 200);
        paddingExpanderRow.add_row(paddingTopRow);
        const paddingRightRow = this.createSpinRow(Language.msg('settings.right'), 'Element_Padding_Right', 0, 200);
        paddingExpanderRow.add_row(paddingRightRow);
        const paddingBottomRow = this.createSpinRow(Language.msg('settings.bottom'), 'Element_Padding_Bottom', 0, 200);
        paddingExpanderRow.add_row(paddingBottomRow);
        const paddingLeftRow = this.createSpinRow(Language.msg('settings.left'), 'Element_Padding_Left', 0, 200);
        paddingExpanderRow.add_row(paddingLeftRow);

        const textOptionsGroup = Language.widget(Adw.PreferencesGroup, {
            title: Language.msg('settings.text_style'),
        });
        this.add(textOptionsGroup);

        const fontEnabled = this.getClockElementData('Text_CustomFontEnabled', 'bool');
        const fontFamily = this.getClockElementData('Text_CustomFontFamily');
        const fontButton = Language.widget(Gtk.FontButton, {
            valign: Gtk.Align.CENTER,
            use_size: false,
            use_font: true,
            level: Gtk.FontChooserLevel.FAMILY, // | Gtk.FontChooserLevel.STYLE,
            font: fontFamily,
        });
        const fontRow = Language.widget(Adw.ActionRow, {
            title: Language.msg('settings.font'),
        });
        fontButton.connect('notify::font', widget => {
            this.setClockElementData('Text_CustomFontFamily', widget.font);
        });
        fontRow.add_suffix(fontButton);
        const fontExpanderRow = Language.widget(Adw.ExpanderRow, {
            title: Language.msg('settings.override_font_family'),
            show_enable_switch: true,
            expanded: fontEnabled,
            enable_expansion: fontEnabled,
        });
        fontExpanderRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData('Text_CustomFontEnabled', widget.enable_expansion);
        });
        fontExpanderRow.add_row(fontRow);
        textOptionsGroup.add(fontExpanderRow);

        const timeFontSizeRow = this.createSpinRow(Language.msg('settings.font_size'), 'Text_Size', 8, 200);
        textOptionsGroup.add(timeFontSizeRow);

        const textColorRow = this.createColorRow(Language.msg('settings.text_color'), 'Text_Color');
        textOptionsGroup.add(textColorRow);

        const shadowExpanderRow = this.createShadowExpanderRow(Language.msg('settings.text_shadow'), 'Text_Shadow');
        textOptionsGroup.add(shadowExpanderRow);

        const borderEnabled = this.getClockElementData('Text_BorderEnabled', 'bool');
        const borderOptionsRow = Language.widget(Adw.ExpanderRow, {
            title: Language.msg('settings.enable_border'),
            show_enable_switch: true,
            enable_expansion: borderEnabled,
        });
        textOptionsGroup.add(borderOptionsRow);
        borderOptionsRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData('Text_BorderEnabled', widget.enable_expansion);
        });

        const borderWidthRow = this.createSpinRow(Language.msg('settings.border_width'), 'Text_BorderWidth', 0, 15);
        borderOptionsRow.add_row(borderWidthRow);
        const borderColorRow = this.createColorRow(Language.msg('settings.border_color'), 'Text_BorderColor');
        borderOptionsRow.add_row(borderColorRow);

        const backgroundEnabled = this.getClockElementData('Text_BackgroundEnabled', 'bool');
        const widgetBackgroundRow = Language.widget(Adw.ExpanderRow, {
            title: Language.msg('settings.enable_background'),
            show_enable_switch: true,
            enable_expansion: backgroundEnabled,
        });
        textOptionsGroup.add(widgetBackgroundRow);

        widgetBackgroundRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData('Text_BackgroundEnabled', widget.enable_expansion);
        });

        const widgetBackgroundColorRow = this.createColorRow(Language.msg('settings.background_color'), 'Text_BackgroundColor');
        widgetBackgroundRow.add_row(widgetBackgroundColorRow);
        const borderRadiusRow = this.createSpinRow(Language.msg('settings.background_radius'), 'Text_BorderRadius', 0, 999);
        widgetBackgroundRow.add_row(borderRadiusRow);
    }
});

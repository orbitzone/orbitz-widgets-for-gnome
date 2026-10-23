const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();
const Language = Me.imports.uiLanguage.Language;

const {Adw, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Language.tr;

const Settings = Me.imports.settings;
const {SubPage} = Settings.SubPage;

const CLOCK_STYLE_COUNT = 9;
const BUTTON_STYLE_COUNT = 5;

var AnalogClockSubPage = GObject.registerClass({GTypeName: 'OrbitzWidgetsAnalogClockSubPage'},
class AzClockAnalogClockSubPage extends SubPage {
    _init(settings, params) {
        super._init(settings, params);

        const timeZoneGroup = new Adw.PreferencesGroup();
        this.add(timeZoneGroup);

        const timeZoneRow = this.createTimeZoneRow();
        timeZoneGroup.add(timeZoneRow);

        const generalGroup = Language.widget(Adw.PreferencesGroup, {
            title: Language.msg('settings.clock_settings'),
        });
        this.add(generalGroup);

        const clockSizeRow = this.createSpinRow(Language.msg('settings.size'), 'Clock_Size', 100, 1000);
        generalGroup.add(clockSizeRow);

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

        const clockFaceGroup = Language.widget(Adw.PreferencesGroup, {
            title: Language.msg('settings.clock_face'),
        });
        this.add(clockFaceGroup);

        const clockStyleRow = this.createSpinRow(Language.msg('settings.style'), 'ClockFace_Style', 1, CLOCK_STYLE_COUNT);
        clockFaceGroup.add(clockStyleRow);

        const clockColorRow = this.createColorRow(Language.msg('settings.color'), 'ClockFace_Color');
        clockFaceGroup.add(clockColorRow);

        const clockBackgroundColorRow = this.createColorRow(Language.msg('settings.background_color'), 'ClockFace_BackgroundColor');
        clockFaceGroup.add(clockBackgroundColorRow);

        const borderEnabled = this.getClockElementData('ClockFace_BorderEnabled', 'bool');

        const borderOptionsRow = Language.widget(Adw.ExpanderRow, {
            title: Language.msg('settings.border'),
            show_enable_switch: true,
            enable_expansion: borderEnabled,
        });
        clockFaceGroup.add(borderOptionsRow);
        borderOptionsRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData('ClockFace_BorderEnabled', widget.enable_expansion);
        });

        const borderWidthRow = this.createSpinRow(Language.msg('settings.border_width'), 'ClockFace_BorderWidth', 0, 15);
        borderOptionsRow.add_row(borderWidthRow);
        const borderColorRow = this.createColorRow(Language.msg('settings.border_color'), 'ClockFace_BorderColor');
        borderOptionsRow.add_row(borderColorRow);

        const shadowExpanderRow = this.createShadowExpanderRow(Language.msg('settings.inner_shadow'), 'ClockFace_Shadow');
        clockFaceGroup.add(shadowExpanderRow);

        const shadowOuterExpanderRow = this.createShadowExpanderRow(Language.msg('settings.outer_shadow'), 'ClockFace_BoxShadow');
        clockFaceGroup.add(shadowOuterExpanderRow);

        const enableSwitch = Language.widget(Gtk.Switch, {
            valign: Gtk.Align.CENTER,
            active: this.getClockElementData('ClockFace_Visible', 'bool'),
        });
        enableSwitch.connect('notify::active', widget => {
            this.setClockElementData('ClockFace_Visible', widget.get_active());

            clockStyleRow.sensitive = widget.get_active();
            clockColorRow.sensitive = widget.get_active();
            clockBackgroundColorRow.sensitive = widget.get_active();
            borderOptionsRow.sensitive = widget.get_active();
            shadowExpanderRow.sensitive = widget.get_active();
            shadowOuterExpanderRow.sensitive = widget.get_active();
        });
        clockFaceGroup.set_header_suffix(enableSwitch);

        clockStyleRow.sensitive = enableSwitch.get_active();
        clockColorRow.sensitive = enableSwitch.get_active();
        clockBackgroundColorRow.sensitive = enableSwitch.get_active();
        borderOptionsRow.sensitive = enableSwitch.get_active();
        shadowExpanderRow.sensitive = enableSwitch.get_active();
        shadowOuterExpanderRow.sensitive = enableSwitch.get_active();

        this.createHandGroup('ClockButton', Language.msg('settings.button_in_center'), BUTTON_STYLE_COUNT);
        this.createHandGroup('SecondHand', Language.msg('settings.second_hand'), CLOCK_STYLE_COUNT);
        this.createHandGroup('MinuteHand', Language.msg('settings.minute_hand'), CLOCK_STYLE_COUNT);
        this.createHandGroup('HourHand', Language.msg('settings.hour_hand'), CLOCK_STYLE_COUNT);
    }

    createHandGroup(elementType, title, maxStyles) {
        const handGroup = Language.widget(Adw.PreferencesGroup, {
            title,
        });
        this.add(handGroup);

        const styleRow = this.createSpinRow(Language.msg('settings.style'), `${elementType}_Style`, 1, maxStyles);
        handGroup.add(styleRow);

        const handColorRow = this.createColorRow(Language.msg('settings.color'), `${elementType}_Color`);
        handGroup.add(handColorRow);

        const shadowExpanderRow = this.createShadowExpanderRow(Language.msg('settings.shadow'), `${elementType}_Shadow`);
        handGroup.add(shadowExpanderRow);

        if (elementType === 'SecondHand' || elementType === 'ClockButton') {
            const enableSwitch = Language.widget(Gtk.Switch, {
                valign: Gtk.Align.CENTER,
                active: this.getClockElementData(`${elementType}_Visible`, 'bool'),
            });
            enableSwitch.connect('notify::active', widget => {
                this.setClockElementData(`${elementType}_Visible`, widget.get_active());

                styleRow.sensitive = widget.get_active();
                shadowExpanderRow.sensitive = widget.get_active();
                handColorRow.sensitive = widget.get_active();
            });
            handGroup.set_header_suffix(enableSwitch);

            styleRow.sensitive = enableSwitch.get_active();
            shadowExpanderRow.sensitive = enableSwitch.get_active();
            handColorRow.sensitive = enableSwitch.get_active();
        }
    }
});

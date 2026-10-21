const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const {Adw, Gdk, GLib, GObject, Gtk} = imports.gi;

const {TimeZoneCatalog} = Me.imports.settings.timeZoneCatalog;

const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const Utils = Me.imports.utils;
const {WidgetsData} = Me.imports.settings.WidgetsData;
const _ = Gettext.gettext;

var SubPage = GObject.registerClass({
    GTypeName: 'OrbitzWidgetsSubPage',
    Properties: {
        'widget-index': GObject.ParamSpec.int(
            'widget-index', 'widget-index', 'widget-index',
            GObject.ParamFlags.READWRITE,
            0, GLib.MAXINT32, 0),
        'element-index': GObject.ParamSpec.int(
            'element-index', 'element-index', 'element-index',
            GObject.ParamFlags.READWRITE,
            0, GLib.MAXINT32, 0),
    },
}, class AzClockSubPage extends Adw.PreferencesPage {
    _init(settings, params) {
        super._init({
            ...params,
        });

        this.children = [];
        this._settings = settings;

        this.topGroup = new Adw.PreferencesGroup();
        this.add(this.topGroup);

        const isWidget = this.element_index === 0;

        const nameEntry = new Gtk.Entry({
            valign: Gtk.Align.CENTER,
            width_chars: 20,
            text: this.getClockElementData('Name'),
        });
        nameEntry.connect('changed', () => {
            this.setClockElementData('Name', nameEntry.get_text());
            this.title = nameEntry.get_text();
        });
        const nameRow = new Adw.ActionRow({
            title: isWidget ? _('Widget Name') : _('Element Name'),
            activatable_widget: nameEntry,
        });
        nameRow.add_suffix(nameEntry);
        this.topGroup.add(nameRow);

        if (!isWidget) {
            const firstElementIndex = 1;
            const lastElementIndex = WidgetsData.data[this.widget_index].length - 1;
            const navGroup = new Adw.PreferencesGroup();
            this.add(navGroup);

            const navRow = new Adw.ActionRow({
                title: _('Move Element'),
            });
            navGroup.add(navRow);

            const navBox = new Gtk.Box({
                css_classes: ['linked'],
                spacing: 0,
            });
            navRow.add_suffix(navBox);

            const downButton = new Gtk.Button({
                icon_name: 'go-down-symbolic',
                valign: Gtk.Align.CENTER,
                sensitive: this.element_index !== lastElementIndex,
                tooltip_text: _('Move element down in order'),
            });
            navBox.append(downButton);
            downButton.connect('clicked', () => this.element_index++);

            const upButton = new Gtk.Button({
                icon_name: 'go-up-symbolic',
                valign: Gtk.Align.CENTER,
                sensitive: this.element_index !== firstElementIndex,
                tooltip_text: _('Move element up in order'),
            });
            navBox.append(upButton);
            upButton.connect('clicked', () => this.element_index--);
        }
    }

    createComboRow(title, setting) {
        const value = this.getClockElementData(setting);
        const stringList = new Gtk.StringList();
        stringList.append(_('Start'));
        stringList.append(_('Center'));
        stringList.append(_('End'));

        let selectedValue = 0;

        if (value === 'Start')
            selectedValue = 0;
        else if (value === 'Center')
            selectedValue = 1;
        else if (value === 'End')
            selectedValue = 2;

        const comboRow = new Adw.ComboRow({
            title: _(title),
            model: stringList,
            selected: selectedValue,
        });
        comboRow.connect('notify::selected', widget => {
            this.setClockElementData(setting, widget.selected_item.string);
        });
        return comboRow;
    }

    createShadowExpanderRow(title, elementType) {
        const shadowEnabled = this.getClockElementData(`${elementType}Enabled`, 'bool');
        const shadowExpanderRow = new Adw.ExpanderRow({
            title: _(title),
            show_enable_switch: true,
            expanded: false,
            enable_expansion: shadowEnabled,
        });
        shadowExpanderRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData(`${elementType}Enabled`, widget.enable_expansion);
        });

        const shadowColorRow = this.createColorRow(_('Shadow Color'), `${elementType}Color`);
        shadowExpanderRow.add_row(shadowColorRow);
        const xOffsetRow = this.createSpinRow(_('Shadow X Offset'), `${elementType}X`, -15, 15);
        shadowExpanderRow.add_row(xOffsetRow);
        const yOffsetRow = this.createSpinRow(_('Shadow Y Offset'), `${elementType}Y`, -15, 15);
        shadowExpanderRow.add_row(yOffsetRow);
        const spreadRow = this.createSpinRow(_('Shadow Spread'), `${elementType}Spread`, 0, 15);
        shadowExpanderRow.add_row(spreadRow);
        const blurRow = this.createSpinRow(_('Shadow Blur'), `${elementType}Blur`, 0, 15);
        shadowExpanderRow.add_row(blurRow);
        return shadowExpanderRow;
    }

    createSpinRow(title, setting, lower, upper, digits = 0) {
        const value = this.getClockElementData(setting, 'int') || 0;
        const spinButton = new Gtk.SpinButton({
            adjustment: new Gtk.Adjustment({
                lower, upper, step_increment: 1, page_increment: 1, page_size: 0,
            }),
            climb_rate: 1,
            digits,
            numeric: true,
            valign: Gtk.Align.CENTER,
        });
        spinButton.set_value(value);
        spinButton.connect('value-changed', widget => {
            this.setClockElementData(setting, widget.get_value());
        });
        const spinRow = new Adw.ActionRow({
            title: _(title),
            activatable_widget: spinButton,
        });

        spinRow.setValue = newValue => {
            spinButton.set_value(newValue);
        };

        spinRow.add_suffix(spinButton);
        return spinRow;
    }

    createColorRow(title, setting) {
        const value = this.getClockElementData(setting);
        let rgba = new Gdk.RGBA();
        rgba.parse(value ?? '');
        const colorButton = new Gtk.ColorButton({
            rgba,
            use_alpha: true,
            valign: Gtk.Align.CENTER,
        });
        colorButton.connect('color-set', widget => {
            this.setClockElementData(setting, widget.get_rgba().to_string());
        });
        const colorRow = new Adw.ActionRow({
            title: _(title),
            activatable_widget: colorButton,
        });
        colorRow.add_suffix(colorButton);

        colorRow.setValue = newValue => {
            rgba = new Gdk.RGBA();
            rgba.parse(newValue);
            colorButton.set_rgba(rgba);
        };
        return colorRow;
    }

    createTimeZoneRow() {
        const timeZoneRow = new Adw.ActionRow({title: _('Time Zone'), activatable: true});

        const timeZoneExpanderRow = new Adw.ExpanderRow({
            title: _('Override Time Zone'),
            show_enable_switch: true,
            expanded: this.getClockElementData('TimeZoneOverrideEnabled', 'bool'),
            enable_expansion: this.getClockElementData('TimeZoneOverrideEnabled', 'bool'),
        });
        timeZoneExpanderRow.connect('notify::enable-expansion', widget => {
            this.setClockElementData('TimeZoneOverrideEnabled', widget.enable_expansion);
        });
        timeZoneExpanderRow.add_row(timeZoneRow);

        const selector = TimeZoneCatalog.createDropDown(GLib, Gtk,
            this.getClockElementData('TimeZoneOverride') || 'UTC');
        selector.set_size_request(390, -1);
        selector.connect('notify::selected', widget => {
            const selected = widget.orbitzTimeZones[widget.selected];
            if (!selected) return;
            this.setClockElementData('TimeZoneOverride', selected.identifier);
            this.setClockElementData('TimeZone', `${selected.city} • ${selected.region}`);
        });
        timeZoneRow.add_suffix(selector);

        return timeZoneExpanderRow;
    }

    getClockElementData(elementType, parseType) {
        return Utils.getData(WidgetsData.data,
            this.widget_index, this.element_index, elementType, parseType) || null;
    }

    setClockElementData(elementType, newValue) {
        const changedData = this.getChangedData(elementType);
        const pending = this._settings.get_value('changed-data').deep_unpack();
        // Catalog callbacks may arrive before the Shell consumes an add/delete event.
        if (pending.WidgetIndex === changedData.WidgetIndex) {
            for (const flag of ['ElementAdded', 'ElementDeleted', 'ElementIndexChanged']) {
                if (pending[flag] === 'true') changedData[flag] = 'true';
            }
        }
        this._settings.set_value('changed-data', new GLib.Variant('a{ss}', changedData));
        Utils.setData(Utils.unpackData(this._settings), this.widget_index,
            this.element_index, elementType, newValue);

        WidgetsData.data = this._settings.get_value('widget-data').deep_unpack();
    }

    getChangedData(elementType) {
        return {
            'WidgetIndex': this.widget_index.toString(),
            'ElementIndex': this.element_index.toString(),
            'ElementType': elementType,
        };
    }

    add(page) {
        this.children.push(page);
        super.add(page);
    }
});

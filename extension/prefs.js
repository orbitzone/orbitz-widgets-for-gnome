/* eslint-disable jsdoc/require-jsdoc */
const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const {Adw, Gdk, Gio, GLib, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const Utils = Me.imports.utils;
const Language = Me.imports.uiLanguage.Language;
const _ = Language.tr;

const {AboutPage} = Me.imports.settings.AboutPage;
const {DialogWindow} = Me.imports.settings.DialogWindow;
const {WidgetsData} = Me.imports.settings.WidgetsData;
const {WidgetSettingsPage} = Me.imports.settings.WidgetSettingsPage;

const WidgetType = {
    DIGITAL: 0,
    ANALOG: 1,
    CUSTOM: 2,
    GROUP: 3,
    CURRENCY: 4,
};

function init() {
    ExtensionUtils.initTranslations();
}

function fillPreferencesWindow(window) {
    const iconTheme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default());
    if (!iconTheme.get_search_path().includes(`${Me.path}/media`))
        iconTheme.add_search_path(`${Me.path}/media`);

    const settings = ExtensionUtils.getSettings();
    Language.configure(settings);

    const widgetsData = new WidgetsData(settings.get_value('widget-data').deep_unpack());

    const homePage = new HomePage(settings);
    window.add(homePage);

    const aboutPage = new AboutPage();
    window.add(aboutPage);

    window.connect('close-request', () => {
        widgetsData.destroy();
    });
}

var HomePage = GObject.registerClass({GTypeName: 'OrbitzWidgetsHomePage'},
class azClockHomePage extends Adw.PreferencesPage {
    _init(settings) {
        super._init(Language.properties(this, {
            title: Language.tr('settings.title'),
            icon_name: 'preferences-system-symbolic',
            name: 'HomePage',
        }));

        Language.configure(settings);
        this._settings = settings;
        Language.set(this, 'title', Language.msg('settings.title'));
        this._widgetRows = [];

        const addClockButton = Language.widget(Gtk.Button, {
            halign: Gtk.Align.START,
            icon_name: 'list-add-symbolic',
            valign: Gtk.Align.CENTER,
            css_classes: ['suggested-action'],
            label: Language.msg('settings.add_widget'),
        });
        addClockButton.connect('clicked', () => {
            const dialog = new AddWidgetsDialog(this._settings, this);
            dialog.show();
            dialog.connect('response', (_w, response) => {
                if (response === Gtk.ResponseType.APPLY) {
                    this.createRows();
                    dialog.destroy();
                }
            });
        });
        this.clocksGroup = new Adw.PreferencesGroup();
        this.add(this.clocksGroup);
        const toolbar = Language.widget(Gtk.Box, {spacing: 8, halign: Gtk.Align.START});
        const languages = Language.widget(Gtk.DropDown, {model: Gtk.StringList.new(['Português (Brasil)', 'English (United States)']),
            selected: Language.getLocale() === 'en-US' ? 1 : 0});
        Language.set(languages, 'tooltip_text', Language.msg('settings.language'));
        languages.connect('notify::selected', () => settings.set_string('ui-language', languages.selected === 1 ? 'en-US' : 'pt-BR'));
        const unwatch = Language.watch(locale => { languages.selected = locale === 'en-US' ? 1 : 0; });
        this.connect('unrealize', unwatch);
        toolbar.append(languages);toolbar.append(addClockButton);
        this.clocksGroup.set_header_suffix(toolbar);
        this.createRows();
    }

    get settings() {
        return this._settings;
    }

    createRows() {
        for (let row of this._widgetRows) {
            this.clocksGroup.remove(row);
            row = null;
        }
        this._widgetRows = [];

        const widgetsData = WidgetsData.data;

        const grouping = Me.imports.grouping;
        this._rowParents = new Map();
        for (const [parent, members] of grouping.planGroups(widgetsData))
            for (const child of members) this._rowParents.set(child, widgetsData[parent][0].Name);
        for (const i of grouping.settingsOrder(widgetsData)) {
            const widgetRow = this._createWidgetRow(i);
            this.clocksGroup.add(widgetRow);
        }
    }

    _createWidgetRow(widgetIndex) {
        const widgetData = WidgetsData.data[widgetIndex];
        const widgetSettings = widgetData[0];
        const parentName = this._rowParents.get(widgetIndex);
        // Data for the widget is always the first element in array.
        const widgetRow = new WidgetRow(this, {
            title: `<b>${parentName !== undefined ? '↳ ' : widgetSettings.Box_IsGroup === 'true' ? '▦ ' : ''}${GLib.markup_escape_text(widgetSettings['Name'], -1)}</b>`,
            widget_index: widgetIndex,
            subtitle: parentName === undefined ? '' : `Subwidget de ${GLib.markup_escape_text(parentName, -1)}`,
        });
        widgetRow.use_markup = true;

        widgetRow.connect('drag-drop-done', (_widget, oldIndex, newIndex) => {
            const modifiedWidgetData = this._settings.get_value('widget-data').deep_unpack();

            const movedData = modifiedWidgetData.splice(oldIndex, 1)[0];
            modifiedWidgetData.splice(newIndex, 0, movedData);

            this._settings.set_value('changed-data', new GLib.Variant('a{ss}', {
                'WidgetIndex': oldIndex.toString(),
                'WidgetIndexNew': newIndex.toString(),
                'WidgetIndexChanged': 'true',
            }));

            this._settings.set_value('widget-data', new GLib.Variant('aaa{ss}', modifiedWidgetData));
            WidgetsData.data = modifiedWidgetData;
            this.createRows();
        });

        this._widgetRows.push(widgetRow);
        return widgetRow;
    }
});

var WidgetRow = GObject.registerClass({
    GTypeName: 'OrbitzWidgetsWidgetRow',
    Properties: {
        'widget-index': GObject.ParamSpec.int(
            'widget-index', 'widget-index', 'widget-index',
            GObject.ParamFlags.READWRITE,
            0, GLib.MAXINT32, 0),
    },
    Signals: {
        'drag-drop-done': {param_types: [GObject.TYPE_UINT, GObject.TYPE_UINT]},
        'drag-drop-prepare': {},
    },
}, class AzClockWidgetRow extends Adw.ActionRow {
    _init(homePage, params) {
        super._init(Language.properties(this, {
            activatable: true,
            ...params,
        }));

        this._params = params;
        this._settings = homePage.settings;
        this._homePage = homePage;

        const widgetsData = WidgetsData.data;

        const widgetData = widgetsData[this.widget_index];
        const widgetSettings = widgetData[0];

        this.dragIcon = Language.widget(Gtk.Image, {
            gicon: Gio.icon_new_for_string('list-drag-handle-symbolic'),
            pixel_size: 12,
        });
        this.add_prefix(this.dragIcon);

        const dragSource = Language.widget(Gtk.DragSource, {actions: Gdk.DragAction.MOVE});
        this.add_controller(dragSource);

        const dropTarget = Language.widget(Gtk.DropTargetAsync, {actions: Gdk.DragAction.MOVE});
        this.add_controller(dropTarget);

        dragSource.connect('drag-begin', (self, gdkDrag) => {
            this._dragParent = self.get_widget().get_parent();
            this._dragParent.dragRow = this;

            const alloc = this.get_allocation();
            const dragWidget = self.get_widget().createDragRow(alloc);
            this._dragParent.dragWidget = dragWidget;

            const icon = Gtk.DragIcon.get_for_drag(gdkDrag);
            icon.set_child(dragWidget);

            gdkDrag.set_hotspot(this._dragParent.dragX, this._dragParent.dragY);
        });

        dragSource.connect('prepare', (self, x, y) => {
            this.emit('drag-drop-prepare');

            this.set_state_flags(Gtk.StateFlags.NORMAL, true);
            const parent = self.get_widget().get_parent();
            // store drag start cursor location
            parent.dragX = x;
            parent.dragY = y;
            return new Gdk.ContentProvider();
        });

        dragSource.connect('drag-end', (_self, _gdkDrag, _deleteData) => {
            this._dragParent.dragWidget = null;
            this._dragParent.drag_unhighlight_row();
            _deleteData = true;
        });

        dropTarget.connect('drag-enter', self => {
            const parent = self.get_widget().get_parent();
            const widget = self.get_widget();

            parent.drag_highlight_row(widget);
        });

        dropTarget.connect('drag-leave', self => {
            const parent = self.get_widget().get_parent();
            parent.drag_unhighlight_row();
        });

        dropTarget.connect('drop', (_self, gdkDrop) => {
            const parent = this.get_parent();
            const dragRow = parent.dragRow; // The row being dragged.
            const dragRowStartIndex = dragRow.widget_index;
            const dragRowNewIndex = this.widget_index;

            gdkDrop.read_value_async(AzClockWidgetRow, 1, null, () => gdkDrop.finish(Gdk.DragAction.MOVE));

            // The drag row hasn't moved
            if (dragRowStartIndex === dragRowNewIndex)
                return true;

            this.emit('drag-drop-done', dragRowStartIndex, dragRowNewIndex);
            return true;
        });

        const openWidgetSettings = () => {
            const widgetSettingsWindow = new WidgetSettingsPage(this._settings, this._homePage, {
                title: widgetSettings['Name'],
                widget_index: this.widget_index,
                transient_for: this.get_root(),
                modal: true,
                resizable: false,
                default_width: 900,
                default_height: 700,
            });
            widgetSettingsWindow.connect('notify::title', () => (this.title = `<b>${GLib.markup_escape_text(widgetSettingsWindow.title, -1)}</b>`));
            widgetSettingsWindow.present();
        };
        this.connect('activated', openWidgetSettings);

        const configureButton = Language.widget(Gtk.Button, {
            label: Language.msg('settings.configure'),
            has_frame: false,
            valign: Gtk.Align.CENTER,
        });
        configureButton.connect('clicked', openWidgetSettings);
        this.add_suffix(configureButton);

        const goNextImage = Language.widget(Gtk.Image, {
            gicon: Gio.icon_new_for_string('go-next-symbolic'),
            halign: Gtk.Align.END,
            valign: Gtk.Align.CENTER,
            hexpand: false,
            vexpand: false,
        });
        this.add_suffix(goNextImage);
    }

    createDragRow(alloc) {
        const dragWidget = new Gtk.ListBox();
        dragWidget.set_size_request(alloc.width, -1);

        const dragRow = new WidgetRow(this._homePage, this._params);
        dragWidget.append(dragRow);
        dragWidget.drag_highlight_row(dragRow);

        return dragWidget;
    }
});

var AddWidgetsDialog = GObject.registerClass({GTypeName: 'OrbitzWidgetsAddWidgetsDialog'},
class AzClockAddWidgetsDialog extends DialogWindow {
    _init(settings, parent) {
        super._init(_('settings.add_widget_label'), parent);
        this._settings = settings;
        this.search_enabled = false;
        this.set_default_size(550, -1);

        this.pageGroup.title = _('settings.preset_widgets');
        this.pageGroup.add(this.addPresetWidget(_('settings.digital_clock_widget'), WidgetType.DIGITAL));
        this.pageGroup.add(this.addPresetWidget(_('settings.analog_clock_widget'), WidgetType.ANALOG));
        this.pageGroup.add(this.addPresetWidget(_('settings.currency_converter'), WidgetType.CURRENCY,
            _('settings.show_a_daily_brl_reference_rate_and_choose_the_target_currency')));
        this.pageGroup.add(this.addPresetWidget('Widget pai · painel', WidgetType.GROUP, 'Alinha subwidgets automaticamente'));
        this.pageGroup.add(this.addPresetWidget(_('settings.custom_widget'), WidgetType.CUSTOM,
            _('settings.add_your_own_custom_elements')));

        const data = WidgetsData.data;
        this.cloneGroup = Language.widget(Adw.PreferencesGroup, {
            title: Language.msg('settings.clone_existing_widget'),
        });
        this.cloneGroup.use_markup = true;
        this.page.add(this.cloneGroup);

        for (let i = 0; i < data.length; i++)
            this.cloneGroup.add(this.addPresetWidget(GLib.markup_escape_text(data[i][0]['Name'], -1), data[i]));
    }

    addPresetWidget(title, widgetType, subtitle) {
        const addButton = Language.widget(Gtk.Button, {
            icon_name: 'list-add-symbolic',
            valign: Gtk.Align.CENTER,
        });

        addButton.connect('clicked', () => {
            const data = this._settings.get_value('widget-data').deep_unpack();
            if (widgetType === WidgetType.DIGITAL)
                data.push(Utils.DigitalClockSettings);
            else if (widgetType === WidgetType.ANALOG)
                data.push(Utils.AnalogClockSettings);
            else if (widgetType === WidgetType.CUSTOM)
                data.push(Utils.EmptyWidgetSettings);
            else if (widgetType === WidgetType.GROUP) {
                const group = JSON.parse(JSON.stringify(Utils.EmptyWidgetSettings));
                group[0] = {...group[0], Name: 'Sistema', Widget_Id: GLib.uuid_string_random(), Box_IsGroup: 'true', Group_Columns: '1', Box_Width: '320', Box_Padding: '16', Box_Spacing: '8', Box_BackgroundEnabled: 'true', Box_BackgroundColor: 'rgba(0,0,0,0.2)', Box_BorderEnabled: 'true', Box_BorderWidth: '3', Box_BorderColor: 'rgb(255,255,255)', Box_BorderRadius: '20'};
                data.push(group);
            } else if (widgetType === WidgetType.CURRENCY) {
                const widget = JSON.parse(JSON.stringify(Utils.CurrencyWidgetSettings));
                widget[0].Widget_Id = GLib.uuid_string_random();
                const script = GLib.build_filenamev([GLib.get_user_data_dir(), 'orbitz-widgets', 'collectors', 'currency-widget.py']);
                widget[1].Text_Command = `/usr/bin/python3 ${GLib.shell_quote(script)} --quote USD`;
                data.push(widget);
            } else {
                const clone = JSON.parse(JSON.stringify(widgetType));
                clone[0].Widget_Id = GLib.uuid_string_random();
                clone[0].Parent_Id = '';
                data.push(clone);
            }

            this._settings.set_value('changed-data', new GLib.Variant('a{ss}', {
                'WidgetIndex': (data.length - 1).toString(),
                'WidgetAdded': 'true',
            }));

            this._settings.set_value('widget-data', new GLib.Variant('aaa{ss}', data));
            WidgetsData.data = data;
            this.emit('response', Gtk.ResponseType.APPLY);
        });

        const row = Language.widget(Adw.ActionRow, {
            subtitle: subtitle ?? '',
            title,
            activatable_widget: addButton,
        });

        row.add_suffix(addButton);
        return row;
    }
});


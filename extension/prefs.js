/* eslint-disable jsdoc/require-jsdoc */
const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const {Adw, Gdk, Gio, GLib, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const Utils = Me.imports.utils;
const _ = Gettext.gettext;

const {AboutPage} = Me.imports.settings.AboutPage;
const {DialogWindow} = Me.imports.settings.DialogWindow;
const {WidgetsData} = Me.imports.settings.WidgetsData;
const {WidgetSettingsPage} = Me.imports.settings.WidgetSettingsPage;

const WidgetType = {
    DIGITAL: 0,
    ANALOG: 1,
    CUSTOM: 2,
};

function init() {
    ExtensionUtils.initTranslations();
}

function fillPreferencesWindow(window) {
    const iconTheme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default());
    if (!iconTheme.get_search_path().includes(`${Me.path}/media`))
        iconTheme.add_search_path(`${Me.path}/media`);

    const settings = ExtensionUtils.getSettings();

    const widgetsData = new WidgetsData(settings.get_value('widget-data').deep_unpack());

    const homePage = new HomePage(settings);
    window.add(homePage);

    const aboutPage = new AboutPage();
    window.add(aboutPage);

    window.connect('close-request', () => {
        widgetsData.destroy();
    });
}

var HomePage = GObject.registerClass(
class azClockHomePage extends Adw.PreferencesPage {
    _init(settings) {
        super._init({
            title: _('Settings'),
            icon_name: 'preferences-system-symbolic',
            name: 'HomePage',
        });

        this._settings = settings;
        this._widgetRows = [];

        const addClockButton = new Gtk.Button({
            halign: Gtk.Align.START,
            icon_name: 'list-add-symbolic',
            valign: Gtk.Align.CENTER,
            css_classes: ['suggested-action'],
            label: _('Add Widget...'),
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
        this.clocksGroup.set_header_suffix(addClockButton);
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

        for (let i = 0; i < widgetsData.length; i++) {
            const widgetRow = this._createWidgetRow(i);
            this.clocksGroup.add(widgetRow);
        }
    }

    _createWidgetRow(widgetIndex) {
        const widgetData = WidgetsData.data[widgetIndex];
        const widgetSettings = widgetData[0];
        // Data for the widget is always the first element in array.
        const widgetRow = new WidgetRow(this, {
            title: `<b>${widgetSettings['Name']}</b>`,
            widget_index: widgetIndex,
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
        super._init({
            activatable: true,
            ...params,
        });

        this._params = params;
        this._settings = homePage.settings;
        this._homePage = homePage;

        const widgetsData = WidgetsData.data;

        const widgetData = widgetsData[this.widget_index];
        const widgetSettings = widgetData[0];

        this.dragIcon = new Gtk.Image({
            gicon: Gio.icon_new_for_string('list-drag-handle-symbolic'),
            pixel_size: 12,
        });
        this.add_prefix(this.dragIcon);

        const dragSource = new Gtk.DragSource({actions: Gdk.DragAction.MOVE});
        this.add_controller(dragSource);

        const dropTarget = new Gtk.DropTargetAsync({actions: Gdk.DragAction.MOVE});
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
            const dragRowStartIndex = dragRow.get_index();
            const dragRowNewIndex = this.get_index();

            gdkDrop.read_value_async(AzClockWidgetRow, 1, null, () => gdkDrop.finish(Gdk.DragAction.MOVE));

            // The drag row hasn't moved
            if (dragRowStartIndex === dragRowNewIndex)
                return true;

            this.emit('drag-drop-done', dragRowStartIndex, dragRowNewIndex);
            return true;
        });

        this.connect('activated', () => {
            const widgetSettingsWindow = new WidgetSettingsPage(this._settings, this._homePage, {
                title: widgetSettings['Name'],
                widget_index: this.widget_index,
                transient_for: this.get_root(),
                modal: true,
                resizable: false,
                default_width: 900,
                default_height: 700,
            });
            widgetSettingsWindow.connect('notify::title', () => (this.title = `<b>${widgetSettingsWindow.title}</b>`));
            widgetSettingsWindow.present();
        });

        const configureLabel = new Gtk.Label({
            label: _('Configure'),
            halign: Gtk.Align.END,
            valign: Gtk.Align.CENTER,
            hexpand: false,
            vexpand: false,
        });
        this.add_suffix(configureLabel);

        const goNextImage = new Gtk.Image({
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

var AddWidgetsDialog = GObject.registerClass(
class AzClockAddWidgetsDialog extends DialogWindow {
    _init(settings, parent) {
        super._init(_('Add Widget'), parent);
        this._settings = settings;
        this.search_enabled = false;
        this.set_default_size(550, -1);

        this.pageGroup.title = _('Preset Widgets');
        this.pageGroup.add(this.addPresetWidget(_('Digital Clock Widget'), WidgetType.DIGITAL));
        this.pageGroup.add(this.addPresetWidget(_('Analog Clock Widget'), WidgetType.ANALOG));
        this.pageGroup.add(this.addPresetWidget(_('Custom Widget'), WidgetType.CUSTOM,
            _('Add your own custom elements')));

        const data = WidgetsData.data;
        this.cloneGroup = new Adw.PreferencesGroup({
            title: _('Clone existing Widget'),
        });
        this.cloneGroup.use_markup = true;
        this.page.add(this.cloneGroup);

        for (let i = 0; i < data.length; i++)
            this.cloneGroup.add(this.addPresetWidget(`${data[i][0]['Name']}`, data[i]));
    }

    addPresetWidget(title, widgetType, subtitle) {
        const addButton = new Gtk.Button({
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
            else
                data.push(widgetType);

            this._settings.set_value('changed-data', new GLib.Variant('a{ss}', {
                'WidgetIndex': (data.length - 1).toString(),
                'WidgetAdded': 'true',
            }));

            this._settings.set_value('widget-data', new GLib.Variant('aaa{ss}', data));
            WidgetsData.data = data;
            this.emit('response', Gtk.ResponseType.APPLY);
        });

        const row = new Adw.ActionRow({
            subtitle: subtitle ?? '',
            title,
            activatable_widget: addButton,
        });

        row.add_suffix(addButton);
        return row;
    }
});


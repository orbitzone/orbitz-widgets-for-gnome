const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const {Adw, GLib, GObject, Gtk} = imports.gi;

const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Gettext.gettext;

const {CommandLabelSubPage} = Me.imports.settings.CommandLabelSubPage;
const {DialogWindow} = Me.imports.settings.DialogWindow;
const {DigitalClockSubPage} = Me.imports.settings.DigitalClockSubPage;
const {AnalogClockSubPage} = Me.imports.settings.AnalogClockSubPage;
const {TextLabelSubPage} = Me.imports.settings.TextLabelSubPage;
const {WidgetsData} = Me.imports.settings.WidgetsData;
const {WidgetSubPage} = Me.imports.settings.WidgetSubPage;
const Utils = Me.imports.utils;

const ElementType = {
    DATE: 0,
    TIME: 1,
    ANALOG: 2,
    TEXT: 3,
    COMMAND: 4,
};

var WidgetSettingsPage = GObject.registerClass({
    Properties: {
        'title': GObject.ParamSpec.string(
            'title', 'title', 'title',
            GObject.ParamFlags.READWRITE,
            ''),
        'widget-index': GObject.ParamSpec.int(
            'widget-index', 'widget-index', 'widget-index',
            GObject.ParamFlags.READWRITE,
            0, GLib.MAXINT32, 0),
    },
}, class AzClockWidgetSettingsPage extends Adw.ApplicationWindow {
    _init(settings, homePage, params) {
        super._init({
            ...params,
        });
        this._homePage = homePage;
        this._settings = settings;

        const widgetData = WidgetsData.data[this.widget_index];

        // The window content widget
        const mainLeaflet = new Adw.Leaflet();
        this.set_content(mainLeaflet);

        // The main content stack
        this._widgetElementsStack = new Gtk.Stack({
            transition_type: Gtk.StackTransitionType.CROSSFADE,
        });

        // Sidebar
        const sidebarBox = new Gtk.Box({
            orientation: Gtk.Orientation.VERTICAL,
        });
        const sidebarHeaderBar = new Adw.HeaderBar({
            title_widget: new Gtk.Label({label: _('Configure Widget')}),
            show_end_title_buttons: false,
        });
        sidebarBox.append(sidebarHeaderBar);
        const sidebarScrolledWindow = new Gtk.ScrolledWindow({
            vexpand: true,
            width_request: 200,
        });
        sidebarBox.append(sidebarScrolledWindow);
        mainLeaflet.append(sidebarBox);

        mainLeaflet.append(new Gtk.Separator({orientation: Gtk.Orientation.VERTICAL}));

        // Sidebar List Box
        this._sidebarListBox = new Gtk.ListBox({
            css_classes: ['navigation-sidebar'],
        });
        sidebarScrolledWindow.set_child(this._sidebarListBox);
        this._sidebarListBox.connect('row-selected', (_self, row) => {
            if (!row)
                return;

            const {settingPage} = row;
            this._contentHeaderBar.title_widget.label = settingPage.title;
            this._widgetElementsStack.set_visible_child(settingPage);
            deleteElementButton.visible = row.get_index() !== 0;
        });
        this._sidebarListBox.set_header_func(row => {
            if (row.get_index() === 1) {
                const separator = new Gtk.Separator({
                    orientation: Gtk.Orientation.HORIZONTAL,
                });
                row.set_header(separator);
            } else {
                row.set_header(null);
            }
        });

        // Populate sidebar and main content stack
        for (let i = 0; i < widgetData.length; i++)
            this.createWidgetSettingsPage(widgetData[i], i);

        // Content ToolbarView
        this._contentBox = new Gtk.Box({
            orientation: Gtk.Orientation.VERTICAL,
            hexpand: true,
            vexpand: true,
        });
        this._contentHeaderBar = new Adw.HeaderBar({
            title_widget: new Gtk.Label({label: widgetData[0]['Name']}),
        });
        this._contentBox.append(this._contentHeaderBar);

        const actionBar = new Gtk.ActionBar({
            valign: Gtk.Align.END,
            vexpand: true,
        });
        const deleteWidgetButton = new Gtk.Button({
            halign: Gtk.Align.START,
            valign: Gtk.Align.CENTER,
            hexpand: false,
            label: _('Delete Widget'),
        });
        deleteWidgetButton.connect('clicked', () => {
            const dialog = new Gtk.MessageDialog({
                text: `<b>${GLib.markup_escape_text(_('Delete %s?').format(widgetData[0]['Name']), -1)}</b>`,
                secondary_text: _('Please confirm you wish to delete %s?').format(widgetData[0]['Name']),
                use_markup: true,
                buttons: Gtk.ButtonsType.YES_NO,
                message_type: Gtk.MessageType.WARNING,
                transient_for: this.get_root(),
                modal: true,
            });
            dialog.connect('response', (widget, response) => {
                if (response === Gtk.ResponseType.YES) {
                    const modifiedWidgetData = this._settings.get_value('widget-data').deep_unpack();
                    modifiedWidgetData.splice(this.widget_index, 1);
                    this._settings.set_value('changed-data', new GLib.Variant('a{ss}', {
                        'WidgetIndex': this.widget_index.toString(),
                        'WidgetDeleted': 'true',
                    }));
                    this._settings.set_value('widget-data', new GLib.Variant('aaa{ss}', modifiedWidgetData));
                    WidgetsData.data = modifiedWidgetData;
                    this.close();
                    this._homePage.createRows();
                }
                dialog.destroy();
            });
            dialog.show();
        });
        const deleteElementButton = new Gtk.Button({
            halign: Gtk.Align.START,
            valign: Gtk.Align.CENTER,
            hexpand: false,
            label: _('Delete Element'),
            visible: false,
        });
        deleteElementButton.connect('clicked', () => {
            const selectedRow = this._sidebarListBox.get_selected_row();
            const elementIndex = selectedRow.get_index();

            if (elementIndex === 0)
                return;

            const name = WidgetsData.data[this.widget_index][elementIndex]['Name'];
            const dialog = new Gtk.MessageDialog({
                text: `<b>${GLib.markup_escape_text(_('Delete %s?').format(name), -1)}</b>`,
                secondary_text: _('Please confirm you wish to delete this element from %s.').format(name),
                use_markup: true,
                buttons: Gtk.ButtonsType.YES_NO,
                message_type: Gtk.MessageType.WARNING,
                transient_for: this.get_root(),
                modal: true,
            });
            dialog.connect('response', (_widget, response) => {
                if (response === Gtk.ResponseType.YES) {
                    const data = settings.get_value('widget-data').deep_unpack();
                    data[this.widget_index].splice(elementIndex, 1);

                    settings.set_value('changed-data', new GLib.Variant('a{ss}', {
                        'WidgetIndex': this.widget_index.toString(),
                        'ElementDeleted': 'true',
                    }));

                    settings.set_value('widget-data', new GLib.Variant('aaa{ss}', data));
                    WidgetsData.data = data;

                    this._repopulatePages(0);
                }
                dialog.destroy();
            });
            dialog.show();
        });

        const addButton = new Gtk.Button({
            valign: Gtk.Align.CENTER,
            label: _('Add Element'),
        });
        addButton.connect('clicked', () => {
            const dialog = new AddElementsDialog(this._settings, this, {
                widget_index: this.widget_index,
                widget_title: this.title,
            });
            dialog.show();
            dialog.connect('response', (_w, response) => {
                if (response === Gtk.ResponseType.APPLY) {
                    this._repopulatePages(dialog.elementIndex);
                    dialog.destroy();
                }
            });
        });
        actionBar.pack_end(addButton);
        actionBar.pack_end(deleteElementButton);
        actionBar.pack_start(deleteWidgetButton);

        this._contentBox.append(this._widgetElementsStack);
        this._contentBox.append(actionBar);
        mainLeaflet.append(this._contentBox);
    }

    _repopulatePages(selectRowIndex = null) {
        this._widgetElementsStack.visible = false;

        // remove all from sidebar
        let child = this._sidebarListBox.get_first_child();
        while (child !== null) {
            const next = child.get_next_sibling();
            this._sidebarListBox.remove(child);
            child = next;
        }

        // remove all from content stack
        child = this._widgetElementsStack.get_first_child();
        while (child !== null) {
            const next = child.get_next_sibling();
            this._widgetElementsStack.remove(child);
            child = next;
        }

        // create new pages
        const widgetData = WidgetsData.data[this.widget_index];
        for (let i = 0; i < widgetData.length; i++)
            this.createWidgetSettingsPage(widgetData[i], i);

        // select a row if set
        if (selectRowIndex !== null) {
            const row = this._sidebarListBox.get_row_at_index(selectRowIndex);
            this._sidebarListBox.select_row(row);
        }
        this._widgetElementsStack.visible = true;
    }

    createWidgetSettingsPage(elementData, elementIndex) {
        const title = elementData['Name'];
        const listBoxRowLabel = new Gtk.Label({
            halign: Gtk.Align.START,
            hexpand: true,
            label: title,
            max_width_chars: 25,
            wrap: true,
        });
        const listBoxRow = new Gtk.ListBoxRow({
            child: listBoxRowLabel,
        });
        this._sidebarListBox.append(listBoxRow);

        let settingPageConstructor;
        if (elementData['Widget_Type'])
            settingPageConstructor = WidgetSubPage;
        else if (elementData['Element_Type'] === 'Digital_Clock')
            settingPageConstructor = DigitalClockSubPage;
        else if (elementData['Element_Type'] === 'Analog_Clock')
            settingPageConstructor = AnalogClockSubPage;
        else if (elementData['Element_Type'] === 'Text_Label')
            settingPageConstructor = TextLabelSubPage;
        else if (elementData['Element_Type'] === 'Command_Label')
            settingPageConstructor = CommandLabelSubPage;

        const settingPage = new settingPageConstructor(this._settings, {
            title,
            widget_index: this.widget_index,
            element_index: elementIndex,
        });
        this._widgetElementsStack.add_child(settingPage);

        settingPage.connect('notify::title', () => {
            if (elementIndex === 0)
                this.title = settingPage.title;

            listBoxRowLabel.label = settingPage.title;
            this._contentHeaderBar.title_widget.label = settingPage.title;
        });

        settingPage.connect('notify::element-index', () => {
            const newIndex = settingPage.element_index;
            const modifiedWidgetsData = this._settings.get_value('widget-data').deep_unpack();
            const modifiedWidgetData = modifiedWidgetsData[this.widget_index];

            const movedElement = modifiedWidgetData.splice(elementIndex, 1)[0];
            modifiedWidgetData.splice(newIndex, 0, movedElement);

            modifiedWidgetsData.splice(this.widget_index, 1, modifiedWidgetData);

            this._settings.set_value('changed-data', new GLib.Variant('a{ss}', {
                'WidgetIndex': this.widget_index.toString(),
                'ElementIndex': elementIndex.toString(),
                'ElementIndexNew': newIndex.toString(),
                'ElementIndexChanged': 'true',
            }));

            this._settings.set_value('widget-data', new GLib.Variant('aaa{ss}', modifiedWidgetsData));
            WidgetsData.data = modifiedWidgetsData;

            this._repopulatePages(newIndex);
        });
        listBoxRow.settingPage = settingPage;
    }
});

var AddElementsDialog = GObject.registerClass(
class AzClockAddElementsDialog extends DialogWindow {
    _init(settings, parent, params) {
        super._init(_('Add Element to %s').format(params.widget_title), parent, params);
        this._settings = settings;
        this.search_enabled = false;
        this.set_default_size(550, -1);

        this.pageGroup.title = _('Preset Elements');
        this.pageGroup.add(this.addPresetElement(_('Date Label'), ElementType.DATE));
        this.pageGroup.add(this.addPresetElement(_('Time Label'), ElementType.TIME));
        this.pageGroup.add(this.addPresetElement(_('Text Label'), ElementType.TEXT));
        this.pageGroup.add(this.addPresetElement(_('Command Label'), ElementType.COMMAND));
        this.pageGroup.add(this.addPresetElement(_('Analog Clock'), ElementType.ANALOG));

        const data = this._settings.get_value('widget-data').deep_unpack();
        this.cloneGroup = new Adw.PreferencesGroup({
            title: _('Clone existing Element'),
        });
        this.cloneGroup.use_markup = true;
        this.page.add(this.cloneGroup);

        for (let i = 0; i < data.length; i++) {
            for (let j = 1; j < data[i].length; j++)
                this.cloneGroup.add(this.addPresetElement(`${GLib.markup_escape_text(data[i][j]['Name'], -1)} <span font-size='small'><i>(${GLib.markup_escape_text(data[i][0]['Name'], -1)})</i></span>`, data[i][j]));
        }
    }

    addPresetElement(title, widgetType, subtitle) {
        const addButton = new Gtk.Button({
            icon_name: 'list-add-symbolic',
            valign: Gtk.Align.CENTER,
        });

        addButton.connect('clicked', () => {
            const data = this._settings.get_value('widget-data').deep_unpack();

            if (widgetType === ElementType.DATE)
                this.elementData = Utils.DigitalClockSettings[2];
            else if (widgetType === ElementType.TIME)
                this.elementData = Utils.DigitalClockSettings[1];
            else if (widgetType === ElementType.TEXT)
                this.elementData = Utils.TextLabel;
            else if (widgetType === ElementType.COMMAND)
                this.elementData = Utils.CommandLabel;
            else if (widgetType === ElementType.ANALOG)
                this.elementData = Utils.AnalogClockSettings[1];
            else
                this.elementData = widgetType;

            data[this.widget_index].push(this.elementData);

            this.elementIndex = data[this.widget_index].length - 1;

            this._settings.set_value('changed-data', new GLib.Variant('a{ss}', {
                'WidgetIndex': this.widget_index.toString(),
                'ElementAdded': 'true',
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


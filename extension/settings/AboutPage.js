const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();
const Language = Me.imports.uiLanguage.Language;

const {Adw, Gdk, Gio, GLib, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Language.tr;

const PROJECT_DESCRIPTION = Language.msg('settings.widgets_monitoring_calendar_and_notes_for_gnome');
const PROJECT_IMAGE = GLib.build_filenamev([Me.path, 'media', 'orbitz-logo.svg']);
const SettingsImport = Me.imports.settings.SettingsImport;

var AboutPage = GObject.registerClass({GTypeName: 'OrbitzWidgetsAboutPage'},
class AzClockAboutPage extends Adw.PreferencesPage {
    _init() {
        super._init(Language.properties(this, {
            title: Language.msg('settings.about'),
            icon_name: 'help-about-symbolic',
            name: 'AboutPage',
        }));

        // Project Logo, title, description-------------------------------------
        const projectHeaderGroup = new Adw.PreferencesGroup();
        const projectHeaderBox = Language.widget(Gtk.Box, {
            orientation: Gtk.Orientation.VERTICAL,
            hexpand: false,
            vexpand: false,
        });

        const projectImage = Language.widget(Gtk.Image, {
            margin_bottom: 5,
            gicon: new Gio.FileIcon({file: Gio.File.new_for_path(PROJECT_IMAGE)}),
            pixel_size: 100,
        });

        const projectTitleLabel = Language.widget(Gtk.Label, {
            label: Me.metadata.name,
            css_classes: ['title-1'],
            vexpand: true,
            valign: Gtk.Align.FILL,
        });

        const projectDescriptionLabel = Language.widget(Gtk.Label, {
            label: PROJECT_DESCRIPTION,
            hexpand: false,
            vexpand: false,
        });
        projectHeaderBox.append(projectImage);
        projectHeaderBox.append(projectTitleLabel);
        projectHeaderBox.append(projectDescriptionLabel);
        projectHeaderGroup.add(projectHeaderBox);

        this.add(projectHeaderGroup);
        // -----------------------------------------------------------------------

        // Extension/OS Info and Links Group------------------------------------------------
        const infoGroup = new Adw.PreferencesGroup();

        const projectVersionRow = Language.widget(Adw.ActionRow, {
            title: Language.msg('settings.orbitz_version'),
        });
        projectVersionRow.add_suffix(Language.widget(Gtk.Label, {
            label: Me.metadata['version-name'] || (Me.metadata.version === 1 ? '1.0' : Me.metadata.version.toString()),
            css_classes: ['dim-label'],
        }));
        infoGroup.add(projectVersionRow);

        if (Me.metadata.commit) {
            const commitRow = Language.widget(Adw.ActionRow, {
                title: Language.msg('settings.git_commit'),
            });
            commitRow.add_suffix(Language.widget(Gtk.Label, {
                label: Me.metadata.commit.toString(),
                css_classes: ['dim-label'],
            }));
            infoGroup.add(commitRow);
        }

        const gnomeVersionRow = Language.widget(Adw.ActionRow, {
            title: Language.msg('settings.gnome_version'),
        });
        gnomeVersionRow.add_suffix(Language.widget(Gtk.Label, {
            label: imports.misc.config.PACKAGE_VERSION.toString(),
            css_classes: ['dim-label'],
        }));
        infoGroup.add(gnomeVersionRow);

        const osRow = Language.widget(Adw.ActionRow, {
            title: Language.msg('settings.os_name'),
        });

        const name = GLib.get_os_info('NAME');
        const prettyName = GLib.get_os_info('PRETTY_NAME');

        osRow.add_suffix(Language.widget(Gtk.Label, {
            label: prettyName ? prettyName : name,
            css_classes: ['dim-label'],
        }));
        infoGroup.add(osRow);

        const sessionTypeRow = Language.widget(Adw.ActionRow, {
            title: Language.msg('settings.windowing_system'),
        });
        sessionTypeRow.add_suffix(Language.widget(Gtk.Label, {
            label: GLib.getenv('XDG_SESSION_TYPE') === 'wayland' ? 'Wayland' : 'X11',
            css_classes: ['dim-label'],
        }));
        infoGroup.add(sessionTypeRow);

        const projectRow = this._createLinkRow(Language.msg('settings.orbitz_on_github'), Me.metadata.url);
        infoGroup.add(projectRow);

        const authorRow = this._createLinkRow('Felipe Santiago · orbitzone', 'https://github.com/orbitzone');
        infoGroup.add(authorRow);

        this.add(infoGroup);
        // -----------------------------------------------------------------------

        // Save/Load Settings----------------------------------------------------------
        const settingsGroup = new Adw.PreferencesGroup();
        const settingsRow = Language.widget(Adw.ActionRow, {
            title: Language.msg('settings.orbitz_settings'),
        });
        const loadButton = Language.widget(Gtk.Button, {
            label: Language.msg('settings.load'),
            valign: Gtk.Align.CENTER,
        });
        loadButton.connect('clicked', () => {
            this._showFileChooser(
                Language.msg('settings.load_settings'),
                {action: Gtk.FileChooserAction.OPEN},
                Language.msg('settings.open'),
                filename => {
                    if (filename)
                        this._importSettings(filename);

                }
            );
        });
        const saveButton = Language.widget(Gtk.Button, {
            label: Language.msg('settings.save'),
            valign: Gtk.Align.CENTER,
        });
        saveButton.connect('clicked', () => {
            this._showFileChooser(
                Language.msg('settings.save_settings'),
                {action: Gtk.FileChooserAction.SAVE},
                Language.msg('settings.save'),
                filename => {
                    if (!filename)
                        return;
                    const settings = ExtensionUtils.getSettings();
                    const values = {};
                    for (const key of settings.settings_schema.list_keys())
                        if (key !== 'changed-data')
                            values[key] = settings.get_value(key).print(true);
                    const content = JSON.stringify({format: 'orbitz-settings-v1', values}, null, 2);
                    Gio.File.new_for_path(filename).replace_contents(new TextEncoder().encode(content), null, false,
                        Gio.FileCreateFlags.PRIVATE, null);

                }
            );
        });
        settingsRow.add_suffix(saveButton);
        settingsRow.add_suffix(loadButton);
        settingsGroup.add(settingsRow);
        this.add(settingsGroup);
        // -----------------------------------------------------------------------

        const creditsGroup = Language.widget(Adw.PreferencesGroup, {title: Language.msg('settings.credits')});
        creditsGroup.add(this._createLinkRow(
            Language.msg('settings.original_base_azclock_andrew_zaech'), 'https://gitlab.com/AndrewZaech/azclock'));
        this.add(creditsGroup);

        const gnuSofwareLabel = Language.widget(Gtk.Label, {
            label: GNU_SOFTWARE,
            use_markup: true,
            justify: Gtk.Justification.CENTER,
        });
        const gnuSofwareLabelBox = Language.widget(Gtk.Box, {
            orientation: Gtk.Orientation.VERTICAL,
            valign: Gtk.Align.END,
            vexpand: true,
        });
        gnuSofwareLabelBox.append(gnuSofwareLabel);
        creditsGroup.add(gnuSofwareLabelBox);
    }

    _showError(message) {
        const dialog = Language.widget(Gtk.MessageDialog, {transient_for: this.get_root(), modal: true,
            message_type: Gtk.MessageType.ERROR, buttons: Gtk.ButtonsType.CLOSE,
            text: Language.msg('settings.operation_error'), secondary_text: message?.orbitzMessage ? message : String(message).slice(0, 2048)});
        dialog.connect('response', () => dialog.destroy());
        dialog.present();
    }

    _importSettings(filename) {
        try {
            const settings = ExtensionUtils.getSettings();
            const prepared = SettingsImport.parse(SettingsImport.read(filename), settings);
            const dialog = Language.widget(Gtk.MessageDialog, {transient_for: this.get_root(), modal: true,
                message_type: Gtk.MessageType.QUESTION, buttons: Gtk.ButtonsType.NONE,
                text: Language.msg('settings.import_commands_confirm')});
            Language.button(dialog, Language.msg('settings.cancel'), Gtk.ResponseType.CANCEL);
            Language.button(dialog, Language.msg('settings.import'), Gtk.ResponseType.ACCEPT);
            const scroll = Language.widget(Gtk.ScrolledWindow, {min_content_width: 550, min_content_height: 220});
            const label = Language.widget(Gtk.Label, {label: prepared.commands.join('\n\n') || Language.msg('settings.no_commands'),
                wrap: true, selectable: true, xalign: 0});
            scroll.set_child(label);
            dialog.get_message_area().append(scroll);
            dialog.connect('response', (_dialog, response) => {
                if (response === Gtk.ResponseType.ACCEPT) {
                    try {
                        const transaction = new Gio.Settings({settings_schema: settings.settings_schema});
                        transaction.delay();
                        for (const [key, value] of Object.entries(prepared.values))
                            if (!transaction.set_value(key, value))
                                throw Language.error(Language.msg('settings.validation.write', {key}));
                        transaction.set_value('changed-data', new GLib.Variant('a{ss}', {}));
                        transaction.apply();
                        Gio.Settings.sync();
                    } catch (error) { this._showError(error.orbitzMessage || error.message); }
                }
                dialog.destroy();
            });
            dialog.present();
        } catch (error) { this._showError(error.orbitzMessage || error.message); }
    }

    _createLinkRow(title, uri) {
        const image = Language.widget(Gtk.Image, {
            icon_name: 'adw-external-link-symbolic',
            valign: Gtk.Align.CENTER,
        });
        const linkRow = Language.widget(Adw.ActionRow, {
            title,
            activatable: true,
        });
        linkRow.connect('activated', () => {
            Gtk.show_uri(this.get_root(), uri, Gdk.CURRENT_TIME);
        });
        linkRow.add_suffix(image);

        return linkRow;
    }

    _showFileChooser(title, params, acceptBtn, acceptHandler) {
        const dialog = Language.widget(Gtk.FileChooserDialog, {
            title,
            transient_for: this.get_root(),
            modal: true,
            action: params.action,
        });
        Language.button(dialog, Language.msg('settings.cancel'), Gtk.ResponseType.CANCEL);
        Language.button(dialog, acceptBtn, Gtk.ResponseType.ACCEPT);

        dialog.connect('response', (self, response) => {
            if (response === Gtk.ResponseType.ACCEPT) {
                try {
                    acceptHandler(dialog.get_file().get_path());
                } catch (e) {
                    this._showError(e.orbitzMessage || e.message);
                }
            }
            dialog.destroy();
        });

        dialog.show();
    }
});

var GNU_SOFTWARE = '<span size="small">' +
    'This program comes with absolutely no warranty.\n' +
    'See the <a href="https://github.com/orbitzone/orbitz-widgets-for-gnome/blob/main/LICENSE">' +
    'GNU General Public License — veja LICENSE do projeto</a>.' +
    '</span>';

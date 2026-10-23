const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();
const Language = Me.imports.uiLanguage.Language;
const {Adw, Gdk, GLib, GObject, Gtk} = imports.gi;
const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Language.tr;
var GWeather = getGWeatherVersion();

const MAX_LOCATIONS = 12;

/**
 * Check for GWeather v4 package.
 * GWeather v3 throws errors wit Gtk4
 */
function getGWeatherVersion() {
    try {
        imports.gi.versions.GWeather = '4.0';
        return imports.gi.GWeather;
    } catch (e) {
        return null;
    }
}

var TimeZoneDialog = GObject.registerClass({
    GTypeName: 'OrbitzWidgetsTimeZoneDialog',
    Signals: {
        'time-zone-changed': {param_types: [GObject.TYPE_STRING, GObject.TYPE_STRING]},
    },
}, class AzClockTimeZoneDialog extends Adw.Window {
    _init(params) {
        super._init(Language.properties(this, {
            ...params,
            default_width: 400,
            default_height: 540,
        }));

        this._locationsRows = [];

        const mainBox = Language.widget(Gtk.Box, {
            orientation: Gtk.Orientation.VERTICAL,
            valign: Gtk.Align.FILL,
            vexpand: true,
        });
        this.set_content(mainBox);

        const headerBar = Language.widget(Adw.HeaderBar, {
            show_start_title_buttons: true,
            show_end_title_buttons: true,
        });
        mainBox.append(headerBar);

        const searchEntry = new Gtk.SearchEntry();
        const searchBar = Language.widget(Gtk.SearchBar, {
            search_mode_enabled: true,
            child: searchEntry,
        });
        mainBox.append(searchBar);

        const stack = new Gtk.Stack();
        mainBox.append(stack);

        const page = Language.widget(Adw.PreferencesPage, {
            valign: Gtk.Align.FILL,
            vexpand: true,
        });
        stack.add_named(page, 'MainPage');

        const statusPage = Language.widget(Adw.StatusPage, {
            title: Language.msg('settings.search_for_a_city'),
            icon_name: 'system-search-symbolic',
        });
        stack.add_named(statusPage, 'StatusPage');

        this._searchResultsGroup = Language.widget(Adw.PreferencesGroup, {
            valign: Gtk.Align.FILL,
        });
        page.add(this._searchResultsGroup);

        stack.set_visible_child_name('StatusPage');

        searchEntry.connect('search-changed', () => {
            for (let i = this._locationsRows.length - 1; i >= 0; i -= 1) {
                this._searchResultsGroup.remove(this._locationsRows[i]);
                this._locationsRows.pop();
            }

            if (searchEntry.text === '') {
                // EMPTY SEARCH
                Language.set(statusPage, 'title', Language.msg('settings.search_for_a_city'));
                stack.set_visible_child_name('StatusPage');
                return;
            }

            const search = searchEntry.text.normalize().toLowerCase();

            const world = GWeather.Location.get_world();

            this.queryLocations(world, search);

            if (this._locationsRows.length === 0) {
                // NO RESULTS
                Language.set(statusPage, 'title', Language.msg('settings.no_results'));
                stack.set_visible_child_name('StatusPage');
                return;
            }

            stack.set_visible_child_name('MainPage');

            this._locationsRows.sort((a, b) => {
                var nameA = a.location.get_sort_name();
                var nameB = b.location.get_sort_name();
                return nameA.localeCompare(nameB);
            });

            this._locationsRows.forEach(row => {
                this._searchResultsGroup.add(row);
            });
        });
    }

    queryLocations(location, search) {
        if (this._locationsRows.length >= MAX_LOCATIONS)
            return;

        switch (location.get_level()) {
        case GWeather.LocationLevel.CITY: {
            const containsName = location.get_sort_name().includes(search);

            let countryName = location.get_country_name();
            if (countryName != null)
                countryName = countryName.normalize().toLowerCase();

            const containsCountryName = countryName != null && countryName.includes(search);

            if (containsName || containsCountryName) {
                const row = this.createLocationRow(location);
                this._locationsRows.push(row);
            }
            return;
        }
        case GWeather.LocationLevel.NAMED_TIMEZONE:
            if (location.get_sort_name().includes(search)) {
                const row = this.createLocationRow(location);
                this._locationsRows.push(row);
            }
            return;
        default:
            break;
        }

        let loc = location.next_child(null);
        while (loc !== null) {
            this.queryLocations(loc, search);
            if (this._locationsRows.length >= MAX_LOCATIONS)
                return;

            loc = location.next_child(loc);
        }
    }

    createLocationRow(location) {
        const interval = location.get_timezone().find_interval(GLib.TimeType.UNIVERSAL, Gdk.CURRENT_TIME);
        const offset = location.get_timezone().get_offset(interval) / 3600;
        const offsetString = offset >= 0 ? `+${offset}` : offset;

        const gTimeZone = GLib.TimeZone.new(location.get_timezone_str());
        const localDateTime = GLib.DateTime.new_now(gTimeZone);
        const abbreviation = localDateTime.get_timezone_abbreviation();

        const hasCountry = location.get_country_name();

        const title = hasCountry ? `${location.get_name()}, ${location.get_country_name()}` : location.get_name();

        const timeZoneRow = Language.widget(Adw.ActionRow, {
            title,
            subtitle: `${location.get_timezone_str()} • ${abbreviation} (UTC ${offsetString})`,
            activatable: true,
        });
        timeZoneRow.use_markup = true;
        timeZoneRow.location = location;

        timeZoneRow.connect('activated', () => {
            this.emit('time-zone-changed', location.get_timezone_str(), `${title} • ${abbreviation}`);
            this.close();
        });

        return timeZoneRow;
    }
});

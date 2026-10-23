// Weather modal; collector owns forecasts, geography and private preferences.
var create = ({Language, Clutter, Gio, GLib, Main, Pango, St, global, getData, readCommandOutput, stopCommandRun}) => ({
    _weatherCommandInfo(command) {
        try {
            const [ok, argv] = GLib.shell_parse_argv(command);
            if (!ok || !argv.some(arg => arg.endsWith('/clima-widget.py'))) return null;
            const read = key => argv.includes(key) ? argv[argv.indexOf(key) + 1] : null;
            const latitude = read('--latitude'), longitude = read('--longitude');
            if ((latitude === null) !== (longitude === null) ||
                (latitude !== null && (!Number.isFinite(Number(latitude)) || Math.abs(Number(latitude)) > 90 ||
                !Number.isFinite(Number(longitude)) || Math.abs(Number(longitude)) > 180))) return null;
            const unit = read('--unit') || 'celsius';
            if (!['celsius', 'fahrenheit'].includes(unit)) return null;
            return {argv, latitude: latitude === null ? -15.7939 : Number(latitude),
                longitude: longitude === null ? -47.8828 : Number(longitude), name: read('--name') || 'Brasília, DF', unit};
        } catch (error) { return null; }
    },

    _weatherCurrent(command, generation) {
        return !this._networkDestroyed && this._networkDialog?.visible && this._networkGeneration === generation &&
            getData(this.widgetIndex, this.elementIndex, 'Text_Command') === command;
    },

    _cancelWeatherRequests() {
        for (const run of this._weatherRequests?.values() || []) {
            if (run.timeout) GLib.source_remove(run.timeout);
            run.timeout = null;
            stopCommandRun(run);
        }
        this._weatherRequests?.clear();
    },

    async _weatherRequest(kind, args, prefix, command) {
        if(!this._weatherCurrent(command,this._networkGeneration))return null;
        this._weatherRequests ||= new Map();
        const previous = this._weatherRequests.get(kind);
        if (previous) {
            if (previous.timeout) GLib.source_remove(previous.timeout);
            previous.timeout = null;stopCommandRun(previous);
        }
        const info = this._weatherCommandInfo(command);
        if (!info) throw Language.error(Language.msg('weather.invalid_command'));
        const queryMessage=kind==='search'?'weather.search_error':kind==='preferences'?'weather.preferences_error':'weather.query_error';
        const run = {cancellable: new Gio.Cancellable(), generation: this._networkGeneration, proc: null, timeout: null};
        this._weatherRequests.set(kind, run);
        try {
            run.proc = Language.spawn(['/usr/bin/setsid', ...info.argv, ...args], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
            run.timeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 15000, () => {
                run.timeout = null;run.timedOut = true;stopCommandRun(run);return GLib.SOURCE_REMOVE;
            });
            const [stdout] = await readCommandOutput(run);
            if (this._weatherRequests.get(kind) !== run || !this._weatherCurrent(command, run.generation) || (run.cancelled && !run.timedOut)) return null;
            if (run.timedOut) throw Language.error(Language.msg('weather.timeout'));
            if (!run.proc.get_successful() || !stdout.startsWith(prefix)) throw Language.error(Language.msg(queryMessage));
            const payload = JSON.parse(stdout.slice(prefix.length));
            if (payload.version !== 1 || typeof payload.ok !== 'boolean') throw Language.error(Language.msg('weather.invalid_response'));
            if (!payload.ok) {
                const error = Language.error(Language.msg(payload.error_code === 'conflict' ? 'weather.conflict' : queryMessage));
                error.weatherCode = payload.error_code;
                throw error;
            }
            return payload;
        } catch (error) {
            if (this._weatherRequests.get(kind) !== run || !this._weatherCurrent(command, run.generation) || (run.cancelled && !run.timedOut)) return null;
            if (run.timedOut) throw Language.error(Language.msg('weather.timeout'));
            throw error;
        } finally {
            if (run.timeout) GLib.source_remove(run.timeout);
            if (this._weatherRequests.get(kind) === run) this._weatherRequests.delete(kind);
        }
    },

    _weatherValidate(data, info) {
        const number = (value, min, max) => typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max;
        const string = (value, max) => typeof value === 'string' && value.length <= max;
        const day = value => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) &&
            Number.isFinite(Date.parse(value + 'T12:00:00Z')) && new Date(value + 'T12:00:00Z').toISOString().slice(0, 10) === value;
        const code = value => Number.isInteger(value) && value >= 0 && value <= 99;
        if (!info || !data || data.version !== 1 || data.ok !== true || data.unit !== info.unit || !data.location ||
            !string(data.location.name, 160) || !string(data.location.timezone, 100) ||
            !number(data.location.latitude, -90, 90) || !number(data.location.longitude, -180, 180) ||
            Math.abs(data.location.latitude - info.latitude) > 0.001 || Math.abs(data.location.longitude - info.longitude) > 0.001 ||
            !data.current || !string(data.current.time,64) || !Number.isFinite(Date.parse(data.current.time)) || !number(data.current.temperature, -200, 200) || !number(data.current.apparent_temperature, -250, 250) ||
            !number(data.current.humidity, 0, 100) || !code(data.current.weather_code) || ![0, 1].includes(data.current.is_day) ||
            !Array.isArray(data.days) || data.days.length !== 7 ||
            data.days.some((item, index) => !item || !day(item.date) || !number(item.temp_min, -200, 200) ||
                !number(item.temp_max, -200, 200) || item.temp_min > item.temp_max || !number(item.precipitation_probability, 0, 100) ||
                !code(item.weather_code) || !number(item.wind_speed_max, 0, 500) || (index > 0 && Date.parse(item.date) - Date.parse(data.days[index - 1].date) !== 86400000)) ||
            !string(data.fetched_at, 64) || !Number.isFinite(Date.parse(data.fetched_at)) || typeof data.stale !== 'boolean' ||
            data.stale || data.attribution?.name !== 'Open-Meteo' || data.attribution?.url !== 'https://open-meteo.com/' || data.attribution?.license !== 'CC-BY-4.0')
            throw Language.error(Language.msg('weather.invalid_response'));
        return data;
    },

    _weatherCondition(code) {
        const key = code === 0 ? 'clear_sky' : [1, 2].includes(code) ? 'partly_cloudy' : code === 3 ? 'cloudy' :
            [45, 48].includes(code) ? 'fog' : [51, 53, 55, 56, 57].includes(code) ? 'drizzle' :
            [61, 63, 65, 66, 67, 80, 81, 82].includes(code) ? 'rain' : [71, 73, 75, 77, 85, 86].includes(code) ? 'snow' :
            [95, 96, 99].includes(code) ? 'thunderstorms' : 'weather';
        return ({clear_sky:Language.msg('widgets.clima_widget.clear_sky'),partly_cloudy:Language.msg('widgets.clima_widget.partly_cloudy'),cloudy:Language.msg('widgets.clima_widget.cloudy'),fog:Language.msg('widgets.clima_widget.fog'),drizzle:Language.msg('widgets.clima_widget.drizzle'),rain:Language.msg('widgets.clima_widget.rain'),snow:Language.msg('widgets.clima_widget.snow'),thunderstorms:Language.msg('widgets.clima_widget.thunderstorms'),weather:Language.msg('widgets.clima_widget.weather')})[key];
    },

    _buildWeatherDialog() {
        this._weatherRequests = new Map();
        this._networkBackdrop = Language.widget(St.Widget, {reactive: true, visible: false});
        this._networkBackdrop.add_constraint(new Clutter.BindConstraint({source: global.stage, coordinate: Clutter.BindCoordinate.ALL}));
        this._networkBackdrop.connect('button-press-event', (_actor, event) => {
            if (this._networkDialog?.contains(event.get_source())) return Clutter.EVENT_PROPAGATE;
            this._closeNetworkDialog();return Clutter.EVENT_STOP;
        });
        Main.uiGroup.add_child(this._networkBackdrop);
        this._networkDialog = Language.widget(St.BoxLayout, {vertical: true, reactive: true,
            style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 10px; padding: 16px; spacing: 12px;'});
        const monitor = Main.layoutManager.findMonitorForActor(this) || Main.layoutManager.primaryMonitor;
        const header = Language.widget(St.BoxLayout, {style: 'spacing: 12px;'});
        this._weatherTitle = Language.widget(St.Label, {text: Language.msg('weather.title'), x_expand: true, style: 'font-size: 18px; font-weight: bold;'});
        this._weatherTitle.clutter_text.set_line_wrap(true);
        this._weatherTitle.style += ` width: ${Math.max(180,Math.min(1000,monitor.width-250))}px;`;
        header.add_child(this._weatherTitle);
        const close = Language.widget(St.Button, {label: '×', reactive: true, can_focus: true, accessible_name: Language.msg('weather.close')});
        this._weatherCloseButton=close;
        close.connect('clicked', () => this._closeNetworkDialog());header.add_child(close);this._networkDialog.add_child(header);
        this._weatherBody = Language.widget(St.BoxLayout, {vertical:true,style:'spacing:12px;'});
        const bodyScroll = Language.widget(St.ScrollView,{reactive:true,overlay_scrollbars:false,style:`max-height: ${Math.max(180,(monitor.height || 900)-150)}px;`});
        bodyScroll.set_policy(St.PolicyType.NEVER,St.PolicyType.AUTOMATIC);bodyScroll.add_actor(this._weatherBody);this._networkDialog.add_child(bodyScroll);
        this._networkBackdrop.connect('key-press-event',(_actor,event)=>{if(event.get_key_symbol()===Clutter.KEY_Escape){if(this._weatherResultsBox?.visible){this._weatherClearSearch();this._weatherSearch.grab_key_focus();}else this._closeNetworkDialog();return Clutter.EVENT_STOP;}return Clutter.EVENT_PROPAGATE;});
        this._weatherControls = Language.widget(St.BoxLayout, {vertical: true, style: 'spacing: 8px;'});
        const units = Language.widget(St.BoxLayout, {style: 'spacing: 8px;'});
        this._weatherUnitButtons = {};
        for (const unit of ['celsius', 'fahrenheit']) {
            const button = Language.widget(St.Button, {label: unit === 'celsius' ? '°C' : '°F', can_focus: true, reactive: true,
                accessible_name: (unit==='celsius'?Language.msg('weather.unit_celsius'):Language.msg('weather.unit_fahrenheit')), style: 'padding: 8px 12px; background-color: #343434; border-radius: 6px;'});
            button.connect('clicked', () => this._weatherSetUnit(unit));units.add_child(button);this._weatherUnitButtons[unit] = button;
        }
        header.insert_child_at_index(units,1);this._weatherBody.add_child(this._weatherControls);
        this._weatherBuildSearch();
        this._weatherCurrentLabel = Language.widget(St.Label, {text: '', style: `font-size:16px; width:${Math.max(220,Math.min(1100,monitor.width-64))}px;`});
        this._weatherCurrentLabel.clutter_text.set_line_wrap(true);this._weatherCurrentLabel.clutter_text.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);this._weatherBody.add_child(this._weatherCurrentLabel);
        this._weatherScroll = Language.widget(St.ScrollView, {reactive: true, overlay_scrollbars: false});
        this._weatherScroll.set_policy(St.PolicyType.NEVER, St.PolicyType.NEVER);
        this._weatherRows = Language.widget(St.BoxLayout, {style: 'spacing: 6px;'});this._weatherScroll.add_actor(this._weatherRows);this._weatherBody.add_child(this._weatherScroll);
        const footer = Language.widget(St.BoxLayout, {vertical:monitor.width<760,style: 'spacing: 12px;'});
        this._networkRefreshButton = Language.widget(St.Button, {label: Language.msg('weather.refresh'), accessible_name: Language.msg('weather.refresh'), reactive: true, can_focus: true,
            style: 'padding: 8px 12px; background-color: #315d80; border-radius: 6px;'});
        this._networkRefreshButton.connect('clicked', () => this._refreshWeatherDialog(true));footer.add_child(this._networkRefreshButton);
        this._networkRefreshStatus = Language.widget(St.Label, {text: '', x_expand:true,style:`font-size:12px; color:#b9c5cf; width:${Math.max(220,Math.min(1100,monitor.width-64)-(monitor.width<760?0:190))}px;`});
        this._networkRefreshStatus.clutter_text.set_line_wrap(true);this._networkRefreshStatus.clutter_text.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);footer.add_child(this._networkRefreshStatus);this._weatherBody.add_child(footer);
        const attribution = Language.widget(St.Button, {label: 'Open-Meteo · CC BY 4.0', reactive: true, can_focus: true,
            accessible_name: Language.msg('weather.attribution'), style: 'font-size: 11px; color: #82cfff;'});
        attribution.connect('clicked', () => {
            try { Gio.AppInfo.launch_default_for_uri('https://open-meteo.com/', null); }
            catch (error) { Language.set(this._networkRefreshStatus, 'text', Language.msg('weather.browser_error')); }
        });
        this._weatherBody.add_child(attribution);this._networkBackdrop.add_child(this._networkDialog);
        this._weatherUpdateControls();
    },

    _renderWeather(data) {
        this._weatherRows.destroy_all_children();
        const monitor = Main.layoutManager.findMonitorForActor(this) || Main.layoutManager.primaryMonitor;
        const width = Math.max(220, Math.min(1100, monitor.width - 64));
        const columnWidth = Math.max(1, Math.floor((width - 6 * 6) / 7) - 12);
        this._weatherScroll.style = `width: ${width}px;`;
        this._weatherRows.style = `width: ${width}px; spacing:6px;`;
        Language.set(this._weatherTitle, 'text', Language.msg('weather.location_title', {name: this._weatherPreferences?.location.id.startsWith('geonames:') ? [data.location.name,this._weatherPreferences.location.region_name,this._weatherPreferences.location.country_name].filter(Boolean).join(' · ') : data.location.name}));
        const format = value => Language.number(value,{maximumFractionDigits:1});
        const suffix = data.unit === 'celsius' ? '°C' : '°F';
        Language.set(this._weatherCurrentLabel, 'text', Language.msg('weather.current', {temperature: format(data.current.temperature), unit: suffix,
            humidity: format(data.current.humidity), apparent: format(data.current.apparent_temperature)}));
        for (const item of data.days) {
            const column = Language.widget(St.BoxLayout, {vertical: true, style: `width: ${columnWidth}px; min-width:0; padding: 6px; spacing: 8px; background-color: #293039; border-radius: 6px;`});
            const date = new Date(item.date + 'T12:00:00Z');
            const title = Language.widget(St.Label, {text: Language.date(date.toISOString(),{timeZone:'UTC',weekday:'short',month:'2-digit',day:'2-digit'}),
                style: 'font-weight: bold;'});
            const fit = label => {
                label.style = (label.style || '') + ` width:${columnWidth}px; min-width:0; text-align:center;`;
                label.clutter_text.set_line_wrap(true);label.clutter_text.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);
                label.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
                return label;
            };
            column.add_child(fit(title));
            const storm = [95,96,99].includes(item.weather_code);
            const windy = item.wind_speed_max >= 40;
            const icon = storm ? 'weather-storm-symbolic' : windy ? 'weather-windy-symbolic' :
                item.weather_code === 0 ? 'weather-clear-symbolic' : [1,2].includes(item.weather_code) ? 'weather-few-clouds-symbolic' :
                item.weather_code === 3 ? 'weather-overcast-symbolic' : [45,48].includes(item.weather_code) ? 'weather-fog-symbolic' :
                [51,53,55,56,57].includes(item.weather_code) ? 'weather-showers-scattered-symbolic' :
                [61,63,65,66,67,80,81,82].includes(item.weather_code) ? 'weather-showers-symbolic' :
                [71,73,75,77,85,86].includes(item.weather_code) ? 'weather-snow-symbolic' : 'dialog-question-symbolic';
            const wind = Language.msg('weather.wind',{speed:format(item.wind_speed_max)});
            const description = windy ? Language.join(this._weatherCondition(item.weather_code),' · ',wind) : this._weatherCondition(item.weather_code);
            column.add_child(Language.widget(St.Icon,{icon_name:icon,icon_size:Math.min(32,columnWidth),x_align:Clutter.ActorAlign.CENTER,
                accessible_name:description,style:'color:#d4e8fa;'}));
            const condition = Language.widget(St.Label, {text: description, style: 'font-size: 12px;'});
            column.add_child(fit(condition));
            column.add_child(fit(Language.widget(St.Label, {text: Language.msg('weather.temperatures', {min: format(item.temp_min), max: format(item.temp_max), unit: suffix})})));
            column.add_child(fit(Language.widget(St.Label, {text: Language.msg('weather.rain', {value: format(item.precipitation_probability)})})));
            Language.set(column, 'accessible_name', Language.msg('weather.day_accessible', {date: Language.date(date.toISOString(),{timeZone:'UTC',weekday:'long',year:'numeric',month:'long',day:'numeric'}), min: format(item.temp_min), max: format(item.temp_max), unit: suffix,
                condition: Language.join(this._weatherCondition(item.weather_code),' · ',wind), rain: format(item.precipitation_probability)}));
            this._weatherRows.add_child(column);
        }
    },

    async _refreshWeatherDialog(force = false, confirmed = false) {
        if (this._networkDestroyed || !this._networkDialog?.visible) return;
        const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
        const generation = this._networkGeneration;
        if ((force && !confirmed) || !this._weatherPreferences || this._weatherNeedsReload) { this._weatherLoadPreferences(force);return; }
        if (this._weatherLocationDraft || this._weatherSaving) return;
        const settings = this._weatherPreferences;
        Language.set(this._weatherTitle,'text',Language.msg('weather.location_title',{name:settings.location.name}));
        const info = {unit: settings.unit, latitude: settings.location.latitude, longitude: settings.location.longitude};
        this._weatherRows.destroy_all_children();this._weatherData = null;
        Language.set(this._weatherCurrentLabel, 'text', '');
        Language.set(this._networkRefreshStatus, 'text', Language.msg('weather.loading'));
        this._networkRefreshButton.reactive = false;
        try {
            const data = await this._weatherRequest('forecast', ['--forecast-json', '--latitude', String(info.latitude), '--longitude', String(info.longitude), '--name', settings.location.name, '--unit', info.unit, ...(force ? ['--refresh'] : [])], 'AZCLOCK_WEATHER:', command);
            if (!data) return;
            if (Array.isArray(data.days) && data.days.length === 0) throw Language.error(Language.msg('weather.empty'));
            this._weatherData = this._weatherValidate(data, info);this._renderWeather(data);
            Language.set(this._networkRefreshStatus, 'text', Language.join(Language.msg('weather.updated', {time: Language.date(data.fetched_at)}),this._weatherPreferenceNotice?Language.join(' · ',this._weatherPreferenceNotice):''));
        } catch (error) {
            if (this._weatherCurrent(command, this._networkGeneration)) {
                this._weatherRows.destroy_all_children();this._weatherData = null;
                Language.set(this._networkRefreshStatus, 'text', error.orbitzMessage || Language.msg('weather.query_error'));
            }
        } finally {
            if (this._weatherCurrent(command,generation)) this._weatherUpdateControls();
        }
    },

    _weatherSetUnit(unit) {
        if (!['celsius', 'fahrenheit'].includes(unit) || this._weatherSaving || !this._weatherPreferences || this._weatherPreferences.unit === unit) return;
        this._weatherCommitPreferences(['--set-unit', unit]);
    },

    _weatherValidatePreferences(data) {
        const location = data?.location;
        if (data?.version !== 1 || data.ok !== true || !Number.isSafeInteger(data.revision) || data.revision < 0 || data.revision > 2147483647 ||
            !['celsius', 'fahrenheit'].includes(data.unit) || !location || typeof location.id !== 'string' ||
            !/^(?:[0-9]{1,12}|builtin-brasilia|geonames:[1-9][0-9]{0,15})$/.test(location.id) || !/^[A-Z]{2}$/.test(location.country_id) ||
            typeof location.region_id !== 'string' || !/^(?:[0-9]{1,12})?$/.test(location.region_id) ||
            typeof location.name !== 'string' || !location.name || location.name.length > 160 ||
            typeof location.latitude !== 'number' || !Number.isFinite(location.latitude) || Math.abs(location.latitude) > 90 ||
            typeof location.longitude !== 'number' || !Number.isFinite(location.longitude) || Math.abs(location.longitude) > 180 ||
            typeof location.timezone !== 'string' || location.timezone.length > 100 ||
            ['country_name','region_name'].some(key=>location[key]!==undefined && (typeof location[key]!=='string'||location[key].length>160)))
            throw Language.error(Language.msg('weather.invalid_response'));
        return data;
    },

    _weatherBuildSearch() {
        const monitor = Main.layoutManager.findMonitorForActor(this) || Main.layoutManager.primaryMonitor;
        const width = Math.max(220, Math.min(560, monitor.width - 80));
        const row = Language.widget(St.BoxLayout, {vertical: monitor.width < 450, style: `spacing:8px; width:${width}px;`});
        this._weatherSearch = Language.widget(St.Entry, {hint_text: Language.msg('weather.search_city'),
            accessible_name: Language.msg('weather.search_city'), can_focus: true, x_expand: true,
            style: 'padding:8px; background-color:#343434; color:white;'});
        this._weatherSearch.clutter_text.set_max_length(100);
        this._weatherSearch.clutter_text.connect('text-changed', () => this._weatherClearSearch());
        this._weatherSearch.clutter_text.connect('activate', () => this._weatherSearchLocations());
        this._weatherSearch.connect('key-press-event', (_actor,event) => {
            if (event.get_key_symbol() === Clutter.KEY_Down) {
                const first = this._weatherResultRows.get_first_child();
                if (first) {first.grab_key_focus();return Clutter.EVENT_STOP;}
            }
            return Clutter.EVENT_PROPAGATE;
        });
        row.add_child(this._weatherSearch);
        this._weatherSearchButton = Language.widget(St.Button, {label: Language.msg('weather.search_button'),
            accessible_name: Language.msg('weather.search_button'), reactive:true, can_focus:true,
            style:'padding:8px 12px; background-color:#315d80; border-radius:6px;'});
        this._weatherSearchButton.connect('clicked', () => this._weatherSearchLocations());row.add_child(this._weatherSearchButton);
        this._weatherControls.add_child(row);
        this._weatherResultsBox = Language.widget(St.BoxLayout, {vertical:true, visible:false, style:`spacing:6px; width:${width}px;`});
        this._weatherSearchStatus = Language.widget(St.Label, {text:'',style:'font-size:12px; color:#b9c5cf;'});
        this._weatherSearchStatus.clutter_text.set_line_wrap(true);this._weatherResultsBox.add_child(this._weatherSearchStatus);
        const scroll = Language.widget(St.ScrollView, {reactive:true, overlay_scrollbars:false, style:'max-height:150px;'});
        scroll.set_policy(St.PolicyType.NEVER,St.PolicyType.AUTOMATIC);
        this._weatherResultRows = Language.widget(St.BoxLayout, {vertical:true,style:'spacing:3px;'});
        scroll.add_actor(this._weatherResultRows);this._weatherResultsBox.add_child(scroll);
        this._weatherControls.add_child(this._weatherResultsBox);
        const credit = Language.widget(St.Button, {label:'Open-Meteo · GeoNames',accessible_name:Language.msg('weather.search_attribution'),
            reactive:true,can_focus:true,x_align:Clutter.ActorAlign.START,style:'font-size:11px; color:#82cfff;'});
        credit.connect('clicked', () => {
            try { Gio.AppInfo.launch_default_for_uri('https://open-meteo.com/en/docs/geocoding-api',null); }
            catch (error) { Language.set(this._networkRefreshStatus,'text',Language.msg('weather.browser_error')); }
        });this._weatherControls.add_child(credit);
    },

    _weatherClearSearch() {
        this._weatherSearchToken = null;this._weatherSearching = false;this._weatherSearchResults = [];
        const run = this._weatherRequests?.get('search');
        if (run) {
            if (run.timeout) GLib.source_remove(run.timeout);
            run.timeout=null;stopCommandRun(run);this._weatherRequests.delete('search');
        }
        this._weatherResultRows?.destroy_all_children();this._weatherResultsBox?.hide();
        this._weatherUpdateControls();
    },

    _weatherValidateSearch(data) {
        const string = (value,max,required=false) => typeof value === 'string' && value.length <= max && (!required || value.trim().length > 0);
        if (data?.version !== 1 || data.ok !== true || data.complete !== false || !Array.isArray(data.results) || data.results.length > 10 ||
            data.attribution?.name !== 'Open-Meteo' || data.attribution?.url !== 'https://open-meteo.com/' ||
            data.attribution?.location_source !== 'GeoNames' || data.attribution?.location_url !== 'https://www.geonames.org/')
            throw Language.error(Language.msg('weather.invalid_response'));
        const ids = new Set();
        for (const item of data.results) {
            if (!item || !Number.isSafeInteger(item.id) || item.id <= 0 || ids.has(item.id) ||
                !string(item.name,160,true) || !string(item.admin1,160) || !string(item.country,160,true) ||
                typeof item.country_code !== 'string' || !/^[A-Z]{2}$/.test(item.country_code) || !string(item.timezone,100,true) ||
                typeof item.latitude !== 'number' || !Number.isFinite(item.latitude) || Math.abs(item.latitude)>90 ||
                typeof item.longitude !== 'number' || !Number.isFinite(item.longitude) || Math.abs(item.longitude)>180 || JSON.stringify(item).length>16000)
                throw Language.error(Language.msg('weather.invalid_response'));
            ids.add(item.id);
        }
        return data.results;
    },

    async _weatherSearchLocations() {
        if (this._weatherSaving || this._weatherSearching || !this._weatherPreferences || this._weatherNeedsReload || !this._networkDialog?.visible) return;
        const query = this._weatherSearch.get_text().trim();
        this._weatherClearSearch();this._weatherResultsBox.show();
        if (query.length < 2 || query.length > 100) {
            Language.set(this._weatherSearchStatus,'text',Language.msg('weather.search_min'));return;
        }
        const token = {};this._weatherSearchToken=token;this._weatherSearching=true;this._weatherUpdateControls();
        Language.set(this._weatherSearchStatus,'text',Language.msg('weather.search_loading'));
        const command=getData(this.widgetIndex,this.elementIndex,'Text_Command'), generation=this._networkGeneration;
        try {
            const result=await this._weatherRequest('search',['--geocode',query],'AZCLOCK_GEOCODING:',command);
            if (!result || this._weatherSearchToken!==token) return;
            this._weatherSearchResults=this._weatherValidateSearch(result);
            const monitor=Main.layoutManager.findMonitorForActor(this)||Main.layoutManager.primaryMonitor;
            for (const item of this._weatherSearchResults) {
                const label=[item.name,item.admin1,item.country].filter(Boolean).join(' · ');
                const button=Language.widget(St.Button,{label,accessible_name:label,reactive:true,can_focus:true,
                    style:`width:${Math.max(200,Math.min(540,monitor.width-100))}px; padding:6px 10px; background-color:#343434; border-radius:4px;`});
                button.get_child?.()?.clutter_text?.set_line_wrap(true);
                button.get_child?.()?.clutter_text?.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);
                button.connect('clicked',()=>this._weatherSelectResult(item));this._weatherResultRows.add_child(button);
            }
            Language.set(this._weatherSearchStatus,'text',Language.msg(this._weatherSearchResults.length?'weather.search_results':'weather.search_empty'));
            this._weatherPlaceDialog();
        } catch (error) {
            if (this._weatherCurrent(command,generation) && this._weatherSearchToken===token)
                Language.set(this._weatherSearchStatus,'text',error.orbitzMessage || Language.msg('weather.search_error'));
        } finally {
            if (this._weatherSearchToken===token) {this._weatherSearching=false;this._weatherUpdateControls();}
        }
    },

    _weatherSelectResult(item) {
        if (this._weatherSaving || !this._weatherSearchResults?.includes(item) || !this._networkDialog?.visible) return;
        this._weatherClearSearch();this._weatherLocationDraft=true;
        this._weatherCommitPreferences(['--set-geocoded-location',JSON.stringify(item)]);
    },

    _weatherUpdateControls() {
        const prefs = this._weatherPreferences;
        const busy = this._weatherSaving || !prefs || this._weatherNeedsReload;
        for (const [unit, button] of Object.entries(this._weatherUnitButtons)) {
            button.reactive = !busy;button.can_focus = !busy;
            const label=unit==='celsius'?Language.msg('weather.unit_celsius'):Language.msg('weather.unit_fahrenheit');
            Language.set(button,'accessible_name',prefs?.unit===unit?Language.msg('weather.selected_unit',{unit:label}):label);
            button.style = 'padding: 8px 12px; border-radius: 6px; background-color: ' + (prefs?.unit === unit ? '#315d80;' : '#343434;');
        }
        if (this._weatherSearch) {this._weatherSearch.reactive=!busy;this._weatherSearch.can_focus=!busy;}
        if (this._weatherSearchButton) {
            this._weatherSearchButton.reactive=!busy && !this._weatherSearching;
            this._weatherSearchButton.can_focus=this._weatherSearchButton.reactive;
        }
        if (this._networkRefreshButton) this._networkRefreshButton.reactive = !busy && !this._weatherLocationDraft && !this._weatherRequests?.has('forecast');
    },

    async _weatherLoadPreferences(force = false) {
        if (!this._networkDialog?.visible || this._networkDestroyed) return;
        const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
        const generation = this._networkGeneration;
        this._weatherClearSearch();
        this._weatherData=null;this._weatherRows.destroy_all_children();Language.set(this._weatherCurrentLabel,'text','');Language.set(this._weatherTitle,'text',Language.msg('weather.title'));this._weatherUpdateControls();
        Language.set(this._networkRefreshStatus, 'text', Language.msg('weather.loading'));
        try {
            const result = await this._weatherRequest('preferences', ['--preferences-json'], 'AZCLOCK_WEATHER_PREFS:', command);
            if (!result) return;
            this._weatherAdoptPreferences(this._weatherValidatePreferences(result));
            this._refreshWeatherDialog(force,true);
        } catch (error) {
            if (this._weatherCurrent(command, generation)) {
                Language.set(this._networkRefreshStatus, 'text', error.orbitzMessage || Language.msg('weather.query_error'));
                this._networkRefreshButton.reactive=true;
            }
        }
    },

    _weatherAdoptPreferences(prefs) {
        this._weatherPreferences = prefs;this._weatherNeedsReload=false;
        this._weatherLocationDraft = false;
        this._weatherUpdateControls();
    },

    async _weatherCommitPreferences(args) {
        if (this._networkDestroyed || this._weatherSaving || !this._weatherPreferences || !this._networkDialog?.visible) return;
        const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
        const generation = this._networkGeneration;
        this._weatherClearSearch();
        const saveToken={};this._weatherSaveToken=saveToken;
        this._weatherSaving = true;this._weatherData = null;this._weatherRows.destroy_all_children();Language.set(this._weatherTitle,'text',Language.msg('weather.title'));
        this._cancelWeatherRequests();this._weatherUpdateControls();
        Language.set(this._weatherCurrentLabel, 'text', '');Language.set(this._networkRefreshStatus, 'text', Language.msg('weather.saving'));
        try {
            const result = await this._weatherRequest('preferences', [...args, '--expected-revision', String(this._weatherPreferences.revision)], 'AZCLOCK_WEATHER_PREFS:', command);
            if (!result) return;
            this._weatherAdoptPreferences(this._weatherValidatePreferences(result));this._weatherPreferenceNotice=null;
            // Cancel any older summary so its late °C/°F result cannot overwrite the saved preference.
            this._cancelCommand();this.refreshCommand();
        } catch (error) {
            if (this._weatherCurrent(command, generation)) {
                this._weatherLocationDraft = true;this._weatherNeedsReload=true;
                this._weatherPreferenceNotice=Language.msg(error.weatherCode==='conflict'?'weather.conflict':'weather.save_error');
                Language.set(this._networkRefreshStatus, 'text', this._weatherPreferenceNotice);
                if (error.weatherCode === 'conflict') this._weatherPreferences = null;
            }
        } finally {
            if(this._weatherSaveToken!==saveToken)return;
            this._weatherSaveToken=null;this._weatherSaving = false;
            if (this._weatherCurrent(command, generation)) {
                this._weatherUpdateControls();
                if (!this._weatherPreferences) this._weatherLoadPreferences();
                else if (!this._weatherLocationDraft) this._refreshWeatherDialog(true,true);
                else if(this._weatherNeedsReload)this._networkRefreshButton.reactive=true;
            }
        }
    },

    _weatherRefreshLocale() {
        // Catalog bindings format dates/numbers in place; do not refetch or replace input actors.
        this._networkDialog?.queue_relayout?.();
    },


    _weatherClose() {
        this._cancelWeatherRequests();this._weatherPreferences=null;this._weatherData=null;
        this._weatherSaveToken=null;this._weatherSaving=false;this._weatherLocationDraft=false;this._weatherNeedsReload=false;this._weatherPreferenceNotice=null;
        this._weatherClearSearch();
    },

    _weatherPlaceDialog() {
        const monitor=Main.layoutManager.findMonitorForActor(this)||Main.layoutManager.primaryMonitor;
        const [,width]=this._networkDialog.get_preferred_width(-1);
        const [,height]=this._networkDialog.get_preferred_height(width);
        const [x,y]=this._networkDialog.get_position();
        this._networkDialog.set_position(Math.max(monitor.x+8,Math.min(x,monitor.x+monitor.width-width-8)),
            Math.max(monitor.y+8,Math.min(y,monitor.y+monitor.height-height-8)));
    },

});

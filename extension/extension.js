/* eslint-disable jsdoc/require-jsdoc */
const {
    Clutter, Gio, GLib, GObject,
    Graphene, Meta, Pango, Shell, St,
} = imports.gi;

const ExtensionUtils = imports.misc.extensionUtils;
const Main = imports.ui.main;
const Me = ExtensionUtils.getCurrentExtension();
const PopupMenu = imports.ui.popupMenu;
let widgetsEnabled = false;
let activeWidgetDrag = null;
const dragWidgets = new Set();
let widgetDragController = null;
let widgetDragGrab = null;
let widgetDragKeySignal = 0;
const activeCommandRuns = new Set();
const pendingStops = new Set();
const Utils = Me.imports.utils;
const Calendar = Me.imports.planner.calendar;

const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Gettext.gettext;

Gio._promisify(Gio.Subprocess.prototype, 'communicate_utf8_async');
Gio._promisify(Gio.Subprocess.prototype, 'wait_async');
Gio._promisify(Gio.InputStream.prototype, 'read_bytes_async');
Gio._promisify(Gio.OutputStream.prototype, 'write_all_async');
Gio._promisify(Gio.DataInputStream.prototype, 'read_line_async');

function collectorBirth(pid) {
    if (!pid || !/^\d+$/.test(pid)) return null;
    try {
        const [, bytes] = GLib.file_get_contents(`/proc/${pid}/stat`);
        const text = new TextDecoder().decode(bytes);
        return text.slice(text.lastIndexOf(')') + 2).trim().split(/\s+/)[19];
    } catch (error) { return null; }
}

function stopCommandRun(run) {
    if (!run) return Promise.resolve();
    if (run.stopPromise) return run.stopPromise;
    run.cancelled = true;
    run.cancellable?.cancel();
    const proc = run.proc;
    if (!proc) return Promise.resolve();
    const pid = proc.get_identifier();
    const birth = run.birth || collectorBirth(pid);
    run.stopPromise = (async () => {
        try {
            if (pid && birth && /^\d+$/.test(pid)) {
                const killer = Gio.Subprocess.new(['python3', GLib.build_filenamev([Me.path, 'stop-collectors.py']), pid, birth],
                    Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE);
                await killer.wait_async(null);
                if (!killer.get_successful()) throw new Error('Falha ao encerrar árvore do coletor.');
            }
        } catch (error) { logError(error, 'Desktop Clock collector cleanup'); }
        try { proc.force_exit(); await proc.wait_async(null); }
        catch (error) { /* Process may already have exited. */ }
    })();
    pendingStops.add(run.stopPromise);
    run.stopPromise.finally(() => pendingStops.delete(run.stopPromise));
    return run.stopPromise;
}

async function readCommandOutput(run, input = null) {
    activeCommandRuns.add(run);
    run.birth = collectorBirth(run.proc.get_identifier());
    let total = 0;
    const read = async stream => {
        const chunks = [];
        let size = 0;
        while (true) {
            const bytes = await stream.read_bytes_async(8192, GLib.PRIORITY_DEFAULT, run.cancellable);
            const chunk = bytes.get_data();
            if (!chunk.length) {
                const data = new Uint8Array(size);
                let offset = 0;
                for (const part of chunks) {
                    data.set(part, offset);
                    offset += part.length;
                }
                return new TextDecoder('utf-8').decode(data);
            }
            total += chunk.length;
            if (total > 262144) {
                run.outputLimit = true;
                stopCommandRun(run);
                throw new Error('Saída do comando excedeu 256 KiB.');
            }
            chunks.push(chunk);
            size += chunk.length;
        }
    };
    const write = async () => {
        if (input !== null) {
            await run.proc.get_stdin_pipe().write_all_async(new TextEncoder().encode(input),
                GLib.PRIORITY_DEFAULT, run.cancellable);
            run.proc.get_stdin_pipe().close(null);
        }
    };
    try {
        const [stdout, stderr] = await Promise.all([
            read(run.proc.get_stdout_pipe()), read(run.proc.get_stderr_pipe()), write(),
            run.proc.wait_async(run.cancellable),
        ]);
        return [stdout, stderr];
    } catch (error) {
        await stopCommandRun(run);
        throw error;
    } finally { activeCommandRuns.delete(run); }

}


const DEBUG_LOG = false;

const ANALOG_CLOCK = 'Analog_Clock';
const DIGITAL_CLOCK = 'Digital_Clock';
const TEXT_LABEL = 'Text_Label';
const COMMAND_LABEL = 'Command_Label';
const WIDGET_DATA_INDEX = 0;

let WIDGETDATA;
const metricLabels = new Set();
let metricProc = null;
let metricCancellable = null;
let metricGeneration = 0;
let metricRestart = null;
let metricWatchdog = null;
let metricLastOutput = 0;
function metricMode(command) {
    try {
        const [, args] = GLib.shell_parse_argv(command);
        if (args.length !== 2 || !['python3', '/usr/bin/python3'].includes(args[0]))
            return null;
        return {'cpu-ram-widget.py': 'cpu', 'processos-widget.py': 'processes', 'rede-widget.py': 'network'}[GLib.path_get_basename(args[1])] || null;
    } catch (error) { return null; }
}
function stopMetrics() {
    metricGeneration++;
    if (metricProc) {
        stopCommandRun({proc: metricProc, cancellable: metricCancellable});
        metricProc = null;
        metricCancellable = null;
    }
    if (metricWatchdog) {
        GLib.source_remove(metricWatchdog);
        metricWatchdog = null;
    }
}
function scheduleMetrics() {
    if (!widgetsEnabled || metricRestart)
        return;
    metricRestart = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
        metricRestart = null;
        startMetrics();
        return GLib.SOURCE_REMOVE;
    });
}
async function startMetrics() {
    if (!widgetsEnabled) return;
    stopMetrics();
    if (!metricLabels.size)
        return;
    const generation = metricGeneration;
    const jobs = new Map();
    let path;
    for (const label of metricLabels) {
        const command = getData(label.widgetIndex, label.elementIndex, 'Text_Command');
        const mode = metricMode(command);
        if (!mode)
            continue;
        const [, args] = GLib.shell_parse_argv(command);
        path = path || GLib.build_filenamev([GLib.path_get_dirname(args[1]), 'metrics-worker.py']);
        const interval = Math.max(2000, Math.min(3600000, Number(getData(label.widgetIndex, label.elementIndex, 'Text_PollingInterval')) || 12000)) / 1000;
        jobs.set(mode, Math.min(jobs.get(mode) || interval, interval));
    }
    if (!jobs.size)
        return;
    try {
        metricCancellable = new Gio.Cancellable();
        metricProc = Gio.Subprocess.new(['/usr/bin/setsid', 'python3', path, ...Array.from(jobs, ([mode, interval]) => `${mode}:${interval}`)],
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE);
        const proc = metricProc;
        const cancellable = metricCancellable;
        const stream = new Gio.DataInputStream({base_stream: proc.get_stdout_pipe()});
        metricLastOutput = GLib.get_monotonic_time();
        metricWatchdog = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 5000, () => {
            const longest = 35;
            if ((GLib.get_monotonic_time() - metricLastOutput) / 1000000 > longest) {
                stopMetrics();
                scheduleMetrics();
                return GLib.SOURCE_REMOVE;
            }
            return GLib.SOURCE_CONTINUE;
        });
        while (generation === metricGeneration) {
            const [bytes] = await stream.read_line_async(GLib.PRIORITY_DEFAULT, cancellable);
            if (!bytes)
                throw new Error('Coletor de métricas encerrou.');
            if (bytes.length > 16384)
                throw new Error('Resposta de métricas excedida.');
            const data = JSON.parse(new TextDecoder().decode(bytes));
            if (!['cpu', 'processes', 'network', 'heartbeat'].includes(data.mode) || typeof data.text !== 'string' || data.text.length > 8192)
                throw new Error('Resposta de métricas inválida.');
            metricLastOutput = GLib.get_monotonic_time();
            if (generation !== metricGeneration)
                break;
            for (const label of metricLabels) {
                if (!label._networkDestroyed && metricMode(getData(label.widgetIndex, label.elementIndex, 'Text_Command')) === data.mode) {
                    if (data.mode === 'cpu') {
                        if (!Array.isArray(data.devices) || data.devices.length > 8 || data.devices.some(device => !device ||
                            typeof device.name !== 'string' || !/^[A-Za-z0-9_.-]{1,128}$/.test(device.name) ||
                            typeof device.identity !== 'string' || device.identity.length > 100)) throw new Error('Mapa de dispositivos inválido.');
                        label._externalDevices = data.devices;
                    }
                    if (label.text !== data.text) { label.text = data.text; label.clutter_text.set_markup(data.text); }
                }
            }
        }
    } catch (error) {
        if (generation === metricGeneration) {
            stopMetrics();
            for (const label of metricLabels)
                if (!label._networkDestroyed)
                    label._setErrorState();
            if (widgetsEnabled && metricLabels.size && !metricRestart)
                metricRestart = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 5000, () => {
                    metricRestart = null;
                    startMetrics();
                    return GLib.SOURCE_REMOVE;
                });
        }
    }
}

const networkClickLabels = new Set();
let networkClickTimer = null;
let desktopInputRects = null;
function releaseWidgetDragCapture() {
    if (widgetDragKeySignal) { global.stage.disconnect(widgetDragKeySignal); widgetDragKeySignal = 0; }
    if (widgetDragGrab) {
        const grab = widgetDragGrab;
        widgetDragGrab = null;
        Main.popModal(grab);
    }
}

function updateWidgetDrag(pointer) {
    if (Main.sessionMode?.isLocked || Main.overview.visible) {
        widgetDragController?.cancel();
        return false;
    }
    if (!widgetDragController && dragWidgets.size) {
        widgetDragController = new Me.imports.dragging.PointerDragController({
            buttonMask: Clutter.ModifierType.BUTTON1_MASK,
            superMask: Clutter.ModifierType.SUPER_MASK,
            mod4Mask: Clutter.ModifierType.MOD4_MASK,
            controlMask: Clutter.ModifierType.CONTROL_MASK,
            widgets: () => [...dragWidgets].filter(widget => !widget._grouped && !widget._widgetDestroyed &&
                widget.get_paint_visibility() && !getData(widget.widgetIndex, 0, 'Lock_Widget', 'bool'))
                .sort((a,b) => a.widgetIndex - b.widgetIndex),
            canStart: pointer => !desktopPointerBlocked(pointer),
            begin: widget => {
                try {
                widgetDragGrab = Main.pushModal(Main.uiGroup);
                widgetDragKeySignal = global.stage.connect('captured-event', (_stage,event) => {
                    if (event.type() === Clutter.EventType.KEY_PRESS && event.get_key_symbol() === Clutter.KEY_Escape) {
                        widgetDragController?.cancel();
                        return Clutter.EVENT_STOP;
                    }
                    return Clutter.EVENT_PROPAGATE;
                });
                widget._onDragBegin();
                } catch (error) { releaseWidgetDragCapture(); logError(error, 'Início do arraste'); return false; }
            },
            move: (widget,x,y) => widget.set_position(x,y),
            finish: (widget,drop) => {
                releaseWidgetDragCapture();
                widget._acceptedDrop = drop;
                widget._onDragEnd();
                if (!drop && !widget._widgetDestroyed) widget.setPositionFromSettings();
            },
        });
    }
    return widgetDragController?.update(pointer) || false;
}

// Polling must obey the same occlusion rules as native window input.
function desktopPointerBlocked(pointer) {
    if (Main.sessionMode?.isLocked || Main.modalCount || Main.overview.visible) return true;
    for (const label of networkClickLabels) {
        if (label._networkBackdrop?.visible || label._networkDialog?.visible) return true;
    }
    const [x, y] = pointer;
    let rects;
    try { rects = desktopInputRects ?? desktopOccludingRects(); }
    catch (error) { return true; } // Wait until window geometry is available again.
    return rects.some(rect => x >= rect.x && x < rect.x + rect.width && y >= rect.y && y < rect.y + rect.height);
}

function desktopOccludingRects() {
    const workspace = global.workspace_manager.get_active_workspace();
    const rects = [];
    for (const actor of global.get_window_actors()) {
        const window = actor.meta_window;
        if (!window || !actor.visible || window.get_window_type() === Meta.WindowType.DESKTOP ||
            window.get_gtk_application_id?.() === 'com.rastersoft.ding' || window.customJS_ding?._keepAtBottom ||
            !window.showing_on_its_workspace() || !window.located_on_workspace(workspace)) continue;
        rects.push(window.get_frame_rect());
    }
    return rects;
}

function bindDesktopLauncher(button, launch) {
    let held = false, start = null, lastLaunch = -Infinity;
    const activate = () => {
        if (!button.get_paint_visibility() || desktopPointerBlocked(global.get_pointer())) return;
        const now = GLib.get_monotonic_time();
        if (now - lastLaunch < 700000) return;
        lastLaunch = now;
        launch();
    };
    button.connect('clicked', activate);
    button._checkNetworkClick = pointer => {
        const [px, py, mask] = pointer;
        const down = !!(mask & Clutter.ModifierType.BUTTON1_MASK);
        const [x, y] = button.get_transformed_position();
        const [width, height] = button.get_transformed_size();
        const inside = button.get_paint_visibility() && px >= x && px < x + width && py >= y && py < y + height;
        const blocked = desktopPointerBlocked(pointer) || activeWidgetDrag ||
            ((mask & (Clutter.ModifierType.SUPER_MASK | Clutter.ModifierType.MOD4_MASK)) && (mask & Clutter.ModifierType.CONTROL_MASK));
        if (blocked) start = null;
        if (down && !held) start = inside && !blocked ? [px, py] : null;
        if (!down && held && inside && !blocked && start && Math.abs(px - start[0]) < 8 && Math.abs(py - start[1]) < 8)
            activate();
        held = down;
        if (!down) start = null;
        return inside && !blocked;
    };
    networkClickLabels.add(button);
    button.connect('destroy', () => networkClickLabels.delete(button));
    scheduleNetworkClicks();
}

function scheduleNetworkClicks(delay = 250) {
    if (networkClickTimer || (!networkClickLabels.size && !dragWidgets.size))
        return;
    networkClickTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, delay, () => {
        networkClickTimer = null;
        let active = false;
        const pointer = global.get_pointer();
        try { desktopInputRects = desktopOccludingRects(); }
        catch (error) { desktopInputRects = null; logError(error, 'Janelas sobre os widgets'); }
        try { active = updateWidgetDrag(pointer); }
        catch (error) {
            try { widgetDragController?.cancel(); } catch (_) { releaseWidgetDragCapture(); }
            logError(error, 'Arraste dos widgets');
        }
        try {
            for (const label of networkClickLabels) {
                try { active = label._checkNetworkClick(pointer) || active; }
                catch (error) { logError(error, 'Interação de um widget'); }
            }
        } finally { desktopInputRects = null; }
        scheduleNetworkClicks(active ? 25 : 250);
        return GLib.SOURCE_REMOVE;
    });
}


const AnchorPoint = {
    TOP_LEFT: 0,
    BOTTOM_LEFT: 1,
    TOP_RIGHT: 2,
    BOTTOM_RIGHT: 3,
};

/**
 * @param {string} msg message to log
 */
function debugLog(msg) {
    if (DEBUG_LOG)
        log(msg);
}

function getData(widgetIndex, elementIndex, elementName, parseType) {
    return Utils.getData(WIDGETDATA, widgetIndex, elementIndex, elementName, parseType);
}

function setData(widgetIndex, elementIndex, elementName, newValue) {
    Utils.setData(WIDGETDATA, widgetIndex, elementIndex, elementName, newValue);
}

function getClockDate(widgetIndex, elementIndex, origDate) {
    const overrideTimeZoneEnabled = getData(widgetIndex, elementIndex, 'TimeZoneOverrideEnabled', 'bool');
    const overrideTimeZone = getData(widgetIndex, elementIndex, 'TimeZoneOverride') || 'UTC';

    if (overrideTimeZoneEnabled) {
        const gTimeZone = GLib.TimeZone.new(overrideTimeZone);
        const localDateTime = GLib.DateTime.new_now(gTimeZone);

        const year = localDateTime.get_year();
        const monthIndex = localDateTime.get_month() - 1;
        const day = localDateTime.get_day_of_month();
        const hours = localDateTime.get_hour();
        const minutes = localDateTime.get_minute();
        const seconds = localDateTime.get_second();

        const newDate = new Date(year, monthIndex, day, hours, minutes, seconds);

        return newDate;
    } else {
        return origDate;
    }
}

const PANEL_TITLE_STYLE = 'font-family: sans-serif; font-size: 15px; font-weight: bold; color: white; padding-bottom: 4px;';

var DesktopWidget = GObject.registerClass(
class AzClockDesktopWidget extends St.Widget {
    _init(index) {
        super._init({
            layout_manager: new Clutter.BoxLayout(),
            reactive: true,
            track_hover: true,
            can_focus: true,
            x_align: Clutter.ActorAlign.FILL,
            y_align: Clutter.ActorAlign.FILL,
            pivot_point: new Graphene.Point({x: 0.5, y: .5}),
        });

        try {
        this._widgetIndex = index;

        const isVertical = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_VerticalLayout', 'bool');
        this.layout_manager.orientation = isVertical ? Clutter.Orientation.VERTICAL : Clutter.Orientation.HORIZONTAL;

        this._menuManager = new PopupMenu.PopupMenuManager(this);

        this.connect('notify::hover', () => this._onHover());
        this.connect('destroy', () => this._onDestroy());

        if (!WIDGETDATA[index][0].Parent_Id && !Utils.getData(WIDGETDATA, index, WIDGET_DATA_INDEX, 'Lock_Widget', 'bool'))
            this.makeDraggable();

        this.createElements();
        this.updateClocks(true);
        } catch (error) { this.destroy(); throw error; }
    }

    _getStableWidth() {
        if (this._grouped) return this._groupWidth || 280;
        const configured = Number(getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_Width'));
        const meta = WIDGETDATA[this._widgetIndex][0];
        if (meta.Box_IsGroup === 'true') {
            const columns = Math.max(1, Math.min(4, Number(meta.Group_Columns) || 1));
            return Math.max(Number.isFinite(configured) ? Math.max(0, Math.min(2000, configured)) : 320,
                columns * 180 + (columns - 1) * (Number(meta.Box_Spacing) || 8) + 2 * (Number(meta.Box_Padding) || 0) + 2 * (Number(meta.Box_BorderWidth) || 0));
        }
        if (Number.isFinite(configured) && configured >= 80 && configured <= 2000)
            return configured;
        const elements = WIDGETDATA[this._widgetIndex].slice(1);
        if (elements.some(element => element.Element_Type === DIGITAL_CLOCK))
            return 440;
        if (elements.some(element => (element.Text_Command || '').includes('/clima-widget.py')))
            return 440;
        return null;
    }

    vfunc_get_preferred_width(forHeight) {
        const width = this._getStableWidth();
        return width === null ? super.vfunc_get_preferred_width(forHeight) : [width, width];
    }

    vfunc_get_preferred_height(forWidth) {
        return super.vfunc_get_preferred_height(this._getStableWidth() ?? forWidth);
    }

    vfunc_allocate(box) {
        if (this._isDragging || this._grouped) {
            super.vfunc_allocate(box);
            return;
        }
        const [, width] = this.get_preferred_width(-1);
        const [, height] = this.get_preferred_height(width);
        box.set_size(width, height);
        const x = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Location_X', 'int');
        const y = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Location_Y', 'int');
        const anchor = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_AnchorPoint', 'int');
        const right = anchor === AnchorPoint.TOP_RIGHT || anchor === AnchorPoint.BOTTOM_RIGHT;
        const bottom = anchor === AnchorPoint.BOTTOM_LEFT || anchor === AnchorPoint.BOTTOM_RIGHT;
        box.set_origin(right ? x - width : x, bottom ? y - height : y);
        super.vfunc_allocate(box);
    }

    get widgetIndex() {
        return this._widgetIndex;
    }

    set widgetIndex(index) {
        this._widgetIndex = index;
        this._updateIndex(index);
    }

    createElements() {
        this.destroy_all_children();

        const clockData = WIDGETDATA[this._widgetIndex];

        this._analogClocks = [];
        this._digitalClocks = [];
        this._textLabels = [];
        this._commandLabels = [];

        if (clockData[0].Panel_Title)
            this.add_child(new St.Label({text: clockData[0].Panel_Title, style: PANEL_TITLE_STYLE}));

        // skip first element as that stores widget layout/style data, not widget elements
        for (let i = 1; i < clockData.length; i++) {
            const clockType = getData(this._widgetIndex, i, 'Element_Type');
            if (clockType === DIGITAL_CLOCK) {
                const digitalClock = new DigitalClock(this._widgetIndex, i);
                const clockButton = new St.Button({reactive:true,can_focus:true,child:digitalClock,
                    accessible_name:'Abrir calendário e tarefas',style:'padding:0;'});
                bindDesktopLauncher(clockButton,()=>Calendar.openCalendar());
                this.add_child(clockButton);
                this._digitalClocks.push(digitalClock);
            } else if (clockType === ANALOG_CLOCK) {
                const analogClock = new AnalogClock(this._widgetIndex, i, clockData[i]);
                this.add_child(analogClock);
                this._analogClocks.push(analogClock);
            } else if (clockType === TEXT_LABEL && ['youtube', 'gemini', 'btop', 'notes'].includes(clockData[i].Launcher_Action)) {
                const notes = clockData[i].Launcher_Action === 'notes';
                const gemini = clockData[i].Launcher_Action === 'gemini';
                const btop = clockData[i].Launcher_Action === 'btop';
                const name = notes ? 'Post-its Orbitz' : btop ? 'Monitor do sistema' : gemini ? 'Gemini' : 'YouTube';
                const button = new St.Button({reactive: true, can_focus: true, accessible_name: `Abrir ${name}`,
                    style: 'padding: 4px; border-radius: 8px;'});
                button.set_child(new St.Icon({gicon: Gio.icon_new_for_string(GLib.build_filenamev([Me.path, notes ? 'notes-widget' : btop ? 'media' : gemini ? 'gemini-widget' : 'youtube-widget', notes ? 'notes.svg' : btop ? 'btop.png' : gemini ? 'gemini.svg' : 'youtube.svg'])), icon_size: 32}));
                bindDesktopLauncher(button, async () => {
                    try {
                        const argv = notes ? ['/usr/bin/env', 'GDK_BACKEND=x11', '/usr/bin/python3', GLib.build_filenamev([GLib.get_user_data_dir(), 'orbitz-postits', 'app', 'postits.py'])] : btop ? ['/usr/bin/tilix', '-e', '/usr/bin/btop'] : gemini
                            ? ['/usr/bin/google-chrome', '--app=https://gemini.google.com/', '--window-size=1100,900']
                            : ['/usr/bin/python3', GLib.build_filenamev([Me.path, 'youtube-widget', 'youtube-widget.py'])];
                        const proc = Gio.Subprocess.new(argv, Gio.SubprocessFlags.NONE);
                        await proc.wait_async(null);
                        if (!proc.get_successful()) throw new Error('O aplicativo encerrou com erro.');
                    } catch (error) {
                        logError(error, `Lançador ${name}`);
                        Main.notify(name, 'Não foi possível abrir o aplicativo. Consulte os logs da sessão.');
                    }
                });
                this.add_child(button);
            } else if (clockType === TEXT_LABEL) {
                const label = new TextLabel(this._widgetIndex, i);
                this.add_child(label);
                this._textLabels.push(label);
            } else if (clockType === COMMAND_LABEL) {
                const commandLabel = new CommandLabel(this._widgetIndex, i);
                this.add_child(commandLabel);
                this._commandLabels.push(commandLabel);
            }
        }

        this.queue_relayout();
    }

    updateClocks(immediate = false) {
        for (const analogClock of this._analogClocks)
            analogClock.updateClock(immediate);
        for (const digitalClock of this._digitalClocks)
            digitalClock.updateClock(immediate);
    }

    setElementsStyle() {
        for (const analogClock of this._analogClocks)
            analogClock.setStyle();
        for (const digitalClock of this._digitalClocks)
            digitalClock.setStyle();
        for (const textLabel of this._textLabels)
            textLabel.setStyle();
        for (const commandLabel of this._commandLabels)
            commandLabel.setStyle();
    }

    _updateIndex(index) {
        for (const analogClock of this._analogClocks)
            analogClock.widgetIndex = index;
        for (const digitalClock of this._digitalClocks)
            digitalClock.widgetIndex = index;
        for (const textLabel of this._textLabels)
            textLabel.widgetIndex = index;
        for (const commandLabel of this._commandLabels)
            commandLabel.widgetIndex = index;
    }

    _refreshCommands() {
        for (const commandLabel of this._commandLabels)
            commandLabel.refreshCommand();
    }

    updateComponents(delay = 300) {
        debugLog('update components');
        let priority = GLib.PRIORITY_DEFAULT_IDLE;
        if (delay !== 300)
            priority = GLib.PRIORITY_DEFAULT;

        if (this._updateClockId)
            return;
        this._updateClockId = GLib.timeout_add(priority, delay, () => {
            this._updateClockId = null;
            try {
            this.setStyle();
            this.setElementsStyle();
            if (this._grouped) this.setStyle();
            if (this._subwidgetBox) this.layout_manager.orientation = Clutter.Orientation.VERTICAL;
            this._refreshCommands();
            this.queue_relayout();
            this.setPositionFromSettings();
            this.queue_relayout();
            this.updateClocks(true);
            } catch (error) { this._onInitializationError?.(error); }
            return GLib.SOURCE_REMOVE;
        });
    }

    setPositionFromSettings() {
        if (this._grouped) return;
        const x = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Location_X', 'int');
        const y = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Location_Y', 'int');
        debugLog(`set pos from settings - (${x}, ${y})`);
        this.set_position(x, y);
    }

    setStyle() {
        const isVertical = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_VerticalLayout', 'bool');
        this.layout_manager.orientation = isVertical ? Clutter.Orientation.VERTICAL : Clutter.Orientation.HORIZONTAL;

        const borderEnabled = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_BorderEnabled', 'bool');
        const borderWidth = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_BorderWidth', 'int');
        const borderRadius = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_BorderRadius', 'int');
        const borderColor = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_BorderColor');
        const backgroundEnabled = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_BackgroundEnabled', 'bool');
        const backgroundColor = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_BackgroundColor');
        const boxSpacing = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_Spacing', 'int');
        const boxPadding = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_Padding', 'int');

        this.layoutManager.spacing = boxSpacing;
        let style = `padding: ${boxPadding}px;`;

        if (backgroundEnabled) {
            style += `background-color: ${backgroundColor};
                      border-radius: ${borderRadius}px;`;
        }

        if (borderEnabled) {
            style += `border-width: ${borderWidth}px;
                      border-color: ${borderColor};`;
        }

        if (this._grouped) {
            style = `padding: 12px; background-color: rgba(20,24,28,0.82); border: 1px solid rgba(190,200,210,0.22); border-radius: 10px;`;
            for (const label of [...this._commandLabels, ...this._textLabels]) {
                label.setStyle();
                label.x_align = Clutter.ActorAlign.FILL;
                label.style = label.style.replace(/text-align\s*:[^;]+;?/g, '') + '; text-align: left; font-family: sans-serif; color: white;';
                label.clutter_text.set_line_alignment(Pango.Alignment.LEFT);
            }
        }
        this.style = style;

        this.z_position = WIDGETDATA.length - this._widgetIndex;
    }

    vfunc_button_press_event() {
        if (this._grouped) return Clutter.EVENT_PROPAGATE;
        const event = Clutter.get_current_event();

        const dragMask = Clutter.ModifierType.SUPER_MASK | Clutter.ModifierType.CONTROL_MASK;
        if (event.get_button() === 1 && (event.get_state() & dragMask) !== dragMask) {
            this._setPopupTimeout();
        } else if (event.get_button() === 3) {
            this._popupMenu();
            return Clutter.EVENT_STOP;
        }

        return Clutter.EVENT_PROPAGATE;
    }

    vfunc_button_release_event() {
        this._removeMenuTimeout();
        return Clutter.EVENT_PROPAGATE;
    }

    _onDragBegin() {
        this._menu?.close(true);
        this._removeMenuTimeout();
        this._isDragging = true;
        this._acceptedDrop = null;
        activeWidgetDrag = this;
        for (const label of networkClickLabels) label._networkClickStart = null;
    }

    _onDragEnd() {
        this._isDragging = false;
        if (activeWidgetDrag === this) activeWidgetDrag = null;
        const drop = this._acceptedDrop;
        this._acceptedDrop = null;
        if (this._widgetDestroyed) return;
        this.queue_relayout();
        if (!drop) return;
        const [px, py] = drop.pointer;
        const monitor = Main.layoutManager.monitors.find(item => px >= item.x && px < item.x + item.width &&
            py >= item.y && py < item.y + item.height) || Main.layoutManager.primaryMonitor;
        if (!monitor) return;
        const anchor = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_AnchorPoint', 'int');
        const position = Me.imports.dragging.dropPosition(drop.x, drop.y, this.width, this.height, monitor, anchor);
        const data = Me.settings.get_value('widget-data').deep_unpack();
        if (!data[this._widgetIndex] || data[this._widgetIndex][0].Parent_Id) return;
        data[this._widgetIndex][0].Location_X = String(position.x);
        data[this._widgetIndex][0].Location_Y = String(position.y);
        Me.settings.set_value('changed-data', new GLib.Variant('a{ss}', {
            WidgetIndex: String(this._widgetIndex), WidgetMoved: 'true',
        }));
        Me.settings.set_value('widget-data', new GLib.Variant('aaa{ss}', data));
        WIDGETDATA[this._widgetIndex][0].Location_X = String(position.x);
        WIDGETDATA[this._widgetIndex][0].Location_Y = String(position.y);
        this.setPositionFromSettings();
    }

    getDragActorSource() {
        return this;
    }

    makeDraggable() {
        this._draggable = true;
        dragWidgets.add(this);
        scheduleNetworkClicks();
    }

    _onHover() {
        if (!this.hover)
            this._removeMenuTimeout();
    }

    _removeMenuTimeout() {
        if (this._menuTimeoutId > 0) {
            GLib.source_remove(this._menuTimeoutId);
            this._menuTimeoutId = 0;
        }
    }

    _setPopupTimeout() {
        this._removeMenuTimeout();
        this._menuTimeoutId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 600, () => {
            this._menuTimeoutId = 0;
            this._popupMenu();
            return GLib.SOURCE_REMOVE;
        });
        GLib.Source.set_name_by_id(this._menuTimeoutId, '[azclock] this.popupMenu');
    }

    _popupMenu() {
        this._removeMenuTimeout();

        if (!this._menu) {
            this._menu = new PopupMenu.PopupMenu(this, 0.5, St.Side.TOP);
            const lockWidgetItem = this._menu.addAction('', () => {
                this._menu.close();
                const lockWidget = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Lock_Widget', 'bool');

                Me.settings.set_value('changed-data', new GLib.Variant('a{ss}', {
                    'WidgetIndex': this._widgetIndex.toString(),
                    'ElementIndex': WIDGET_DATA_INDEX.toString(),
                    'ElementType': 'Lock_Widget',
                }));

                setData(this._widgetIndex, WIDGET_DATA_INDEX, 'Lock_Widget', !lockWidget);
            });

            const lockWidget = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Lock_Widget', 'bool');
            lockWidgetItem.label.text = lockWidget ? _('Unlock') : _('Lock');

            this._menu.addAction(_('Desktop Clock Settings'), () => {
                ExtensionUtils.openPrefs();
            });

            Main.uiGroup.add_actor(this._menu.actor);
            this._menuManager.addMenu(this._menu);
        }

        this._menu.open();
        return false;
    }

    _onDestroy() {
        this._widgetDestroyed = true;
        if (widgetDragController?.state?.widget === this) widgetDragController.cancel();
        dragWidgets.delete(this);
        if (activeWidgetDrag === this) activeWidgetDrag = null;
        if (!dragWidgets.size && !networkClickLabels.size && networkClickTimer) { GLib.source_remove(networkClickTimer); networkClickTimer = null; }
        this._removeMenuTimeout();
        if (this._menu) {
            this._menuManager.removeMenu(this._menu);
            this._menu.destroy();
            this._menu = null;
        }

        if (this._updateClockId) {
            GLib.source_remove(this._updateClockId);
            this._updateClockId = null;
        }

    }
});

var AnalogClock = GObject.registerClass(
class AzClockAnalogClock extends Clutter.Actor {
    _init(widgetIndex, elementIndex, elementData) {
        super._init({
            layout_manager: new Clutter.BinLayout(),
            x_align: Clutter.ActorAlign.FILL,
            y_align: Clutter.ActorAlign.FILL,
        });

        this.widgetIndex = widgetIndex;
        this.elementIndex = elementIndex;

        this._clockFace = new St.Icon({
            x_align: Clutter.ActorAlign.FILL,
            y_align: Clutter.ActorAlign.FILL,
            visible: elementData['ClockFace_Visible'] === 'true',
        });

        this._secondHand = new St.Icon({
            pivot_point: new Graphene.Point({x: 0.5, y: .5}),
            y_expand: false,
            y_align: Clutter.ActorAlign.START,
            visible: elementData['SecondHand_Visible'] === 'true',
        });

        this._minuteHand = new St.Icon({
            pivot_point: new Graphene.Point({x: 0.5, y: .5}),
            y_align: Clutter.ActorAlign.START,
        });

        this._hourHand = new St.Icon({
            pivot_point: new Graphene.Point({x: 0.5, y: .5}),
            y_align: Clutter.ActorAlign.START,
        });

        this._clockButton = new St.Icon({
            pivot_point: new Graphene.Point({x: 0.5, y: .5}),
            x_align: Clutter.ActorAlign.FILL,
            y_align: Clutter.ActorAlign.FILL,
            visible: elementData['ClockButton_Visible'] === 'true',
        });

        this.add_actor(this._clockFace);
        this.add_actor(this._hourHand);
        this.add_actor(this._minuteHand);
        this.add_actor(this._secondHand);
        this.add_actor(this._clockButton);
    }

    setAnalogClockStyle(element, elementName) {
        const clockData = WIDGETDATA[this.widgetIndex];
        const directoryName = elementName.toLowerCase();
        const filePath = `${Me.path}/media/${directoryName}/${directoryName}`;

        const data = clockData[this.elementIndex];
        const styleType = data[`${elementName}_Style`] || 1;

        element.style = this.getStyle(data, elementName);

        if (elementName === 'ClockFace' || elementName === 'SecondHand' || elementName === 'ClockButton')
            element.visible = getData(this.widgetIndex, this.elementIndex, `${elementName}_Visible`, 'bool');

        element.gicon = Gio.icon_new_for_string(`${filePath}-${styleType}-symbolic.svg`);
        element.icon_size = parseInt(data['Clock_Size']);
    }

    getStyle(data, element) {
        let style = `color: ${data[`${element}_Color`]};`;

        const backgroundColor = data[`${element}_BackgroundColor`];
        const borderRadius = data[`${element}_BorderRadius`];
        const borderEnabled = data[`${element}_BorderEnabled`] === 'true';
        const shadowEnabled = data[`${element}_ShadowEnabled`] === 'true';
        const boxShadowEnabled = data[`${element}_BoxShadowEnabled`] === 'true';

        if (backgroundColor)
            style += `background-color: ${backgroundColor};`;
        if (borderRadius)
            style += `border-radius: ${borderRadius}px;`;

        if (borderEnabled) {
            const borderWidth = data[`${element}_BorderWidth`];
            const borderColor = data[`${element}_BorderColor`];
            if (borderWidth)
                style += `border: ${borderWidth}px;`;
            if (borderColor)
                style += `border-color: ${borderColor};`;
        }

        if (shadowEnabled) {
            const shadow = `${element}_Shadow`;
            style += `icon-shadow: ${data[`${shadow}X`]}px ${data[`${shadow}Y`]}px ${data[`${shadow}Blur`]}px ${data[`${shadow}Spread`]}px ${data[`${shadow}Color`]};`;
        }
        if (boxShadowEnabled) {
            const boxShadow = `${element}_BoxShadow`;
            style += `box-shadow: ${data[`${boxShadow}X`]}px ${data[`${boxShadow}Y`]}px ${data[`${boxShadow}Blur`]}px ${data[`${boxShadow}Spread`]}px ${data[`${boxShadow}Color`]};`;
        }
        return style;
    }

    setStyle() {
        this.setAnalogClockStyle(this._clockFace, 'ClockFace');
        this.setAnalogClockStyle(this._secondHand, 'SecondHand');
        this.setAnalogClockStyle(this._minuteHand, 'MinuteHand');
        this.setAnalogClockStyle(this._hourHand, 'HourHand');
        this.setAnalogClockStyle(this._clockButton, 'ClockButton');
    }

    updateClock(immediate = false) {
        const date = new Date();

        const elementDate = getClockDate(this.widgetIndex, this.elementIndex, date);
        this.tickClock(elementDate, immediate);

        this.queue_relayout();
    }

    tickClock(date, immediate) {
        // Keep hours in 12 hour format for analog clock
        if (date.getHours() >= 12)
            date.setHours(date.getHours() - 12);

        const degrees = 6; // each minute and second tick represents a 6 degree increment.
        const secondsInDegrees = date.getSeconds() * degrees;
        const minutesInDegrees = date.getMinutes() * degrees;
        const hoursInDegrees = date.getHours() * 30;

        if (this._secondHand.visible)
            this.tickClockHand(this._secondHand, secondsInDegrees, immediate);

        this.tickClockHand(this._minuteHand, minutesInDegrees, immediate);
        this.tickClockHand(this._hourHand, hoursInDegrees + minutesInDegrees / 12, immediate);
    }

    tickClockHand(hand, rotationDegree, immediate) {
        hand.remove_all_transitions();
        if (rotationDegree === hand.rotation_angle_z)
            return;

        // Prevent the clock hand from spinning counter clockwise back to 0.
        if (rotationDegree === 0 && hand.rotation_angle_z !== 0)
            rotationDegree = 360;

        hand.ease({
            opacity: 255, // onComplete() seems to trigger instantly without this.
            rotation_angle_z: rotationDegree,
            mode: Clutter.AnimationMode.EASE_OUT_QUAD,
            duration: immediate ? 0 : 300,
            onComplete: () => {
                if (rotationDegree === 360)
                    hand.rotation_angle_z = 0;
            },
        });
    }
});

var Label = GObject.registerClass(
class AzClockLabel extends St.Label {
    _init(widgetIndex, elementIndex) {
        this.widgetIndex = widgetIndex;
        this.elementIndex = elementIndex;
        super._init({
            y_align: Clutter.ActorAlign.CENTER,
            pivot_point: new Graphene.Point({x: 0.5, y: 0.5}),
        });

        this.clutter_text.set({
            ellipsize: Pango.EllipsizeMode.NONE,
            line_wrap: false,
            line_wrap_mode: Pango.WrapMode.WORD_CHAR,
        });
    }

    setStyle() {
        const index = this.elementIndex;
        const configuredWidth = Number(getData(this.widgetIndex, WIDGET_DATA_INDEX, 'Box_Width'));
        const elements = WIDGETDATA[this.widgetIndex].slice(1);
        const wrap = (Number.isFinite(configuredWidth) && configuredWidth >= 80 && configuredWidth <= 2000) ||
            elements.some(element => element.Element_Type === DIGITAL_CLOCK ||
                (element.Text_Command || '').includes('/clima-widget.py'));
        this.clutter_text.set_line_wrap(wrap);


        const shadowEnabled = getData(this.widgetIndex, index, 'Text_ShadowEnabled', 'bool');
        const shadowX = getData(this.widgetIndex, index, 'Text_ShadowX');
        const shadowY = getData(this.widgetIndex, index, 'Text_ShadowY');
        const shadowSpread = getData(this.widgetIndex, index, 'Text_ShadowSpread');
        const shadowBlur = getData(this.widgetIndex, index, 'Text_ShadowBlur');
        const shadowColor = getData(this.widgetIndex, index, 'Text_ShadowColor');

        const customFontEnabled = getData(this.widgetIndex, index, 'Text_CustomFontEnabled', 'bool');
        const customFontFamily = getData(this.widgetIndex, index, 'Text_CustomFontFamily');

        const textColor = getData(this.widgetIndex, index, 'Text_Color');
        const textSize = getData(this.widgetIndex, index, 'Text_Size');

        const textAlignmentX = getData(this.widgetIndex, index, 'Text_AlignmentX', 'clutter_align');
        const textAlignmentY = getData(this.widgetIndex, index, 'Text_AlignmentY', 'clutter_align');
        const grouped = !!WIDGETDATA[this.widgetIndex][0].Parent_Id;
        const compact = grouped && (getData(this.widgetIndex, index, 'Text_Command') || '').includes('/cpu-ram-widget.py');
        const textLineAlignment = grouped ? 'left' : getData(this.widgetIndex, index, 'Text_LineAlignment', 'align');

        const marginTop = getData(this.widgetIndex, index, 'Element_Margin_Top', 'int');
        const marginLeft = getData(this.widgetIndex, index, 'Element_Margin_Left', 'int');
        const marginBottom = getData(this.widgetIndex, index, 'Element_Margin_Bottom', 'int');
        const marginRight = getData(this.widgetIndex, index, 'Element_Margin_Right', 'int');

        const paddingTop = getData(this.widgetIndex, index, 'Element_Padding_Top', 'int');
        const paddingLeft = getData(this.widgetIndex, index, 'Element_Padding_Left', 'int');
        const paddingBottom = getData(this.widgetIndex, index, 'Element_Padding_Bottom', 'int');
        const paddingRight = getData(this.widgetIndex, index, 'Element_Padding_Right', 'int');

        const borderEnabled = getData(this.widgetIndex, index, 'Text_BorderEnabled', 'bool');
        const borderWidth = getData(this.widgetIndex, index, 'Text_BorderWidth', 'int');
        const borderRadius = getData(this.widgetIndex, index, 'Text_BorderRadius', 'int');
        const borderColor = getData(this.widgetIndex, index, 'Text_BorderColor');
        const backgroundEnabled = getData(this.widgetIndex, index, 'Text_BackgroundEnabled', 'bool');
        const backgroundColor = getData(this.widgetIndex, index, 'Text_BackgroundColor');

        const margin = `margin: ${marginTop}px ${marginRight}px ${marginBottom}px ${marginLeft}px`;
        const padding = `padding: ${paddingTop}px ${paddingRight}px ${paddingBottom}px ${paddingLeft}px`;

        let textStyle = `color: ${textColor}; ${margin}; ${padding};`;

        if (backgroundEnabled) {
            textStyle += `background-color: ${backgroundColor};
                            border-radius: ${borderRadius}px;`;
        }

        if (borderEnabled) {
            textStyle += `border-width: ${borderWidth}px;
                            border-color: ${borderColor};`;
        }

        if (shadowEnabled)
            textStyle += `text-shadow: ${shadowX}px ${shadowY}px ${shadowBlur}px ${shadowSpread}px ${shadowColor};`;

        if (customFontEnabled) {
            const fontDesc = Pango.font_description_from_string(customFontFamily);
            textStyle += `font-family: "${fontDesc.get_family()}";`;
        }

        if (textLineAlignment)
            textStyle += `text-align: ${textLineAlignment}`;

        this.style = `font-size: ${compact ? '10px' : grouped ? '15px' : textSize + 'pt'}; font-feature-settings: "tnum";${textStyle}`;

        this.x_align = textAlignmentX;
        this.y_align = textAlignmentY;
    }
});

var DigitalClock = GObject.registerClass(
class AzClockDigitalClock extends Label {
    _init(widgetIndex, elementIndex) {
        super._init(widgetIndex, elementIndex);
    }

    setStyle() {
        super.setStyle();
        const dateFormat = getData(this.widgetIndex, this.elementIndex, 'Text_DateFormat');
        this._dateFormat = dateFormat;
    }

    updateClock() {
        const date = new Date();

        const dateFormat = this._dateFormat;
        const elementDate = getClockDate(this.widgetIndex, this.elementIndex, date);

        if (dateFormat) {
            const next = elementDate.toLocaleFormat(dateFormat);
            if (this.text === next)
                return;
            this.text = next;
            this.clutter_text.set_markup(this.text);
        }

        this.queue_relayout();
    }
});

var TextLabel = GObject.registerClass(
class AzClockTextLabel extends Label {
    _init(widgetIndex, elementIndex) {
        super._init(widgetIndex, elementIndex);
    }

    setStyle() {
        super.setStyle();
        const text = getData(this.widgetIndex, this.elementIndex, 'Text_Text');
        this.text = text;
        this.clutter_text.set_markup(this.text);
    }
});

var CommandLabel = GObject.registerClass(
Me.imports.commandPanels.install(class AzClockCommandLabel extends Label {
    _init(widgetIndex, elementIndex) {
        super._init(widgetIndex, elementIndex);

        this.connect('destroy', () => this._removePollingInterval());

        this._hasError = false;
        this._commandRun = null;
        this._pendingCommand = null;
        this._networkTooltip = null;
        this._networkTooltipText = '';
        this._networkConnectionsText = '';
        this._networkConnectionItems = [];
        this._networkConnectionSignature = null;
        this._networkRefreshProcess = null;
        this._networkRefreshRun = null;
        this._networkRefreshPending = false;
        this._networkGeneration = 0;
        this._networkRefreshTimeout = null;
        this._networkDestroyed = false;
        this.reactive = true;
        this.track_hover = true;
        this._networkDialog = null;
        this._networkDialogLabel = null;
        this._speedtestProcess = null;
        this._speedtestTimeout = null;
        this._networkClickTimer = null;
        this._networkClickHeld = false;
        this._networkClickStart = null;
        this.connect('destroy', () => {
            this._networkDestroyed = true;
            metricLabels.delete(this);
            if (!metricLabels.size) {
                stopMetrics();
                if (metricRestart) {
                    GLib.source_remove(metricRestart);
                    metricRestart = null;
                }
            } else { scheduleMetrics(); }
            networkClickLabels.delete(this);
            if (!networkClickLabels.size && !dragWidgets.size && networkClickTimer) {
                GLib.source_remove(networkClickTimer);
                networkClickTimer = null;
            }
            stopCommandRun(this._ejectRun);
            this._stopMedia();
            this._pendingCommand = null;
            this._cancelCommand();
            if (this._speedtestTimeout) {
                GLib.source_remove(this._speedtestTimeout);
                this._speedtestTimeout = null;
            }
            if (this._speedtestProcess) {
                stopCommandRun(this._speedtestRun);
                this._speedtestProcess = null;
            }
            this._closeNetworkDialog();
            if (this._networkDialog) {
                this._networkDialog.destroy();
                this._networkDialog = null;
            }
            if (this._networkClickTimer) {
                GLib.source_remove(this._networkClickTimer);
                this._networkClickTimer = null;
            }
            this._networkBackdrop?.destroy();
            if (this._networkTooltip) {
                this._networkTooltip.destroy();
                this._networkTooltip = null;
            }
        });
    }

    _scheduleNetworkClick() {
        if (this._networkDestroyed)
            return;
        networkClickLabels.add(this);
        scheduleNetworkClicks();
    }

    _storageTarget(pointer) {
        const [ok, localX, localY] = this.clutter_text.transform_stage_point(pointer[0], pointer[1]);
        if (!ok) return null;
        const [, index] = this.clutter_text.get_layout().xy_to_index(0, Math.round(localY * Pango.SCALE));
        const text = this.clutter_text.get_text();
        const before = new TextDecoder().decode(new TextEncoder().encode(text).slice(0, index));
        const line = text.split('\n')[before.split('\n').length - 1] || '';
        if (/^\s*CPU\b/.test(line)) return 'cpu';
        if (/^\s*RAM\b/.test(line)) return 'ram';
        if (/^!?\s*SSD\b/.test(line)) return 'ssd';
        const external = line.match(/^[!⏏]?\s*EXT(\d*)\b/);
        if (!external) return null;
        const [, clicked] = this.clutter_text.get_layout().xy_to_index(Math.round(localX * Pango.SCALE), Math.round(localY * Pango.SCALE));
        const character = new TextDecoder().decode(new TextEncoder().encode(text).slice(clicked));
        return `${character.startsWith('⏏') ? 'eject' : 'external'}:${Number(external[1] || 0)}`;
    }

    async _ejectExternalDevice(device) {
        if (this._ejectRun || this._networkDestroyed) return;
        const run = {cancellable: new Gio.Cancellable(), proc: null};
        this._ejectRun = run;
        Main.notify(`${device.label} · ${device.name}`, 'Ejetando dispositivo. Aguarde a confirmação antes de desconectar.');
        let timeout, timedOut = false;
        try {
            const [, argv] = GLib.shell_parse_argv(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
            run.proc = Gio.Subprocess.new(['/usr/bin/setsid', ...argv, '--eject', '--device', device.name, '--identity', device.identity],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
            timeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 25000, () => { timeout = null; timedOut = true; stopCommandRun(run); return GLib.SOURCE_REMOVE; });
            const [stdout] = await readCommandOutput(run);
            if (this._networkDestroyed) return;
            if (run.cancelled) { if (timedOut) Main.notify('Ejeção não concluída', 'Tempo excedido. Não desconecte ainda.'); return; }
            if (!run.proc.get_successful() || !stdout.startsWith('AZCLOCK_EJECT:')) throw new Error('Falha na ejeção. Não desconecte ainda.');
            const result = JSON.parse(stdout.slice('AZCLOCK_EJECT:'.length));
            if (typeof result.ok !== 'boolean' || typeof result.message !== 'string' || result.message.length > 256)
                throw new Error('Resposta de ejeção inválida. Não desconecte ainda.');
            Main.notify(`${device.label} · ${device.name}`, result.message);
            if (result.ok) { stopMetrics(); scheduleMetrics(); }
        } catch (error) {
            if (!this._networkDestroyed) Main.notify('Ejeção não concluída', timedOut ? 'Tempo excedido. Não desconecte ainda.' : error.message);
        } finally {
            if (timeout) GLib.source_remove(timeout);
            if (this._ejectRun === run) this._ejectRun = null;
        }
    }

    _checkNetworkClick(pointer) {
        if (this._networkDestroyed)
            return false;
        const [px, py, modifiers] = pointer;
        const [x, y] = this.get_transformed_position();
        const [w, h] = this.get_transformed_size();
        const inside = this.get_paint_visibility() && px >= x && px < x + w && py >= y && py < y + h;
        const down = !!(modifiers & Clutter.ModifierType.BUTTON1_MASK);
        const moving = desktopPointerBlocked(pointer) || activeWidgetDrag || ((modifiers & (Clutter.ModifierType.SUPER_MASK | Clutter.ModifierType.MOD4_MASK)) && (modifiers & Clutter.ModifierType.CONTROL_MASK));
        if (moving || !inside) this._networkClickStart = null;
        if (down && !this._networkClickHeld) {
            this._networkClickStart = inside && !moving && !this._networkDialog?.visible ? [px, py] : null;
            this._networkClickDeviceMap = this._externalDevices;
        }
        if (!down && this._networkClickHeld && inside && this._networkClickStart) {
            const [sx, sy] = this._networkClickStart;
            if (Math.abs(px - sx) < 8 && Math.abs(py - sy) < 8) {
                try {
                if (metricMode(getData(this.widgetIndex, this.elementIndex, 'Text_Command')) === 'cpu') {
                    const target = this._storageTarget(pointer);
                    if (!target || target !== this._storageTarget([sx, sy])) { this._networkClickHeld = false; this._networkClickStart = null; return false; }
                    this._hardwareMode = ['cpu', 'ram'].includes(target) ? target : null;
                    this._storageExternal = target.startsWith('external:') || target.startsWith('eject:');
                    this._storageDevice = null;
                    if (this._storageExternal) {
                        const index = Number(target.split(':')[1]);
                        const device = this._networkClickDeviceMap?.[index];
                        if (!device) throw new Error('Dispositivo não disponível. Aguarde a próxima atualização.');
                        this._storageDevice = {...device, label: index ? `EXT${index}` : 'EXT'};
                        if (target.startsWith('eject:')) {
                            this._ejectExternalDevice(this._storageDevice);
                            this._networkClickStart = null; this._networkClickHeld = false;
                            return false;
                        }
                    }
                }
                this._openNetworkDialog();
                } catch (error) {
                logError(error, 'Desktop Clock network click');
                }
            }
        }
        this._networkClickHeld = down;
        if (!down)
            this._networkClickStart = null;
        return inside && !moving && !this._networkDialog?.visible;
    }

    _closeNetworkDialog() {
        if (this._networkModalGrab) {
            Main.popModal(this._networkModalGrab);
            this._networkModalGrab = null;
        }
        this._cancelFirewallInspection();
        this._networkInspecting = false;
        this._networkConnectionSignature = null;
        this._networkGeneration++;
        this._networkRefreshPending = false;
        this._networkDialog?.hide();
        this._networkBackdrop?.hide();
        this._networkClickStart = null;
        if (this._networkRefreshTimeout) {
            GLib.source_remove(this._networkRefreshTimeout);
            this._networkRefreshTimeout = null;
        }
        stopCommandRun(this._networkRefreshRun);
        if (this._speedtestTimeout) {
            GLib.source_remove(this._speedtestTimeout);
            this._speedtestTimeout = null;
        }
        stopCommandRun(this._speedtestRun);
    }

    async _refreshNetworkDialog() {
        if (this._trafficDialog && this._speedtestProcess) {
            this._networkRefreshStatus.text = 'Aguarde o teste de velocidade terminar.';
            return;
        }
        if (this._networkDestroyed || !this._networkDialog?.visible)
            return;
        if (this._networkRefreshRun) {
            if (this._networkRefreshRun.generation !== this._networkGeneration)
                this._networkRefreshPending = true;
            return;
        }
        const run = {generation: this._networkGeneration, cancellable: new Gio.Cancellable(), proc: null};
        this._networkRefreshRun = run;
        this._networkRefreshButton.reactive = false;
        this._networkRefreshButton.accessible_name = this._temperatureRows ? 'Consultando temperaturas' : this._processesDialog ? 'Consultando processos' : this._updatesRows ? 'Consultando atualizações' : this._dockerRows ? 'Atualizando serviços Docker' : this._firewallRows ? 'Atualizando eventos do firewall' : 'Atualizando conexões e portas';
        this._networkRefreshStatus.text = '';
        let proc;
        try {
            const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
            const [, argv] = GLib.shell_parse_argv(command);
            if (this._storageExternal) {
                argv.push('--external');
                if (this._storageDevice) argv.push('--device', this._storageDevice.name, '--identity', this._storageDevice.identity);
            }
            if (this._hardwareMode) argv.push('--hardware', this._hardwareMode);
            proc = Gio.Subprocess.new(['/usr/bin/setsid', ...argv, '--details'], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
            this._networkRefreshProcess = proc;
            run.proc = proc;
            this._networkRefreshTimeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 15000, () => {
                this._networkRefreshTimeout = null;
                stopCommandRun(run);
                return GLib.SOURCE_REMOVE;
            });
            const [stdout] = await readCommandOutput(run);
            if (this._networkDestroyed || run.cancelled || run.generation !== this._networkGeneration || !this._networkDialog.visible)
                return;
            if (this._hardwareMode) {
                if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_HARDWARE:')) throw new Error('Falha ao consultar o hardware.');
                this._renderHardware(JSON.parse(stdout.slice('AZCLOCK_HARDWARE:'.length)));
                this._networkRefreshStatus.text = 'Consultado às ' + GLib.DateTime.new_now_local().format('%H:%M');
                return;
            }
            if (command.includes('/armazenamento-widget.py') || command.includes('/cpu-ram-widget.py')) {
                if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_STORAGE:')) throw new Error('Falha ao consultar armazenamento.');
                this._renderStorage(JSON.parse(stdout.slice('AZCLOCK_STORAGE:'.length)));
                this._networkRefreshStatus.text = 'Consultado às ' + GLib.DateTime.new_now_local().format('%H:%M');
                return;
            }
            if (command.includes('/rede-widget.py')) {
                if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_QUALITY:')) throw new Error('Não foi possível testar a qualidade.');
                this._renderQuality(JSON.parse(stdout.slice('AZCLOCK_QUALITY:'.length)));
                this._networkRefreshStatus.text = 'Consultado às ' + GLib.DateTime.new_now_local().format('%H:%M');
                return;
            }
            if (command.includes('/servicos-widget.py')) {
                if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_SERVICES:'))
                    throw new Error('Não foi possível consultar os serviços.');
                this._renderServices(JSON.parse(stdout.slice('AZCLOCK_SERVICES:'.length)));
                this._networkRefreshStatus.text = 'Consultado às ' + GLib.DateTime.new_now_local().format('%H:%M');
                return;
            }
            if (command.includes('/temperaturas-widget.py')) {
                if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_TEMPERATURES:'))
                    throw new Error('Não foi possível consultar os sensores.');
                this._renderTemperatures(JSON.parse(stdout.slice('AZCLOCK_TEMPERATURES:'.length)));
                this._networkRefreshStatus.text = 'Atualizado às ' + GLib.DateTime.new_now_local().format('%H:%M');
                return;
            }
            if (command.includes('/processos-widget.py')) {
                if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_PROCESSES:'))
                    throw new Error('Não foi possível consultar os processos.');
                this._renderProcesses(JSON.parse(stdout.slice('AZCLOCK_PROCESSES:'.length)));
                this._networkRefreshStatus.text = 'Consultado às ' + GLib.DateTime.new_now_local().format('%H:%M');
                return;
            }
            if (command.includes('/atualizacoes-widget.py')) {
                if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_UPDATES:'))
                    throw new Error('Não foi possível consultar as atualizações.');
                const data = JSON.parse(stdout.slice('AZCLOCK_UPDATES:'.length));
                this._renderUpdates(data);
                this.text = data.text;
                this.clutter_text.set_markup(GLib.markup_escape_text(data.text, -1));
                this._networkRefreshStatus.text = 'Consultado às ' + GLib.DateTime.new_now_local().format('%H:%M');
                return;
            }
            if (command.includes('/docker-widget.py')) {
                if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_DOCKER:'))
                    throw new Error('Não foi possível consultar o Docker.');
                const data = JSON.parse(stdout.slice('AZCLOCK_DOCKER:'.length));
                this._renderDocker(data);
                this.text = data.text;
                this.clutter_text.set_markup(GLib.markup_escape_text(data.text, -1));
                this._networkRefreshStatus.text = data.error || ('Atualizado às ' + GLib.DateTime.new_now_local().format('%H:%M'));
                return;
            }
            if (command.includes('/firewall-widget.py')) {
                if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_FIREWALL:'))
                    throw new Error('Sem acesso aos logs ou falha na coleta.');
                const data = JSON.parse(stdout.slice('AZCLOCK_FIREWALL:'.length));
                this._renderFirewall(data);
                this.text = data.text;
                this.clutter_text.set_markup(GLib.markup_escape_text(data.text, -1));
                this._networkRefreshStatus.text = 'Atualizado: ' + data.updated;
                return;
            }
            if (!proc.get_successful() || !stdout.startsWith('AZCLOCK_NETWORK:'))
                throw new Error('Não foi possível atualizar. Tente novamente.');
            const payload = JSON.parse(stdout.slice('AZCLOCK_NETWORK:'.length));
            if (typeof payload.tooltip !== 'string' || payload.tooltip.length > 8192 || !Array.isArray(payload.connection_items) || payload.connection_items.length > 200 ||
                payload.connection_items.some(item => !item || typeof item.ip !== 'string' || typeof item.port !== 'string' ||
                    typeof item.hostname !== 'string' || typeof item.display !== 'string' || item.hostname.length > 253 || item.display.length > 253 ||
                    item.ip.length > 64 || !/^\d{1,5}$/.test(item.port) || Number(item.port) < 1 || Number(item.port) > 65535))
                throw new Error('Resposta inválida.');
            this._networkTooltipText = payload.tooltip || 'Nenhuma porta escutando';
            this._networkConnectionItems = payload.connection_items || [];
            this._networkConnectionOmitted = Number.isInteger(payload.omitted) && payload.omitted > 0 ? payload.omitted : 0;
            this._updateNetworkTooltip();
            this._networkRefreshStatus.text = 'Atualizado às ' + GLib.DateTime.new_now_local().format('%H:%M');
        } catch (error) {
            if (!this._networkDestroyed && run.generation === this._networkGeneration && this._networkDialog?.visible)
                this._networkRefreshStatus.text = error.message || 'Não foi possível atualizar. Tente novamente.';
        } finally {
            if (this._networkRefreshTimeout) {
                GLib.source_remove(this._networkRefreshTimeout);
                this._networkRefreshTimeout = null;
            }
            this._networkRefreshProcess = null;
            this._networkRefreshRun = null;
            const pending = this._networkRefreshPending;
            this._networkRefreshPending = false;
            if (!this._networkDestroyed) {
                this._networkRefreshButton.reactive = true;
                this._networkRefreshButton.accessible_name = this._temperatureRows ? 'Atualizar temperaturas' : this._processesDialog ? 'Atualizar diagnóstico e processos' : this._updatesRows ? 'Atualizar consulta de atualizações' : this._dockerRows ? 'Atualizar serviços Docker' : this._firewallRows ? 'Atualizar eventos do firewall' : 'Atualizar conexões e portas';
                if (pending && this._networkDialog?.visible)
                    this._refreshNetworkDialog();
            }
        }
    }

    _openNetworkDialog() {
        if (this._networkDestroyed)
            return;
        if (this._networkDialog && this._networkDialog.visible) {
            this._closeNetworkDialog();
            return;
        }
        if (metricMode(getData(this.widgetIndex, this.elementIndex, 'Text_Command')) === 'cpu' && !this._networkDialog)
            this._buildStorageDialog();
        if (getData(this.widgetIndex, this.elementIndex, 'Text_Command').includes('/armazenamento-widget.py') && !this._networkDialog)
            this._buildStorageDialog();
        if (getData(this.widgetIndex, this.elementIndex, 'Text_Command').includes('/rede-widget.py') && !this._networkDialog)
            this._buildTrafficDialog();
        if (getData(this.widgetIndex, this.elementIndex, 'Text_Command').includes('/servicos-widget.py') && !this._networkDialog)
            this._buildServicesDialog();
        if (getData(this.widgetIndex, this.elementIndex, 'Text_Command').includes('/temperaturas-widget.py') && !this._networkDialog)
            this._buildTemperaturesDialog();
        if (getData(this.widgetIndex, this.elementIndex, 'Text_Command').includes('/processos-widget.py') && !this._networkDialog)
            this._buildProcessesDialog();
        if (getData(this.widgetIndex, this.elementIndex, 'Text_Command').includes('/atualizacoes-widget.py') && !this._networkDialog)
            this._buildUpdatesDialog();
        const firewall = getData(this.widgetIndex, this.elementIndex, 'Text_Command').includes('/firewall-widget.py');
        if (getData(this.widgetIndex, this.elementIndex, 'Text_Command').includes('/docker-widget.py') && !this._networkDialog)
            this._buildDockerDialog();
        if (firewall && !this._networkDialog)
            this._buildFirewallDialog();
        if (!this._networkDialog) {
            this._networkBackdrop = new St.Widget({reactive: true, visible: false});
            this._networkBackdrop.add_constraint(new Clutter.BindConstraint({source: global.stage, coordinate: Clutter.BindCoordinate.ALL}));
            this._networkBackdrop.connect('button-press-event', (_actor, event) => {
            if (this._networkDialog?.contains(event.get_source()))
                return Clutter.EVENT_PROPAGATE;
                this._closeNetworkDialog();
                return Clutter.EVENT_STOP;
            });
            Main.uiGroup.add_child(this._networkBackdrop);
            this._networkDialog = new St.BoxLayout({
                vertical: true,
                reactive: true,
                style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 8px; padding: 12px; spacing: 8px;',
            });
            const columns = new St.BoxLayout({vertical: false, style: 'spacing: 18px;'});
            const buildColumn = (title, width, interactive = false) => {
                const column = new St.BoxLayout({vertical: true, style: 'spacing: 8px;'});
                column.add_child(new St.Label({text: title, style: 'font-weight: bold; color: #ededed;'}));
                const scroll = new St.ScrollView({
                    style: width === null ? 'height: 260px;' : `width: ${width}px; height: 260px;`,
                    reactive: true, overlay_scrollbars: false,
                });
                scroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
                const box = new St.BoxLayout({vertical: true});
                const label = new St.Label({
                    style: 'font-family: monospace; font-size: 14px; padding: 6px;',
                    x_align: Clutter.ActorAlign.START,
                });
                label.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
                label.clutter_text.set_line_wrap(true);
                if (!interactive)
                    box.add_child(label);
                scroll.add_actor(box);
                column.add_child(scroll);
                columns.add_child(column);
                return interactive ? box : label;
            };
            this._networkDialogLabel = buildColumn('Portas locais', 130);
            this._networkConnectionsBox = buildColumn('Conexões externas · destino / porta', null, true);
            this._networkConnectionSignature = null;
            this._networkDialog.add_child(columns);
            const footer = new St.BoxLayout({style: 'spacing: 8px;'});
            this._networkRefreshButton = new St.Button({
                reactive: true, can_focus: true, accessible_name: 'Atualizar conexões e portas',
                x_align: Clutter.ActorAlign.START,
                style: 'background-color: transparent; color: white; padding: 6px;',
            });
            this._networkRefreshButton.set_child(new St.Icon({
                icon_name: 'view-refresh-symbolic', icon_size: 18, style: 'color: white;',
            }));
            this._networkRefreshButton.connect('clicked', () => this._refreshNetworkDialog());
            footer.add_child(this._networkRefreshButton);
            this._networkRefreshStatus = new St.Label({text: '', style: 'color: #c8c8c8; font-size: 12px;', y_align: Clutter.ActorAlign.CENTER});
            footer.add_child(this._networkRefreshStatus);
            this._networkDialog.add_child(footer);
            this._networkBackdrop.add_child(this._networkDialog);
        }
        this._networkBackdrop.show();
        if (!this._networkModalGrab)
            this._networkModalGrab = Main.pushModal(this._networkBackdrop, {
                actionMode: Shell.ActionMode.POPUP,
            });
        Main.uiGroup.set_child_above_sibling(this._networkBackdrop, null);
        this._networkDialog.show();
        const [x, y] = this.get_transformed_position();
        const [, h] = this.get_transformed_size();
        const [, pw] = this._networkDialog.get_preferred_width(-1);
        const [, ph] = this._networkDialog.get_preferred_height(pw);
        const monitor = Main.layoutManager.monitors.find(m =>
            x >= m.x && x < m.x + m.width && y >= m.y && y < m.y + m.height);
        let px = x;
        let py = y + h + 8;
        if (monitor) {
            px = Math.max(monitor.x + 8, Math.min(px, monitor.x + monitor.width - pw - 8));
            if (py + ph > monitor.y + monitor.height)
                py = y - ph - 8;
            py = Math.max(monitor.y + 8, py);
        }
        this._networkDialog.set_position(px, py);
        this._networkBackdrop.set_child_above_sibling(this._networkDialog, null);
        this._refreshNetworkDialog();
    }

    async _startSpeedtest() {
        if (this._networkRefreshRun) {
            this._speedtestStatus.text = 'Aguarde o teste de qualidade terminar.';
            this._speedtestStatus.show();
            return;
        }
        if (this._networkDestroyed || !this._networkDialog?.visible || this._speedtestProcess)
            return;
        this._speedtestButton.reactive = false;
        this._speedtestButton.can_focus = false;
        this._speedtestButton.label = 'Testando…';
        this._speedtestStatus.hide();
        const run = {generation: this._networkGeneration, proc: null, cancellable: new Gio.Cancellable()};
        this._speedtestRun = run;
        let proc = null;
        let timedOut = false;
        try {
            const binary = GLib.build_filenamev([Me.path, 'speedtest']);
            proc = Gio.Subprocess.new(['/usr/bin/setsid', binary, '--accept-license', '--accept-gdpr', '--format=json', '--progress=no'],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
            this._speedtestProcess = proc;
            run.proc = proc;
            this._speedtestTimeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 120000, () => {
                this._speedtestTimeout = null;
                timedOut = true;
                stopCommandRun(run);
                return GLib.SOURCE_REMOVE;
            });
            const [stdout] = await readCommandOutput(run);
            if (this._networkDestroyed || run.generation !== this._networkGeneration || !this._networkDialog?.visible)
                return;
            if (timedOut)
                throw new Error('O teste demorou demais. Tente novamente.');
            if (!proc.get_successful())
                throw new Error('Não foi possível concluir. Verifique a conexão e tente novamente.');
            const data = JSON.parse(stdout);
            const download = Number(data.download?.bandwidth) * 8 / 1000000;
            const upload = Number(data.upload?.bandwidth) * 8 / 1000000;
            const ping = Number(data.ping?.latency);
            if (![download, upload, ping].every(Number.isFinite))
                throw new Error('O serviço retornou um resultado inválido.');
            const format = value => value.toFixed(1).replace('.', ',');
            this._speedtestResult.text = `Download: ${format(download)} Mbps\nUpload: ${format(upload)} Mbps\nPing: ${format(ping)} ms`;
            this._speedtestResult.show();
            const time = GLib.DateTime.new_now_local().format('%H:%M');
            this._speedtestStatus.text = `Último teste: ${time}\nSpeedtest by Ookla`;
            this._speedtestStatus.show();
        } catch (error) {
            if (!this._networkDestroyed && run.generation === this._networkGeneration && this._networkDialog?.visible) {
                this._speedtestStatus.text = timedOut ? 'O teste demorou demais. Tente novamente.' :
                    (proc ? error.message : 'Serviço de teste indisponível. Recarregue a extensão.');
                this._speedtestStatus.show();
            }
        } finally {
            if (this._speedtestTimeout) {
                GLib.source_remove(this._speedtestTimeout);
                this._speedtestTimeout = null;
            }
            this._speedtestProcess = null;
            this._speedtestRun = null;
            if (!this._networkDestroyed) {
                this._speedtestButton.label = 'Testar novamente';
                this._speedtestButton.reactive = true;
                this._speedtestButton.can_focus = true;
            }
        }
    }

    _updateNetworkTooltip() {
        // The details now appear only in the click-opened modal.
        if (!this._networkDestroyed && this._networkDialogLabel) {
            this._networkDialogLabel.text = this._networkTooltipText;
            if (this._networkConnectionsBox && !this._networkInspecting) {
                const signature = JSON.stringify([this._networkConnectionItems, this._networkConnectionOmitted || 0]);
                if (signature !== this._networkConnectionSignature) {
                    this._networkConnectionSignature = signature;
                    this._networkConnectionsBox.destroy_all_children();
                    for (const item of this._networkConnectionItems) {
                        const row = new St.BoxLayout({style: 'spacing: 6px; padding: 6px; font-family: monospace; font-size: 14px;'});
                        if (item.hostname) {
                            const host = new St.Button({
                                label: item.display || item.hostname,
                                reactive: true, can_focus: true,
                                accessible_name: `Copiar hostname completo: ${item.hostname}`,
                                style: 'color: #82cfff; padding: 0px;',
                            });
                            host.connect('clicked', () => {
                                St.Clipboard.get_default().set_text(St.ClipboardType.CLIPBOARD, item.hostname);
                            });
                            row.add_child(host);
                        }
                        const ip = new St.Button({label: `(${item.ip})`, reactive: true, can_focus: true,
                            accessible_name: `Consultar IP ${item.ip}`, style: 'color: #82cfff; padding: 0px;'});
                        ip.connect('clicked', () => this._inspectFirewall('ip', item.ip));
                        row.add_child(ip);
                        row.add_child(new St.Label({text: '—', style: 'color: #c8c8c8;'}));
                        const port = new St.Button({label: String(item.port), reactive: true, can_focus: true,
                            accessible_name: `Consultar porta ${item.port}`, style: 'color: #ffd479; padding: 0px;'});
                        port.connect('clicked', () => this._inspectFirewall('port', item.port));
                        row.add_child(port);
                        this._networkConnectionsBox.add_child(row);
                    }
                    if (this._networkConnectionOmitted)
                        this._networkConnectionsBox.add_child(new St.Label({text: `${this._networkConnectionOmitted} conexões adicionais omitidas.`, style: 'padding: 6px;'}));
                    if (!this._networkConnectionItems.length)
                        this._networkConnectionsBox.add_child(new St.Label({text: 'Nenhuma conexão externa', style: 'padding: 6px;'}));
                }
            }
        }
    }

    _setErrorState() {
        this._hasError = true;
        this.text = _('error');
        this.clutter_text.set_markup(this.text);
    }

    refreshCommand() {
        this._hasError = false;
        this._removePollingInterval();
        this._executeCommand();
        this._startPollingInterval();
    }

    _startPollingInterval() {
        const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
        if (metricMode(command) || command.includes('/atualizacoes-widget.py') || command.startsWith('playerctl -p spotify,chromium metadata'))
            return;
        const interval = command.includes('/firewall-widget.py') ? 60000 : command.includes('/clima-widget.py')
            ? 300000
            : Math.max(getData(this.widgetIndex, this.elementIndex, 'Text_PollingInterval'), 250);
        this._pollingIntervalId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, interval, () => {
            this._executeCommand();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _removePollingInterval() {
        if (this._pollingIntervalId) {
            GLib.source_remove(this._pollingIntervalId);
            this._pollingIntervalId = null;
        }
    }

    setStyle() {
        super.setStyle();
        if (this._mediaRow) {
            this._mediaRow.x_align = this.x_align;
            this._mediaRow.y_align = this.y_align;
        }
    }

    _setMediaIcon(player) {
        if (!player) {
            this._mediaIcon?.hide();
            return;
        }
        if (!this._mediaRow) {
            const parent = this.get_parent();
            if (!parent)
                return;
            const index = parent.get_children().indexOf(this);
            const row = new St.BoxLayout({vertical: false, x_align: this.x_align, y_align: this.y_align,
                style: 'spacing: 6px;'});
            parent.remove_child(this);
            row.add_child(this);
            this._mediaIcon = new St.Icon({icon_size: 16, y_align: Clutter.ActorAlign.CENTER,
                style: 'icon-size: 16px;', visible: false});
            row.add_child(this._mediaIcon);
            parent.insert_child_at_index(row, index);
            this._mediaRow = row;
        }
        const spotify = /^org\.mpris\.MediaPlayer2\.spotify(?:\.|$)/.test(player);
        const youtube = /^org\.mpris\.MediaPlayer2\.io\.orbitz\.YouTubeWidget(?:\.|$)/.test(player);
        const filename = spotify ? 'spotify.svg' : youtube ? 'youtube.svg' : 'chrome.svg';
        if (this._mediaIconFile !== filename) {
            this._mediaIcon.gicon = Gio.icon_new_for_string(GLib.build_filenamev([Me.path, 'media', 'players', filename]));
            this._mediaIcon.accessible_name = spotify ? 'Spotify' : youtube ? 'YouTube' : 'Google Chrome';
            this._mediaIconFile = filename;
        }
        this._mediaIcon.show();
    }

    _stopMedia() {
        this._mediaCancellable?.cancel();
        this._mediaCancellable = null;
        this._mediaIcon?.hide();
        this._mediaBusy = false;
        this._mediaPending = false;
        if (this._mediaTimer) {
            GLib.source_remove(this._mediaTimer);
            this._mediaTimer = null;
        }
        this._mediaGeneration = (this._mediaGeneration || 0) + 1;
        for (const id of this._mediaSubscriptions || [])
            Gio.DBus.session.signal_unsubscribe(id);
        this._mediaSubscriptions = null;
    }

    _queueMedia() {
        if (this._mediaTimer || this._networkDestroyed)
            return;
        this._mediaTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
            this._mediaTimer = null;
            this._refreshMedia();
            return GLib.SOURCE_REMOVE;
        });
    }

    _refreshMedia() {
        if (!widgetsEnabled || this._networkDestroyed) return;
        if (this._mediaBusy) {
            this._mediaPending = true;
            return;
        }
        this._mediaBusy = true;
        if (!this._mediaSubscriptions) {
            this._mediaSubscriptions = [
                Gio.DBus.session.signal_subscribe(null, 'org.freedesktop.DBus.Properties', 'PropertiesChanged',
                    '/org/mpris/MediaPlayer2', null, Gio.DBusSignalFlags.NONE, () => this._queueMedia()),
                Gio.DBus.session.signal_subscribe('org.freedesktop.DBus', 'org.freedesktop.DBus', 'NameOwnerChanged',
                    '/org/freedesktop/DBus', null, Gio.DBusSignalFlags.NONE, (_c, _s, _p, _i, _m, args) => {
                        if (args.deep_unpack()[0].startsWith('org.mpris.MediaPlayer2.'))
                            this._queueMedia();
                    }),
            ];
        }
        const generation = this._mediaGeneration = (this._mediaGeneration || 0) + 1;
        const cancellable = this._mediaCancellable = new Gio.Cancellable();
        const call = (name, path, iface, method, params) => new Promise((resolve, reject) => {
            Gio.DBus.session.call(name, path, iface, method, params, null, Gio.DBusCallFlags.NONE, 3000, cancellable,
                (connection, result) => {
                    try { resolve(connection.call_finish(result)); } catch (error) { reject(error); }
                });
        });
        (async () => {
            let text = '\u200b';
            let selectedPlayer = null;
            let bestScore = -1;
            try {
                const names = (await call('org.freedesktop.DBus', '/org/freedesktop/DBus',
                    'org.freedesktop.DBus', 'ListNames', null)).deep_unpack()[0];
                const players = names.filter(name => /^org\.mpris\.MediaPlayer2\.(spotify|chromium|chrome|io\.orbitz\.YouTubeWidget)(\.|$)/.test(name))
                    .sort((a, b) => Number(!a.includes('.spotify')) - Number(!b.includes('.spotify')));
                for (const player of players) {
                    try {
                        const values = (await call(player, '/org/mpris/MediaPlayer2', 'org.freedesktop.DBus.Properties',
                            'GetAll', new GLib.Variant('(s)', ['org.mpris.MediaPlayer2.Player']))).deep_unpack()[0];
                        const status = values.PlaybackStatus?.deep_unpack();
                        const metadata = values.Metadata?.deep_unpack() || {};
                        const title = metadata['xesam:title']?.deep_unpack() || '';
                        const artist = metadata['xesam:artist']?.deep_unpack() || [];
                        if (!['Playing', 'Paused'].includes(status) || typeof title !== 'string' || !title.trim())
                            continue;
                        const score = status === 'Playing' ? 2 : 1;
                        if (score > bestScore) {
                            bestScore = score;
                            selectedPlayer = player;
                            const artists = Array.isArray(artist) ? artist.filter(value => typeof value === 'string' && value.trim()).join(', ') : '';
                            text = `${status === 'Playing' ? '▶️' : '⏸️'}  ${artists ? artists + ' — ' : ''}${title}`.slice(0, 1024);
                        }
                        if (score === 2)
                            break;
                    } catch (error) { /* Player may disappear between discovery and read. */ }
                }
            } catch (error) { text = 'Mídia indisponível'; }
            if (!this._networkDestroyed && generation === this._mediaGeneration) {
                this.text = text;
                this.clutter_text.set_text(text);
                this._setMediaIcon(selectedPlayer);
                this._mediaBusy = false;
                if (this._mediaPending) {
                    this._mediaPending = false;
                    this._queueMedia();
                }
            }
        })();
    }

    _executeCommand() {
        if (!widgetsEnabled || this._networkDestroyed) return;
        const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
        if (metricMode(command)) {
            if (['cpu', 'processes', 'network'].includes(metricMode(command)))
                this._scheduleNetworkClick();
            this._cancelCommand();
            if (this._mediaSubscriptions)
                this._stopMedia();
            metricLabels.add(this);
            scheduleMetrics();
            return;
        }
        if (metricLabels.delete(this))
            scheduleMetrics();
        if (command.startsWith('playerctl -p spotify,chromium metadata')) {
            this._cancelCommand();
            this._refreshMedia();
            return;
        }
        if (this._mediaSubscriptions)
            this._stopMedia();
        this._execCommand(command);
    }

    _cancelCommand() {
        const run = this._commandRun;
        if (!run)
            return;
        run.cancelled = true;
        if (run.timeout) {
            GLib.source_remove(run.timeout);
            run.timeout = null;
        }
        stopCommandRun(run);
    }

    async _execCommand(command, input = null, cancellable = null) {
        if (this._networkDestroyed)
            return;
        if (this._commandRun) {
            if (this._commandRun.cancelled || command !== this._commandRun.command) {
                this._pendingCommand = {command, input, cancellable};
                this._cancelCommand();
            }
            return;
        }
        if (!command || command.length === 0) {
            this._setErrorState();
            log('Desktop Clock - Error executing command. No command detected.');
            return;
        }
        const run = {command, proc: null, timeout: null, cancelled: false,
            cancellable: new Gio.Cancellable()};
        this._commandRun = run;
        let cancelId = null;
        try {
            if (cancellable) {
                cancelId = cancellable.connect(() => this._cancelCommand());
                if (cancellable.is_cancelled()) {
                    this._cancelCommand();
                    return;
                }
            }
            const summaryCommand = command.includes('/seguranca-widget.py') ? command + ' --summary' : command;
            const argv = ['/usr/bin/setsid', 'bash', '-c', summaryCommand];

            let flags = Gio.SubprocessFlags.STDOUT_PIPE |
                Gio.SubprocessFlags.STDERR_PIPE;

            if (input !== null)
                flags |= Gio.SubprocessFlags.STDIN_PIPE;

            const proc = Gio.Subprocess.new(argv, flags);
            run.proc = proc;
            run.timeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 30000, () => {
                run.timeout = null;
                this._cancelCommand();
                if (!this._networkDestroyed)
                    this._setErrorState();
                return GLib.SOURCE_REMOVE;
            });
            const [stdout, stderr] = await readCommandOutput(run, input);
            if (this._networkDestroyed || run.cancelled)
                return;

            if (!proc.get_successful() || stderr) {
                this._setErrorState();
                const status = proc.get_exit_status();
                log(`Desktop Clock - Error executing command "${command}": ${stderr ? stderr.trim().slice(0, 1024) : GLib.strerror(status)}`);
                return;
            }

            const response = stdout.trim();

            if (!response) {
                this._setErrorState();
                log(`Desktop Clock - Error executing command "${command}": no output.`);
                return;
            }

            let displayText = response;
            if (command.includes('/armazenamento-widget.py') && response.startsWith('AZCLOCK_STORAGE:')) {
                const payload = JSON.parse(response.slice('AZCLOCK_STORAGE:'.length));
                if (typeof payload.text !== 'string' || payload.text.length > 160) throw new Error('Resumo de armazenamento inválido.');
                displayText = GLib.markup_escape_text(payload.text, -1);
                this._scheduleNetworkClick();
            }

            if (command.includes('/servicos-widget.py') && response.startsWith('AZCLOCK_SERVICES:')) {
                const payload = JSON.parse(response.slice('AZCLOCK_SERVICES:'.length));
                if (typeof payload.text !== 'string' || payload.text.length > 160) throw new Error('Resumo de serviços inválido.');
                displayText = GLib.markup_escape_text(payload.text, -1);
                this._scheduleNetworkClick();
            }

            if (command.includes('/temperaturas-widget.py'))
                this._scheduleNetworkClick();
            if (command.includes('/atualizacoes-widget.py') && response.startsWith('AZCLOCK_UPDATES:')) {
                const payload = JSON.parse(response.slice('AZCLOCK_UPDATES:'.length));
                if (typeof payload.text !== 'string' || payload.text.length > 128)
                    throw new Error('Resposta de atualizações inválida.');
                displayText = GLib.markup_escape_text(payload.text, -1);
                this._scheduleNetworkClick();
            }

            if (command.includes('/docker-widget.py') && response.startsWith('AZCLOCK_DOCKER:')) {
                const payload = JSON.parse(response.slice('AZCLOCK_DOCKER:'.length));
                displayText = payload.text;
                this._scheduleNetworkClick();
            }

            if (command.includes('/firewall-widget.py') && response.startsWith('AZCLOCK_FIREWALL:')) {
                const payload = JSON.parse(response.slice('AZCLOCK_FIREWALL:'.length));
                displayText = payload.text;
                this.accessible_name = payload.text + ' · ' + (payload.updated || 'Atualização manual pendente');
                this._scheduleNetworkClick();
            }
            if (command.includes('/seguranca-widget.py') && response.startsWith('AZCLOCK_NETWORK:')) {
                const payload = JSON.parse(response.slice('AZCLOCK_NETWORK:'.length));
                displayText = payload.text;
                this._scheduleNetworkClick();

            }
            if (this.text !== displayText) {
                this.text = displayText;
                this.clutter_text.set_markup(this.text);
            }
        } catch (err) {
            if (!this._networkDestroyed && (!run.cancelled || run.outputLimit)) {
                this._setErrorState();
                log(`Desktop Clock - Error executing command "${command}": ${err}`);
            }
        } finally {
            if (run.timeout)
                GLib.source_remove(run.timeout);
            if (cancelId !== null)
                cancellable.disconnect(cancelId);
            this._commandRun = null;
            const pending = this._pendingCommand;
            this._pendingCommand = null;
            if (!this._networkDestroyed && pending)
                this._execCommand(pending.command, pending.input, pending.cancellable);
        }
    }
}, {Clutter, Gio, GLib, Main, Me, Pango, St, Utils, getData, readCommandOutput, stopCommandRun, global}));

// eslint-disable-next-line no-unused-vars
function init() {
    ExtensionUtils.initTranslations(Me.metadata['gettext-domain']);
    return new AzClock();
}

class AzClock {
    enable() {
        Calendar.enable(Me.path, () => {
            if (!this._running || !WIDGETDATA) return null;
            const widget = this.widgets.find(w => w.get_paint_visibility() &&
                WIDGETDATA[w.widgetIndex]?.some(element => element.Element_Type === DIGITAL_CLOCK));
            if (!widget) return null;
            const [x,y] = widget.get_transformed_position();
            const [width,height] = widget.get_transformed_size();
            return {x,y,width,height};
        });
        widgetsEnabled = false;
        this.widgets = [];
        this._running = false;
        this._controller = new St.Button({reactive: true, can_focus: true, visible: true,
            width: 40, height: 36, accessible_name: 'Iniciar widgets',
            style: 'padding: 0px; border: 0px; background-color: transparent; box-shadow: none;'});
        this._controllerButton = this._controller;
        this._controllerIcons = {
            stopped: Gio.icon_new_for_string(GLib.build_filenamev([Me.path, 'media', 'controls', 'widgets-white.svg'])),
            running: Gio.icon_new_for_string(GLib.build_filenamev([Me.path, 'media', 'controls', 'widgets-white.svg'])),
        };
        this._controllerIcon = new St.Icon({gicon: this._controllerIcons.stopped, icon_size: 24, visible: true,
            x_align: Clutter.ActorAlign.CENTER, y_align: Clutter.ActorAlign.CENTER});
        this._controller.set_child(this._controllerIcon);
        this._controller.connect('clicked', () => this._running ? this._stopWidgets() : this._startWidgets());
        Main.layoutManager.addChrome(this._controller, {affectsStruts: false, trackFullscreen: false});
        this._controllerWindows = new Set();
        const watchWindow = window => {
            if (this._controllerWindows.has(window)) return;
            this._controllerWindows.add(window);
            window.connectObject('position-changed', () => this._stackControllerBehindWindows(),
                'size-changed', () => this._stackControllerBehindWindows(),
                'notify::minimized', () => this._stackControllerBehindWindows(),
                'notify::gtk-application-id', () => this._stackControllerBehindWindows(),
                'notify::title', () => this._stackControllerBehindWindows(),
                'unmanaged', () => {
                    this._controllerWindows.delete(window);
                    window.disconnectObject(this._controller);
                    this._stackControllerBehindWindows();
                }, this._controller);
        };
        for (const actor of global.get_window_actors()) watchWindow(actor.meta_window);
        global.display.connectObject('restacked', () => this._stackControllerBehindWindows(),
            'window-created', (_display, window) => { watchWindow(window); this._stackControllerBehindWindows(); }, this._controller);
        global.workspace_manager.connectObject('active-workspace-changed', () => this._stackControllerBehindWindows(), this._controller);
        Main.layoutManager.connectObject('monitors-changed', () => this._positionController(), this._controller);
        try {
            this._controllerSettings = ExtensionUtils.getSettings();
            this._controllerSettings.connectObject('changed::widget-data', () => this._positionController(), this._controller);
        } catch (error) { logError(error, 'Posição dos widgets indisponível'); }
        this._positionController();
    }

    _stackControllerBehindWindows() {
        if (!this._controller) return;
        const workspace = global.workspace_manager.get_active_workspace();
        const {x, y, width, height} = this._controller;
        // A desktop window can intercept input below window_group on Wayland.
        // Keep native button input, but never expose it over an application window.
        const covered = [...this._controllerWindows].some(window => {
            // DING emulates a desktop window on Wayland without changing its
            // NORMAL window type. Its full-monitor surface must not hide us.
            const desktopIcons = window.get_gtk_application_id?.() === 'com.rastersoft.ding' ||
                window.customJS_ding?._keepAtBottom === true;
            if (desktopIcons || window.get_window_type() === Meta.WindowType.DESKTOP ||
                !window.showing_on_its_workspace() || !window.located_on_workspace(workspace)) return false;
            const rect = window.get_frame_rect();
            return rect.x < x + width && rect.x + rect.width > x &&
                rect.y < y + height && rect.y + rect.height > y;
        });
        this._controller.visible = !covered;
    }

    _controllerMonitor() {
        const fallback = Main.layoutManager.primaryMonitor;
        try {
            const data = this._controllerSettings?.get_value('widget-data').deep_unpack();
            if (!Array.isArray(data)) return fallback;
            const scores = new Map();
            for (const widget of data.slice(0, 100)) {
                const box = Array.isArray(widget) ? widget[0] : null;
                if (box?.Parent_Id && data.some(widget => widget[0]?.Widget_Id === box.Parent_Id && widget[0]?.Box_IsGroup === 'true')) continue;
                if (!box || box.Location_X === undefined || box.Location_Y === undefined) continue;
                const anchor = Number(box.Box_AnchorPoint) || 0;
                const x = Number(box.Location_X) + (anchor === 2 || anchor === 3 ? -0.5 : 0.5);
                const y = Number(box.Location_Y) + (anchor === 1 || anchor === 3 ? -0.5 : 0.5);
                if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
                const monitor = (Main.layoutManager.monitors || []).find(m => x >= m.x && x < m.x + m.width && y >= m.y && y < m.y + m.height);
                if (monitor) scores.set(monitor, (scores.get(monitor) || 0) + 1);
            }
            let selected = fallback, highest = 0;
            for (const [monitor, count] of scores) {
                if (count > highest) { selected = monitor; highest = count; }
            }
            return selected;
        } catch (error) { return fallback; }
    }

    _positionController() {
        if (!this._controller) return;
        const monitor = this._controllerMonitor();
        if (!monitor) { this._controller.hide(); return; }
        const primary = Main.layoutManager.primaryMonitor;
        const panelHeight = monitor === primary ? Math.max(28, Main.panel.height || 0) : 0;
        this._controller.set_position(monitor.x + monitor.width - 52, monitor.y + panelHeight + 8);
        this._controller.show();
        this._stackControllerBehindWindows();
    }

    _setControllerState(running, busy = false) {
        if (!this._controllerButton) return;
        this._controllerButton.reactive = !busy;
        this._controllerButton.can_focus = !busy;
        this._controllerIcon.gicon = running || busy ? this._controllerIcons.running : this._controllerIcons.stopped;
        this._controllerButton.accessible_name = busy ? 'Encerrando widgets' : running ? 'Encerrar todos os widgets' : 'Iniciar widgets';
    }

    _startWidgets() {
        if (this._running || this._stopping) return;
        try {
            Me.settings = ExtensionUtils.getSettings();
            this._updateWidgetData();
            Me.imports.settings.SettingsImport.validateWidgets(WIDGETDATA);
            widgetsEnabled = true;
            this._running = true;
            this._createWidgets();
            this._startClockTimer();
            this._openPostits();
            this._setControllerState(true);
        } catch (error) { this._startupFailed(error); }
    }

    _startupFailed(error) {
        logError(error, 'Falha ao iniciar widgets');
        this._stopWidgets();
        Main.notifyError('Widgets interrompidos', String(error.message || error).slice(0, 300));
    }

    _openPostits() {
        try {
            Gio.Subprocess.new(['/usr/bin/env', 'GDK_BACKEND=x11', '/usr/bin/python3',
                GLib.build_filenamev([GLib.get_user_data_dir(), 'orbitz-postits', 'app', 'postits.py'])],
                Gio.SubprocessFlags.NONE);
        } catch (error) {
            logError(error, 'Falha ao abrir Sticky Notes');
            Main.notifyError('Sticky Notes', 'Não foi possível abrir as notas.');
        }
    }

    _closePostits() {
        // Do not activate the application when it is already closed.
        Gio.DBus.session.call('io.orbitz.Postits', '/io/orbitz/Postits',
            'org.gtk.Actions', 'Activate',
            new GLib.Variant('(sava{sv})', ['quit', [], {}]), null,
            Gio.DBusCallFlags.NO_AUTO_START, 3000, null, (connection, result) => {
                try { connection.call_finish(result); } catch (error) {
                    if (!error.matches(Gio.DBusError, Gio.DBusError.NAME_HAS_NO_OWNER) &&
                        !error.matches(Gio.DBusError, Gio.DBusError.SERVICE_UNKNOWN))
                        logError(error, 'Falha ao encerrar post-its');
                }
            });
    }

    _stopWidgets() {
        if (this._stopping) return this._stopping;
        this._closePostits();
        this._running = false;
        widgetsEnabled = false;
        this._setControllerState(false, true);
        Me.settings?.disconnectObject(this);
        Main.layoutManager.disconnectObject(this);
        if (this._dataChangedTimeoutId) {
            GLib.source_remove(this._dataChangedTimeoutId);
            this._dataChangedTimeoutId = null;
        }
        this._removeClockTimer();
        this._destroyWidgets();
        for (const run of activeCommandRuns) stopCommandRun(run);
        activeCommandRuns.clear();
        stopMetrics();
        if (metricRestart) { GLib.source_remove(metricRestart); metricRestart = null; }
        if (networkClickTimer) { GLib.source_remove(networkClickTimer); networkClickTimer = null; }
        metricLabels.clear();
        networkClickLabels.clear();
        widgetDragController?.cancel();
        widgetDragController = null;
        dragWidgets.clear();
        WIDGETDATA = null;
        this._stopping = Promise.allSettled([...pendingStops]).then(() => {
            this._stopping = null;
            this._setControllerState(false);
        });
        return this._stopping;
    }

    disable() {
        Calendar.disable();
        this._stopWidgets();
        this._controller?.destroy();
        this._controllerWindows?.clear();
        this._controller = null;
        this._controllerButton = null;
        this._controllerIcon = null;
        this._controllerIcons = null;
        this._controllerSettings = null;
        Me.settings = null;
    }

    _startClockTimer() {
        if (!this._running || this._updateClockId || !WIDGETDATA?.some(widget => widget.some(element => [DIGITAL_CLOCK, ANALOG_CLOCK].includes(element.Element_Type))))
            return;
        this._updateClockId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 1000, () => {
            try {
                for (const widget of this.widgets) widget.updateClocks();
            } catch (error) { this._startupFailed(error); return GLib.SOURCE_REMOVE; }

            return GLib.SOURCE_CONTINUE;
        });
    }

    _removeClockTimer() {
        if (this._updateClockId) {
            GLib.source_remove(this._updateClockId);
            this._updateClockId = null;
        }
    }

    _destroyWidget(index) {
        const widget = this.widgets[index];
        this.widgets.splice(index, 1);
        widget.destroy();
    }

    _detachWidgetGroups() {
        for (const widget of this.widgets || []) {
            if (!widget._grouped) continue;
            widget.get_parent()?.remove_child(widget);
            Main.layoutManager._backgroundGroup.add_child(widget);
            widget._grouped = false;
            widget._groupWidth = null;

        }
        for (const widget of this.widgets || []) {
            widget._subwidgetBox?.destroy();
            widget._subwidgetBox = null;
        }
    }

    _applyWidgetGroups() {
        for (const widget of this.widgets || []) {
            if (!widget.setStyle) continue;
            widget.setStyle();
            widget.setElementsStyle();
            widget.setPositionFromSettings();
            if (!widget._draggable && !getData(widget.widgetIndex, 0, 'Lock_Widget', 'bool')) widget.makeDraggable();
        }
        if (!WIDGETDATA?.some(widget => widget[0].Parent_Id || widget[0].Box_IsGroup === 'true')) return;
        const groups = Me.imports.grouping.planGroups(WIDGETDATA);
        for (const [index, members] of groups) {
            const parent = this.widgets[index], meta = WIDGETDATA[index][0];
            const columns = Math.max(1, Math.min(4, Number(meta.Group_Columns) || 1));
            const width = parent._getStableWidth();
            const spacing = Math.max(0, Math.min(50, Number(meta.Box_Spacing) || 8));
            parent.layout_manager.orientation = Clutter.Orientation.VERTICAL;
            const box = new St.BoxLayout({vertical: true, style: `spacing: ${spacing}px;`});
            box.add_child(new St.Label({text: meta.Name || 'Sistema', style: PANEL_TITLE_STYLE}));
            parent.add_child(box);
            parent._subwidgetBox = box;
            let row;
            for (const [position, childIndex] of members.entries()) {
                if (position % columns === 0) {
                    row = new St.BoxLayout({style: `spacing: ${spacing}px;`}); box.add_child(row);
                }
                const child = this.widgets[childIndex];
                child.get_parent()?.remove_child(child);
                child._grouped = true;
                child._groupWidth = Math.max(100, (width - 2 * (Number(meta.Box_Padding) || 0) - 2 * (Number(meta.Box_BorderWidth) || 0) - (columns - 1) * spacing) / columns);
                child.set_position(0, 0);
                row.add_child(child);
                child.setStyle();
            }
            parent.queue_relayout();
        }
    }

    _destroyWidgets() {
        this._detachWidgetGroups();
        const widgets = this.widgets || [];
        this.widgets = [];
        for (const widget of widgets) {
            try { widget.destroy(); }
            catch (error) { logError(error, 'Falha ao destruir widget'); }
        }
    }

    _createWidget(index, updateDelay = 300) {
        const widget = new DesktopWidget(index);
        widget._onInitializationError = error => this._startupFailed(error);
        try {
            Main.layoutManager._backgroundGroup.add_child(widget);
            widget.updateComponents(updateDelay);
            return widget;
        } catch (error) { widget.destroy(); throw error; }
    }

    _createWidgetsWithoutSignals() {
        this.widgets = [];

        for (let i = 0; i < WIDGETDATA.length; i++) {
            const widget = this._createWidget(i);
            this.widgets.push(widget);
        }
        this._applyWidgetGroups();

    }

    _createWidgets() {
        this._createWidgetsWithoutSignals();
        Me.settings.connectObject('changed::widget-data', () => {
            if (!this._running) return;
            if (this._dataChangedTimeoutId)
                GLib.source_remove(this._dataChangedTimeoutId);

            this._dataChangedTimeoutId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 300, () => {
                if (this._running) {
                    try { this._updateWidgetData(); this._widgetDataChangedEvent(); }
                    catch (error) { this._startupFailed(error); }
                }
                this._dataChangedTimeoutId = null;
                return GLib.SOURCE_REMOVE;
            });
        }, this);

        Main.layoutManager.connectObject('monitors-changed', () => {
            if (!this._running) return;
            if (global.display.get_n_monitors() === 0)
                return;

            debugLog('Monitors-changed event');
            this._updateWidgetData();
            for (const widget of this.widgets) {
                widget.setPositionFromSettings();
                this._updateWidgetData();
            }
        }, this);
    }

    _updateWidgetData() {
        debugLog('update widget data');
        WIDGETDATA = Utils.unpackData(Me.settings);
    }

    _updateWidgetsIndex() {
        for (let i = 0; i < this.widgets.length; i++) {
            this.widgets[i].widgetIndex = i;
            this.widgets[i].z_position = this.widgets.length - i;
        }
    }

    _widgetDataChangedEvent() {
        this._detachWidgetGroups();
        const changedData = Me.settings.get_value('changed-data').deep_unpack();
        const widgetIndex = /^\d+$/.test(changedData['WidgetIndex'] || '') ? Number(changedData['WidgetIndex']) : NaN;
        const elementIndex_ = /^\d+$/.test(changedData['ElementIndex'] || '') ? Number(changedData['ElementIndex']) : NaN;
        const elementType = changedData['ElementType'];
        const widgetDeleted = changedData['WidgetDeleted'] === 'true';
        const widgetAdded = changedData['WidgetAdded'] === 'true';
        const elementDeleted = changedData['ElementDeleted'] === 'true';
        const elementAdded = changedData['ElementAdded'] === 'true';
        const widgetMoved = changedData['WidgetMoved'] === 'true';
        const widgetIndexChanged = changedData['WidgetIndexChanged'] === 'true';
        const widgetIndexNew = /^\d+$/.test(changedData['WidgetIndexNew'] || '') ? Number(changedData['WidgetIndexNew']) : NaN;
        const elementIndexChanged = changedData['ElementIndexChanged'] === 'true';

        if (!Number.isInteger(widgetIndex) || widgetIndex < 0 || widgetIndex > this.widgets.length || (widgetIndex === this.widgets.length && !widgetAdded) ||
            (widgetIndexChanged && (!Number.isInteger(widgetIndexNew) || widgetIndexNew < 0 || widgetIndexNew >= this.widgets.length))) {
            debugLog('update all this.widgets');

            this._destroyWidgets();
            this._createWidgetsWithoutSignals();
        } else if (widgetIndexChanged) {
            debugLog(`widget index changed from ${widgetIndex} to ${widgetIndexNew}`);

            const movedWidget = this.widgets.splice(widgetIndex, 1)[0];
            this.widgets.splice(widgetIndexNew, 0, movedWidget);

            this._updateWidgetsIndex();
        } else if (widgetMoved) {
            debugLog(`widget ${widgetIndex} moved`);
        } else if (widgetAdded) {
            debugLog(`widget ${widgetIndex} created`);

            const widget = this._createWidget(widgetIndex);
            this.widgets.push(widget);
            this._updateWidgetsIndex();
        } else if (widgetDeleted) {
            debugLog(`widget ${widgetIndex} deleted`);

            this._destroyWidget(widgetIndex);
            this._updateWidgetsIndex();
        } else if (elementType === 'Lock_Widget') {
            debugLog(`widget ${widgetIndex} locked/unlocked`);

            const oldWidget = this.widgets[widgetIndex];
            this.widgets[widgetIndex] = this._createWidget(widgetIndex, 0);
            oldWidget.destroy();
        } else if (elementType && (!Number.isInteger(elementIndex_) || elementIndex_ < 0 || !WIDGETDATA[widgetIndex]?.[elementIndex_])) {
            this.widgets[widgetIndex].createElements();
            this.widgets[widgetIndex].updateComponents(0);
        } else if (elementDeleted || elementAdded || elementIndexChanged) {
            debugLog(`element added/deleted/index-changed at widget ${widgetIndex}`);

            this.widgets[widgetIndex].createElements();
            this.widgets[widgetIndex].updateComponents(0);
        } else {
            debugLog(`widget ${widgetIndex} element setting changed`);

            this.widgets[widgetIndex].updateComponents();
        }

        this._detachWidgetGroups();
        this._applyWidgetGroups();
        this._removeClockTimer();
        this._startClockTimer();
        Me.settings.set_value('changed-data', new GLib.Variant('a{ss}', {}));
    }
}


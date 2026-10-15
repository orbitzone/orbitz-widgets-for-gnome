/* eslint-disable jsdoc/require-jsdoc */
const {
    Clutter, Gio, GLib, GObject,
    Graphene, Meta, Pango, St,
} = imports.gi;

const DND = imports.ui.dnd;
const ExtensionUtils = imports.misc.extensionUtils;
const Main = imports.ui.main;
const Me = ExtensionUtils.getCurrentExtension();
const PopupMenu = imports.ui.popupMenu;
let widgetsEnabled = false;
const activeCommandRuns = new Set();
const pendingStops = new Set();
const Utils = Me.imports.utils;

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
                if (!label._networkDestroyed && metricMode(getData(label.widgetIndex, label.elementIndex, 'Text_Command')) === data.mode && label.text !== data.text) {
                    label.text = data.text;
                    label.clutter_text.set_markup(data.text);
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
function scheduleNetworkClicks(delay = 250) {
    if (networkClickTimer || !networkClickLabels.size)
        return;
    networkClickTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, delay, () => {
        networkClickTimer = null;
        let active = false;
        const pointer = global.get_pointer();
        for (const label of networkClickLabels)
            active = label._checkNetworkClick(pointer) || active;
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

        if (!Utils.getData(WIDGETDATA, index, WIDGET_DATA_INDEX, 'Lock_Widget', 'bool'))
            this.makeDraggable();

        this.createElements();
        this.updateClocks(true);
        } catch (error) { this.destroy(); throw error; }
    }

    _getStableWidth() {
        const configured = Number(getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_Width'));
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
        if (this._isDragging) {
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

        // skip first element as that stores widget layout/style data, not widget elements
        for (let i = 1; i < clockData.length; i++) {
            const clockType = getData(this._widgetIndex, i, 'Element_Type');
            if (clockType === DIGITAL_CLOCK) {
                const digitalClock = new DigitalClock(this._widgetIndex, i);
                this.add_child(digitalClock);
                this._digitalClocks.push(digitalClock);
            } else if (clockType === ANALOG_CLOCK) {
                const analogClock = new AnalogClock(this._widgetIndex, i, clockData[i]);
                this.add_child(analogClock);
                this._analogClocks.push(analogClock);
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

        this.style = style;

        this.z_position = WIDGETDATA.length - this._widgetIndex;
    }

    vfunc_button_press_event() {
        const event = Clutter.get_current_event();

        if (event.get_button() === 1) {
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
        if (this._menu)
            this._menu.close(true);
        this._removeMenuTimeout();

        this._isDragging = true;
        this._dragMonitor = {
            dragMotion: this._onDragMotion.bind(this),
        };
        DND.addDragMonitor(this._dragMonitor);

        this._dragX = this.x;
        this._dragY = this.y;
    }

    _onDragMotion(dragEvent) {
        this.deltaX = dragEvent.x - (dragEvent.x - this._dragX);
        this.deltaY = dragEvent.y - (dragEvent.y - this._dragY);

        const [x, y] = this.allocation.get_origin();
        this._dragX = x;
        this._dragY = y;

        return DND.DragMotionResult.CONTINUE;
    }

    _onDragEnd() {
        this._isDragging = false;
        if (this._dragMonitor) {
            DND.removeDragMonitor(this._dragMonitor);
            this._dragMonitor = null;
        }

        let [x, y] = [Math.round(this.deltaX), Math.round(this.deltaY)];
        const width = this.get_width();
        const height = this.get_height();
        const newX = x + width;
        const newY = y + height;

        const anchorPoint = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_AnchorPoint', 'int');
        if (anchorPoint === AnchorPoint.BOTTOM_LEFT) {
            y = newY;
        } else if (anchorPoint === AnchorPoint.TOP_RIGHT) {
            x = newX;
        } else if (anchorPoint === AnchorPoint.BOTTOM_RIGHT) {
            x = newX;
            y = newY;
        }

        Me.settings.set_value('changed-data', new GLib.Variant('a{ss}', {
            'WidgetIndex': this._widgetIndex.toString(),
            'WidgetMoved': 'true',
        }));
        setData(this._widgetIndex, WIDGET_DATA_INDEX, 'Location_X', x);
        setData(this._widgetIndex, WIDGET_DATA_INDEX, 'Location_Y', y);
        debugLog(`drag end - (${x}, ${y})`);
    }

    getDragActorSource() {
        return this;
    }

    makeDraggable() {
        this._draggable = DND.makeDraggable(this);
        this._draggable._dragActorDropped = () => {
            this._draggable._animationInProgress = true;
            this._draggable._dragCancellable = false;
            this._draggable._dragState = DND.DragState.INIT;
            this._draggable._onAnimationComplete(this._draggable._dragActor, Clutter.get_current_event().get_time());
            return true;
        };

        this.dragBeginId = this._draggable.connect('drag-begin', this._onDragBegin.bind(this));
        this.dragEndId = this._draggable.connect('drag-end', this._onDragEnd.bind(this));
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

        if (this._dragMonitor) {
            DND.removeDragMonitor(this._dragMonitor);
            this._dragMonitor = null;
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
        const textLineAlignment = getData(this.widgetIndex, index, 'Text_LineAlignment', 'align');

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

        this.style = `font-size: ${textSize}pt; font-feature-settings: "tnum";${textStyle}`;

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
class AzClockCommandLabel extends Label {
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
            if (!networkClickLabels.size && networkClickTimer) {
                GLib.source_remove(networkClickTimer);
                networkClickTimer = null;
            }
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
            this._closeNetworkDialog();
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

    _checkNetworkClick(pointer) {
        if (this._networkDestroyed)
            return false;
        const [px, py, modifiers] = pointer;
        const [x, y] = this.get_transformed_position();
        const [w, h] = this.get_transformed_size();
        const inside = px >= x && px < x + w && py >= y && py < y + h;
        const down = !!(modifiers & Clutter.ModifierType.BUTTON1_MASK);
        if (down && !this._networkClickHeld)
            this._networkClickStart = inside && !this._networkDialog?.visible ? [px, py] : null;
        if (!down && this._networkClickHeld && inside && this._networkClickStart) {
            const [sx, sy] = this._networkClickStart;
            if (Math.abs(px - sx) < 8 && Math.abs(py - sy) < 8) {
                try {
                this._openNetworkDialog();
                } catch (error) {
                logError(error, 'Desktop Clock network click');
                }
            }
        }
        this._networkClickHeld = down;
        if (!down)
            this._networkClickStart = null;
        return inside && !this._networkDialog?.visible;
    }

    _closeNetworkDialog() {
        this._cancelFirewallInspection();
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

    _buildUpdatesDialog() {
        this._networkBackdrop = new St.Widget({reactive: true, visible: false});
        this._networkBackdrop.add_constraint(new Clutter.BindConstraint({source: global.stage, coordinate: Clutter.BindCoordinate.ALL}));
        this._networkBackdrop.connect('button-press-event', () => {
            this._closeNetworkDialog();
            return Clutter.EVENT_STOP;
        });
        Main.uiGroup.add_child(this._networkBackdrop);
        this._networkDialog = new St.BoxLayout({vertical: true, reactive: true,
            style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 8px; padding: 12px; spacing: 10px;'});
        this._updatesHeading = new St.Label({text: 'Atualizações', style: 'font-weight: bold; font-size: 18px;'});
        this._networkDialog.add_child(this._updatesHeading);
        const note = new St.Label({text: 'Consulte os pacotes abaixo. Passe o mouse nas ações para ver o comando.', style: 'font-size: 12px; color: #c8c8c8;'});
        note.clutter_text.set_line_wrap(true);
        this._updatesNote = note;
        this._networkDialog.add_child(note);
        const scroll = new St.ScrollView({style: 'width: 720px; height: 300px;', reactive: true});
        scroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this._updatesRows = new St.BoxLayout({vertical: true, style: 'spacing: 8px;'});
        scroll.add_actor(this._updatesRows);
        this._networkDialog.add_child(scroll);
        this._updatesActions = new St.BoxLayout({vertical: true, style: 'spacing: 8px;'});
        this._networkDialog.add_child(this._updatesActions);
        const footer = new St.BoxLayout({style: 'spacing: 8px;'});
        this._networkRefreshButton = new St.Button({reactive: true, can_focus: true, label: 'Reler lista', accessible_name: 'Reler lista de atualizações', style: 'background-color: transparent; color: white; padding: 6px;'});
        this._networkRefreshButton.connect('clicked', () => this._refreshNetworkDialog());
        footer.add_child(this._networkRefreshButton);
        this._networkRefreshStatus = new St.Label({text: '', style: 'font-size: 12px; color: #c8c8c8;'});
        footer.add_child(this._networkRefreshStatus);
        this._networkDialog.add_child(footer);
        Main.uiGroup.add_child(this._networkDialog);
    }

    _renderUpdates(data) {
        if (typeof data.text !== 'string' || data.text.length > 128 || typeof data.reboot !== 'boolean' ||
            typeof data.index_updated !== 'string' || data.index_updated.length > 64 ||
            typeof data.error !== 'string' || data.error.length > 256 || !Array.isArray(data.items) || data.items.length > 100 ||
            !Number.isInteger(data.omitted) || data.omitted < 0 ||
            !Array.isArray(data.notices) || data.notices.length > 20 || data.notices.some(x => typeof x !== 'string' || x.length > 2048) ||
            !Array.isArray(data.actions) || data.actions.length > 20 || data.actions.some(x => !x ||
                typeof x.id !== 'string' || !/^[a-z0-9-]{1,40}$/.test(x.id) || typeof x.name !== 'string' || x.name.length > 80 ||
                typeof x.command !== 'string' || x.command.length > 2048) ||
            data.items.some(item => !item || !['name', 'installed', 'version', 'source'].every(k => typeof item[k] === 'string' && item[k].length <= 512)))
            throw new Error('Resposta de atualizações inválida.');
        this._updatesHeading.text = data.text;
        this._updatesRows.destroy_all_children();
        const add = (text, color = '#c8c8c8') => {
            const label = new St.Label({text, style: `padding: 4px; color: ${color};`});
            label.clutter_text.set_line_wrap(true);
            this._updatesRows.add_child(label);
        };
        add(data.reboot ? 'Reinicialização pendente.' : 'Sem indicação de reinicialização pendente.');
        add('Índice APT mais antigo: ' + data.index_updated);
        for (const notice of data.notices) add(notice);
        if (data.error) add(data.error);
        if (data.omitted) add(`${data.omitted} pacotes adicionais.`);
        for (const source of ['APT', 'Snap', 'Flatpak']) {
            const items = data.items.filter(item => item.source === source);
            add(source + ' · ' + items.length, 'white');
            for (const item of items)
                add((item.security ? '[Segurança] ' : '') + item.name + ' · ' + item.installed + ' → ' + item.version, item.security ? '#ffd479' : '#82cfff');
        }
        this._updatesActions.destroy_all_children();
        this._updatesActions.add_child(new St.Label({text: 'Ações · confirme com Enter no terminal',
            style: 'font-size: 12px; color: #c8c8c8;'}));
        let row;
        for (const [index, action] of data.actions.entries()) {
            if (index % 4 === 0) {
                row = new St.BoxLayout({style: 'spacing: 8px;', x_expand: true});
                this._updatesActions.add_child(row);
            }
            const button = new St.Button({reactive: true, can_focus: true,
                accessible_name: action.name + ': ' + action.command, x_expand: true,
                style: 'width: 156px; padding: 8px; border-radius: 6px; background-color: #315d80; color: white;'});
            const label = new St.Label({text: action.name, x_align: Clutter.ActorAlign.CENTER});
            label.clutter_text.set_line_wrap(true);
            label.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
            button.set_child(label);
            this._attachActionTooltip(button, action.command);
            button.connect('clicked', () => {
                try {
                    const [, argv] = GLib.shell_parse_argv(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
                    Gio.Subprocess.new([...argv, '--action', action.id], Gio.SubprocessFlags.NONE);
                    this._networkRefreshStatus.text = 'Comando aberto no terminal; releia a lista após concluir.';
                } catch (error) { this._networkRefreshStatus.text = 'Não foi possível abrir o terminal.'; }
            });
            row.add_child(button);
        }
    }

    _attachActionTooltip(button, command) {
        const tooltip = new St.Label({text: command, visible: false, reactive: false,
            style: 'max-width: 620px; padding: 10px 12px; border-radius: 6px; background-color: #101820; color: #e5f3ff; border: 1px solid #6088a8; font-family: monospace; font-size: 12px;'});
        tooltip.clutter_text.set_line_wrap(true);
        tooltip.clutter_text.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);
        tooltip.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
        Main.uiGroup.add_child(tooltip);
        const hide = () => tooltip.hide();
        const show = () => {
            if (!this._networkDialog.visible) return;
            tooltip.show();
            const [x, y] = button.get_transformed_position();
            const [width, height] = tooltip.get_preferred_size().slice(2);
            const monitor = Main.layoutManager.findMonitorForActor(button) || Main.layoutManager.primaryMonitor;
            tooltip.set_position(Math.max(monitor.x + 8, Math.min(x, monitor.x + monitor.width - width - 8)),
                y - height - 8 >= monitor.y ? y - height - 8 : y + button.height + 8);
        };
        button.track_hover = true;
        button.connect('notify::hover', () => button.hover ? show() : hide());
        button.connect('key-focus-in', show);
        button.connect('key-focus-out', hide);
        button.connect('clicked', hide);
        const visibilitySignal = this._networkDialog.connect('notify::visible', hide);
        button.connect('destroy', () => {
            this._networkDialog.disconnect(visibilitySignal);
            tooltip.destroy();
        });
        return show;
    }

    _buildTemperaturesDialog() {
        this._networkBackdrop = new St.Widget({reactive: true, visible: false});
        this._networkBackdrop.add_constraint(new Clutter.BindConstraint({source: global.stage, coordinate: Clutter.BindCoordinate.ALL}));
        this._networkBackdrop.connect('button-press-event', () => {
            this._closeNetworkDialog();
            return Clutter.EVENT_STOP;
        });
        Main.uiGroup.add_child(this._networkBackdrop);
        this._networkDialog = new St.BoxLayout({vertical: true, reactive: true,
            style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 10px; padding: 16px; spacing: 12px;'});
        this._temperatureHeading = new St.Label({text: 'Temperaturas · sensores', style: 'font-size: 18px; font-weight: bold;'});
        this._networkDialog.add_child(this._temperatureHeading);
        this._networkDialog.add_child(new St.Label({text: 'Acima de 80 °C em vermelho · identificação fornecida pelo sistema', style: 'font-size: 12px; color: #b9c5cf;'}));
        this._temperatureRows = new St.BoxLayout({style: 'spacing: 12px;'});
        this._networkDialog.add_child(this._temperatureRows);
        const footer = new St.BoxLayout({style: 'spacing: 12px;'});
        this._networkRefreshButton = new St.Button({label: 'Atualizar', reactive: true, can_focus: true,
            accessible_name: 'Atualizar temperaturas', style: 'padding: 8px 12px; border-radius: 6px; background-color: #315d80; color: white;'});
        this._networkRefreshButton.connect('clicked', () => this._refreshNetworkDialog());
        footer.add_child(this._networkRefreshButton);
        this._networkRefreshStatus = new St.Label({text: '', style: 'font-size: 12px; color: #b9c5cf;', y_align: Clutter.ActorAlign.CENTER});
        footer.add_child(this._networkRefreshStatus);
        this._networkDialog.add_child(footer);
        Main.uiGroup.add_child(this._networkDialog);
    }

    _temperatureCategory(item) {
        const code = item.name.split(' · ').pop();
        if (item.group.startsWith('coretemp') || code === 'x86_pkg_temp') return 'CPU';
        if (item.group.startsWith('NVIDIA') || item.group.startsWith('amdgpu')) return 'GPU';
        if (item.group.startsWith('nvme')) return 'Armazenamento';
        if (!item.group.startsWith('applesmc')) return 'Outros sensores';
        if (code === 'TCGC' || code.startsWith('TG')) return 'GPU';
        if (code.startsWith('TC')) return 'CPU';
        if (/^TH0[A-Ca-c]$/.test(code)) return 'Armazenamento';
        if (code === 'TM0P') return 'Memória RAM';
        if (['TPCD', 'TTLD', 'TTRD', 'TW0P'].includes(code)) return 'Placa e conectividade';
        if (/^Th[0-9]H$/.test(code)) return 'Dissipação';
        if (['Ts0P', 'Ts1P', 'Ts0S', 'Ts1S'].includes(code)) return 'Gabinete';
        if (code === 'TA0V') return 'Ambiente';
        return 'Outros sensores';
    }

    _temperatureColumns(items) {
        const groups = new Map();
        for (const item of items) {
            const title = this._temperatureCategory(item);
            if (!groups.has(title)) groups.set(title, []);
            groups.get(title).push(item);
        }
        const columns = [[], [], [], []];
        const heights = [0, 0, 0, 0];
        const critical = new Set(['CPU', 'GPU', 'Memória RAM', 'Armazenamento']);
        const segments = [...groups].map(([title, sensors]) => ({title,
            items: sensors.sort((a, b) => a.name.localeCompare(b.name, undefined, {numeric: true}))}));
        segments.sort((a, b) => b.items.length - a.items.length);
        for (const segment of segments) {
            const start = critical.has(segment.title) ? 0 : 2;
            const index = heights[start] <= heights[start + 1] ? start : start + 1;
            columns[index].push(segment);
            heights[index] += 36 + segment.items.length * 34;
        }
        return columns;
    }

    _renderTemperatures(data) {
        if (!data || !Array.isArray(data.items) || data.items.length > 256 || !Number.isInteger(data.omitted) || data.omitted < 0)
            throw new Error('Resposta dos sensores inválida.');
        // Unavailable records never enter component state or acquire actors/signals.
        const available = data.items.filter(x => x && typeof x === 'object' &&
            Number.isFinite(x.value) && x.value >= -20 && x.value <= 250);
        if (available.some(x => typeof x.group !== 'string' || x.group.length > 128 || typeof x.name !== 'string' || x.name.length > 100 ||
            (x.description !== undefined && (typeof x.description !== 'string' || x.description.length > 512))))
            throw new Error('Resposta dos sensores inválida.');
        data = {items: available.map(x => ({group: x.group, name: x.name, value: x.value, description: x.description})), omitted: data.omitted};
        this._temperatureData = data;
        const monitor = Main.layoutManager.findMonitorForActor(this) || Main.layoutManager.primaryMonitor;
        const columns = this._temperatureColumns(data.items);
        this._temperatureHeading.text = `Temperaturas · ${data.items.length} sensores`;
        this._temperatureRows.destroy_all_children();
        for (const [index, segments] of columns.entries()) {
            const column = new St.BoxLayout({vertical: true, style: 'spacing: 0px; width: 220px;'});
            column.add_child(new St.Label({text: index < 2 ? 'Hardware crítico' : 'Sensores auxiliares',
                style: `font-size: 11px; color: ${index < 2 ? '#8bd5ca' : '#b9c5cf'}; padding: 0px 4px 8px;`}));
            for (const segment of segments) {
                column.add_child(new St.Label({text: segment.title,
                    style: 'font-size: 12px; font-weight: bold; color: #b9d5e8; padding: 8px 4px 6px;'}));
                for (const item of segment.items) {
                const hot = item.value > 80;
                const card = new St.BoxLayout({vertical: true,
                    style: 'height: 24px; padding: 3px 8px; margin-bottom: 4px; border-radius: 5px; background-color: #293039;'});
                const line = new St.BoxLayout({style: 'spacing: 8px;'});
                const name = new St.Label({text: item.name, x_expand: true, style: 'font-size: 13px; color: #e6edf3;'});
                name.clutter_text.set_ellipsize(Pango.EllipsizeMode.END);
                line.add_child(name);
                const help = new St.Button({label: '?', reactive: true, can_focus: true,
                    accessible_name: 'Descrição de ' + item.name,
                    style: 'font-size: 12px; padding: 0px 4px; border-radius: 8px; background-color: #405268; color: #dcecff;'});
                const showHelp = this._attachActionTooltip(help, (item.description || 'Sensor ' + item.name + ': descrição específica indisponível.') + '\nFonte: ' + item.group);
                help.connect('clicked', showHelp);
                line.add_child(help);
                line.add_child(new St.Label({text: `${item.value.toFixed(1)} °C`,
                    style: `font-size: 14px; font-weight: bold; color: ${hot ? '#ff5c5c' : '#8bd5ca'};`}));
                card.add_child(line);
                card.accessible_name = `${item.group}: ${item.name}, ${item.value} graus Celsius`;
                column.add_child(card);
                }
                column.add_child(new St.Widget({style: 'height: 6px;'}));
            }
            this._temperatureRows.add_child(column);
        }
        if (!data.items.length)
            this._temperatureRows.add_child(new St.Label({text: 'Nenhum sensor de temperatura disponível.', style: 'padding: 16px; color: #b9c5cf;'}));
        if (data.omitted) this._temperatureHeading.text += ` · ${data.omitted} adicionais`;
        const [, width] = this._networkDialog.get_preferred_width(-1);
        const [, height] = this._networkDialog.get_preferred_height(width);
        this._networkDialog.set_position(monitor.x + Math.max(8, (monitor.width - width) / 2), monitor.y + Math.max(8, (monitor.height - height) / 2));
    }

    _buildProcessesDialog() {
        this._buildUpdatesDialog();
        this._processesDialog = true;
        this._updatesHeading.text = 'Processos · desempenho';
        this._updatesNote.text = 'Diagnóstico da amostra atual. CPU por processo pode superar 100% ao usar vários núcleos.';
        this._networkRefreshButton.label = 'Atualizar';
        this._networkRefreshButton.accessible_name = 'Atualizar diagnóstico e processos';
    }

    _renderProcesses(data) {
        const validRows = rows => Array.isArray(rows) && rows.length <= 7 && rows.every(r => r &&
            Number.isInteger(r.pid) && r.pid > 0 && typeof r.name === 'string' && r.name.length <= 80 &&
            Number.isFinite(r.cpu) && r.cpu >= 0 && Number.isFinite(r.memory) && r.memory >= 0);
        if (!data || typeof data.summary !== 'string' || data.summary.length > 2048 ||
            !Array.isArray(data.notices) || data.notices.length > 20 || data.notices.some(n => typeof n !== 'string' || n.length > 2048) ||
            !validRows(data.cpu_rows) || !validRows(data.memory_rows) ||
            !Array.isArray(data.actions) || data.actions.length > 8 || data.actions.some(a => !a ||
                !['monitor', 'startup', 'balanced', 'performance'].includes(a.id) ||
                ['name', 'command', 'effect'].some(k => typeof a[k] !== 'string' || a[k].length > 2048)))
            throw new Error('Resposta de processos inválida.');
        this._updatesRows.destroy_all_children();
        this._updatesActions.destroy_all_children();
        const add = (text, color = '#c8c8c8') => {
            const label = new St.Label({text, style: `padding: 4px; color: ${color};`});
            label.clutter_text.set_line_wrap(true);
            label.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
            this._updatesRows.add_child(label);
        };
        add(data.summary, '#82cfff');
        for (const notice of data.notices) add(notice);
        for (const [title, rows] of [['Maior uso de CPU', data.cpu_rows], ['Maior uso de RAM', data.memory_rows]]) {
            add(title, 'white');
            for (const row of rows)
                add(`${row.name} · PID ${row.pid} · CPU ${row.cpu.toFixed(1)}% · RAM ${row.memory} MiB`);
        }
        this._updatesActions.add_child(new St.Label({text: 'Ações · confira o comando no tooltip e confirme com Enter no terminal',
            style: 'font-size: 12px; color: #c8c8c8;'}));
        let row;
        for (const [index, action] of data.actions.entries()) {
            if (index % 4 === 0) {
                row = new St.BoxLayout({style: 'spacing: 8px;'});
                this._updatesActions.add_child(row);
            }
            const button = new St.Button({reactive: true, can_focus: true,
                accessible_name: action.name + ': ' + action.effect + ' ' + action.command,
                style: 'width: 156px; padding: 8px; border-radius: 6px; background-color: #315d80; color: white;'});
            const label = new St.Label({text: action.name, x_align: Clutter.ActorAlign.CENTER});
            label.clutter_text.set_line_wrap(true);
            button.set_child(label);
            this._attachActionTooltip(button, action.effect + '\n\n' + action.command);
            button.connect('clicked', () => {
                try {
                    const [, argv] = GLib.shell_parse_argv(getData(this.widgetIndex, this.elementIndex, 'Text_Command'));
                    Gio.Subprocess.new([...argv, '--action', action.id], Gio.SubprocessFlags.NONE);
                    this._networkRefreshStatus.text = 'Ação aberta no terminal. Atualize o diagnóstico após concluir.';
                } catch (error) {
                    this._networkRefreshStatus.text = 'Não foi possível abrir a ação.';
                }
            });
            row.add_child(button);
        }
    }

    _buildDockerDialog() {
        this._networkBackdrop = new St.Widget({reactive: true, visible: false});
        this._networkBackdrop.add_constraint(new Clutter.BindConstraint({source: global.stage, coordinate: Clutter.BindCoordinate.ALL}));
        this._networkBackdrop.connect('button-press-event', () => {
            this._closeNetworkDialog();
            return Clutter.EVENT_STOP;
        });
        Main.uiGroup.add_child(this._networkBackdrop);
        this._networkDialog = new St.BoxLayout({vertical: true, reactive: true,
            style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 8px; padding: 12px; spacing: 10px;'});
        this._dockerHeading = new St.Label({text: 'Docker · serviços em execução', style: 'font-weight: bold; font-size: 18px;'});
        this._networkDialog.add_child(this._dockerHeading);
        const note = new St.Label({text: 'Clique no serviço para abrir a porta TCP publicada. Portas sem HTTP podem não abrir uma página.', style: 'font-size: 12px; color: #c8c8c8;'});
        note.clutter_text.set_line_wrap(true);
        this._networkDialog.add_child(note);
        const scroll = new St.ScrollView({style: 'width: 720px; height: 300px;', reactive: true});
        scroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this._dockerRows = new St.BoxLayout({vertical: true, style: 'spacing: 8px;'});
        scroll.add_actor(this._dockerRows);
        this._networkDialog.add_child(scroll);
        const footer = new St.BoxLayout({style: 'spacing: 8px;'});
        this._networkRefreshButton = new St.Button({reactive: true, can_focus: true, accessible_name: 'Atualizar serviços Docker', style: 'background-color: transparent; color: white; padding: 6px;'});
        this._networkRefreshButton.set_child(new St.Icon({icon_name: 'view-refresh-symbolic', icon_size: 18, style: 'color: white;'}));
        this._networkRefreshButton.connect('clicked', () => this._refreshNetworkDialog());
        footer.add_child(this._networkRefreshButton);
        this._networkRefreshStatus = new St.Label({text: '', style: 'font-size: 12px; color: #c8c8c8;'});
        footer.add_child(this._networkRefreshStatus);
        this._networkDialog.add_child(footer);
        Main.uiGroup.add_child(this._networkDialog);
    }

    _validDockerUrl(url) {
        try {
            const uri = GLib.Uri.parse(url, GLib.UriFlags.NONE);
            return ['http', 'https'].includes(uri.get_scheme()) && !!uri.get_host() &&
                !uri.get_userinfo() && uri.get_port() >= 1 && uri.get_port() <= 65535 &&
                !uri.get_query() && !uri.get_fragment();
        } catch (error) { return false; }
    }

    _renderDocker(data) {
        if (typeof data.text !== 'string' || data.text.length > 128 || !Array.isArray(data.items) || data.items.length > 100 ||
            data.items.some(item => !item || !['name', 'ports', 'url'].every(key => typeof item[key] === 'string') ||
                item.name.length > 128 || item.ports.length > 256 || item.url.length > 512 ||
                (item.url && !this._validDockerUrl(item.url))))
            throw new Error('Resposta Docker inválida.');
        this._dockerHeading.text = 'Docker · ' + data.text;
        this._dockerRows.destroy_all_children();
        if (!data.items.length)
            this._dockerRows.add_child(new St.Label({text: data.error || 'Nenhum contêiner em execução.', style: 'padding: 8px;'}));
        if (Number.isInteger(data.skipped_containers) && data.skipped_containers > 0)
            this._dockerRows.add_child(new St.Label({text: `${data.skipped_containers} contêineres adicionais não inspecionados nesta consulta.`}));
        if (Number.isInteger(data.omitted) && data.omitted > 0)
            this._dockerRows.add_child(new St.Label({text: `${data.omitted} entradas adicionais; consulte o Docker para a lista completa.`}));
        for (const item of data.items) {
            const row = new St.BoxLayout({style: 'spacing: 12px; padding: 8px;'});
            const service = new St.Button({label: item.name, reactive: !!item.url, can_focus: !!item.url,
                style: 'color: #82cfff;', accessible_name: item.url ? `Abrir ${item.name}: ${item.url}` : item.name});
            service.connect('clicked', () => {
                try { Gio.AppInfo.launch_default_for_uri(item.url, null); }
                catch (error) { this._networkRefreshStatus.text = 'Não foi possível abrir o navegador.'; }
            });
            row.add_child(service);
            row.add_child(new St.Label({text: item.ports, style: 'color: #ffd479;'}));
            this._dockerRows.add_child(row);
        }
    }

    _buildFirewallDialog() {
        this._networkBackdrop = new St.Widget({reactive: true, visible: false});
        this._networkBackdrop.add_constraint(new Clutter.BindConstraint({source: global.stage, coordinate: Clutter.BindCoordinate.ALL}));
        this._networkBackdrop.connect('button-press-event', () => {
            this._closeNetworkDialog();
            return Clutter.EVENT_STOP;
        });
        Main.uiGroup.add_child(this._networkBackdrop);
        this._networkDialog = new St.BoxLayout({vertical: true, reactive: true,
            style: 'background-color: #202020; color: white; border: 1px solid #606060; border-radius: 8px; padding: 12px; spacing: 10px;'});
        this._firewallHeading = new St.Label({text: 'Firewall · padrões de atividade', style: 'font-weight: bold; font-size: 18px;'});
        this._networkDialog.add_child(this._firewallHeading);
        const note = new St.Label({text: 'Destaques por persistência e variação de portas, destinos ou protocolos. Um padrão indica o que revisar; não comprova invasão.', style: 'font-size: 12px; color: #c8c8c8;'});
        note.clutter_text.set_line_wrap(true);
        this._networkDialog.add_child(note);
        const scroll = new St.ScrollView({style: 'width: 720px; height: 300px;', reactive: true});
        scroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this._firewallRows = new St.BoxLayout({vertical: true, style: 'spacing: 8px;'});
        scroll.add_actor(this._firewallRows);
        this._networkDialog.add_child(scroll);
        const footer = new St.BoxLayout({style: 'spacing: 8px;'});
        this._networkRefreshButton = new St.Button({reactive: true, can_focus: true, accessible_name: 'Atualizar eventos do firewall', style: 'background-color: transparent; color: white; padding: 6px;'});
        this._networkRefreshButton.set_child(new St.Icon({icon_name: 'view-refresh-symbolic', icon_size: 18, style: 'color: white;'}));
        this._networkRefreshButton.connect('clicked', () => this._refreshNetworkDialog());
        footer.add_child(this._networkRefreshButton);
        this._networkRefreshStatus = new St.Label({text: '', style: 'font-size: 12px; color: #c8c8c8;'});
        footer.add_child(this._networkRefreshStatus);
        this._networkDialog.add_child(footer);
        Main.uiGroup.add_child(this._networkDialog);
    }

    _renderFirewall(data) {
        this._cancelFirewallInspection();
        if (typeof data.text !== 'string' || data.text.length > 128 || typeof data.scope !== 'string' || data.scope.length > 4096 || typeof data.updated !== 'string' || !Array.isArray(data.groups) || data.groups.length > 50)
            throw new Error('Resposta do firewall inválida.');
        for (const row of data.groups) {
            if (!row || !['source', 'destination', 'protocol', 'ports', 'last', 'kind', 'interface'].every(key => typeof row[key] === 'string' && row[key].length <= 512) || !Number.isInteger(row.count) || row.count < 1 || (data.pattern_mode && (typeof row.reason !== 'string' || row.reason.length > 4096)))
                throw new Error('Evento do firewall inválido.');
        }
        this._firewallData = data;
        this._firewallHeading.text = data.text + ' · Firewall';
        this._firewallRows.destroy_all_children();
        const scope = new St.Label({text: data.scope, style: 'font-size: 11px; color: #c8c8c8;'});
        scope.clutter_text.set_line_wrap(true);
        scope.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
        this._firewallRows.add_child(scope);
        if (!data.groups.length)
            this._firewallRows.add_child(new St.Label({text: 'Nenhum padrão atingiu os critérios de destaque na janela coletada.', style: 'color: #8bd5a1; padding: 8px;'}));
        for (const item of data.groups) {
            const box = new St.BoxLayout({vertical: true, style: 'padding: 8px; spacing: 4px; border-bottom: 1px solid #444;'});
            const escape = value => GLib.markup_escape_text(String(value), -1);
            if (data.pattern_mode && typeof item.reason === 'string') {
                const evidence = new St.Label({text: item.reason, style: 'font-size: 12px; color: #ffd479;'});
                evidence.clutter_text.set_line_wrap(true);
                evidence.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
                box.add_child(evidence);
            }
            const sourceColor = item.source_remote === true || item.kind === 'Origem externa' ? '#ff9e64' : '#82cfff';
            const title = new St.BoxLayout({style: 'spacing: 8px;'});
            const source = new St.Button({label: item.source, reactive: true, can_focus: true, style: `color: ${sourceColor}; padding: 0px; font-family: monospace;`});
            source.connect('clicked', () => this._inspectFirewall('ip', item.source));
            title.add_child(source);
            title.add_child(new St.Label({text: '→'}));
            const destination = new St.Button({label: item.destination, reactive: true, can_focus: true, style: 'color: #82cfff; padding: 0px; font-family: monospace;'});
            destination.connect('clicked', () => this._inspectFirewall('ip', item.destination));
            title.add_child(destination);
            title.add_child(new St.Label({text: `${item.count} eventos`}));
            box.add_child(title);
            box.add_child(new St.Label({text: `${item.kind}${item.local ? ' · origem local/reservada' : ''} · ${item.protocol} · ${item.interface || '—'}`, style: 'color: #c8c8c8; font-size: 12px;'}));
            let ports = new St.BoxLayout({style: 'spacing: 8px;'});
            ports.add_child(new St.Label({text: 'Portas destino:', style: 'font-size: 12px;'}));
            const portValues = item.ports.split(', ').slice(0, 30);
            for (let i = 0; i < portValues.length; i++) {
                const value = portValues[i];
                if (i > 0 && i % 8 === 0) {
                    box.add_child(ports);
                    ports = new St.BoxLayout({style: 'spacing: 8px;'});
                }
                if (/^\d+$/.test(value) && Number(value) > 0 && Number(value) <= 65535) {
                    const port = new St.Button({label: value, reactive: true, can_focus: true, style: 'color: #ffd479; padding: 0px;'});
                    port.connect('clicked', () => this._inspectFirewall('port', value));
                    ports.add_child(port);
                } else {
                    ports.add_child(new St.Label({text: value, style: 'color: #ffd479;'}));
                }
            }
            box.add_child(ports);
            box.add_child(new St.Label({text: `Primeiro: ${item.first || item.last} · Último: ${item.last}`, style: 'color: #aaa; font-size: 11px;'}));
            this._firewallRows.add_child(box);
        }
    }

    _cancelFirewallInspection() {
        const run = this._firewallInspection;
        if (!run)
            return;
        if (run.timeout) {
            GLib.source_remove(run.timeout);
            run.timeout = null;
        }
        stopCommandRun(run);
        this._firewallInspection = null;
    }

    async _inspectFirewall(kind, target) {
        if (this._networkDestroyed || !this._networkDialog?.visible)
            return;
        this._cancelFirewallInspection();
        const run = {proc: null, cancellable: new Gio.Cancellable(), generation: this._networkGeneration, timeout: null};
        this._firewallInspection = run;
        this._firewallRows.destroy_all_children();
        const toolbar = new St.BoxLayout({style: 'spacing: 12px;'});
        const button = (text, action) => {
            const actor = new St.Button({label: text, reactive: true, can_focus: true, style: 'color: #82cfff; padding: 6px;'});
            actor.connect('clicked', action);
            toolbar.add_child(actor);
        };
        button('← Voltar', () => this._renderFirewall(this._firewallData));
        button('Copiar endereço / porta', () => St.Clipboard.get_default().set_text(St.ClipboardType.CLIPBOARD, target));
        this._firewallRows.add_child(toolbar);
        const label = new St.Label({text: 'Consultando…', style: 'width: 680px; font-family: monospace; font-size: 12px; padding: 8px;'});
        label.clutter_text.set_line_wrap(true);
        label.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
        this._firewallRows.add_child(label);
        try {
            const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
            const [, argv] = GLib.shell_parse_argv(command);
            const flag = kind === 'dns' ? '--dns' : (kind === 'port' ? '--inspect-port' : '--inspect-ip');
            run.proc = Gio.Subprocess.new(['/usr/bin/setsid', ...argv, flag, target], Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE);
            run.timeout = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 15000, () => {
                run.timeout = null;
                run.timedOut = true;
                stopCommandRun(run);
                return GLib.SOURCE_REMOVE;
            });
            const [stdout, stderr] = await readCommandOutput(run);
            if (this._firewallInspection !== run || run.cancelled || this._networkDestroyed || run.generation !== this._networkGeneration)
                return;
            if (!run.proc.get_successful() || !stdout.startsWith('AZCLOCK_FIREWALL:'))
                throw new Error(stderr.trim().slice(0, 300) || 'Falha ao inspecionar.');
            const data = JSON.parse(stdout.slice('AZCLOCK_FIREWALL:'.length));
            if (typeof data.inspect !== 'string')
                throw new Error('Resposta inválida.');
            const escaped = GLib.markup_escape_text(data.inspect, -1);
            const selected = GLib.markup_escape_text(target, -1);
            const color = kind === 'port' ? '#ffd479' : (data.remote === true ? '#ff9e64' : '#82cfff');
            label.clutter_text.set_markup(escaped.split(selected).join(`<span foreground="${color}">${selected}</span>`));
            if (kind === 'ip') {
                const notice = new St.Label({text: 'Consultas abaixo usam a rede e revelam o IP consultado ao provedor.', style: 'font-size: 12px; color: #ffd479;'});
                notice.clutter_text.set_line_wrap(true);
                this._firewallRows.add_child(notice);
                button('Consultar DNS (rede)', () => this._inspectFirewall('dns', target));
                if (data.remote === true)
                    button('WHOIS / RDAP (externo)', () => {
                        try {
                            Gio.AppInfo.launch_default_for_uri(`https://rdap.org/ip/${encodeURIComponent(target).replace(/%3A/gi, ':')}`, null);
                        } catch (error) {
                            label.text = 'Não foi possível abrir a consulta externa.';
                        }
                    });
            }
        } catch (error) {
            if (this._firewallInspection === run && !this._networkDestroyed && run.generation === this._networkGeneration)
                label.text = run.timedOut ? 'Consulta demorou demais. Tente novamente.' : error.message;
        } finally {
            if (run.timeout)
                GLib.source_remove(run.timeout);
            if (this._firewallInspection === run)
                this._firewallInspection = null;
        }
    }

    _openNetworkDialog() {
        if (this._networkDestroyed)
            return;
        if (this._networkDialog && this._networkDialog.visible) {
            this._closeNetworkDialog();
            return;
        }
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
            this._networkBackdrop.connect('button-press-event', () => {
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
            const speedColumn = new St.BoxLayout({
                vertical: true,
                style: 'width: 220px; spacing: 12px; padding-left: 12px; border-left: 1px solid #606060;',
            });
            speedColumn.add_child(new St.Label({text: 'Velocidade da internet', style: 'font-weight: bold; color: #ededed;'}));
            this._speedtestButton = new St.Button({
                label: 'Testar velocidade', reactive: true, can_focus: true,
                style: 'background-color: #315d85; color: white; border-radius: 6px; padding: 10px;',
            });
            this._speedtestButton.connect('clicked', () => this._startSpeedtest());
            speedColumn.add_child(this._speedtestButton);
            this._speedtestResult = new St.Label({text: '', visible: false, style: 'font-size: 15px;'});
            speedColumn.add_child(this._speedtestResult);
            this._speedtestStatus = new St.Label({text: '', visible: false, style: 'font-size: 12px; color: #c8c8c8;'});
            this._speedtestStatus.clutter_text.set_line_wrap(true);
            this._speedtestStatus.clutter_text.set_ellipsize(Pango.EllipsizeMode.NONE);
            speedColumn.add_child(this._speedtestStatus);
            columns.add_child(speedColumn);
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
            Main.uiGroup.add_child(this._networkDialog);
        }
        this._networkBackdrop.show();
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
        Main.uiGroup.set_child_above_sibling(this._networkDialog, null);
        this._refreshNetworkDialog();
    }

    async _startSpeedtest() {
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
            if (this._networkConnectionsBox) {
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
                        row.add_child(new St.Label({text: `(${item.ip}) —`, style: 'color: #c8c8c8;'}));
                        row.add_child(new St.Label({text: String(item.port), style: 'color: #ffd479;'}));
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
        const filename = spotify ? 'spotify.svg' : 'chrome.svg';
        if (this._mediaIconFile !== filename) {
            this._mediaIcon.gicon = Gio.icon_new_for_string(GLib.build_filenamev([Me.path, 'media', 'players', filename]));
            this._mediaIcon.accessible_name = spotify ? 'Spotify' : 'Google Chrome';
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
                const players = names.filter(name => /^org\.mpris\.MediaPlayer2\.(spotify|chromium|chrome)(\.|$)/.test(name))
                    .sort((a, b) => Number(!a.includes('.spotify')) - Number(!b.includes('.spotify')));
                for (const player of players) {
                    try {
                        const values = (await call(player, '/org/mpris/MediaPlayer2', 'org.freedesktop.DBus.Properties',
                            'GetAll', new GLib.Variant('(s)', ['org.mpris.MediaPlayer2.Player']))).deep_unpack()[0];
                        const status = values.PlaybackStatus?.deep_unpack();
                        const metadata = values.Metadata?.deep_unpack() || {};
                        const title = metadata['xesam:title']?.deep_unpack() || '';
                        const artist = metadata['xesam:artist']?.deep_unpack() || [];
                        const score = status === 'Playing' ? 2 : status === 'Paused' ? 1 : 0;
                        if (score > bestScore) {
                            bestScore = score;
                            selectedPlayer = player;
                            text = `${status === 'Playing' ? '▶️' : status === 'Paused' ? '⏸️' : '⏹️'}  ${Array.isArray(artist) ? artist.join(', ') : ''} — ${title}`.slice(0, 1024);
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
            if (metricMode(command) === 'processes')
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
});

// eslint-disable-next-line no-unused-vars
function init() {
    ExtensionUtils.initTranslations(Me.metadata['gettext-domain']);
    return new AzClock();
}

class AzClock {
    enable() {
        widgetsEnabled = false;
        this.widgets = [];
        this._running = false;
        this._controller = new St.Button({reactive: true, can_focus: true, visible: true,
            width: 40, height: 36, accessible_name: 'Iniciar widgets',
            style: 'padding: 0px; border: 0px; background-color: transparent; box-shadow: none;'});
        this._controllerButton = this._controller;
        this._controllerIcons = {
            stopped: Gio.icon_new_for_string(GLib.build_filenamev([Me.path, 'media', 'controls', 'widgets-white.svg'])),
            running: Gio.icon_new_for_string(GLib.build_filenamev([Me.path, 'media', 'controls', 'widgets-active.svg'])),
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
            this._setControllerState(true);
        } catch (error) { this._startupFailed(error); }
    }

    _startupFailed(error) {
        logError(error, 'Falha ao iniciar widgets');
        this._stopWidgets();
        Main.notifyError('Widgets interrompidos', String(error.message || error).slice(0, 300));
    }

    _stopWidgets() {
        if (this._stopping) return this._stopping;
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
        WIDGETDATA = null;
        this._stopping = Promise.allSettled([...pendingStops]).then(() => {
            this._stopping = null;
            this._setControllerState(false);
        });
        return this._stopping;
    }

    disable() {
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

    _destroyWidgets() {
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

        this._removeClockTimer();
        this._startClockTimer();
        Me.settings.set_value('changed-data', new GLib.Variant('a{ss}', {}));
    }
}


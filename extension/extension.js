/* eslint-disable jsdoc/require-jsdoc */
const {
    Clutter, Gio, GLib, GObject,
    Graphene, Pango, St,
} = imports.gi;

const DND = imports.ui.dnd;
const ExtensionUtils = imports.misc.extensionUtils;
const Main = imports.ui.main;
const Me = ExtensionUtils.getCurrentExtension();
const PopupMenu = imports.ui.popupMenu;
const Utils = Me.imports.utils;

const Gettext = imports.gettext.domain(Me.metadata['gettext-domain']);
const _ = Gettext.gettext;

Gio._promisify(Gio.Subprocess.prototype, 'communicate_utf8_async');
Gio._promisify(Gio.Subprocess.prototype, 'wait_async');
Gio._promisify(Gio.InputStream.prototype, 'read_bytes_async');
Gio._promisify(Gio.OutputStream.prototype, 'write_all_async');

function stopCommandRun(run) {
    if (!run)
        return;
    run.cancelled = true;
    if (run.proc) {
        const pid = run.proc.get_identifier();
        if (pid && /^\d+$/.test(pid)) {
            try {
                GLib.spawn_sync(null, ['/usr/bin/kill', '-KILL', '--', `-${pid}`],
                    null, GLib.SpawnFlags.DEFAULT, null);
            } catch (error) {
                logError(error, 'Desktop Clock process group cleanup');
            }
        }
        run.proc.force_exit();
    }
    run.cancellable.cancel();
}

async function readCommandOutput(run, input = null) {
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
    const [stdout, stderr] = await Promise.all([
        read(run.proc.get_stdout_pipe()), read(run.proc.get_stderr_pipe()), write(),
        run.proc.wait_async(run.cancellable),
    ]);
    return [stdout, stderr];
}


const DEBUG_LOG = false;

const ANALOG_CLOCK = 'Analog_Clock';
const DIGITAL_CLOCK = 'Digital_Clock';
const TEXT_LABEL = 'Text_Label';
const COMMAND_LABEL = 'Command_Label';
const WIDGET_DATA_INDEX = 0;

let WIDGETDATA;

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
    }

    vfunc_allocate(box) {
        if (this._isDragging) {
            super.vfunc_allocate(box);
            return;
        }

        const x = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Location_X', 'int');
        const y = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Location_Y', 'int');

        const width = box.get_width();
        const height = box.get_height();
        const newX = x - width;
        const newY = y - height;

        const anchorPoint = getData(this._widgetIndex, WIDGET_DATA_INDEX, 'Box_AnchorPoint', 'int');
        if (anchorPoint === AnchorPoint.TOP_LEFT)
            box.set_origin(x, y);
        else if (anchorPoint === AnchorPoint.BOTTOM_LEFT)
            box.set_origin(x, newY);
        else if (anchorPoint === AnchorPoint.TOP_RIGHT)
            box.set_origin(newX, y);
        else if (anchorPoint === AnchorPoint.BOTTOM_RIGHT)
            box.set_origin(newX, newY);

        const childBox = new Clutter.ActorBox();
        childBox.x1 = 0;
        childBox.y1 = 0;

        for (const child of this.get_children()) {
            const [childWidth] = child.get_preferred_width(-1);
            const [childHeight] = child.get_preferred_height(-1);

            let adjustedWidth = width;
            let adjustedHeight = height;

            if (childWidth >= width)
                adjustedWidth = childWidth;
            if (childHeight >= height)
                adjustedHeight = childHeight;

            box.set_size(adjustedWidth, adjustedHeight);
        }

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

        this._updateClockId = GLib.timeout_add(priority, delay, () => {
            this.setStyle();
            this.setElementsStyle();
            this._refreshCommands();
            this.queue_relayout();
            this.setPositionFromSettings();
            this.queue_relayout();
            this.updateClocks(true);
            this._updateClockId = null;
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
        });
    }

    setStyle() {
        const index = this.elementIndex;

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
            this.text = elementDate.toLocaleFormat(dateFormat);
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
            this._pendingCommand = null;
            this._cancelCommand();
            if (this._speedtestTimeout) {
                GLib.source_remove(this._speedtestTimeout);
                this._speedtestTimeout = null;
            }
            if (this._speedtestProcess) {
                this._speedtestProcess.force_exit();
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

    _scheduleNetworkClick(delay = 250) {
        if (this._networkDestroyed || this._networkClickTimer)
            return;
        this._networkClickTimer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, delay, () => {
            this._networkClickTimer = null;
            if (this._networkDestroyed)
                return GLib.SOURCE_REMOVE;
            const [px, py, modifiers] = global.get_pointer();
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
            // Only detect the widget click; never collect or render modal data here.
            this._scheduleNetworkClick(inside && !this._networkDialog?.visible ? 25 : 250);
            return GLib.SOURCE_REMOVE;
        });
    }

    _closeNetworkDialog() {
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
        this._networkRefreshButton.accessible_name = this._firewallRows ? 'Atualizando eventos do firewall' : 'Atualizando conexões e portas';
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
            if (typeof payload.tooltip !== 'string' || !Array.isArray(payload.connection_items) ||
                payload.connection_items.some(item => !item || typeof item.ip !== 'string' || typeof item.port !== 'string' ||
                    typeof item.hostname !== 'string' || typeof item.display !== 'string'))
                throw new Error('Resposta inválida.');
            this._networkTooltipText = payload.tooltip || 'Nenhuma porta escutando';
            this._networkConnectionItems = payload.connection_items || [];
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
                this._networkRefreshButton.accessible_name = this._firewallRows ? 'Atualizar eventos do firewall' : 'Atualizar conexões e portas';
                if (pending && this._networkDialog?.visible)
                    this._refreshNetworkDialog();
            }
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
        this._firewallHeading = new St.Label({text: 'Firewall · eventos bloqueados', style: 'font-weight: bold; font-size: 18px;'});
        this._networkDialog.add_child(this._firewallHeading);
        const note = new St.Label({text: 'Pacote bloqueado não comprova invasão. Repetições são agrupadas por origem, destino e protocolo.', style: 'font-size: 12px; color: #c8c8c8;'});
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
        if (typeof data.text !== 'string' || typeof data.scope !== 'string' || typeof data.updated !== 'string' || !Array.isArray(data.groups) || data.groups.length > 50)
            throw new Error('Resposta do firewall inválida.');
        for (const row of data.groups) {
            if (!row || !['source', 'destination', 'protocol', 'ports', 'last', 'kind', 'interface'].every(key => typeof row[key] === 'string') || !Number.isInteger(row.count) || row.count < 1)
                throw new Error('Evento do firewall inválido.');
        }
        this._firewallHeading.text = data.text + ' · Firewall';
        this._firewallRows.destroy_all_children();
        const scope = new St.Label({text: data.scope, style: 'font-size: 11px; color: #c8c8c8;'});
        this._firewallRows.add_child(scope);
        if (!data.groups.length)
            this._firewallRows.add_child(new St.Label({text: 'Nenhum evento bloqueado encontrado na amostra.', style: 'color: #8bd5a1; padding: 8px;'}));
        for (const item of data.groups) {
            const box = new St.BoxLayout({vertical: true, style: 'padding: 8px; spacing: 4px; border-bottom: 1px solid #444;'});
            const color = item.kind === 'Descoberta / multicast' ? '#82cfff' : (item.count >= 10 ? '#ffd479' : '#ededed');
            box.add_child(new St.Label({text: `${item.source} → ${item.destination}   ·   ${item.count} eventos`, style: `font-family: monospace; color: ${color};`}));
            box.add_child(new St.Label({text: `${item.kind} · ${item.protocol} · portas: ${item.ports} · interface: ${item.interface || '—'}`, style: 'color: #c8c8c8; font-size: 12px;'}));
            box.add_child(new St.Label({text: `Último registro: ${item.last}`, style: 'color: #aaa; font-size: 11px;'}));
            this._firewallRows.add_child(box);
        }
    }

    _openNetworkDialog() {
        if (this._networkDestroyed)
            return;
        if (this._networkDialog && this._networkDialog.visible) {
            this._closeNetworkDialog();
            return;
        }
        const firewall = getData(this.widgetIndex, this.elementIndex, 'Text_Command').includes('/firewall-widget.py');
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
                const signature = JSON.stringify(this._networkConnectionItems);
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
        if (command.includes('/firewall-widget.py'))
            return;
        const interval = command.includes('/clima-widget.py')
            ? 300000
            : Math.max(getData(this.widgetIndex, this.elementIndex, 'Text_PollingInterval'), 250);
        this._pollingIntervalId = GLib.timeout_add(GLib.PRIORITY_HIGH, interval, () => {
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

    _executeCommand() {
        const command = getData(this.widgetIndex, this.elementIndex, 'Text_Command');
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
            if (command.includes('/firewall-widget.py') && response.startsWith('AZCLOCK_FIREWALL:')) {
                const payload = JSON.parse(response.slice('AZCLOCK_FIREWALL:'.length));
                displayText = payload.text;
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
        Me.settings = ExtensionUtils.getSettings();
        this._updateWidgetData();
        this._createWidgets();
        this._startClockTimer();
    }

    disable() {
        Me.settings.set_value('changed-data', new GLib.Variant('a{ss}', {}));

        Me.settings.disconnectObject(this);
        Main.layoutManager.disconnectObject(this);

        if (this._dataChangedTimeoutId) {
            GLib.source_remove(this._dataChangedTimeoutId);
            this._dataChangedTimeoutId = null;
        }

        this._removeClockTimer();
        this._destroyWidgets();

        WIDGETDATA = null;

        Me.settings = null;
    }

    _startClockTimer() {
        this._updateClockId = GLib.timeout_add(GLib.PRIORITY_HIGH, 1000, () => {
            for (const widget of this.widgets)
                widget.updateClocks();

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
        for (const widget of this.widgets)
            widget.destroy();

        this.widgets = null;
    }

    _createWidget(index, updateDelay = 300) {
        const widget = new DesktopWidget(index);
        Main.layoutManager._backgroundGroup.add_child(widget);
        widget.updateComponents(updateDelay);
        return widget;
    }

    _createWidgets() {
        this.widgets = [];

        for (let i = 0; i < WIDGETDATA.length; i++) {
            const widget = this._createWidget(i);
            this.widgets.push(widget);
        }

        Me.settings.connectObject('changed::widget-data', () => {
            if (this._dataChangedTimeoutId)
                GLib.source_remove(this._dataChangedTimeoutId);

            this._dataChangedTimeoutId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 300, () => {
                this._updateWidgetData();
                this._widgetDataChangedEvent();
                this._dataChangedTimeoutId = null;
                return GLib.SOURCE_REMOVE;
            });
        }, this);

        Main.layoutManager.connectObject('monitors-changed', () => {
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
        const widgetIndex = parseInt(changedData['WidgetIndex']);
        const elementIndex_ = parseInt(changedData['ElementIndex']);
        const elementType = changedData['ElementType'];
        const widgetDeleted = changedData['WidgetDeleted'];
        const widgetAdded = changedData['WidgetAdded'];
        const elementDeleted = changedData['ElementDeleted'];
        const elementAdded = changedData['ElementAdded'];
        const widgetMoved = changedData['WidgetMoved'];
        const widgetIndexChanged = changedData['WidgetIndexChanged'];
        const widgetIndexNew = parseInt(changedData['WidgetIndexNew']);
        const elementIndexChanged = changedData['ElementIndexChanged'];

        if (widgetIndex === undefined) {
            debugLog('update all this.widgets');

            for (const widget of this.widgets)
                widget.updateComponents();
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
        } else if (elementDeleted || elementAdded || elementIndexChanged) {
            debugLog(`element added/deleted/index-changed at widget ${widgetIndex}`);

            this.widgets[widgetIndex].createElements();
            this.widgets[widgetIndex].updateComponents(0);
        } else {
            debugLog(`widget ${widgetIndex} element setting changed`);

            this.widgets[widgetIndex].updateComponents();
        }

        Me.settings.set_value('changed-data', new GLib.Variant('a{ss}', {}));
    }
}


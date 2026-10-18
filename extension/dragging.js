/* Convert a stage-space drop into saved anchor coordinates, bounded to a monitor. */
var dropPosition = function(x, y, width, height, monitor, anchor) {
    if (![x,y,width,height,monitor.x,monitor.y,monitor.width,monitor.height].every(Number.isFinite) || width < 0 || height < 0)
        throw new Error('Posição de arraste inválida.');
    x = Math.max(monitor.x, Math.min(x, monitor.x + Math.max(0, monitor.width - width)));
    y = Math.max(monitor.y, Math.min(y, monitor.y + Math.max(0, monitor.height - height)));
    return {
        x: Math.round(x + (anchor === 2 || anchor === 3 ? width : 0)),
        y: Math.round(y + (anchor === 1 || anchor === 3 ? height : 0)),
    };
};

/* Pointer state machine: independent of desktop-window event delivery. */
var PointerDragController = class {
    constructor(options) { this.options = options; this.state = null; this.held = false; }
    update(pointer) {
        const [x,y,mask] = pointer, o = this.options;
        const down = !!(mask & o.buttonMask);
        const modifiers = !!(mask & (o.superMask | o.mod4Mask)) && !!(mask & o.controlMask);
        if (!this.state && down && !this.held && modifiers && o.canStart(pointer)) {
            const widget = o.widgets().find(widget => {
                const [wx,wy] = widget.get_transformed_position(), [w,h] = widget.get_transformed_size();
                return x >= wx && x < wx+w && y >= wy && y < wy+h;
            });
            if (widget) {
                const [wx,wy] = widget.get_transformed_position();
                if (o.begin(widget) !== false) this.state = {widget,x,y,wx,wy};
            }
        }
        if (this.state) {
            const s = this.state;
            o.move(s.widget,s.wx+x-s.x,s.wy+y-s.y);
            if (!down) {
                this.state = null;
                o.finish(s.widget,{x:s.wx+x-s.x,y:s.wy+y-s.y,pointer:[x,y]});
            }
        }
        this.held = down;
        return !!this.state || modifiers;
    }
    cancel() {
        if (!this.state) return;
        const {widget} = this.state;
        this.state = null;
        this.options.finish(widget,null);
    }
};

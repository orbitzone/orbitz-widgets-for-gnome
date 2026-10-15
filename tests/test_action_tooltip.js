const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(require('path').join(__dirname, '../extension/extension.js'), 'utf8');
class Label {
    constructor(props = {}) { Object.assign(this, props); this.signals = {}; this.clutter_text = {set_line_wrap() {}, set_line_wrap_mode() {}, set_ellipsize() {}}; }
    connect(signal, callback) {
        if (signal === 'clicked' && !(this instanceof Button)) throw new Error('No clicked signal on Label');
        this.signals[signal] = callback;
        return signal;
    }
    disconnect() {}
    hide() { this.visible = false; }
    destroy() { this.destroyed = true; }
}
class Button extends Label {}
const tooltips = [];
const context = {St: {Label, Button}, Pango: {WrapMode: {WORD_CHAR: 0}, EllipsizeMode: {NONE: 0}}, Main: {uiGroup: {add_child(actor) {tooltips.push(actor);}}}};
vm.createContext(context);
const start = source.indexOf('    _attachActionTooltip(button, command) {');
const end = source.indexOf('    _buildTemperaturesDialog()', start);
vm.runInContext('this.attach = function' + source.slice(start + '    _attachActionTooltip'.length, end).trim(), context);
for (const actor of [new Label(), new Button()]) {
    const host = {_networkDialog: new Label({visible: true})};
    context.attach.call(host, actor, 'Details');
    assert.equal(!!actor.signals.clicked, actor instanceof Button);
    assert(actor.signals['notify::hover']);
    actor.signals['key-focus-out']();
    assert.equal(tooltips.at(-1).visible, false);
    actor.signals.destroy();
    assert(tooltips.at(-1).destroyed);
}
console.log('OK: tooltips accept labels and buttons with their supported signals.');

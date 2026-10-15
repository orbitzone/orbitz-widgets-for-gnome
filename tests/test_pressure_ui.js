const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(require('path').join(__dirname, '../extension/extension.js'), 'utf8');
class Actor {
    constructor(props) { Object.assign(this, props); this.children = []; this.clutter_text = {set_line_wrap() {}, set_ellipsize() {}}; }
    add_child(child) { this.children.push(child); }
}
const context = {St: {BoxLayout: Actor, Label: Actor}, Pango: {EllipsizeMode: {NONE: 0}}};
vm.createContext(context);
vm.runInContext('this.render = function' + source.slice(source.indexOf('    _renderPressure(data) {') + '    _renderPressure'.length, source.indexOf('    _buildStorageDialog()')), context);
const host = {_updatesRows: new Actor({})};
const data = {text: 'Sem pressão relevante', items: ['cpu','memory','io'].map(resource => ({resource, name: resource, suggestion: 'Revisar', averages: [0,1,2], full: null, level: 'normal'}))};
context.render.call(host, data);
assert.equal(host._updatesRows.children[0].children.length, 3);
data.items[1].averages = null; data.items[1].level = 'unavailable';
context.render.call(host, data);
assert.equal(host._updatesRows.children[1].children[1].children[1].text, 'Leitura indisponível');
data.items[1].level = 'normal';
assert.throws(() => context.render.call(host, data), /inválida/);
data.items[1].level = 'unavailable';
data.items[0].averages = [NaN, 0, 0];
assert.throws(() => context.render.call(host, data), /inválida/);
console.log('OK: three PSI columns, missing readings and invalid payload rejection.');

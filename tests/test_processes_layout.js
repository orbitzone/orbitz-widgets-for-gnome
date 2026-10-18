const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
class Actor {
    constructor(props = {}) { Object.assign(this, props); this.children = []; this.clutter_text = {set_ellipsize() {}, set_line_wrap() {}}; }
    add_child(child) { this.children.push(child); }
    set_child(child) { this.children = [child]; }
    destroy_all_children() { this.children = []; }
    connect() {}
}
const context = {Clutter: {ActorAlign: {CENTER: 0}}, St: {BoxLayout: Actor, Label: Actor, Button: Actor, Icon: Actor}, Pango: {EllipsizeMode: {END: 1}}};
vm.createContext(context);
context.render = require('./helpers/command_panels').load(context)._renderProcesses;
const tooltips = [];
const host = {_updatesRows: new Actor(), _updatesActions: new Actor(), _renderPressure() {}, _attachActionTooltip(actor, text) {tooltips.push(text);}};
const rows = Array.from({length:7}, (_,i) => ({pid:i+1, name:'Process '+i, cpu:i*10, memory:i*100}));
const data = {summary:'Resumo detalhado', notices:['Observação detalhada'], cpu_rows:rows, memory_rows:rows, actions:[{id:'monitor',name:'Ver processos',command:'top',effect:'Revisar processos'}]};
context.render.call(host, data);
assert.equal(host._updatesRows.children.length, 2); // overview and side-by-side rankings
const cards = host._updatesRows.children[1].children;
assert.equal(cards.length, 2);
assert.equal(cards[0].children.length, 4); // heading + top three
assert.equal(cards[1].children.length, 4);
assert(tooltips.includes(data.summary)); assert(tooltips.includes(data.notices[0]));
assert(tooltips.some(text => text.includes('PID 1')));
context.render.call(host, {...data, cpu_rows:[], memory_rows:[], actions:[]});
assert.equal(host._updatesRows.children[1].children[0].children[1].text, 'Nenhum processo nesta amostra');
assert.throws(() => context.render.call(host, {...data, cpu_rows:[{pid:-1}]}), /inválida/);
console.log('OK: compact process cards, top-three limit, details in tooltips, empty and invalid data.');

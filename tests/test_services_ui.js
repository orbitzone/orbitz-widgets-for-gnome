const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
class Actor {
    constructor(props = {}) { Object.assign(this, props); this.children = []; this.clutter_text = {set_ellipsize() {}, set_line_wrap() {}}; }
    add_child(child) { this.children.push(child); }
    set_child(child) { this.children = [child]; }
    destroy_all_children() { this.children = []; }
}
const context = {St:{BoxLayout:Actor, Label:Actor, Button:Actor}, Pango:{EllipsizeMode:{END:0}}};
vm.createContext(context);
context.render = require('./helpers/command_panels').load(context)._renderServices;
const tips=[];
const host={_updatesRows:new Actor(),_attachActionTooltip(actor,text){tips.push(context.Language.text(text));}};
const item={name:'test.service',description:'Test service',result:'exit-code',status:'1',changed:'Today'};
const data={text:'Serviços: 1 com falha',groups:[{scope:'system',items:[item],count:1,error:''},{scope:'user',items:[],count:0,error:'Sem acesso'}]};
context.render.call(host,data);
const cards=host._updatesRows.children[0].children;
assert.equal(cards.length,2); assert.equal(cards[1].children[1].text,'Sem acesso');
assert(tips[0].includes('exit-code')); assert(tips[0].includes('Today'));
assert.throws(()=>context.render.call(host,{...data,groups:[]}),/inválida/);
assert.throws(() => context.render.call(host, {...data, groups: [{...data.groups[0], count: 0}, data.groups[1]]}), /inválida/);
assert.throws(() => context.render.call(host, {...data, groups: [{...data.groups[0], count: Number.MAX_SAFE_INTEGER + 1}, data.groups[1]]}), /inválida/);
console.log('OK: separate system/session cards, unavailable scope and result tooltips.');

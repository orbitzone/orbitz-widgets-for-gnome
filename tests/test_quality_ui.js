const assert=require('assert'),fs=require('fs'),vm=require('vm');
class Actor {constructor(props={}){Object.assign(this,props);this.children=[];} add_child(actor){this.children.push(actor);} set_child(actor){this.children=[actor];} destroy_all_children(){this.children=[];}}
const context={St:{BoxLayout:Actor,Button:Actor,Label:Actor}};vm.createContext(context);
context.render = require('./helpers/command_panels').load(context)._renderQuality;
const tips=[];const host={_updatesRows:new Actor(),_attachActionTooltip(actor,text){tips.push(text);}};
const data={items:[{name:'Roteador',target:'192.168.1.1',loss:0,latency:2,jitter:1,error:''},{name:'Internet',target:'1.1.1.1',loss:100,latency:null,jitter:null,error:''}]};
context.render.call(host,data);
const cards=host._updatesRows.children[0].children;assert.equal(cards.length,2);
assert.equal(cards[1].children[0].children[1].text,'Sem resposta ICMP');
assert(tips[1].includes('1.1.1.1'));
assert.throws(()=>context.render.call(host,{items:[{...data.items[0],loss:101},data.items[1]]}),/inválida/);
console.log('OK: quality cards, ICMP nonresponse, destinations and validation.');

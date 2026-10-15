const assert=require('assert'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync(require('path').join(__dirname,'../extension/extension.js'),'utf8');
class Actor {constructor(props={}){Object.assign(this,props);this.children=[];this.clutter_text={set_ellipsize(){}};} add_child(actor){this.children.push(actor);} set_child(actor){this.children=[actor];} destroy_all_children(){this.children=[];}}
const context={St:{BoxLayout:Actor,Button:Actor,Label:Actor},Pango:{EllipsizeMode:{END:0}}};vm.createContext(context);
vm.runInContext('this.render = function'+source.slice(source.indexOf('    _renderStorage(data) {')+'    _renderStorage'.length,source.indexOf('    _buildTrafficDialog()')),context);
const tips=[];const host={_updatesHeading:{},_updatesRows:new Actor(),_attachActionTooltip(actor,text){tips.push(text);}};
const data={text:'Armazenamento',error:'',omitted:0,disks:[],items:[{files:[],content_error:'',more:false,mount:'/',device:'/dev/a1',disk:'/dev/a',total:1000000000,available:50000000,percent:95,inodes:10}]};
context.render.call(host,data);
const card=host._updatesRows.children[0].children[0];
assert.equal(card.children[0].children[4].text,'SMART: indisponível');
assert(card.children[0].children[1].style.includes('#ff6b6b'));
assert(tips[0].includes('Inodes usados: 10%'));
assert.equal(card.children[0].children[2].text,'Capacidade: 0.9 GiB');
host._storageExternal=true;data.items[0].files=['▸ Documentos','· foto.jpg'];
context.render.call(host,data);
assert.equal(host._updatesHeading.text,'EXT · volumes e conteúdo');
assert(tips[1].includes('foto.jpg'));
assert.throws(()=>context.render.call(host,{...data,items:[{...data.items[0],percent:101}]}),/inválida/);
console.log('OK: storage cards, capacity alerts, missing SMART and invalid values.');

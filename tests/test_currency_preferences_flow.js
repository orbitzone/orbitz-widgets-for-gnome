const assert=require('assert'),fs=require('fs'),vm=require('vm'),path=require('path');
const created=[];
class Widget {
 constructor(...args){this.handlers={};this.nodes=[];created.push(this);this._init(...args);}
 _init(props={}){for(const [key,value] of Object.entries(props))this[key.replaceAll('-','_')]=value;}
 connect(signal,fn){this.handlers[signal]=fn;return 1;}
 emit(signal,...args){this.handlers[signal]?.(this,...args);}
 add(item){this.nodes.push(item);} append(item){this.add(item);} add_row(item){this.add(item);}
 add_prefix(item){this.add(item);} add_suffix(item){this.add(item);} set_child(item){this.add(item);} set_content(item){this.add(item);}
 add_child(item){this.add(item);} add_controller(){} pack_start(item){this.add(item);} pack_end(item){this.add(item);}
 get_first_child(){return this.nodes[0]||null;} get_next_sibling(){return null;}
 remove(item){this.nodes=this.nodes.filter(n=>n!==item);} get_row_at_index(i){return this.nodes[i];}
 select_row(row){this.emit('row-selected',row);} get_index(){return 0;}
 get_selected_row(){return this.nodes[0];} set_visible_child(item){this.visible_child=item;}
 get_root(){return this;} present(){this.presented=true;} set_value(value){this.value=value;}
 get_value(){return this.value;} get_text(){return this.text||'';} get_active(){return this.active;}
 set_header_func(){} set_size_request(){} set_policy(){} set_rgba(){}
 set selected(value){this._selected=value;this.handlers['notify::selected']?.(this);}
 get selected(){return this._selected||0;}
 set active(value){this._active=value;this.handlers['notify::active']?.(this);}
 get active(){return this._active||false;}
}
class StringList {constructor(){this.items=[];}append(item){this.items.push(item);}static new(items){const list=new StringList();list.items=items;return list;}}
const Gtk={};for(const key of ['Box','Label','Button','Entry','Switch','DropDown','SpinButton','Adjustment','ColorButton','FontButton','Image','DragSource','DropTargetAsync','Stack','ScrolledWindow','Separator','ListBox','ListBoxRow','ActionBar','CheckButton','MessageDialog'])Gtk[key]=Widget;
Object.assign(Gtk,{INVALID_LIST_POSITION:4294967295,StringList,Align:{CENTER:0,FILL:1,START:2,END:3},Orientation:{VERTICAL:1},ResponseType:{APPLY:1},FontChooserLevel:{FAMILY:1},StackTransitionType:{CROSSFADE:1}});
const Adw={};for(const key of ['PreferencesPage','PreferencesGroup','ActionRow','ExpanderRow','HeaderBar','Leaflet','ApplicationWindow','ComboRow'])Adw[key]=Widget;
// Intentionally no Adw.SwitchRow: actual GNOME42/libadwaita1.1 does not provide it.
const settingsModules={DialogWindow:{DialogWindow:Widget},timeZoneCatalog:{TimeZoneCatalog:{}},TimeZoneDialog:{},AboutPage:{AboutPage:Widget}};
const Me={metadata:{},imports:{settings:settingsModules,utils:{},worldClock:{WorldClock:{}}}};
const catalogRequests=[];let deferredCatalogs=false;const pendingCatalogs=[];
const gi={Gtk,Adw,Gdk:{DragAction:{MOVE:1},RGBA:class{parse(){} }},
 GObject:{registerClass:(...args)=>args.at(-1),ParamSpec:{int(){},string(){}},ParamFlags:{READWRITE:1}},
 GLib:{MAXINT32:2147483647,Variant:class{constructor(type,value){this.value=value;}},
  get_user_data_dir:()=>'/user-data',build_filenamev:p=>p.join('/'),shell_quote:x=>`'${x}'`,
  shell_parse_argv:x=>[true,x.match(/'[^']*'|\S+/g).map(t=>t.replace(/^'|'$/g,''))],markup_escape_text:x=>x},
 Gio:{icon_new_for_string:x=>x,SubprocessFlags:{STDOUT_PIPE:1,STDERR_SILENCE:2},Subprocess:{new(argv){
   const crypto=argv.includes('crypto');catalogRequests.push(argv);
   const output=crypto?{source:'Powered by CoinPaprika',assets:[{id:'btc-bitcoin',symbol:'BTC',name:'Bitcoin'},{id:'eth-ethereum',symbol:'ETH',name:'Ethereum'}]}:{USD:'US Dollar',EUR:'Euro'};
   const proc={communicate_utf8_async:(a,b,cb)=>{if(deferredCatalogs)pendingCatalogs.push(()=>cb(proc,{}));else cb(proc,{});},communicate_utf8_finish:()=>[true,JSON.stringify(output)],get_successful:()=>true};return proc;
 }}}};
const imports={gi,misc:{extensionUtils:{getCurrentExtension:()=>Me}},gettext:{domain:()=>({gettext:x=>x})}};
function load(file,name){const context=vm.createContext({imports,console});vm.runInContext("String.prototype.format=function(...args){let i=0;return this.replace(/%s/g,()=>args[i++]);};",context);vm.runInContext(fs.readFileSync(path.join(__dirname,'../extension',file),'utf8'),context);return context[name];}
const UtilsContext=vm.createContext({imports});vm.runInContext(fs.readFileSync(path.join(__dirname,'../extension/utils.js'),'utf8'),UtilsContext);
let data=[JSON.parse(JSON.stringify(UtilsContext.CurrencyWidgetSettings))];
data[0][1].Text_Command="/usr/bin/python3 '/user-data/orbitz-widgets/collectors/currency-widget.py' --quote USD";
let changed={};
const settings={get_value:key=>({deep_unpack:()=>JSON.parse(JSON.stringify(key==='changed-data'?changed:data))}),set_value(key,value){if(key==='widget-data')data=JSON.parse(JSON.stringify(value.value));else if(key==='changed-data')changed=value.value;}};
Me.imports.utils={getData:(all,w,e,key,parse)=>parse==='int'?Number(all[w][e][key]):parse==='bool'?all[w][e][key]==='true':all[w][e][key],unpackData:()=>settings.get_value('widget-data').deep_unpack(),setData:(all,w,e,key,value)=>{all[w][e][key]=String(value);settings.set_value('widget-data',new gi.GLib.Variant('aaa{ss}',all));}};
settingsModules.WidgetsData={WidgetsData:{data}};
for(const name of ['SubPage','WidgetSubPage','TextLabelSubPage','CommandLabelSubPage'])settingsModules[name]={[name]:load('settings/'+name+'.js',name)};
for(const name of ['DigitalClockSubPage','AnalogClockSubPage'])settingsModules[name]={[name]:Widget};
settingsModules.WidgetSettingsPage={WidgetSettingsPage:load('settings/WidgetSettingsPage.js','WidgetSettingsPage')};
const Row=load('prefs.js','WidgetRow');const row=new Row({settings,createRows(){}},{widget_index:0});
const configure=row.nodes.find(n=>n.label==='Configure');assert(configure,'real prefs Configure button');
configure.emit('clicked');
const window=created.find(n=>n instanceof settingsModules.WidgetSettingsPage.WidgetSettingsPage);
assert(window.presented,'Configure presents settings window');
assert.equal(window._sidebarListBox.nodes.length,2,'metadata and command pages populated during construction');
const page=window._sidebarListBox.nodes[1].settingPage;
assert(page instanceof settingsModules.CommandLabelSubPage.CommandLabelSubPage);
assert.equal(data[0][1].Text_PollingInterval,'14400000');
const descend=node=>[node,...(node.nodes||[]).flatMap(descend)];
const group=descend(page).find(g=>g.title==='Currency converter');assert(group,'full SubPage/TextLabel/CommandLabel constructors succeeded');
const [categoryRow,pickerRow,directionRow]=group.nodes;
const category=categoryRow.nodes[0],picker=pickerRow.nodes[0],direction=directionRow.nodes[0];
assert(data[0][1].Text_Command.endsWith('--quote USD'));
direction.active=true;assert(data[0][1].Text_Command.endsWith('--quote USD --reverse'));
category.selected=1;assert(data[0][1].Text_Command.includes('--mode crypto --asset btc-bitcoin --reverse'));
assert.equal(categoryRow.subtitle,'Powered by CoinPaprika');
picker.selected=1;assert(data[0][1].Text_Command.includes('--asset eth-ethereum'));
direction.active=false;assert(!data[0][1].Text_Command.includes('--reverse'));assert.equal(pickerRow.title,'USD → ETH');
category.selected=0;assert(data[0][1].Text_Command.endsWith('--quote USD'));
assert.equal(data.length,1,'no separate Bitcoin widget');assert(catalogRequests.some(argv=>argv.includes('crypto')));
console.log('OK: Configure → real settings window → widget/command subpages on Adw1.1; fiat/crypto asset/direction and4h persistence.');

module.exports={settings,settingsModules,created,gi,load,row,getData:()=>data,getChanged:()=>changed,deferCatalogs:()=>{deferredCatalogs=true;},flushCatalogs:()=>{while(pendingCatalogs.length)pendingCatalogs.shift()();deferredCatalogs=false;}};

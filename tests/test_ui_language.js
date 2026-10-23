const assert=require('assert'),fs=require('fs'),vm=require('vm'),path=require('path');
let language='pt-BR',changed;const env=[];
const settings={get_string:()=>language,connect:(name,fn)=>{assert.equal(name,'changed::ui-language');changed=fn;return 1;},disconnect(){}};
const root=path.resolve(__dirname,'..');
const GLib={getenv:()=>null,get_user_data_dir:()=>'/synthetic',build_filenamev:p=>path.join(...p),FileTest:{IS_REGULAR:1},
 file_test:p=>fs.existsSync(p),file_get_contents:p=>[true,fs.readFileSync(p)],idle_add:(p,fn)=>{fn();return 1;},PRIORITY_DEFAULT_IDLE:0,SOURCE_REMOVE:0};
const Gio={SubprocessLauncher:class{setenv(...args){env.push(args);}spawnv(argv){return argv;}}};
const imports={gi:{GLib,Gio},misc:{extensionUtils:{getCurrentExtension:()=>({path:path.join(root,'extension')})}}};
const context=vm.createContext({imports,TextDecoder,WeakRef,logError:error=>{throw error;}});
vm.runInContext(fs.readFileSync(path.join(root,'extension/uiLanguage.js'),'utf8'),context);
const L=context.Language;L.configure(settings);
class Widget{constructor(props){Object.assign(this,props);}set_text(value){this.label=value;}}
const label=L.widget(Widget,{label:L.msg('settings.add_widget')});
const user=L.widget(Widget,{label:'Adicionar widget…'});
assert.equal(label.label,'Adicionar widget…');language='en-US';changed();assert.equal(label.label,'Add widget…');
assert.equal(user.label,'Adicionar widget…','literal/user data is never translated');
L.call(label,'set_text',L.msg('sticky.save_error',{error:'USER CONTENT'}));assert.equal(label.label,'Could not save: USER CONTENT');
language='pt-BR';changed();assert.equal(label.label,'Não foi salvo: USER CONTENT');
L.set(label,'label','raw user text');language='en-US';changed();assert.equal(label.label,'raw user text');
L.set(user,'label','EN-US user title');language='en-US';changed();assert.equal(user.label,'EN-US user title');
assert.equal(L.normalize('invalid'),'pt-BR');assert.equal(L.tr('unknown.id'),'unknown.id');
const args=['python3','/synthetic/collector.py'];assert.strictEqual(L.spawn(args,0),args);
assert(env.some(item=>item[0]==='ORBITZ_LOCALE'&&item[1]==='en-US'));
assert(env.some(item=>item[0]==='ORBITZ_I18N_DIR'&&path.resolve(item[1])===path.join(root,'i18n')));
console.log('OK: live GJS catalog bindings, explicit messages only, parameters/defaults and subprocess locale.');
// Settings models keep their stored IDs and selected index through a live refresh.
class Combo {
 constructor(props={}){this.events={};Object.assign(this,props);}
 connect(name,fn){this.events[name]=fn;}
 get selected(){return this._selected??0;}
 set selected(value){this._selected=value;this.events['notify::selected']?.(this);}
 set model(value){this._model=value;this.selected=0;}
 get model(){return this._model;}
 add_suffix(){}
}
class StringList {static new(values){return {values};}}
const writes=[],rows=[];
const parentData=[[{Widget_Id:'parent',Box_IsGroup:'true',Name:'USER Pai'}],[{Widget_Id:'child',Parent_Id:'parent',Name:'USER Child'}]];
const moduleContext=vm.createContext({imports:{gi:{Adw:{ComboRow:Combo,ActionRow:Combo},Gtk:{StringList,Switch:Combo,Align:{CENTER:1}},GLib:{},GObject:{registerClass:(_props,Class)=>Class}},misc:{extensionUtils:{getCurrentExtension:()=>({metadata:{},imports:{uiLanguage:{Language:L},settings:{SubPage:{SubPage:class{}}}}})}},gettext:{domain:()=>({})}}});
vm.runInContext(fs.readFileSync(path.join(root,'extension/settings/WidgetSubPage.js'),'utf8'),moduleContext);
const page=Object.assign(Object.create(moduleContext.WidgetSubPage.prototype),{widget_index:1,_settings:{get_value:()=>({deep_unpack:()=>parentData})},getClockElementData:()=>3,setClockElementData:(...args)=>writes.push(args),createSpinRow:()=>({})});
page._addGroupingControls({add:row=>rows.push(row)});const parent=rows[0];
const anchor=page.createComboRow(L.msg('settings.anchor_point'),'Box_AnchorPoint');
assert.equal(parent.selected,1);assert.equal(anchor.selected,3);
language='en-US';changed();assert.equal(parent.model.values[0],'Desktop · no parent');assert.equal(parent.model.values[1],'USER Pai');
assert.equal(parent.title,'Parent widget · move to');assert.equal(anchor.selected,3);assert.equal(parent.selected,1);assert.equal(writes.length,0);
language='pt-BR';changed();assert.equal(parent.model.values[0],'Desktop · sem pai');assert.equal(writes.length,0);
anchor.selected=2;assert.equal(writes.length,1);assert.equal(writes[0][0],'Box_AnchorPoint');assert.equal(writes[0][1],2);
console.log('OK: live parent/anchor models preserve selection, user names and stored IDs without writes.');

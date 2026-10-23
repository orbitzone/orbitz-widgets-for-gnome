// Actual catalog/runtime and exported panel factories: update existing actors in place.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');let locale='pt-BR',changed;
const settings={get_string:()=>locale,connect:(_name,fn)=>{changed=fn;return 1;}};
const monitor={x:0,y:0,width:1280,height:900};const all=[];
class Actor {
 constructor(props={}){Object.assign(this,props);this.children=[];this.clutter_text={set_line_wrap(){},set_line_wrap_mode(){},set_ellipsize(){},set_max_length(){},connect(){},set_markup:value=>this.text=value};all.push(this);}
 insert_child_at_index(child,index){this.children.splice(index,0,child);}add_child(child){this.children.push(child);}add_actor(child){this.add_child(child);}set_child(child){this.children=[child];}
 connect(){return 1;}disconnect(){}add_constraint(){}set_policy(){}set_position(){}show(){this.visible=true;}hide(){this.visible=false;}
 destroy_all_children(){this.children=[];}get_preferred_width(){return [0,900];}get_preferred_height(){return [0,400];}get_preferred_size(){return [0,0,200,100];}
 get_transformed_position(){return [0,0];}get_text(){return this.text;}
}
const St={Widget:Actor,BoxLayout:Actor,Label:Actor,Button:Actor,ScrollView:Actor,Entry:Actor,Icon:Actor,PolicyType:{NEVER:0,AUTOMATIC:1}};
const GLib={getenv:()=>null,get_user_data_dir:()=>'/synthetic',build_filenamev:p=>path.join(...p),FileTest:{IS_REGULAR:1},file_test:fs.existsSync,file_get_contents:p=>[true,fs.readFileSync(p)],idle_add:(_p,fn)=>fn(),PRIORITY_DEFAULT_IDLE:0,SOURCE_REMOVE:0};
const Main={uiGroup:new Actor(),layoutManager:{findMonitorForActor:()=>monitor,primaryMonitor:monitor}};
const context=vm.createContext({imports:{gi:{GLib,Gio:{}},misc:{extensionUtils:{getCurrentExtension:()=>({path:path.join(root,'extension')})}}},TextDecoder,WeakRef,logError:e=>{throw e;},St,GLib,Main,Pango:{EllipsizeMode:{END:1,NONE:0},WrapMode:{WORD_CHAR:1}},Clutter:{BindConstraint:class{},BindCoordinate:{ALL:1},ActorAlign:{CENTER:1}},global:{stage:{}},getData:()=>'/synthetic/currency-widget.py --quote USD'});
vm.runInContext(fs.readFileSync(path.join(root,'extension/uiLanguage.js'),'utf8'),context);
const L=context.Language;L.configure(settings);
const methods=require('./helpers/command_panels').load(context);
vm.runInContext(fs.readFileSync(path.join(root,'extension/panels/currency.js'),'utf8'),context);Object.assign(methods,context.create(context));
const host=()=>({...methods,_refreshNetworkDialog(){}});
const docker=host();docker._buildDockerDialog();docker._networkDialog.visible=true;
docker._renderDocker({text:'USER summary',items:[{name:'USER Serviço',ports:'80/tcp',url:''}],omitted:2});
const temperatures=host();temperatures._buildTemperaturesDialog();temperatures._networkDialog.visible=true;
temperatures._renderTemperatures({items:[{name:'USER sensor',group:'nvme',value:40}],omitted:3});
const network=host();network._buildTrafficDialog();network._networkDialog.visible=true;
network._renderQuality({items:[{name:'USER gateway',target:'1.1.1.1',error:'',loss:0,latency:2,jitter:null},{name:'USER WAN',target:'2.2.2.2',error:'external erro',loss:null,latency:null,jitter:null}]});
const storage=host();storage._buildStorageDialog();storage._networkDialog.visible=true;
storage._renderStorage({text:'external',error:'',omitted:0,items:[],disks:[],unmounted:[{device:'/dev/USER',disk:'USER',fstype:'ext4',total:100,available:null,used:null}]});
const updates=host();updates._buildUpdatesDialog();updates._renderUpdates({text:'external updates',reboot:true,index_updated:'USER date',error:'',items:[],omitted:2,notices:['USER notice'],actions:[]});
const services=host();services._buildServicesDialog();services._renderServices({text:'external services',groups:[{scope:'system',count:1,error:'',items:[{name:'USER.service',description:'USER description',result:'exit-code',status:'1',changed:'USER time'}]},{scope:'user',count:0,error:'',items:[]}]});
const processes=host();processes._buildProcessesDialog();processes._renderProcesses({summary:'USER summary',notices:['USER notice'],pressure:{text:'external',items:['cpu','memory','io'].map(resource=>({resource,name:'USER '+resource,suggestion:'USER suggestion',level:'unavailable',averages:null,full:null}))},cpu_rows:[],memory_rows:[],actions:[]});
const firewall=host();firewall._buildFirewallDialog();firewall._renderFirewall({text:'USER firewall',scope:'USER scope',updated:'USER time',groups:[]});
const currency=host();currency._buildCurrencyDialog();const entry=currency._currencyAmountEntry;entry.text='1.234,56';currency._currencyQuote={base:'BRL',quote:'USD',rate:'0.2'};currency._updateCurrencyCalculation();
const weather=host();weather._buildWeatherDialog();weather._networkDialog.visible=true;
const wx={unit:'celsius',location:{name:'USER Brasília'},current:{temperature:25.5,apparent_temperature:26.5,humidity:60},days:Array.from({length:7},(_,i)=>({date:`2026-10-${22+i}`,temp_min:17.5,temp_max:29.5,precipitation_probability:30,wind_speed_max:42.5,weather_code:0})),fetched_at:'2026-10-22T15:00:00Z'};
weather._weatherData=wx;weather._renderWeather(wx);weather._weatherSearch.text='USER typed search';
const wxEntry=weather._weatherSearch,wxColumns=[...weather._weatherRows.children];
assert(weather._weatherRows.children[0].children[1].accessible_name.includes('42,5 km/h'));assert(weather._weatherCurrentLabel.text.includes('25,5°C'));assert(weather._weatherRows.children[0].children[0].text.includes('22/10'));
const stopWeatherLanguage=L.watch(()=>weather._weatherRefreshLocale());
const texts=()=>all.map(actor=>actor.text??actor.label).filter(v=>typeof v==='string');
assert(texts().includes('2 pacotes adicionais.'));assert(texts().includes('Armazenamento'));assert.equal(currency._currencyTotalLabel.text,'Total: 246,91 USD');
const localError=L.error(L.msg('panels.error.storage'));
L.set(storage._networkRefreshStatus, 'text', localError.orbitzMessage);
const actorsBefore=all.length;
locale='en-US';changed();
assert.equal(storage._networkRefreshStatus.text,'Invalid storage response.');
assert.equal(all.length,actorsBefore,'locale notification does not recreate panel actors');
for(const expected of ['2 additional packages.','Storage','No failed services','No processes in this sample','Not mounted','No patterns met the highlight criteria in the collected window.','Loss: 0% · 5 packets'])assert(texts().includes(expected),expected);
assert.equal(temperatures._temperatureHeading.text,'Temperatures · 1 sensors · 3 additional');
assert.equal(docker._dockerHeading.text,'Docker · USER summary');
assert(weather._weatherCurrentLabel.text.includes('25.5°C'));assert(weather._weatherCurrentLabel.text.includes('Humidity 60%'));
assert(weather._weatherRows.children[0].children[0].text.includes('10/22'));assert.equal(weather._weatherRows.children[0].children[2].text,'Clear sky · Wind: 42.5 km/h');assert(weather._weatherRows.children[0].children[1].accessible_name.includes('Wind: 42.5 km/h'));
assert.strictEqual(weather._weatherSearch,wxEntry);assert.equal(wxEntry.text,'USER typed search');assert.deepEqual(weather._weatherRows.children,wxColumns);
assert.strictEqual(currency._currencyAmountEntry,entry);assert.equal(entry.text,'1.234,56');assert.equal(entry.accessible_name,'Amount in BRL');
assert(texts().includes('USER sensor'));assert(texts().includes('USER.service'));assert(texts().includes('USER notice'));
assert(texts().some(value=>value.includes('Result: exit-code')&&value.includes('USER description')),'existing tooltip updates and preserves service data');
assert(texts().some(value=>value.includes('Source: nvme')&&value.includes('USER sensor')),'nested message placeholders update');
L.set(docker._dockerHeading,'text','USER replacement');locale='pt-BR';changed();assert.equal(docker._dockerHeading.text,'USER replacement');
assert.equal(temperatures._temperatureHeading.text,'Temperaturas · 1 sensores · 3 adicionais');
stopWeatherLanguage();
console.log('OK: all ten panel modules switch PT↔EN in place; nested tooltips, errors, external data and currency drafts preserved.');

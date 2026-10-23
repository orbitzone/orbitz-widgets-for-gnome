const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const scope=vm.createContext({});vm.runInContext(fs.readFileSync('extension/panels/weather.js','utf8'),scope);
class Actor {
 constructor(props={}){Object.assign(this,props);this.children=[];this.events={};this.text=props.text||'';this.textEvents={};this.clutter_text={set_line_wrap(){},set_line_wrap_mode(){},set_max_length(){},set_ellipsize(){},connect:(name,fn)=>this.textEvents[name]=fn};}
 insert_child_at_index(child,index){this.children.splice(index,0,child);}get_first_child(){return this.children[0];}add_child(child){this.children.push(child);}add_actor(child){this.add_child(child);}connect(name,fn){this.events[name]=fn;}add_constraint(){}set_policy(...values){this.policy=values;}
 set_child_above_sibling(){}grab_key_focus(){this.focused=true;}
 destroy_all_children(){this.children=[];}get_text(){return this.text;}set_text(value){this.text=value;this.textEvents['text-changed']?.();}show(){this.visible=true;}hide(){this.visible=false;}get_preferred_width(){return[0,720];}get_preferred_height(){return[0,650];}get_position(){return[this.x||0,this.y||0];}set_position(x,y){this.x=x;this.y=y;}
}
let command='/usr/bin/python3 /synthetic/clima-widget.py';const stops=[],queue=[],timers=new Map();let timer=0;
const GLib={shell_parse_argv:value=>[true,value.match(/'[^']*'|\S+/g).map(token=>token.replace(/^'|'$/g,''))],timeout_add:(_p,_ms,fn)=>{timers.set(++timer,fn);return timer;},source_remove:id=>timers.delete(id),PRIORITY_DEFAULT:0,SOURCE_REMOVE:0};
const base=require('./helpers/ui_language').create({},'pt-BR');
const Language={...base,spawn:args=>({args,get_successful:()=>true})};
const deps={Language,GLib,Pango:{WrapMode:{WORD_CHAR:1},EllipsizeMode:{END:1}},Gio:{Cancellable:class{},SubprocessFlags:{STDOUT_PIPE:1,STDERR_PIPE:2}},Main:{uiGroup:new Actor(),layoutManager:{findMonitorForActor:()=>({x:0,y:0,width:740,height:720}),primaryMonitor:{width:1280}}},St:{Widget:Actor,BoxLayout:Actor,Label:Actor,Button:Actor,ScrollView:Actor,Entry:Actor,Icon:Actor,PolicyType:{AUTOMATIC:1,NEVER:0}},Clutter:{BindConstraint:class{},BindCoordinate:{ALL:1},ActorAlign:{START:0,CENTER:1},KEY_Down:65364,KEY_Escape:65307,EVENT_STOP:1,EVENT_PROPAGATE:0},global:{stage:{}},getData:()=>command,readCommandOutput:run=>new Promise((resolve,reject)=>queue.push({run,resolve,reject})),stopCommandRun:run=>{if(!run)return;run.cancelled=true;stops.push(run);}};Object.assign(scope,deps);const methods=scope.create(deps);
const prefs=(unit='celsius',revision=0)=>({version:1,ok:true,unit,revision,location:{id:'builtin-brasilia',country_id:'BR',region_id:'',name:'Brasília, DF',latitude:-15.7939,longitude:-47.8828,timezone:'America/Sao_Paulo'}});
const host=()=>({...methods,_weatherPreferences:prefs(),_weatherUnitButtons:{},_cancelCommand(){},refreshCommand(){},_networkGeneration:1,_networkDestroyed:false,_networkDialog:{visible:true},_weatherRows:new Actor(),_weatherCurrentLabel:{},_weatherTitle:{},_weatherScroll:{},_networkRefreshStatus:{},_networkRefreshButton:{}});
const forecast=()=>({version:1,ok:true,unit:'celsius',location:{name:'USER Brasília',latitude:-15.7939,longitude:-47.8828,timezone:'America/Sao_Paulo'},current:{time:'2026-10-22T12:00',temperature:25,apparent_temperature:26,humidity:60,weather_code:0,is_day:1},days:Array.from({length:7},(_,i)=>({date:`2026-10-${String(22+i).padStart(2,'0')}`,temp_min:17,temp_max:29,precipitation_probability:30,wind_speed_max:15,weather_code:i})),fetched_at:'2026-10-22T15:00:00Z',stale:false,attribution:{name:'Open-Meteo',url:'https://open-meteo.com/',license:'CC-BY-4.0'}});
const info=methods._weatherCommandInfo(command);assert.equal(info.unit,'celsius');assert.equal(info.name,'Brasília, DF');
assert.equal(methods._weatherCommandInfo(command+' --latitude 1'),null);assert.equal(methods._weatherCommandInfo(command+' --unit kelvin'),null);
methods._weatherValidate(forecast(),info);
for(const change of [data=>data.days[0].wind_speed_max=501,data=>delete data.days[0].wind_speed_max,data=>data.days.pop(),data=>data.days[1].date=data.days[0].date,data=>data.stale=true,data=>data.unit='fahrenheit',data=>data.current.humidity=101,data=>data.days[0].temp_min=100,data=>data.location.latitude=0,data=>data.attribution.url='https://unknown.invalid']){
 const data=forecast();change(data);assert.throws(()=>methods._weatherValidate(data,info));
}
const built=host();built._buildWeatherDialog();built._networkDialog.visible=true;built._renderWeather(forecast());
assert.equal(built._weatherRows.children.length,7);
assert.equal(new Set(built._weatherRows.children.map(actor=>actor.style)).size,1,'seven equal-width day columns');
assert.equal(built._weatherScroll.policy[0],0,'no horizontal scrollbar');
assert(built._weatherCurrentLabel.text.includes('Umidade 60%'));assert(built._weatherTitle.text.includes('USER Brasília'));
// Seven compact columns fit the available content box on both requested viewports.
for(const viewport of [740,1034]) {
 const find=deps.Main.layoutManager.findMonitorForActor;
 deps.Main.layoutManager.findMonitorForActor=()=>({x:0,y:0,width:viewport,height:720});
 const compact=host();compact._buildWeatherDialog();const sample=forecast();
 sample.days.forEach((day,i)=>day.weather_code=[0,1,3,45,51,61,71][i]);compact._renderWeather(sample);
 assert.equal(compact._weatherRows.children.length,7);assert.equal(compact._weatherScroll.policy[0],0);
 const widths=compact._weatherRows.children.map(actor=>Number(actor.style.match(/width: (\d+)px/)[1])+12);
 const available=Number(compact._weatherScroll.style.match(/width: (\d+)px/)[1]);
 assert.equal(new Set(widths).size,1);assert(widths.reduce((a,b)=>a+b,0)+6*6<=available);assert(available<=viewport-64);
 assert.equal(new Set(compact._weatherRows.children.map(actor=>actor.children[1].icon_name)).size,7);
 assert(compact._weatherRows.children[6].accessible_name.includes('Vento: 15 km/h'));
 sample.days[0].wind_speed_max=39.9;sample.days[1].wind_speed_max=40;sample.days[2].wind_speed_max=100;sample.days[2].weather_code=95;
 compact._renderWeather(sample);
 assert.equal(compact._weatherRows.children[0].children[1].icon_name,'weather-clear-symbolic');
 assert.equal(compact._weatherRows.children[1].children[1].icon_name,'weather-windy-symbolic');
 assert.equal(compact._weatherRows.children[2].children[1].icon_name,'weather-storm-symbolic');
 assert(compact._weatherRows.children[1].children[1].accessible_name.includes('Vento: 40 km/h'));
 deps.Main.layoutManager.findMonitorForActor=find;
}
(async()=>{
 const h=host();let first=h._refreshWeatherDialog();assert.equal(h._weatherRows.children.length,0);assert(h._networkRefreshStatus.text.includes('Carregando'));
 const one=queue.shift();let second=h._refreshWeatherDialog();const two=queue.shift();assert(one.run.cancelled);
 one.resolve(['AZCLOCK_WEATHER:'+JSON.stringify(forecast())]);await first;assert.equal(h._weatherRows.children.length,0,'late request never restores old rows');
 two.resolve(['AZCLOCK_WEATHER:'+JSON.stringify(forecast())]);await second;assert.equal(h._weatherRows.children.length,7);assert.equal(timers.size,0);
 const pending=h._refreshWeatherDialog();const closed=queue.shift();h._networkDialog.visible=false;h._networkGeneration++;h._cancelWeatherRequests();closed.resolve(['AZCLOCK_WEATHER:'+JSON.stringify(forecast())]);await pending;
 assert.equal(h._weatherRows.children.length,0);assert.equal(timers.size,0);
 const flush=async()=>{for(let i=0;i<8;i++)await Promise.resolve();};
 const city=id=>({id,name:'USER City '+id,admin1:'USER Region',country:'USER Country',country_code:'BR',latitude:-15.7939,longitude:-47.8828,timezone:'America/Sao_Paulo'});
 const geo=results=>({version:1,ok:true,results,complete:false,attribution:{name:'Open-Meteo',url:'https://open-meteo.com/',location_source:'GeoNames',location_url:'https://www.geonames.org/'}});
 const g=host();g._buildWeatherDialog();g._networkDialog.visible=true;g._weatherAdoptPreferences(prefs());
 assert.equal(g._weatherGeoButtons,undefined,'old cascade is absent');
 assert.equal(g._weatherSearchButton.label,'Pesquisar');
 let refreshes=0,cancels=0;g._cancelCommand=()=>cancels++;g.refreshCommand=()=>refreshes++;
 g._weatherSearch.set_text('USER City');assert.equal(queue.length,0,'typing does not trigger a request');
 g._weatherSearch.textEvents.activate();let request=queue.shift();assert.deepEqual(Array.from(request.run.proc.args.slice(-2)),['--geocode','USER City']);
 assert.equal(g._weatherSearchButton.reactive,false);
 request.resolve(['AZCLOCK_GEOCODING:'+JSON.stringify(geo([city(1),city(2)]))]);await flush();
 assert.equal(g._weatherResultRows.children[0].label,'USER City 1 · USER Region · USER Country');
 assert.equal(g._weatherResultRows.children[0].accessible_name,g._weatherResultRows.children[0].label);
 g._weatherSearch.events['key-press-event'](null,{get_key_symbol:()=>65364});assert(g._weatherResultRows.children[0].focused);
 g._weatherResultRows.children[0].events.clicked();request=queue.shift();
 assert(request.run.proc.args.includes('--set-geocoded-location'));
 assert.deepEqual(JSON.parse(request.run.proc.args[request.run.proc.args.indexOf('--set-geocoded-location')+1]),city(1));
 assert.deepEqual(Array.from(request.run.proc.args.slice(-2)),['--expected-revision','0']);
 assert.equal(refreshes,0,'summary is not refreshed before ACK');
 assert.equal(g._weatherSaving,true);assert.equal(g._weatherUnitButtons.fahrenheit.reactive,false);
 const selected=prefs('celsius',1);selected.location={...selected.location,id:'geonames:1',name:'USER City 1',country_name:'USER Country',region_name:'USER Region'};
 request.resolve(['AZCLOCK_WEATHER_PREFS:'+JSON.stringify(selected)]);await flush();
 assert.equal(refreshes,1);assert.equal(cancels,1);request=queue.shift();assert(request.run.proc.args.includes('--forecast-json'));
 const selectedForecast=forecast();selectedForecast.location.name='USER City 1';request.resolve(['AZCLOCK_WEATHER:'+JSON.stringify(selectedForecast)]);await flush();
 assert.equal(g._weatherPreferences.location.id,'geonames:1');assert(g._weatherTitle.text.includes('USER City 1 · USER Region · USER Country'));
 assert.equal(g._weatherRows.children.length,7);
 for(const mutate of [d=>d.results[0].id=0,d=>d.results[0].latitude=91,d=>d.results[0].country_code='br',d=>d.results.push(d.results[0]),d=>d.results=Array(11).fill(city(1)),d=>d.attribution.location_url='https://unknown.invalid']){
  const data=geo([city(1)]);mutate(data);assert.throws(()=>g._weatherValidateSearch(data));
 }
 // Unit writes are confirmed before updating both desktop summary and forecast.
 g._weatherSetUnit('fahrenheit');request=queue.shift();assert(request.run.proc.args.includes('--set-unit'));assert.equal(g._weatherRows.children.length,0);assert.equal(refreshes,1);
 const fahrenheit={...selected,unit:'fahrenheit',revision:2};request.resolve(['AZCLOCK_WEATHER_PREFS:'+JSON.stringify(fahrenheit)]);await flush();request=queue.shift();
 assert.equal(refreshes,2);assert.equal(cancels,2);
 assert.equal(request.run.proc.args[request.run.proc.args.indexOf('--unit')+1],'fahrenheit');
 const fData={...selectedForecast,unit:'fahrenheit'};request.resolve(['AZCLOCK_WEATHER:'+JSON.stringify(fData)]);await flush();assert(g._weatherCurrentLabel.text.includes('°F'));assert(g._weatherUnitButtons.fahrenheit.accessible_name.includes('selecionada'));
 // A CAS conflict reloads preferences and never repeats a write or refreshes summary as a success.
 g._weatherSetUnit('celsius');request=queue.shift();request.resolve(['AZCLOCK_WEATHER_PREFS:'+JSON.stringify({version:1,ok:false,error_code:'conflict'})]);await flush();
 assert.equal(refreshes,2);
 request=queue.shift();assert(request.run.proc.args.includes('--preferences-json'));request.resolve(['AZCLOCK_WEATHER_PREFS:'+JSON.stringify(fahrenheit)]);await flush();
 request=queue.shift();assert(!request.run.proc.args.includes('--set-unit'));request.resolve(['AZCLOCK_WEATHER:'+JSON.stringify(fData)]);await flush();assert(g._networkRefreshStatus.text.includes('outra janela'));
 // Empty, invalid and failed searches leave explicit feedback and the same button retries.
 g._weatherSearch.set_text('x');await g._weatherSearchLocations();assert.equal(queue.length,0);assert(g._weatherSearchStatus.text.includes('2 a 100'));
 g._weatherSearch.set_text('Nowhere');g._weatherSearchButton.events.clicked();request=queue.shift();request.resolve(['AZCLOCK_GEOCODING:'+JSON.stringify(geo([]))]);await flush();
 assert(g._weatherSearchStatus.text.includes('Nenhuma cidade'));assert.equal(g._weatherResultRows.children.length,0);
 const failing=g._weatherSearchLocations();request=queue.shift();request.reject(new Error('external failure'));await failing;assert(g._weatherSearchStatus.text.includes('tentar novamente'));assert(g._weatherSearchButton.reactive);
 g._weatherSearchButton.events.clicked();request=queue.shift();request.resolve(['AZCLOCK_GEOCODING:'+JSON.stringify(geo([city(3)]))]);await flush();assert.equal(g._weatherResultRows.children.length,1);
 // Editing cancels old results immediately; superseded responses and buttons cannot select a stale city.
 const staleButton=g._weatherResultRows.children[0];g._weatherSearch.set_text('OLD');g._weatherSearchLocations();const oldSearch=queue.shift();
 g._weatherSearch.set_text('NEW');g._weatherSearchLocations();const newSearch=queue.shift();assert(oldSearch.run.cancelled);
 staleButton.events.clicked();assert.equal(queue.length,0);
 oldSearch.resolve(['AZCLOCK_GEOCODING:'+JSON.stringify(geo([city(4)]))]);await flush();assert.equal(g._weatherResultRows.children.length,0);
 newSearch.resolve(['AZCLOCK_GEOCODING:'+JSON.stringify(geo([city(5)]))]);await flush();assert.equal(g._weatherResultRows.children[0].label,'USER City 5 · USER Region · USER Country');
 assert.equal(g._networkBackdrop.events['key-press-event'](null,{get_key_symbol:()=>65307}),1);assert.equal(g._weatherResultsBox.visible,false);assert(g._weatherSearch.focused);
 // Closing and reopening during a write cannot clear the new write's busy state.
 g._weatherSetUnit('celsius');const oldSave=queue.shift();g._weatherClose();g._networkGeneration++;
 g._networkDialog.visible=true;g._weatherAdoptPreferences({...fahrenheit,revision:4});g._weatherSetUnit('celsius');const newSave=queue.shift();
 oldSave.resolve(['AZCLOCK_WEATHER_PREFS:'+JSON.stringify({...selected,revision:3})]);await flush();assert.equal(g._weatherSaving,true);
 assert.deepEqual(Array.from(newSave.run.proc.args.slice(-2)),['--expected-revision','4']);
 newSave.resolve(['AZCLOCK_WEATHER_PREFS:'+JSON.stringify({...selected,revision:5})]);await flush();request=queue.shift();request.resolve(['AZCLOCK_WEATHER:'+JSON.stringify(selectedForecast)]);await flush();assert.equal(g._weatherPreferences.unit,'celsius');
 g._weatherSearch.set_text('Closing');g._weatherSearchLocations();const closingSearch=queue.shift();g._weatherClose();g._networkGeneration++;g._networkDialog.visible=false;
 closingSearch.resolve(['AZCLOCK_GEOCODING:'+JSON.stringify(geo([city(6)]))]);await flush();assert.equal(g._weatherResultRows.children.length,0);assert.equal(g._weatherPreferences,null);
 assert.equal(timers.size,0);
 // Exercise the actual shared CommandLabel routes, not just the weather factory.
 const source=fs.readFileSync('extension/extension.js','utf8');
 const method=(start,end)=>source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start)));
 deps.Main.layoutManager.monitors=[{x:0,y:0,width:740,height:720}];const grabs=[];
 deps.Main.pushModal=()=>{grabs.push('push');return {};};deps.Main.popModal=()=>grabs.push('pop');
 Object.assign(scope,{metricMode:()=>null,metricLabels:new Set(),widgetsEnabled:true,Shell:{ActionMode:{POPUP:1}}});
 vm.runInContext('this.Shared=class {'+method('    _closeNetworkDialog()','    async _refreshNetworkDialog()')+method('    async _refreshNetworkDialog()','    _openNetworkDialog()')+method('    _openNetworkDialog()','    async _startSpeedtest()')+method('    _executeCommand()','    _cancelCommand()')+method('    _cancelCommand()','    async _execCommand(')+method('    refreshCommand()','    _startPollingInterval()')+'}',scope);
 const shared=Object.assign(new scope.Shared(),methods,{_networkGeneration:1,_networkDestroyed:false,_networkDialog:null,_weatherPreferences:null,_cancelFirewallInspection(){},get_transformed_position:()=>[10,10],get_transformed_size:()=>[180,50]});
 let scheduled=0,summaryCommand;shared._scheduleNetworkClick=()=>scheduled++;shared._execCommand=value=>summaryCommand=value;
 shared._executeCommand();assert.equal(scheduled,1);assert.equal(summaryCommand,command,'existing summary command remains intact');
 shared._openNetworkDialog();assert.equal(grabs[0],'push');assert(shared._weatherSearch.focused);request=queue.shift();assert(request.run.proc.args.includes('--preferences-json'));
 request.resolve(['AZCLOCK_WEATHER_PREFS:'+JSON.stringify(prefs())]);await flush();request=queue.shift();request.resolve(['AZCLOCK_WEATHER:'+JSON.stringify(forecast())]);await flush();assert.equal(shared._weatherRows.children.length,7);
 // Actual CommandLabel cancellation + refresh preserve command and restart the regular interval.
 let removed=0,started=0;shared._removePollingInterval=()=>removed++;shared._startPollingInterval=()=>started++;
 const oldSummary={timeout:null};shared._commandRun=oldSummary;
 shared._weatherSetUnit('fahrenheit');request=queue.shift();assert.equal(oldSummary.cancelled,undefined);
 request.resolve(['AZCLOCK_WEATHER_PREFS:'+JSON.stringify(prefs('fahrenheit',1))]);await flush();
 assert.equal(oldSummary.cancelled,true);assert.equal(removed,1);assert.equal(started,1);assert.equal(summaryCommand,command);assert.equal(scheduled,2);
 request=queue.shift();request.resolve(['AZCLOCK_WEATHER:'+JSON.stringify({...forecast(),unit:'fahrenheit'})]);await flush();
 shared._networkBackdrop.events['key-press-event'](null,{get_key_symbol:()=>65307});assert.equal(grabs.at(-1),'pop');assert.equal(shared._networkDialog.visible,false);assert.equal(shared._weatherPreferences,null);
 console.log('OK: seven equal forecast columns, city search/result click, immediate summary refresh, confirmed unit/location persistence, CAS recovery, retry/empty states and stale/closed forecast/search/save rejection.');
})().catch(error=>{console.error(error);process.exitCode=1;});

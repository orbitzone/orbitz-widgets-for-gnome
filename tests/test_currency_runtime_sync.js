const assert=require('assert'),fs=require('fs'),vm=require('vm');
const flow=require('./test_currency_preferences_flow');
const {settings,settingsModules,created,gi,load}=flow;
const source=fs.readFileSync('extension/extension.js','utf8');
const method=source.slice(source.indexOf('    _widgetDataChangedEvent() {'),source.indexOf('\n}\n',source.indexOf('    _widgetDataChangedEvent() {')));
const context=vm.createContext({Me:{settings},GLib:gi.GLib,WIDGETDATA:flow.getData(),debugLog(){}});
vm.runInContext('this.Manager=class {'+method+'\n}',context);
let builds=0,updates=0,commands=[];
const widget={_elementLayout:JSON.stringify(['Command_Label']),
 createElements(){builds++;this._elementLayout=JSON.stringify(context.WIDGETDATA[0].slice(1).map(e=>e.Element_Type));},
 updateComponents(){updates++;commands=context.WIDGETDATA[0].slice(1).map(e=>e.Text_Command);}};
const manager=Object.assign(new context.Manager(),{widgets:[widget],_detachWidgetGroups(){},_applyWidgetGroups(){},_removeClockTimer(){},_startClockTimer(){}});
const Add=load('settings/WidgetSettingsPage.js','AddElementsDialog');
const clone=JSON.parse(JSON.stringify(flow.getData()[0][1]));clone.Name='Cotação USD / BTC';
const addHost={widget_index:0,_settings:settings,emit(){}};
const addRow=Add.prototype.addPresetElement.call(addHost,'Clone',clone);
addRow.nodes[0].emit('clicked');
assert.equal(flow.getChanged().ElementAdded,'true','actual add dialog writes structural marker');
flow.deferCatalogs();
flow.row.nodes.find(n=>n.label==='Configure').emit('clicked');
const window=created.filter(n=>n instanceof settingsModules.WidgetSettingsPage.WidgetSettingsPage).at(-1);
const cryptoPage=window._sidebarListBox.nodes[2].settingPage;
const descend=n=>[n,...(n.nodes||[]).flatMap(descend)];
const group=descend(cryptoPage).find(n=>n.title==='Currency converter');
group.nodes[0].nodes[0].selected=1;
flow.flushCatalogs(); // Both catalogs complete before the Shell's 300ms debounce.
group.nodes[2].nodes[0].active=true;
assert.equal(flow.getChanged().ElementType,'Text_Command');
assert.equal(flow.getChanged().ElementAdded,'true','catalog/property callbacks preserve marker before debounce');
context.WIDGETDATA=flow.getData();manager._widgetDataChangedEvent();
assert.equal(builds,1);assert.equal(commands.length,2);
assert(commands[0].includes('--quote USD'));assert(commands[1].includes('--mode crypto --asset btc-bitcoin --reverse'));
// A plain property edit must not rebuild the widget after pending marker is consumed.
cryptoPage.setClockElementData('Text_Color','red');context.WIDGETDATA=flow.getData();manager._widgetDataChangedEvent();
assert.equal(builds,1);assert.equal(updates,2);
// A deletion marker also survives a settings callback before the debounce.
const data=flow.getData().slice();data[0]=data[0].slice(0,2);
settings.set_value('changed-data',new gi.GLib.Variant('a{ss}',{WidgetIndex:'0',ElementDeleted:'true'}));
settings.set_value('widget-data',new gi.GLib.Variant('aaa{ss}',data));settingsModules.WidgetsData.WidgetsData.data=data;
const fiatPage=window._sidebarListBox.nodes[1].settingPage;fiatPage.setClockElementData('Text_Color','blue');
assert.equal(flow.getChanged().ElementDeleted,'true');context.WIDGETDATA=flow.getData();manager._widgetDataChangedEvent();
assert.equal(builds,2);assert.equal(commands.length,1);
console.log('OK: real add→catalog→settings→Shell debounce preserves fiat/crypto elements; plain edits avoid rebuild and deletion survives.');

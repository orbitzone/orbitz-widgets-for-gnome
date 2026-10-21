const assert=require('assert');
function fresh(){delete require.cache[require.resolve('./test_currency_preferences_flow')];return require('./test_currency_preferences_flow');}
for(const scenario of ['unchanged','remove-element','reorder-elements','remove-widget','reorder-widgets','unrealize']){
 const flow=fresh(),{settings,settingsModules,gi,created}=flow;
 const save=data=>{settings.set_value('widget-data',new gi.GLib.Variant('aaa{ss}',data));settingsModules.WidgetsData.WidgetsData.data=data;};
 let data=flow.getData();
 if(scenario==='reorder-elements'){data[0].push({...data[0][1],Name:'Other converter',Text_Command:data[0][1].Text_Command+' --reverse'});save(data);}
 if(scenario==='reorder-widgets'){data.push([{...data[0][0],Name:'Other widget',Widget_Id:'other'}]);save(data);}
 flow.deferCatalogs();flow.row.nodes.find(n=>n.label==='Configure').emit('clicked');
 const window=created.filter(n=>n instanceof settingsModules.WidgetSettingsPage.WidgetSettingsPage).at(-1);
 const page=window._sidebarListBox.nodes[1].settingPage;
 const descend=n=>[n,...(n.nodes||[]).flatMap(descend)];
 const group=descend(page).find(n=>n.title==='Currency converter');
 group.nodes[0].nodes[0].selected=1; // Explicit user intent; response is still pending.
 data=flow.getData();
 if(scenario==='remove-element')data[0].splice(1,1);
 if(scenario==='reorder-elements')[data[0][1],data[0][2]]=[data[0][2],data[0][1]];
 if(scenario==='remove-widget')data.splice(0,1);
 if(scenario==='reorder-widgets')[data[0],data[1]]=[data[1],data[0]];
 if(scenario==='unrealize')page.emit('unrealize');
 if(scenario!=='unchanged'&&scenario!=='unrealize')save(data);
 const before=JSON.stringify(flow.getData());
 if(scenario!=='unchanged')page.setClockElementData('Name','Stale page edit');
 flow.flushCatalogs();
 if(scenario==='unchanged')assert(flow.getData()[0][1].Text_Command.includes('--mode crypto --asset btc-bitcoin'));
 else assert.equal(JSON.stringify(flow.getData()),before,scenario+' must never write a late catalog into current indices');
}
// Merely opening a page, even with a successful catalog, must be read-only.
{
 const flow=fresh(),before=JSON.stringify(flow.getData());flow.deferCatalogs();
 flow.row.nodes.find(n=>n.label==='Configure').emit('clicked');flow.flushCatalogs();
 assert.equal(JSON.stringify(flow.getData()),before);
}
console.log('OK: delayed catalog cannot write after element/widget remove/reorder/unrealize; valid intent works and opening is read-only.');

for(const command of ["--quote ZZZ", "--mode crypto --asset missing-asset"]){
 const flow=fresh(),data=flow.getData();
 data[0][1].Text_Command="/usr/bin/python3 '/user-data/orbitz-widgets/collectors/currency-widget.py' "+command;
 flow.settings.set_value('widget-data',new flow.gi.GLib.Variant('aaa{ss}',data));flow.settingsModules.WidgetsData.WidgetsData.data=data;
 const before=JSON.stringify(flow.getData());flow.deferCatalogs();flow.row.nodes.find(n=>n.label==='Configure').emit('clicked');flow.flushCatalogs();
 const window=flow.created.filter(n=>n instanceof flow.settingsModules.WidgetSettingsPage.WidgetSettingsPage).at(-1);
 const descend=n=>[n,...(n.nodes||[]).flatMap(descend)];
 const group=descend(window._sidebarListBox.nodes[1].settingPage).find(n=>n.title==='Currency converter');
 assert.equal(group.nodes[1].nodes[0].selected,4294967295);assert(group.nodes[1].title.includes('Unavailable asset'));
 assert.equal(JSON.stringify(flow.getData()),before,'missing configured ID cannot silently select option zero');
 group.nodes[1].nodes[0].selected=0;
 assert.notEqual(JSON.stringify(flow.getData()),before,'explicit new choice may replace unavailable ID');
}
console.log('OK: missing fiat/crypto IDs remain configured until an explicit asset selection.');

// A legitimate rename is an edit by this same page, not a change of identity.
for(const timing of ['after-catalog','during-catalog']){
 const flow=fresh();flow.deferCatalogs();flow.row.nodes.find(n=>n.label==='Configure').emit('clicked');
 const window=flow.created.filter(n=>n instanceof flow.settingsModules.WidgetSettingsPage.WidgetSettingsPage).at(-1);
 const page=window._sidebarListBox.nodes[1].settingPage;
 const descend=n=>[n,...(n.nodes||[]).flatMap(descend)];
 const group=descend(page).find(n=>n.title==='Currency converter');
 if(timing==='after-catalog')flow.flushCatalogs();
 page.setClockElementData('Name','Renamed converter');
 if(timing==='during-catalog')flow.flushCatalogs();
 const picker=group.nodes[1].nodes[0];
 assert(picker.sensitive);assert(picker.model.items[0].startsWith('EUR'));
 picker.selected=0;
 assert(flow.getData()[0][1].Text_Command.endsWith('--quote EUR'),timing+' rename must keep saving EUR');
 assert.equal(flow.getData()[0][1].Name,'Renamed converter');
}
console.log('OK: rename before/after catalog preserves identity and enabled EUR selection persists.');

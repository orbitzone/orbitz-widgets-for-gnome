// Execute the actual launcher branch without starting apps or touching saved widget data.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('extension/extension.js','utf8');
const start=source.indexOf("                const btop = clockData[i].Launcher_Action === 'btop';");
const end=source.indexOf('            } else if (clockType === TEXT_LABEL) {',start);
assert(start>=0 && end>start);
class Actor {
 constructor(props={}){Object.assign(this,props);this.children=[];}
 set_child(child){this.children=[child];}add_child(child){this.children.push(child);}
}
let fail=false;const commands=[],terminal=[],errors=[],notifications=[];
const process={wait_async:async()=>{},get_successful:()=>!fail};
const context={St:{Button:Actor,Icon:Actor},Gio:{icon_new_for_string:value=>value,SubprocessFlags:{NONE:0},Subprocess:{new(argv,flags){commands.push({argv:Array.from(argv),flags});return process;}}},
 GLib:{build_filenamev:parts=>parts.join('/')},Me:{path:'/extension'},
 bindDesktopLauncher:(button,callback)=>button.launch=callback,
 launchTerminalAction:(argv,owner)=>{terminal.push({argv:Array.from(argv),owner});return process;},
 logError:(error,label)=>errors.push({error,label}),Main:{notify:(...args)=>notifications.push(args)}};
context.Language=require('./helpers/ui_language').create(context,'pt-BR');
vm.createContext(context);
context.Actor=Actor;
vm.runInContext(`this.Launchers=class extends Actor {build(action){const clockData=[{}, {Launcher_Action:action}];const i=1;${source.slice(start,end)}}}`,context);
(async()=>{
 assert(!source.includes("['youtube', 'gemini', 'btop', 'notes']"),'independent apps are not widget launchers');
 assert(!source.includes("'/usr/bin/flatpak', 'run', '--user', 'io.orbitz.Postits'"));
 assert(!source.includes("'/usr/bin/flatpak', 'run', '--user', 'io.orbitz.YouTubeDesktop'"));
 assert(!fs.existsSync('extension/youtube-widget'),'legacy YouTube app source is removed from the widget repository');
 assert(source.includes('io\\.orbitz\\.YouTubeDesktop'),'MPRIS recognizes the independent YouTube app');
 assert(!source.includes('io\\.orbitz\\.YouTubeWidget'),'MPRIS no longer recognizes the legacy app identity');
 const gemini=new context.Launchers();gemini.build('gemini');await gemini.children[0].launch();
 assert.deepEqual(commands.at(-1).argv,['/usr/bin/google-chrome','--app=https://gemini.google.com/','--window-size=1100,900']);
 const btop=new context.Launchers();btop.build('btop');await btop.children[0].launch();
 assert.deepEqual(terminal[0].argv,['/usr/bin/tilix','--action=app-new-window','-e','/usr/bin/btop']);assert.strictEqual(terminal[0].owner,btop);
 const before=commands.length;fail=true;const missing=new context.Launchers();missing.build('gemini');await missing.children[0].launch();
 assert.equal(commands.length,before+1);
 assert.equal(errors.length,1);assert.equal(notifications.length,1);
 assert(!source.includes('orbitz-postits\', \'app\', \'postits.py'));
 assert(!source.includes("'org.gtk.Actions', 'Activate'"),'extension has no app quit bus action');
 console.log('OK: Sticky Notes and YouTube are no longer widget launchers; Gemini, btop and launch failure feedback preserved.');
})().catch(error=>{console.error(error);process.exitCode=1;});

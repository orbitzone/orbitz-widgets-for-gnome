const assert=require('assert'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync(require('path').join(__dirname,'../extension/extension.js'),'utf8');
const context={Pango:{SCALE:1024},TextEncoder,TextDecoder};vm.createContext(context);
vm.runInContext('this.target = function'+source.slice(source.indexOf('    _storageTarget(pointer) {')+'    _storageTarget'.length,source.indexOf('    _checkNetworkClick(pointer)')),context);
const lines=['CPU ███ 30%','','RAM ██ 20%','','! SSD █████ 93%','','! EXT ██ 95%'];const text=lines.join('\n');
let line=0;
const host={clutter_text:{transform_stage_point:()=>[true,0,line*15],get_text:()=>text,get_layout:()=>({xy_to_index:()=>[true,new TextEncoder().encode(lines.slice(0,line).join('\n')+(line?'\n':'')).length,0]})}};
for(const [index,expected] of [[0,null],[2,null],[4,'ssd'],[6,'external'],[3,null]]){line=index;assert.equal(context.target.call(host,[0,0]),expected);}
console.log('OK: Stats activates storage only on SSD/EXT lines, including UTF-8 bars and alert prefix.');

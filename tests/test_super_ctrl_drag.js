const assert=require('assert'),fs=require('fs'),vm=require('vm'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../extension/extension.js'),'utf8');
const helper={};vm.createContext(helper);vm.runInContext(fs.readFileSync(path.join(__dirname,'../extension/dragging.js'),'utf8'),helper);
const monitor={x:-1280,y:0,width:1280,height:1024};
assert.deepEqual({...helper.dropPosition(-1200,50,200,100,monitor,3)},{x:-1000,y:150});
assert.deepEqual({...helper.dropPosition(-2000,1100,200,100,monitor,0)},{x:-1280,y:924});
assert.throws(()=>helper.dropPosition(NaN,0,200,100,monitor,0),/inválida/);

const widget={get_transformed_position:()=>[100,100],get_transformed_size:()=>[200,100]};
let begins=0,moves=[],finishes=[];
const controller=new helper.PointerDragController({buttonMask:1,superMask:64,mod4Mask:128,controlMask:4,
 widgets:()=>[widget],canStart:()=>true,begin(){begins++;},move(w,x,y){moves.push([x,y]);},finish(w,drop){finishes.push(drop);}});
// No native mouse event is supplied: the entire gesture comes from global pointer samples.
controller.update([120,120,0]);controller.update([120,120,1|4]);controller.update([120,120,0]);assert.equal(begins,0);
controller.update([120,120,1|64|4]);controller.update([180,160,1|64|4]);controller.update([190,170,64|4]);
assert.equal(begins,1);assert.deepEqual(moves.at(-1),[170,150]);assert.equal(finishes[0].x,170);assert.equal(finishes[0].y,150);
controller.update([120,120,0]);controller.update([120,120,1|128|4]);assert.equal(begins,2);controller.cancel();assert.equal(finishes[1],null);
controller.update([160,160,1|128|4]);assert.equal(begins,2); // no restart until mouse release
controller.update([160,160,0]);
controller.options.canStart=()=>false;controller.update([120,120,1|64|4]);assert.equal(begins,2); // foreground window or modal
console.log('OK: pointer-driven drag without native events, Super/MOD4+Ctrl, exact drop, cancellation and blocked foreground.');

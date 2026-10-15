const assert=require('assert'),fs=require('fs'),vm=require('vm');
const code=fs.readFileSync(require('path').join(__dirname,'../extension/grouping.js'),'utf8');
const scope={};vm.createContext(scope);vm.runInContext(code,scope);
const widget=(id,parent='',group=false)=>[{Widget_Id:id,Parent_Id:parent,Box_IsGroup:group?'true':'false'}];
const data=[widget('root','',true),widget('a','root'),widget('b','root'),widget('solo')];
assert.deepEqual([...scope.planGroups(data).get(0)],[1,2]);
const reordered=[data[2],data[3],data[0],data[1]];
assert.deepEqual([...scope.planGroups(reordered).get(2)],[0,3]);
assert.equal(scope.planGroups([data[1],data[2]]).size,0);
assert.equal(scope.planGroups([widget('a','b',true),widget('b','a',true)]).size,0);
assert.equal(scope.planGroups([widget('root','',true),widget('root','',true),widget('c','root')]).size,0);
assert.equal(scope.planGroups([widget('root','',true),widget('nested','root',true),widget('c','nested')]).has(1),false);
console.log('OK: stable IDs, ordering, deletion fallback, duplicate IDs, nested groups and cycles.');

assert.deepEqual([...scope.settingsOrder([widget('sensors'),widget('a','root'),widget('b','root'),widget('root','',true)])],[0,3,1,2]);
assert.deepEqual([...scope.settingsOrder([widget('a','missing'),widget('solo')])],[0,1]);
console.log('OK: preferences list children under their actual parent; orphan widgets remain visible.');

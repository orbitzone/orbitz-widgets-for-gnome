// UI tests can exercise their own controls without mocking locale catalogs by hand.
const catalog=require('../../i18n/en-US.json');
exports.create=(context,locale='en-US')=>{
 const catalog=require('../../i18n/'+locale+'.json');
 const tr=(key,values={})=>(catalog[key]??key).replace(/\{(\w+)\}/g,(match,name)=>Object.hasOwn(values,name)?text(values[name]):match);
 const msg=(key,values={})=>({orbitzMessage:true,key,values});
 const text=value=>value?.orbitzFormat==='number'?Number(value.value).toLocaleString(locale,value.options):value?.orbitzFormat==='date'?new Date(value.value).toLocaleString(locale,value.options):value?.orbitzParts?value.orbitzParts.map(text).join(''):value?.orbitzMessage?tr(value.key,value.values):value;
 const join=(...parts)=>({orbitzParts:parts});
 return {tr,msg,text,join,number:(value,options={})=>({orbitzFormat:'number',value,options}),date:(value,options={})=>({orbitzFormat:'date',value,options}),error:value=>{const e=new Error(text(value));if(value?.orbitzMessage)e.orbitzMessage=value;return e;},configure(){},getLocale:()=>locale,watch:()=>()=>{},
  widget:(Constructor,props)=>new Constructor(Object.fromEntries(Object.entries(props).map(([key,value])=>[key,text(value)]))),
  properties:(owner,props)=>Object.fromEntries(Object.entries(props).map(([key,value])=>[key,text(value)])),
  set:(owner,key,value)=>{owner[key]=text(value);return owner;},
  call:(owner,key,value,...args)=>{owner[key](text(value),...args);return owner;},
  items:(owner,StringList,values)=>{const selected=owner.selected;const list=StringList.new?StringList.new(values.map(text)):new StringList();if(!StringList.new)values.forEach(value=>list.append(text(value)));owner.model=list;owner.selected=selected;return owner;},
  button:(dialog,value,response)=>{const owner=dialog.add_button(text(value),response);owner.label=text(value);return owner;},
  spawn:(args,flags)=>context.Gio.Subprocess.new(args,flags)};
};

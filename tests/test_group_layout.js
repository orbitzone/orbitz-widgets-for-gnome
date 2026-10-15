const assert=require('assert'),fs=require('fs'),vm=require('vm');
const path=require('path');const source=fs.readFileSync(path.join(__dirname,'../extension/extension.js'),'utf8');
const scope={};vm.createContext(scope);vm.runInContext(fs.readFileSync(path.join(__dirname,'../extension/grouping.js'),'utf8'),scope);
class Actor {
 constructor(props={}){Object.assign(this,props);this.children=[];this.layout_manager={};}
 add_child(child){assert(!child.parent);this.children.push(child);child.parent=this;}
 remove_child(child){this.children.splice(this.children.indexOf(child),1);child.parent=null;}
 get_parent(){return this.parent;}
 destroy(){this.destroyed=true;for(const child of [...this.children])child.destroy();this.parent?.remove_child(this);}
 set_position(){} setStyle(){} setElementsStyle(){} setPositionFromSettings(){} makeDraggable(){this._draggable={};} queue_relayout(){} _getStableWidth(){return 520;}
}
const background=new Actor();const context={PANEL_TITLE_STYLE:'shared title style',Me:{imports:{grouping:scope}},St:{BoxLayout:Actor,Label:Actor},Clutter:{Orientation:{VERTICAL:1}},Main:{layoutManager:{_backgroundGroup:background}},getData:()=>true,WIDGETDATA:[[{Widget_Id:'root',Box_IsGroup:'true',Group_Columns:'2',Box_Width:'520',Box_Padding:'16'}],[{Parent_Id:'root'}],[{Parent_Id:'root'}],[{Parent_Id:'root'}]]};
vm.createContext(context);
vm.runInContext('class Manager {'+source.slice(source.indexOf('    _detachWidgetGroups()'),source.indexOf('    _destroyWidgets()'))+'};this.Manager=Manager',context);
const manager=new context.Manager();manager.widgets=Array.from({length:4},()=>new Actor());manager.widgets.forEach((widget,index)=>{widget.widgetIndex=index;background.add_child(widget);});
for(let i=0;i<3;i++){
 manager._applyWidgetGroups();
 assert.equal(manager.widgets[0]._subwidgetBox.children.length,3); // heading + two rows
 assert(manager.widgets[1]._grouped); assert.equal(manager.widgets[1]._groupWidth,240);
 manager._detachWidgetGroups();
 assert.equal(background.children.length,4);
 assert(manager.widgets.every(widget=>!widget.destroyed&&!widget._grouped));
}
context.WIDGETDATA[0][0].Box_IsGroup='false';manager._applyWidgetGroups();assert.equal(background.children.length,4);
console.log('OK: grid rows/width, repeated grouping/ungrouping preserves actors, removed-parent fallback.');

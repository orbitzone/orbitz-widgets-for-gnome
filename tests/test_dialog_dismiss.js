const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(require('path').join(__dirname, '../extension/extension.js'), 'utf8');
const pattern = /this\._networkBackdrop\.connect\('button-press-event', (\(_actor, event\) => \{[\s\S]*?return Clutter\.EVENT_STOP;\s*\})\);/g;
let count = 0;
for (const match of source.matchAll(pattern)) {
    let closed = 0;
    const inside = {};
    const host = {_networkDialog: {contains: actor => actor === inside}, _closeNetworkDialog() {closed++;}};
    const context = {Clutter: {EVENT_PROPAGATE: 0, EVENT_STOP: 1}, host};
    vm.createContext(context);
    const handler = vm.runInContext('(function() {return ' + match[1] + ';}).call(host)', context);
    assert.equal(handler(null, {get_source: () => inside}), 0); assert.equal(closed, 0);
    assert.equal(handler(null, {get_source: () => ({})}), 1); assert.equal(closed, 1);
    count++;
}
assert.equal(count, 5);
console.log('OK: outside click closes all five dialog backdrops; inside click remains interactive.');

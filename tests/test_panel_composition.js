const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const factories = {};
for (const name of ['common', 'updates', 'temperatures', 'storage', 'resources', 'network', 'docker', 'firewall']) {
    const context = vm.createContext({});
    vm.runInContext(fs.readFileSync(path.join(__dirname, '../extension/panels', name + '.js'), 'utf8'), context);
    factories[name] = context;
}
const context = vm.createContext({imports: {misc: {extensionUtils: {getCurrentExtension: () => ({imports: {panels: factories}})}}}});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../extension/commandPanels.js'), 'utf8'), context);
class Label {}
class CommandLabel extends Label { lifecycle() { return 'alive'; } }
assert.strictEqual(context.install(CommandLabel, {}), CommandLabel);
const host = new CommandLabel();
assert(host instanceof Label);
assert.equal(host.lifecycle(), 'alive');
assert.equal(host._temperatureCategory({group: 'coretemp', name: 'Core 0'}), 'CPU');
assert.equal(host._temperatureColumns([]).length, 4);
assert.equal(Object.getOwnPropertyNames(CommandLabel.prototype).length, 26);
assert.throws(() => context.install(CommandLabel, {}), /Duplicate command panel method/);
console.log('OK: panel composition preserves superclass, lifecycle, sibling dispatch and rejects collisions.');

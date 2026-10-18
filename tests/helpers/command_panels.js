const fs = require('fs');
const path = require('path');
const vm = require('vm');
const names = ['common', 'updates', 'temperatures', 'storage', 'resources', 'network', 'docker', 'firewall'];
const sources = () => names.map(name => fs.readFileSync(path.join(__dirname, '../../extension/panels', name + '.js'), 'utf8'));

// Exercise the exported factory and actual methods, without slicing class bodies.
exports.load = context => {
    const methods = {};
    for (const source of sources()) {
        vm.runInContext(source, context);
        Object.assign(methods, context.create(context));
    }
    return methods;
};
exports.source = () => sources().join('\n');

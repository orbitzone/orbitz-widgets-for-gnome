// Compose panel methods before GObject registration; no runtime prototype mutation.
const Me = imports.misc.extensionUtils.getCurrentExtension();
const modules = ['common', 'updates', 'temperatures', 'storage', 'resources', 'network', 'docker', 'firewall', 'currency'];

var install = function (klass, dependencies) {
    for (const name of modules) {
        const methods = Me.imports.panels[name].create(dependencies);
        for (const method of Object.keys(methods)) {
            if (Object.prototype.hasOwnProperty.call(klass.prototype, method))
                throw new Error(`Duplicate command panel method: ${method}`);
        }
        Object.defineProperties(klass.prototype, Object.getOwnPropertyDescriptors(methods));
    }
    return klass;
};

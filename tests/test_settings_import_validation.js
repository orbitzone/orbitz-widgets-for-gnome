const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = vm.createContext({imports: {gi: {Gio: {}, GLib: {}}}});
vm.runInContext(fs.readFileSync('extension/settings/SettingsImport.js', 'utf8'), context);
const validate = context.validateWidgets;
const widget = (command, interval) => [[{Widget_Type: 'Widget_Box'}, {
    Element_Type: 'Command_Label', Text_Command: command, Text_PollingInterval: String(interval),
}]];
assert.equal(validate(widget('/usr/bin/python3 /path/currency-widget.py --quote USD', 14400000)).length, 1);
assert.throws(() => validate(widget('/usr/bin/python3 /path/other-widget.py', 14400000)), /Intervalo de comando inválido/);
assert.equal(validate(widget('/usr/bin/python3 /path/other-widget.py', 3600000)).length, 1);
console.log('OK: 4-hour polling imports for FX are accepted while other command intervals remain capped at one hour.');

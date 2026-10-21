const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

let command = "/usr/bin/python3 '/user-data/orbitz-widgets/collectors/currency-widget.py' --quote EUR";
const writes = [];
const refreshed = [];
const widgetData = [[{}, {Text_Command: command}]];
const Me = {settings: {set_value: (...args) => writes.push(args)}};
const Utils = {
    setData: (data, widgetIndex, elementIndex, key, value) => {
        data[widgetIndex][elementIndex][key] = value;
        command = value;
    },
};
const GLib = {
    shell_parse_argv: value => [true, value.match(/'[^']*'|\S+/g).map(token => token.replace(/^'|'$/g, ''))],
    shell_quote: value => `'${value.replaceAll("'", "'\\''")}'`,
    Variant: class { constructor(signature, value) { this.signature = signature; this.value = value; } },
};
const context = vm.createContext({});
vm.runInContext(fs.readFileSync('extension/panels/currency.js', 'utf8'), context);
const methods = context.create({GLib, Me, Utils});
const host = {
    widgetIndex: 0,
    elementIndex: 1,
    _currencyDirectionButton: {},
    _updateCurrencyDirectionButton: methods._updateCurrencyDirectionButton,
    _refreshCurrencyDialog: value => refreshed.push(value),
};
const getData = (_widget, _element, key) => key === 'Text_Command' ? command : undefined;
const panelMethods = context.create({GLib, Me, Utils, getData, getWidgetData: () => widgetData});
Object.assign(host, panelMethods);
host._refreshCurrencyDialog = value => refreshed.push(value);
assert.deepEqual(host._currencyCommandInfo(command).quote, 'EUR');
assert.equal(host._currencyCommandInfo(command).reverse, false);
host._toggleCurrencyDirection();
assert.deepEqual(GLib.shell_parse_argv(command)[1].slice(-2), ['EUR', '--reverse']);
assert.equal(writes.at(-1)[0], 'changed-data');
assert.equal(writes.at(-1)[1].signature, 'a{ss}');
assert.equal(JSON.stringify(writes.at(-1)[1].value), JSON.stringify({WidgetIndex: '0', ElementIndex: '1', ElementType: 'Text_Command'}));
assert.deepEqual(GLib.shell_parse_argv(refreshed.at(-1))[1].at(-1), '--reverse');
host._toggleCurrencyDirection();
assert.equal(GLib.shell_parse_argv(command)[1].includes('--reverse'), false);
console.log('OK: modal direction toggles persist the selected currency and reverse flag in widget-data and request an immediate refresh.');

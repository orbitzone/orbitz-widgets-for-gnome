const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

(async () => {
    const context = vm.createContext({});
    vm.runInContext(fs.readFileSync('extension/panels/currency.js', 'utf8'), context);
    const GLib = {
        shell_parse_argv: value => [true, value.match(/'[^']*'|\S+/g).map(token => token.replace(/^'|'$/g, ''))],
        timeout_add: () => 1,
        source_remove: () => {},
        PRIORITY_DEFAULT: 0,
        markup_escape_text: value => value,
        DateTime: {new_now_local: () => ({format: () => '12:00'})},
    };
    const Gio = {
        SubprocessFlags: {STDOUT_PIPE: 1, STDERR_PIPE: 2},
        Subprocess: {new: () => ({get_successful: () => true})},
        Cancellable: class {},
    };
    const response = 'Cotação indisponível · serviço temporariamente indisponível';
    const methods = context.create({
        Gio, GLib,
        Me: {}, Utils: {},
        getData: () => "/usr/bin/python3 '/user-data/orbitz-widgets/collectors/currency-widget.py' --quote USD",
        readCommandOutput: async () => [response, ''],
        stopCommandRun: () => {},
    });
    const host = {
        ...methods,
        _networkDestroyed: false,
        _networkDialog: {visible: true},
        _networkGeneration: 0,
        _networkRefreshRun: null,
        _networkRefreshButton: {reactive: true, label: '', accessible_name: ''},
        _networkRefreshStatus: {text: ''},
        _currencyRateLabel: {text: ''},
        clutter_text: {set_markup: value => { host.markup = value; }},
        text: '1 BRL → 5.00 USD',
        widgetIndex: 0,
        elementIndex: 1,
    };
    await methods._refreshCurrencyDialog.call(host);
    assert.equal(host._currencyRateLabel.text, response);
    assert.equal(host.text, response);
    assert.equal(host._networkRefreshStatus.text, 'A consulta falhou. Tente novamente.');
    assert.equal(host._networkRefreshStatus.text.includes('Atualizado às'), false);
    console.log('OK: FX error output replaces the previous value and is never reported with a success timestamp.');
})().catch(error => { console.error(error); process.exitCode = 1; });

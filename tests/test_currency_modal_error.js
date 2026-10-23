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
    let response = JSON.stringify({error: 'serviço temporariamente indisponível'});
    let command="/usr/bin/python3 '/user-data/orbitz-widgets/collectors/currency-widget.py' --quote USD";
    const methods = context.create({Language: require('./helpers/ui_language').create({Gio},'pt-BR'),
        Gio, GLib,
        Me: {}, Utils: {},
        getData: () => command,
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
    assert.equal(host._currencyRateLabel.text, 'Cotação indisponível · serviço temporariamente indisponível');
    assert.equal(host.text, host._currencyRateLabel.text);
    assert.equal(host._networkRefreshStatus.text, 'serviço temporariamente indisponível');
    assert.equal(host._networkRefreshStatus.text.includes('Atualizado às'), false);
    class Actor {
        constructor(props = {}) {
            Object.assign(this, props); this.children = []; this.signals = {};
            this.clutter_text = {set_line_wrap() {}, set_ellipsize() {}, set_max_length() {},
                connect: (signal, fn) => { this.signals[signal] = fn; }};
        }
        add_child(child) { this.children.push(child); }
        set_child(child) { this.child = child; }
        add_constraint() {}
        connect(signal, fn) { this.signals[signal] = fn; }
        get_text() { return this.text; }
    }
    const ui = context.create({Language: require('./helpers/ui_language').create({Gio},'pt-BR'), Gio, GLib, getData: () => command,
        St: {Widget: Actor, BoxLayout: Actor, Label: Actor, Button: Actor, Icon: Actor, Entry: Actor},
        Clutter: {BindConstraint: class {}, BindCoordinate: {ALL: 0}, ActorAlign: {CENTER: 0}},
        Pango: {EllipsizeMode: {NONE: 0}}, global: {stage: {}}, Main: {uiGroup: new Actor()}});
    const built = {...ui};
    built._buildCurrencyDialog();
    built._currencyQuote = {base:'BRL', quote:'USD', rate:'0.19829'};
    built._currencyAmountEntry.text = '100';
    built._currencyAmountEntry.signals['text-changed']();
    assert.equal(built._currencyTotalLabel.text, 'Total: 19,83 USD');
    assert(built._networkDialog.children.includes(built._currencyAmountEntry));
    let amount = '1.000,50';
    host._currencyAmountEntry = {get_text: () => amount};
    host._currencyTotalLabel = {text: ''};
    response = JSON.stringify({base:'BRL', quote:'USD', rate:'0.19829'});
    await host._refreshCurrencyDialog();
    assert.equal(host.text, '1 BRL → 0,20 USD');
    assert.equal(host._currencyTotalLabel.text, 'Total: 198,39 USD');
    for (const [input, expected] of [['0','0,00'], ['10.50','2,08'], ['1.000','198,29'], ['0,005','0,00']]) {
        amount = input; host._updateCurrencyCalculation();
        assert.equal(host._currencyTotalLabel.text, `Total: ${expected} USD`);
    }
    for (const input of ['', '-1', 'NaN', 'Infinity', '1,2,3', '1e3']) {
        amount = input; host._updateCurrencyCalculation();
        assert(!host._currencyTotalLabel.text.startsWith('Total:'));
    }
    amount = '2';
    assert.equal(host._currencyProduct('100000', '0.000016273845678'), '1,63');
    assert.equal(host._currencyProduct('2', '83060.16777893'), '166.120,34');
    assert.equal(host._currencyProduct('1', '1.005'), '1,01');
    assert.equal(host._currencyProduct('100', '1e-8'), '0,00');
    command="/usr/bin/python3 '/user-data/orbitz-widgets/collectors/currency-widget.py' --mode crypto --asset btc-bitcoin";
    host._currencySourceLabel={text:''};host._currencyDirectionButton={};
    host._updateCurrencyDirectionButton(command);
    assert.equal(host._currencyDirectionButton.label,'Inverter: USD → BTC');
    assert.equal(host._currencyCommandInfo(command).quote,'btc-bitcoin');
    host._updateCurrencyDirectionButton(command+' --reverse');
    assert.equal(host._currencyDirectionButton.label,'Inverter: BTC → USD');
    host._updateCurrencyDirectionButton(command);
    response=JSON.stringify({base:'USD',quote:'BTC',rate:'0.000016273845678',asset:'btc-bitcoin',updated_at:'2026-10-21T12:00:00Z'});
    await host._refreshCurrencyDialog();
    assert.equal(host.text, '1 USD → 0,00 BTC');
    amount = '400'; host._updateCurrencyCalculation();
    assert.equal(host._currencyTotalLabel.text, 'Total: 0,0065095382712 BTC');
    assert.equal(host._currencyProduct('100', '1e-18', true), '0,0000000000000001');
    assert.equal(host._currencyProduct('2', '83060.16777893', true), '166.120,33555786');
    assert.equal(host._currencyProduct('0', '1e-18', true), '0');
    assert.equal(host._currencyProduct('2.50', '4', true), '10');
    assert.equal(host._currencyProduct('2', '1e3', true), '2.000');
    for (const [rate, expected] of [['83060.16777893', '83.060,17'], ['5.5', '5,50'], ['1.005', '1,01'], ['999.999', '1.000,00']]) {
        response=JSON.stringify({base:'BTC',quote:'USD',rate,asset:'btc-bitcoin',updated_at:'2026-10-21T12:00:00Z'});
        await host._refreshCurrencyDialog();
        assert.equal(host.text, `1 BTC → ${expected} USD`);
        assert.equal(host._currencyTotalLabel.text, `Total: ${host._currencyProduct(amount, rate, true)} USD`);
    }
    assert(host._currencySourceLabel.text.includes('Powered by CoinPaprika · 2026-10-21T12:00:00Z'));
    response=JSON.stringify({error:'Sem preço atual disponível'});
    await host._refreshCurrencyDialog();
    assert.equal(host.text,'Cotação indisponível · Sem preço atual disponível');
    assert.equal(host._currencySourceLabel.text,'Powered by CoinPaprika');
    assert.equal(host._currencyQuote, null);
    assert(!host._currencyTotalLabel.text.startsWith('Total:'));
    console.log('OK: calculator uses full rate, localized input, invalid input and error clearing.');
    console.log('OK: crypto cents display, attribution/timestamp and error removes stale quote.');
    console.log('OK: FX error output replaces the previous value and is never reported with a success timestamp.');
})().catch(error => { console.error(error); process.exitCode = 1; });

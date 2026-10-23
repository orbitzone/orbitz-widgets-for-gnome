const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('extension/extension.js', 'utf8');
const start = source.indexOf('    _closeNetworkDialog() {');
const end = source.indexOf('    async _refreshNetworkDialog()', start);
assert(start >= 0 && end > start, 'shared modal close method exists');

let popFails = true;
let grabActive = true;
let pushError = null;
let pushResult = 'new-grab';
const logged = [];
const stopped = [];
const removed = [];
const scope = vm.createContext({
    Main: {
        pushModal() {
            assert.equal(grabActive, false, 'a new modal can open after the old actor was dismissed');
            if (pushError) throw pushError;
            if (pushResult) grabActive = true;
            return pushResult;
        },
        popModal(token) {
            assert(['grab', 'new-grab'].includes(token));
            if (!grabActive) throw Error('Incorrect pop() call: modal token is stale');
            grabActive = false;
            if (popFails) throw Error('synthetic modal pop failure');
        },
    },
    Shell: {ActionMode: {POPUP: 1}},
    GLib: {source_remove(id) { removed.push(id); }},
    stopCommandRun(run) { if (run) { stopped.push(run); if (run.fail) throw Error('synthetic process cancellation failure'); } },
    logError(error, context) { logged.push([error.message, context]); },
});
vm.runInContext(`this.Host = class {\n${source.slice(start, end)}\n}`, scope);

const host = Object.assign(new scope.Host(), {
    _networkModalGrab: 'grab', _networkRefreshRun: {id: 'refresh', fail: true}, _speedtestRun: {id: 'speedtest'},
    _networkRefreshTimeout: 11, _speedtestTimeout: 12,
    _networkInspecting: true, _networkConnectionSignature: 'old', _networkGeneration: 7,
    _networkDialog: {visible: true, hide() { this.visible = false; }},
    _networkBackdrop: {visible: true, reactive: true, hide() { this.visible = false; }},
    _cancelFirewallInspection() { throw Error('synthetic firewall cancellation failure'); },
    _weatherClose() { throw Error('synthetic weather cleanup failure'); },
});
// GNOME can dismiss the modal actor before its owner closes it. Its subsequent
// pop throws after the Shell has already returned input to the desktop.
grabActive = false;
host._closeNetworkDialog();
assert.equal(host._networkDialog.visible, false, 'modal error does not leave visible dialog');
assert.equal(host._networkBackdrop.visible, false, 'modal error does not leave an input-blocking backdrop');
assert.equal(host._networkBackdrop.reactive, false, 'backdrop is made non-reactive before hiding');
assert.equal(grabActive, false, 'incorrect pop leaves no active Shell grab');
assert.equal(host._networkModalGrab, null, 'incorrect-pop token is discarded');
assert.equal(host._networkInspecting, false);assert.equal(host._networkConnectionSignature, null);assert.equal(host._networkGeneration, 8);
assert.equal(host._networkRefreshTimeout, null);assert.equal(host._speedtestTimeout, null);
assert.deepEqual(removed, [11, 12], 'both dialog timers are removed despite earlier errors');
assert.equal(stopped.length, 2, 'both dialog-owned commands are cancelled despite one failure');
assert.deepEqual(logged.map(item => item[0]), [
    'Incorrect pop() call: modal token is stale', 'synthetic firewall cancellation failure', 'synthetic weather cleanup failure',
    'synthetic process cancellation failure',
]);
assert.equal(host._networkModalGrab, null, 'all pop attempts discard tokens after Shell mutates its modal stack');

popFails = true;
host._networkModalGrab = scope.Main.pushModal();
assert.equal(host._networkModalGrab, 'new-grab', 'reopening after stale-token cleanup pushes a fresh modal');
host._closeNetworkDialog();
assert.equal(host._networkModalGrab, null, 'failed pop token is never retried after stack mutation');
assert.equal(grabActive, false, 'GNOME pop failure mutated the modal stack before throwing');
assert.equal(host._networkBackdrop.reactive, false);assert.equal(host._networkBackdrop.visible, false);
popFails = false;

const openHost = Object.assign(new scope.Host(), {
    _networkBackdrop: {visible: false, reactive: false, show() { this.visible = true; }, hide() { this.visible = false; }},
    _networkModalGrab: null,
});
openHost._pushNetworkModal();
assert.equal(openHost._networkBackdrop.visible, true);
assert.equal(openHost._networkBackdrop.reactive, true);
assert.equal(openHost._networkModalGrab, 'new-grab');
grabActive = false;
openHost._networkModalGrab = null;
pushError = Error('synthetic push failure');
assert.throws(() => openHost._pushNetworkModal(), /synthetic push failure/);
assert.equal(openHost._networkBackdrop.visible, false, 'failed grab hides the backdrop');
assert.equal(openHost._networkBackdrop.reactive, false, 'failed grab cannot intercept input');
assert.equal(openHost._networkModalGrab, null, 'failed grab leaves no stale local token');
pushError = null;
pushResult = null;
assert.throws(() => openHost._pushNetworkModal(), /não criou o grab modal/);
assert.equal(openHost._networkBackdrop.visible, false, 'missing grab hides the backdrop');
assert.equal(openHost._networkBackdrop.reactive, false, 'missing grab cannot intercept input');
pushResult = 'new-grab';

const destroyHook = source.match(/this\._networkBackdrop\.connect\('destroy', \(\) => \{[^}]+\}\);/);
assert(destroyHook, 'backdrop destruction synchronizes the modal token');
const callback = {};
const owner = {_networkBackdrop: {connect(name, fn) { assert.equal(name, 'destroy'); callback.destroy = fn; }}, _networkModalGrab: 'auto-dismissed'};
vm.runInContext(`(function() { ${destroyHook[0]} }).call(owner)`, vm.createContext({owner}));
callback.destroy();
assert.equal(owner._networkModalGrab, null, 'destroyed backdrop cannot leave an obsolete modal token');
assert.equal(grabActive, false, 'reopening after stale-token cleanup leaves shell input available');
console.log('OK: stale modal tokens are discarded after pop/destroy; callbacks cannot skip backdrop or work cleanup.');

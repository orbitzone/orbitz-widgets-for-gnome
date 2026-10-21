const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('extension/worldClock.js', 'utf8');
const context = vm.createContext({});
vm.runInContext(source, context);
const formatter = context.WorldClock.format;
const isTimeFormat = context.WorldClock.isTimeFormat;

let requestedZone = null;
const GLib = {
    TimeZone: {
        new(identifier) {
            requestedZone = identifier;
            return identifier === 'America/New_York' || identifier === 'UTC'
                ? {get_identifier: () => identifier}
                : {get_identifier: () => 'UTC'};
        },
    },
    DateTime: {
        new_now(zone) {
            return {format: pattern => `${zone.get_identifier()} ${pattern}`};
        },
    },
};

assert.equal(formatter(GLib, 'America/New_York', '%H:%M'), 'America/New_York %H:%M');
assert.equal(requestedZone, 'America/New_York');
assert.equal(formatter(GLib, 'UTC'), 'UTC %H:%M');
assert.equal(formatter(GLib, 'Not/A_Zone'), '');
assert.equal(formatter(GLib, ''), '');
assert.equal(isTimeFormat('%H∶%M∶%S'), true);
assert.equal(isTimeFormat('%A %b %d'), false);
console.log('OK: world clock formats the selected timezone and rejects unknown identifiers.');

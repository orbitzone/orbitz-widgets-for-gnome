const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const context = vm.createContext({});
vm.runInContext(fs.readFileSync('extension/settings/timeZoneCatalog.js', 'utf8'), context);
const catalog = context.TimeZoneCatalog;
const entries = catalog.parse([
    '# zone.tab fixture',
    'BR\t-2332-04637\tAmerica/Sao_Paulo\tSao Paulo',
    'US\t+404251-0740023\tAmerica/New_York\tNew York',
    'GB\t+513030-0000731\tEurope/London\tLondon',
    'bad\tline',
].join('\n'));

assert.equal(entries.length, 4);
assert.deepEqual(Array.from(catalog.search(entries, 'sao paulo'), item => item.identifier), ['America/Sao_Paulo']);
assert.deepEqual(Array.from(catalog.search(entries, 'europe'), item => item.city), ['London']);
assert.deepEqual(Array.from(catalog.search(entries, 'new_york'), item => item.city), ['New York']);
assert.deepEqual(Array.from(catalog.search(entries, '').map(item => item.identifier)), []);
console.log('OK: timezone catalog lists named regions/cities and searches by city, region, or identifier.');

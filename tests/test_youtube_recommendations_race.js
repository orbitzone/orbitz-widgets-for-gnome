const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('extension/youtube-widget/index.html', 'utf8');
const start = html.indexOf('async function loadRecommendations(){');
const end = html.indexOf("$('query').addEventListener('input'", start);
assert(start >= 0 && end > start, 'recommendation loader is present');

let resolveRecommendations;
const results = { items: [], replaceChildren(...items) { this.items = items; } };
const status = {};
const query = { value: '' };
const context = vm.createContext({
  $: id => ({ results, status, query })[id],
  api: () => new Promise(resolve => { resolveRecommendations = resolve; }),
  renderResults(items) { results.items = items; },
  uiPrune() {}, uiText(_node, key) { status.key = key; }, uiErrorText() {},
  openSettings() {},
});
vm.runInContext(`let sequence=0,activeTab='videos';${html.slice(start, end)};globalThis.setTabForTest=tab=>{++sequence;activeTab=tab};`, context);
context.loadRecommendations();
context.setTabForTest('shorts');
resolveRecommendations({ items: [{ id: 'abcdefghijk' }] });

Promise.resolve().then(() => Promise.resolve()).then(() => {
  assert.deepEqual(results.items, [], 'stale recommendations do not appear in another tab');
  assert.equal(status.key, 'youtube.loading_recommendations', 'stale completion leaves the active tab hint unchanged');
  console.log('OK: delayed recommendations cannot overwrite Shorts or Live results.');
}).catch(error => { console.error(error); process.exitCode = 1; });

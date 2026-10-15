const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync(require('path').join(__dirname, '../extension/extension.js'), 'utf8');
const start = source.indexOf('async function readCommandOutput(');
const end = source.indexOf('const DEBUG_LOG', start);
let stops = 0;
const active = new Set();
const context = {activeCommandRuns: active, collectorBirth: () => '123', GLib: {PRIORITY_DEFAULT: 0}, TextDecoder, TextEncoder, Uint8Array,
    stopCommandRun: async run => { stops++; run.cancelled = true; }};
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);
const pipe = text => {
    let first = true;
    return {async read_bytes_async() {
        const data = first ? new TextEncoder().encode(text) : new Uint8Array();
        first = false;
        return {get_data: () => data};
    }};
};
const runWith = (stdout, stderr, wait = async () => {}) => ({cancellable: {}, proc: {
    get_identifier: () => '42', get_stdout_pipe: () => stdout, get_stderr_pipe: () => stderr, wait_async: wait,
}});
(async () => {
    const ok = runWith(pipe('hello'), pipe('warning'));
    const result = await context.readCommandOutput(ok);
    assert.equal(result[0], 'hello'); assert.equal(result[1], 'warning');
    assert.equal(stops, 0); assert.equal(active.size, 0);
    const broken = runWith({async read_bytes_async() {throw new Error('broken pipe');}}, pipe(''));
    await assert.rejects(context.readCommandOutput(broken), /broken pipe/);
    assert(broken.cancelled); assert.equal(active.size, 0);
    const oversized = runWith(pipe('x'.repeat(262145)), pipe(''));
    await assert.rejects(context.readCommandOutput(oversized), /256 KiB/);
    assert(oversized.outputLimit); assert(oversized.cancelled); assert.equal(active.size, 0);
    const failedWait = runWith(pipe(''), pipe(''), async () => {throw new Error('wait failed');});
    await assert.rejects(context.readCommandOutput(failedWait), /wait failed/);
    assert(failedWait.cancelled); assert.equal(active.size, 0);
    console.log('OK: successful reads, pipe failure, output cap and wait failure clean up tracked runs.');
})().catch(error => {console.error(error); process.exitCode = 1;});

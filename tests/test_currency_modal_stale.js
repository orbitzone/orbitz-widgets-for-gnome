const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx=vm.createContext({});vm.runInContext(fs.readFileSync('extension/panels/currency.js','utf8'),ctx);
const fiat='/usr/bin/python3 /synthetic/currency-widget.py --quote USD';
const crypto='/usr/bin/python3 /synthetic/currency-widget.py --mode crypto --asset btc-bitcoin';
function fixture(){
 let command=fiat,resolve,reject;const timers=new Map();let next=0;
 const GLib={shell_parse_argv:c=>[true,c.split(' ')],PRIORITY_DEFAULT:0,SOURCE_REMOVE:0,
  timeout_add:(priority,ms,fn)=>{timers.set(++next,fn);return next;},source_remove:id=>timers.delete(id),
  markup_escape_text:x=>x,DateTime:{new_now_local:()=>({format:()=> '12:00'})}};
 const methods=ctx.create({Language: {...require('./helpers/ui_language').create(ctx,'pt-BR'), spawn:()=>({get_successful:()=>true})}, GLib,Gio:{Cancellable:class{},SubprocessFlags:{STDOUT_PIPE:1,STDERR_PIPE:2},
  Subprocess:{new:()=>({get_successful:()=>true})}},getData:()=>command,
  readCommandOutput:()=>new Promise((a,b)=>{resolve=a;reject=b;}),stopCommandRun:run=>{run.cancelled=true;}});
 const writes=[];const host={...methods,widgetIndex:0,elementIndex:1,_networkGeneration:1,
  _networkDialog:{visible:true},_networkRefreshButton:{},_networkRefreshStatus:{},_currencyRateLabel:{},
  _currencySourceLabel:{text:''},clutter_text:{set_markup:text=>writes.push(text)},text:'initial'};
 return {host,writes,timers,setCommand:c=>command=c,complete:value=>resolve([JSON.stringify(value),'']),fail:()=>reject(new Error('late failed process'))};
}
const fiatQuote={base:'BRL',quote:'USD',rate:'0.2'};
const cryptoQuote={base:'USD',quote:'BTC',rate:'0.00001',asset:'btc-bitcoin',updated_at:'2026-10-21T12:00:00Z'};
(async()=>{
 for(const failure of [false,true]){
  const f=fixture(),pending=f.host._refreshCurrencyDialog();
  f.setCommand(crypto);f.host.text='1 USD → 0.00001 BTC';
  if(failure)f.fail();else f.complete(fiatQuote);
  await pending;
  assert.equal(f.host.text,'1 USD → 0.00001 BTC','late fiat output/error cannot replace current desktop text');
  assert.equal(f.writes.length,0);assert.equal(f.host._currencyQuote,null);
  assert.equal(f.host._currencySourceLabel.text,'');
  assert(!f.host._networkRefreshStatus.text.includes('Atualizado às'));
  assert.equal(f.host._networkRefreshButton.reactive,true);assert.equal(f.host._networkRefreshRun,null);assert.equal(f.timers.size,0);
  assert(f.host._currencyRateLabel.text.includes('Configuração alterada'));
 }
 for(const [command,quote,symbol] of [[fiat,fiatQuote,'BRL'],[crypto,cryptoQuote,'BTC']]){
  const f=fixture();f.setCommand(command);const pending=f.host._refreshCurrencyDialog();f.complete(quote);await pending;
  assert(f.host.text.includes(symbol));assert.equal(f.writes.length,1);
  assert(f.host._networkRefreshStatus.text.includes('Atualizado às'));
  assert.equal(f.host._networkRefreshRun,null);assert.equal(f.timers.size,0);
 }
 // Existing cancellation/generation guards must still discard matching-command results.
 for(const invalidate of [f=>{f.host._networkRefreshRun.cancelled=true;},f=>{f.host._networkGeneration++;}]){
  const f=fixture(),pending=f.host._refreshCurrencyDialog();invalidate(f);f.complete(fiatQuote);await pending;
  assert.equal(f.writes.length,0);assert.equal(f.host.text,'initial');assert.equal(f.timers.size,0);
 }
 // The watchdog still reports a timeout for the current command, but never for a stale one.
 for(const stale of [false,true]){
  const f=fixture(),pending=f.host._refreshCurrencyDialog();
  if(stale){f.setCommand(crypto);f.host.text='current crypto';}
  const [id,watchdog]=f.timers.entries().next().value;f.timers.delete(id);watchdog();f.fail();await pending;
  if(stale){assert.equal(f.host.text,'current crypto');assert.equal(f.writes.length,0);}
  else assert(f.host.text.includes('A consulta demorou demais'));
  assert.equal(f.host._networkRefreshRun,null);assert.equal(f.host._networkRefreshButton.reactive,true);assert.equal(f.timers.size,0);
 }
 console.log('OK: delayed fiat output/error cannot overwrite crypto; valid fiat/crypto, cancellation/generation and cleanup preserved.');
})().catch(error=>{console.error(error);process.exitCode=1;});

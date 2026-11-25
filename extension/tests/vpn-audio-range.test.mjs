import test from 'node:test';
import assert from 'node:assert/strict';
await import('../dist/unpacked/player/replacement-player.js');
const {ReplacementPlayer}=globalThis.__CELIKOM_REPLACEMENT_PLAYER_V1__;
const flush=async()=>{for(let i=0;i<50;i++)await Promise.resolve()};
function fixture({fault=()=>null,fast=true}={}){
 const bytes=Uint8Array.from({length:66560},(_,i)=>i%251),requests=[],appended=[];let pauses=0;
 class Buffer extends EventTarget{constructor(){super();this.buffered={length:0}}appendBuffer(data){appended.push(new Uint8Array(data));queueMicrotask(()=>this.dispatchEvent(new Event('updateend')))}}
 const source={readyState:'open',addSourceBuffer:()=>new Buffer(),endOfStream(){this.readyState='ended'}};
 const audio={dataset:{},currentTime:0,paused:false,muted:false,addEventListener(){},pause(){pauses++}};
 const env={document:{createElement:()=>audio},AbortController,setTimeout:(fn,ms)=>setTimeout(fn,fast&&[500,1000].includes(ms)?1:ms),clearTimeout,
  fetch:async(url,options)=>{
   const [,a,b]=/^bytes=(\d+)-(\d+)$/.exec(options.headers.Range),from=Number(a),last=Math.min(Number(b),bytes.length-1);
   requests.push({from,last,url});assert.equal(options.credentials,'omit');assert.equal(options.cache,'no-store');
   const f=fault(from,requests.filter(x=>x.from===from).length);
   if(f==='headers')throw new TypeError('VPN route reset');
   if(f==='slow503')await new Promise((resolve,reject)=>{const timer=setTimeout(resolve,7000);options.signal.addEventListener('abort',()=>{clearTimeout(timer);reject(new DOMException('Aborted','AbortError'))},{once:true})});
   const status=typeof f==='number'?f:f==='slow503'?503:206;
   return {status,headers:new Headers({'content-type':status===206?'audio/mpeg':'application/json','content-range':`bytes ${from}-${last}/${bytes.length}`}),body:{cancel:async()=>{}},arrayBuffer:async()=>{
    if(f==='body')throw new TypeError('VPN body interrupted');
    if(f==='short')return new ArrayBuffer(1);
    return bytes.slice(from,last+1).buffer;
   }};
  }};
 const player=new ReplacementPlayer(env,()=>{});player.mediaSource=source;player.fetchAbort=new AbortController();audio.muted=false;player.wantPlay=true;
 return {player,source,bytes,requests,appended,audio,get pauses(){return pauses},run:()=>player.pumpRemote({url:'https://fixture.invalid/api/v1/audio/1?token=fixture',durationMs:200000})};
}
for(const failure of ['headers','body'])test('buffered MP3 survives VPN '+failure+' reset by retrying only the unappended range',async()=>{
 const f=fixture({fault:(from,n)=>from===65536&&n===1?failure:null});await f.run();
 assert.deepEqual(f.requests.map(x=>x.from),[0,65536,65536]);assert.equal(f.appended.length,2);
 const result=new Uint8Array(66560);let offset=0;for(const part of f.appended){result.set(part,offset);offset+=part.length}
 assert.deepEqual(result,f.bytes);assert.equal(f.player.streamState.networkRetries,1);
 assert.equal(f.pauses,0);assert.equal(f.audio.muted,false);assert.equal(f.source.readyState,'ended');
});
test('network retries are bounded and revoked/malformed audio is never retried or appended',async()=>{
 const f=fixture({fault:()=> 'headers'});await assert.rejects(f.run(),/remote-stream-network/);assert.equal(f.requests.length,3);assert.equal(f.appended.length,0);
 for(const fault of [401,403,'short']){
  const f=fixture({fault:()=>fault});await assert.rejects(f.run(),fault==='short'?/remote-stream-range/:/remote-stream-http/);
  assert.equal(f.requests.length,1);assert.equal(f.appended.length,0);
 }
});
test('all retries share the original fifteen-second range deadline',async t=>{
 t.mock.timers.enable({apis:['Date','setTimeout'],now:1000000});const f=fixture({fault:()=> 'slow503',fast:false});
 const task=assert.rejects(f.run(),/remote-stream-timeout/);await flush();
 t.mock.timers.tick(7000);await flush();t.mock.timers.tick(500);await flush();t.mock.timers.tick(7000);await flush();
 assert.equal(f.requests.length,2);t.mock.timers.tick(500);await flush();await task;
 assert.equal(f.player.streamState.phase,'timeout');assert.equal(f.requests.length,2);
});
test('Stop during range retry wait cancels it without another download',async t=>{
 t.mock.timers.enable({apis:['Date','setTimeout'],now:1000000});const f=fixture({fault:()=> 'headers',fast:false});
 const task=f.run();await flush();assert.equal(f.requests.length,1);
 f.player.destroyed=true;f.player.fetchAbort.abort();await flush();await task;
 t.mock.timers.tick(20000);await flush();assert.equal(f.requests.length,1);assert.equal(f.appended.length,0);
});

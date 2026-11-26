import test from 'node:test';
import assert from 'node:assert/strict';
await import('../dist/unpacked/player/core.js');
await import('../dist/unpacked/player/sync-engine.js');
await import('../dist/unpacked/player/replacement-player.js');
await import('../dist/unpacked/player/fail-open-controller.js');
await import('../dist/unpacked/player/replacement-controller.js');
const {ReplacementPlayer}=globalThis.__CELIKOM_REPLACEMENT_PLAYER_V1__;
const {ReplacementController}=globalThis.__CELIKOM_REPLACEMENT_CONTROLLER_V1__;
const flush=async()=>{for(let i=0;i<60;i++)await Promise.resolve();};

// Transport and media decoding are controlled independently. The production
// controller/player run unchanged; no production endpoint or account is used.
function fixture(t, firstHeadersDelay, {bodyDelay=0, decode=false, status=206}={}) {
  t.mock.timers.enable({apis:['Date','setTimeout'],now:1000000});
  let requests=0, aborted=0, source, current;
  const players=[],fatals=[],bridgeRequests=[];
  class Audio extends EventTarget {
    constructor(){super();this.dataset={};this.readyState=0;this.duration=200;this.currentTime=7;this.paused=true;this.muted=true;this.volume=1;this.seeking=false;}
    load(){if(source?.readyState==='closed')queueMicrotask(()=>{source.readyState='open';source.dispatchEvent(new Event('sourceopen'));});}
    play(){this.paused=false;return Promise.resolve();}
    pause(){this.paused=true;}
    removeAttribute(){}
    remove(){}
  }
  class Buffer extends EventTarget {
    constructor(){super();this.buffered={length:0};}
    appendBuffer(){queueMicrotask(()=>{const audio=players.at(-1).audio;if(!decode){audio.readyState=4;audio.dispatchEvent(new Event('canplay'));}this.dispatchEvent(new Event('updateend'));});}
  }
  class Source extends EventTarget {
    static isTypeSupported(){return true;}
    constructor(){super();source=this;this.readyState='closed';}
    addSourceBuffer(){return new Buffer();}
    endOfStream(){this.readyState='ended';}
  }
  const environment={
    document:{hidden:false,createElement:()=>new Audio(),documentElement:{append(){}}},
    setTimeout,clearTimeout,AbortController,MediaSource:Source,
    URL:{createObjectURL:()=> 'blob:test',revokeObjectURL(){}},
    fetch:async(_url,options)=>{
      requests++;
      if(requests===1&&firstHeadersDelay)await new Promise((resolve,reject)=>{
        const timer=setTimeout(resolve,firstHeadersDelay);
        options.signal.addEventListener('abort',()=>{aborted++;clearTimeout(timer);reject(new DOMException('Aborted','AbortError'));},{once:true});
      });
      return {status,body:{cancel:async()=>{}},headers:new Headers({'content-type':'audio/mpeg','content-range':'bytes 0-1023/1024'}),arrayBuffer:async()=>{if(bodyDelay)await new Promise((resolve,reject)=>{const timer=setTimeout(resolve,bodyDelay);options.signal.addEventListener('abort',()=>{clearTimeout(timer);reject(new DOMException('Aborted','AbortError'));},{once:true});});return new ArrayBuffer(1024);}};
    }
  };
  const bridge={sessionId:'startup',isHealthy:()=>true,post(){},getSnapshot:async()=>current,request:async(type)=>{bridgeRequests.push(type);return {snapshot:current,released:true};}};
  const asset={found:true,url:'https://fixture.invalid/audio',mimeType:'audio/mpeg',durationMs:200000,expiresAt:2000000};
  const engine=new ReplacementController(bridge,environment,{resolveAsset:async()=>asset,createPlayer:fatal=>{
    const p=new ReplacementPlayer(environment,(...args)=>{fatals.push(args);fatal(...args);});players.push(p);return p;
  }});
  function update(){current={observedAt:Date.now(),track:{id:'144530503',confidence:240,ambiguous:false,metadata:{durationMs:200000}},player:{mediaId:'media-2',paused:false,ended:false,seeking:false,readyState:4,currentTime:(Date.now()-1000000)/1000+7,duration:200,volume:1,muted:false,playbackRate:1}};engine.update(current);}
  engine.configure(true,'');update();
  t.after(()=>engine.destroy());
  return {engine,players,fatals,bridgeRequests,update,get requests(){return requests;},get aborted(){return aborted;},async advance(ms){t.mock.timers.tick(ms);update();await flush();}};
}

test('eleven-second first headers activate on the first attempt without a toggle',async t=>{
  const f=fixture(t,11000);await flush();
  await f.advance(10000);
  assert.equal(f.engine.phase,'PREPARING');assert.equal(f.engine.lastError,null);
  assert.equal(f.aborted,0);assert.equal(f.requests,1);
  assert.equal(f.bridgeRequests.includes('GUARD_ENGAGE'),false,'initial original keeps playing while downloading');
  await f.advance(1000);
  assert.equal(f.engine.activationCount,1);assert.equal(f.engine.phase,'REPLACEMENT_ACTIVE');
  assert.equal(f.requests,1);assert.equal(f.engine.restoreCount,0);
});

test('stalled first headers hit the transport deadline and retry automatically',async t=>{
  const f=fixture(t,16000);await flush();await f.advance(15000);
  assert.equal(f.engine.lastError,'remote-stream-timeout');
  assert.equal(f.engine.lastRestore.detail.receivedBytes,0);
  assert.equal(f.engine.lastRestore.detail.httpStatus,null);
  assert.equal(f.aborted,1);assert.equal(f.players[0].destroyed,true);
  assert.equal(f.bridgeRequests.includes('GUARD_ENGAGE'),false);
  await f.advance(4999);assert.equal(f.requests,1);
  await f.advance(1);assert.equal(f.requests,2);
  assert.equal(f.engine.activationCount,1);assert.equal(f.engine.phase,'REPLACEMENT_ACTIVE');
});

test('nine-second headers successfully activate without a manual toggle',async t=>{
  const f=fixture(t,9000);await flush();await f.advance(9000);
  assert.equal(f.requests,1);assert.equal(f.engine.activationCount,1);
  assert.equal(f.engine.lastError,null);assert.equal(f.engine.phase,'REPLACEMENT_ACTIVE');
});

test('Stop after startup timeout prevents the queued automatic retry',async t=>{
  const f=fixture(t,16000);await flush();await f.advance(15000);
  assert.equal(f.engine.lastError,'remote-stream-timeout');
  f.engine.configure(false,'');await f.advance(20000);
  assert.equal(f.requests,1);assert.equal(f.engine.operation,null);assert.equal(f.engine.activationCount,0);
});


test('first body keeps the same transport budget instead of spending decoder time',async t=>{
  const f=fixture(t,9000,{bodyDelay:2000});await flush();await f.advance(9000);await f.advance(2000);
  assert.equal(f.engine.activationCount,1);assert.equal(f.requests,1);assert.equal(f.engine.lastError,null);
});

test('decoder gets ten seconds after first verified append and cannot hang forever',async t=>{
  const f=fixture(t,11000,{decode:true});await flush();await f.advance(11000);
  assert.equal(f.engine.phase,'PREPARING');await f.advance(9999);assert.equal(f.engine.phase,'PREPARING');
  await f.advance(1);assert.equal(f.engine.lastError,'replacement-load-timeout');
  assert.equal(f.players[0].destroyed,true);assert.equal(f.engine.activationCount,0);
});

test('Stop during delayed first headers aborts the request with no late activation',async t=>{
  const f=fixture(t,11000);await flush();await f.advance(7000);f.engine.configure(false,'');await flush();await f.advance(20000);
  assert.equal(f.aborted,1);assert.equal(f.requests,1);assert.equal(f.engine.operation,null);assert.equal(f.engine.activationCount,0);
});

test('revoked audio is rejected immediately and never enters automatic network retry',async t=>{
  const f=fixture(t,0,{status:403});await flush();
  assert.equal(f.engine.lastError,'remote-stream-http');assert.equal(f.engine.retryBlock,null);
  assert.equal(f.players[0].destroyed,true);await f.advance(20000);
  assert.equal(f.requests,1);assert.equal(f.engine.activationCount,0);
});

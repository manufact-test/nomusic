import assert from 'node:assert/strict';
import test from 'node:test';
await import('../dist/unpacked/player/sync-engine.js');
await import('../dist/unpacked/player/replacement-player.js');
const {ReplacementPlayer}=globalThis.__CELIKOM_REPLACEMENT_PLAYER_V1__;

function fixture(t,{delays=[1800,15],seeking=false}={}){
 let clock=10000,writes=0;const timers=new Map();let timerId=0;
 t.mock.method(Date,'now',()=>clock);
 class Audio extends EventTarget{
  constructor(){super();this.dataset={};this.position=0;this.duration=200;this.readyState=4;this.paused=true;this.muted=true;this.seeking=false;}
  get currentTime(){return this.position;}
  set currentTime(value){this.position=value;this.seeking=true;this.readyState=2;writes++;
   queueMicrotask(()=>{clock+=delays[writes-1]??15;this.seeking=false;this.readyState=4;this.dispatchEvent(new Event('seeked'));});
  }
  pause(){this.paused=true;}load(){}removeAttribute(){}remove(){}
 }
 const environment={document:{createElement:()=>new Audio()},setTimeout(fn,ms){const id=++timerId;timers.set(id,{fn,ms});return id;},clearTimeout(id){timers.delete(id);}};
 const player=new ReplacementPlayer(environment,()=>{});
 const snapshot=()=>({observedAt:clock,track:{id:'42'},player:{currentTime:42+(clock-10000)/1000,duration:200,paused:false,seeking,readyState:4,playbackRate:1}});
 return{player,snapshot,timers,writes:()=>writes};
}
test('newly approved MP3 waits for missing middle bytes and realigns the same decoder to a fresh native clock',async t=>{
 const f=fixture(t);await f.player.prepareJoin(f.snapshot(),async()=>f.snapshot());
 assert.equal(f.writes(),2,'cold seek is followed by one completed-seek alignment, not a new download');
 assert.ok(Math.abs(f.player.audio.currentTime-f.snapshot().player.currentTime)<.1);
 assert.equal(f.player.audio.muted,true);assert.equal(f.player.audio.paused,true);assert.equal(f.timers.size,0);
});

test('already buffered approval joins once without delaying an aligned decoder',async t=>{
 const f=fixture(t,{delays:[10]});await f.player.prepareJoin(f.snapshot(),async()=>f.snapshot());
 assert.equal(f.writes(),1);assert.equal(f.timers.size,0);
});
test('a continually lagging decoder has bounded alignment attempts and releases listeners',async t=>{
 const f=fixture(t,{delays:[500,500,500]});
 await assert.rejects(f.player.prepareJoin(f.snapshot(),async()=>f.snapshot()),/replacement-join-not-ready/);
 assert.equal(f.writes(),3);assert.equal(f.timers.size,0);assert.equal(f.player.audio.muted,true);
});
test('source ownership loss after cold seek prevents another alignment or adoption',async t=>{
 const f=fixture(t);
 await assert.rejects(f.player.prepareJoin(f.snapshot(),async()=>{f.player.destroy();throw Error('Replacement cancelled');}),/Replacement cancelled/);
 assert.equal(f.writes(),1);assert.equal(f.timers.size,0);
});
test('a user seek during approval warmup cannot adopt the old target',async t=>{
 const f=fixture(t,{seeking:true});
 await assert.rejects(f.player.prepareJoin(f.snapshot(),async()=>f.snapshot()),/replacement-join-not-ready/);
 assert.equal(f.writes(),1);assert.equal(f.timers.size,0);
});

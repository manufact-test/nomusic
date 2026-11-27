import test from 'node:test';
import assert from 'node:assert/strict';
await import('../dist/unpacked/player/sync-engine.js');
const {SyncEngine}=globalThis.__CELIKOM_SYNC_ENGINE_V1__;
function fixture(){
 let position=20,writes=0;
 const audio={duration:200,seeking:false,get currentTime(){return position},set currentTime(v){position=v;writes++;audio.seeking=true}};
 const player={audio,demoLoop:false,applyState(){},play(){},pause(){}};
 const snapshot={observedAt:1000,player:{currentTime:20,duration:200,playbackRate:1,paused:false,seeking:false,readyState:4}};
 return {audio,player,snapshot,sync:new SyncEngine(),get writes(){return writes}};
}
test('aligned PLAY and duplicate SEEK completion do not start another decoder seek',()=>{
 const f=fixture();f.sync.sync(f.player,f.snapshot,true,1000);
 assert.equal(f.writes,0);
 f.snapshot.player.currentTime=134;f.sync.sync(f.player,f.snapshot,true,1001);assert.equal(f.writes,1);
 f.sync.sync(f.player,f.snapshot,true,1002);assert.equal(f.writes,1);
});
test('lagging decoder seek is allowed to finish while the native clock advances',()=>{
 const f=fixture();f.snapshot.player.currentTime=134;f.sync.sync(f.player,f.snapshot,true,1000);
 for(let i=1;i<=8;i++){f.snapshot.player.currentTime=134+i*.5;f.snapshot.observedAt=1000+i*500;f.sync.sync(f.player,f.snapshot,false,f.snapshot.observedAt);}
 assert.equal(f.writes,1,'periodic drift correction must not restart the pending seek');
 f.audio.seeking=false;f.sync.sync(f.player,f.snapshot,false,6000);assert.equal(f.writes,2);
});
test('a genuinely new user seek supersedes a pending decoder seek',()=>{
 const f=fixture();f.snapshot.player.currentTime=134;f.sync.sync(f.player,f.snapshot,true,1000);
 f.snapshot.player.currentTime=26;f.sync.sync(f.player,f.snapshot,true,1100);
 assert.equal(f.writes,2);assert.equal(f.audio.currentTime,26.1);
});

test('ordinary half-second drift keeps the playing decoder and corrects rate within four percent',()=>{
 const f=fixture();Object.assign(f.audio,{currentTime:19.5,paused:false,readyState:4,seeking:false});
 const writes=f.writes;
 f.sync.sync(f.player,f.snapshot,false,1000);
 assert.equal(f.writes,writes);assert.equal(f.audio.playbackRate,1.04);assert.equal(f.sync.mode,'rate');
 f.audio.currentTime=19.85;f.audio.seeking=false;const correctionWrites=f.writes;
 f.sync.sync(f.player,f.snapshot,false,1000);
 assert.equal(f.writes,correctionWrites);assert.equal(f.sync.mode,'rate','finish the correction instead of leaving residual drift');
});
test('rate correction respects user speed and stops at alignment, pause, or buffering',()=>{
 const f=fixture();f.player.applyState=state=>{f.audio.playbackRate=state.playbackRate};
 Object.assign(f.audio,{currentTime:20.5,paused:false,readyState:4,seeking:false});f.snapshot.player.playbackRate=1.5;
 f.sync.sync(f.player,f.snapshot,false,1000);assert.equal(f.audio.playbackRate,1.44);
 f.audio.currentTime=20.04;f.audio.seeking=false;f.sync.sync(f.player,f.snapshot,false,1000);assert.equal(f.audio.playbackRate,1.5);
 f.audio.currentTime=19.5;f.snapshot.player.paused=true;f.sync.sync(f.player,f.snapshot,false,1000);
 assert.equal(f.audio.playbackRate,1.5);assert.notEqual(f.sync.mode,'rate');
 f.snapshot.player.paused=false;f.snapshot.player.readyState=2;
 f.sync.sync(f.player,f.snapshot,false,1000);assert.notEqual(f.sync.mode,'rate');
});
test('explicit seek and large desynchronization still seek immediately with a ready playing decoder',()=>{
 for(const [target,force] of [[20.5,true],[24,false]]){
  const f=fixture();Object.assign(f.audio,{paused:false,readyState:4});f.snapshot.player.currentTime=target;
  f.sync.sync(f.player,f.snapshot,force,1000);
  assert.equal(f.writes,1);assert.equal(f.sync.seekCount,1);assert.equal(f.sync.lastCorrection.explicit,force);
 }
});
test('minor drift correction converges without any decoder seek under repeated snapshots',()=>{
 const f=fixture();let actual=19.5;let seeks=0;
 const audio={duration:200,paused:false,seeking:false,readyState:4,playbackRate:1,
  get currentTime(){return actual},set currentTime(value){actual=value;seeks++}};
 f.player.audio=audio;f.player.applyState=state=>{audio.playbackRate=state.playbackRate};
 for(let i=0;i<40;i++){
  f.snapshot.observedAt=1000+i*500;f.snapshot.player.currentTime=20+i*.5;
  f.sync.sync(f.player,f.snapshot,false,f.snapshot.observedAt);actual+=.5*audio.playbackRate;
 }
 assert.equal(seeks,0);assert.ok(Math.abs(f.sync.driftMs)<=80);assert.equal(audio.playbackRate,1);
});
test('a transient buffering state does not seek away the existing half-second buffer; user seek still wins',()=>{
 const f=fixture();Object.assign(f.audio,{currentTime:19.5,paused:false,readyState:1,seeking:false});
 const writes=f.writes;f.sync.sync(f.player,f.snapshot,false,1000);
 assert.equal(f.writes,writes);assert.equal(f.sync.mode,'buffering');
 f.snapshot.player.currentTime=30;f.sync.sync(f.player,f.snapshot,true,1001);
 assert.equal(f.writes,writes+1);
});

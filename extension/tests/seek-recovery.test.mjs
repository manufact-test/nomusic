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

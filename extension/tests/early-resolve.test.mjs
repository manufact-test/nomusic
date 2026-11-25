import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../dist/unpacked/player/replacement-controller.js',import.meta.url),'utf8');
const flush=async()=>{for(let i=0;i<35;i++)await Promise.resolve();};
const defer=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};};
function fixture(resolveAsset){
 let now=100000,current,healthy=true;const calls=[],guards=[],players=[];
 const ctx=vm.createContext({Date:{now:()=>now},
 __CELIKOM_PLAYER_CORE_V1__:{normalizeTrackId:id=>/^[1-9]\d*$/.test(id||'')?id:null},
 __CELIKOM_REPLACEMENT_PLAYER_V1__:{ReplacementPlayer:class{}},
 __CELIKOM_SYNC_ENGINE_V1__:{SyncEngine:class{sync(){return 0;}}},
 __CELIKOM_FAIL_OPEN_V1__:{FailOpenController:class{restore(operation){operation.player?.destroy();return Promise.resolve();}}}});
 vm.runInContext(source,ctx);
 const bridge={sessionId:'s',post(){},isHealthy:()=>healthy,getSnapshot:async()=>current,
 request:async(type,payload)=>{guards.push({type,payload});return {snapshot:current};}};
 const ctrl=new ctx.__CELIKOM_REPLACEMENT_CONTROLLER_V1__.ReplacementController(bridge,{document:{hidden:false}},{
 resolveAsset:(id,opts)=>{calls.push({id,...opts});return resolveAsset(id,opts);},
 createPlayer:()=>{const p={audio:{duration:200},prepare:async()=>{},destroy(){p.destroyed=true;}};players.push(p);return p;}});
 ctrl.configure(true,'');
 const update=(id='1',ready=false,extra={})=>{current={observedAt:now,track:{id,confidence:200,ambiguous:false,metadata:{durationMs:200000}},
 player:{mediaId:'m',currentTime:0,paused:true,seeking:false,ended:false,duration:ready?200:NaN,readyState:ready?4:0},...extra};ctrl.update(current);return current;};
 return {ctrl,calls,guards,players,update,advance:n=>now+=n,unhealthy:()=>healthy=false};
}
const asset=()=>({found:true,expiresAt:500000,durationMs:200000,mimeType:'audio/mpeg'});
test('resolve overlaps native loading; no audio/guard until existing duration/readiness admission succeeds',async()=>{
 const gate=defer(),f=fixture(()=>gate.promise);
 f.update();await flush();assert.equal(f.calls.length,1);assert.equal(f.players.length,0);assert.equal(f.guards.length,0);
 f.advance(250);f.update();await flush();assert.equal(f.calls.length,1,'duplicate loading snapshots share one warm-up');
 gate.resolve(asset());await flush();assert.equal(f.players.length,0,'descriptor alone cannot admit audio');
 f.advance(200);f.update('1',true);await flush();assert.equal(f.calls.length,1);assert.equal(f.players.length,1);
 assert.equal(f.ctrl.phase,'REPLACEMENT_ACTIVE');assert.equal(f.ctrl.startupHistory[0].warmLeadMs,450);
});
test('pending warm-up is shared when native becomes ready before resolve returns',async()=>{
 const gate=defer(),f=fixture(()=>gate.promise);f.update();await flush();f.update('1',true);await flush();
 assert.equal(f.calls.length,1);assert.equal(f.players.length,0);gate.resolve(asset());await flush();assert.equal(f.players.length,1);
});
test('track change ignores stale warm-up result and never prepares old audio',async()=>{
 const first=defer(),second=defer(),f=fixture(id=>id==='1'?first.promise:second.promise);
 f.update();await flush();f.update('2');await flush();f.update('2',true);await flush();
 first.resolve(asset());await flush();assert.equal(f.players.length,0);second.resolve(asset());await flush();
 assert.equal(f.players.length,1);assert.equal(f.ctrl.operation.trackId,'2');
});
test('obsolete warm-up rejection is handled and does not block another song',async()=>{
 const gate=defer(),f=fixture(id=>id==='1'?gate.promise:Promise.resolve(asset()));
 f.update();await flush();f.update('2',true);await flush();gate.reject(new Error('api_network_error'));await flush();
 assert.equal(f.ctrl.phase,'REPLACEMENT_ACTIVE');assert.equal(f.ctrl.lastError,null);assert.equal(f.ctrl.operation.trackId,'2');
});
test('Stop, access suspension and manual original discard warmed grants',async()=>{
 for(const action of [f=>f.ctrl.configure(false,''),f=>f.ctrl.suspendAccess(true,'api_forbidden'),f=>f.ctrl.manualRestore()]){
  const gate=defer(),f=fixture(()=>gate.promise);f.update();await flush();action(f);gate.resolve(asset());await flush();
  f.update('1',true);await flush();assert.equal(f.players.length,0);assert.equal(f.guards.length,0);assert.equal(f.ctrl.warmedAsset,null);
 }
});
test('ambiguous, low-confidence, unknown, disabled and unhealthy snapshots do not warm',async()=>{
 for(const mode of ['ambiguous','low','unknown','disabled','unhealthy']){
  const f=fixture(()=>Promise.resolve(asset()));
  if(mode==='disabled')f.ctrl.configure(false,'');if(mode==='unhealthy')f.unhealthy();
  const track={id:mode==='unknown'?null:'1',confidence:mode==='low'?50:200,ambiguous:mode==='ambiguous',metadata:{durationMs:200000}};
  f.update('1',false,{track});await flush();assert.equal(f.calls.length,0,mode);
 }
});
test('warm-up neither renews expired grants nor reuses a descriptor after five seconds',async()=>{
 for(const expired of [true,false]){
  let n=0;const f=fixture(()=>Promise.resolve(++n===1&&expired?{...asset(),expiresAt:100500}:asset()));
  f.update();await flush();f.advance(expired?600:5001);f.update('1',true);await flush();
  assert.equal(f.calls.length,2);assert.equal(f.players.length,1);assert.equal(f.ctrl.phase,'REPLACEMENT_ACTIVE');
 }
});
test('negative warmed answer retains existing negative-cache behavior and never creates audio',async()=>{
 const f=fixture(()=>Promise.resolve({found:false,retryAfterMs:5000}));f.update();await flush();f.update('1',true);await flush();
 for(let i=0;i<10;i++)f.ctrl.tick();await flush();assert.equal(f.calls.length,1);assert.equal(f.players.length,0);assert.equal(f.guards.length,0);
});

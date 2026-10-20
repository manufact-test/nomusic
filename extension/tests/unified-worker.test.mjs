import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createMusicTabs} from '../dist/unpacked/background/music-tabs.js';
import {registerTabRecovery} from '../dist/unpacked/background/tab-recovery.js';
import {createActionIcon} from '../dist/unpacked/background/action-icon.js';
import {createUploadBroker} from '../dist/unpacked/background/upload-broker.js';
import {createUploadJournal} from '../dist/unpacked/upload/upload-journal.js';
import {readFile} from 'node:fs/promises';
const source=(await readFile(new URL('../dist/unpacked/background/service-worker.js',import.meta.url),'utf8')).replace(/^import .*$/gm,'');
function fixture() {
 const networkListeners=new Map();
 let handler,allowed=true,trialStarted=0,localSession=true,controller={track:{id:"144530503"},player:{mediaId:"1"},phase:"READY",bridge:{healthy:true}},connectionError=null;
 const local={enabled:false},sent=[],icons=[];
 const commands={getStatus:'CELIKOM_STATUS_GET',setEnabled:'CELIKOM_ENABLED_SET',setTestTrack:'CELIKOM_TEST_TRACK_SET',retryReplacement:'CELIKOM_REPLACEMENT_RETRY',restoreOriginal:'CELIKOM_RESTORE_ORIGINAL'};
 const chrome={action:{setIcon:async value=>icons.push(value),setTitle:async()=>{}},runtime:{id:'worker',getManifest:()=>({version:'0.4.7'}),getURL:p=>'chrome-extension://worker/'+p,onInstalled:{addListener(){}},onStartup:{addListener(){}},onMessage:{addListener:fn=>{handler=fn}}},storage:{local:{get:async()=>({...local}),set:async x=>Object.assign(local,x)}},tabs:{query:async()=>[{id:1,url:'https://music.yandex.ru/'}],sendMessage:async(id,m)=>{sent.push(m);return {ok:true}}}};
 const auth={installationId:async()=>'',perform:async action=>action==='account-preview'?{ok:true,localSession}:{ok:true},withEntitledAccess:async()=>{},entitlement:async activation=>{if(activation)trialStarted++;return {allowed,valid_until:new Date(Date.now()+432000000).toISOString(),reason:allowed?'trial_active':'trial_inactive'}}};
 vm.runInNewContext(source,{addEventListener:(name,fn)=>networkListeners.set(name,fn),chrome,COMMANDS:commands,normalizeEnabled:v=>v===true,registerTabRecovery,createActionIcon,createMusicTabs,createAuthBroker:()=>auth,createApiBroker:()=>async()=>({ok:true}),createUploadBroker,createUploadJournal,createControllerBootstrap:()=>({ensure:async()=>({status:controller,error:connectionError}),ensureOpenTabs:async()=>{}}),Date,URL,Promise});
 const send=(type,more={},sender={id:'worker',url:'chrome-extension://worker/popup/popup.html'})=>new Promise(resolve=>handler({type,...more},sender,resolve));
 return {setController:(value,error=null)=>{controller=value;connectionError=error},send,local,sent,icons,auth,network:(name)=>networkListeners.get(name)?.(),setAllowed:v=>allowed=v,setSignedIn:v=>localSession=v,get trials(){return trialStarted}};
}
test('Stage10 verified Start activates trial before enabling the existing controller',async()=>{
 const f=fixture();const state=await f.send('CELIKOM_ENABLED_SET',{enabled:true});
 assert.equal(f.trials,1);assert.equal(state.enabled,true);assert.equal(f.sent.at(-1).type,'CELIKOM_REPLACEMENT_RETRY');
});
test('network authorization failure suspends playback without turning off CELIKOM',async()=>{
 const f=fixture();f.local.enabled=true;f.auth.entitlement=async()=>{throw Error('auth_unavailable')};
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,healthy:true},{id:'worker',url:'https://music.yandex.ru/',tab:{id:1}});
 await new Promise(resolve=>setImmediate(resolve));assert.equal(f.local.enabled,true);
 assert.equal(f.sent.at(-1).state,'unavailable');
});
test('declared incident suspends playback and remains enabled for automatic recovery',async()=>{
 const f=fixture();f.local.enabled=true;f.auth.entitlement=async()=>({allowed:false,reason:'service_incident'});
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,healthy:true},{id:'worker',url:'https://music.yandex.ru/',tab:{id:1}});
 await new Promise(resolve=>setImmediate(resolve));assert.equal(f.local.enabled,true);assert.equal(f.sent.at(-1).state,'incident');
});
test('Stage10 denied Start never mutes/enables; logout stops buffered playback',async()=>{
 const f=fixture();f.setAllowed(false);const state=await f.send('CELIKOM_ENABLED_SET',{enabled:true});
 assert.equal(state.accessError,'trial_inactive');assert.equal(f.local.enabled,false);assert.equal(f.sent.length,0);
 f.setAllowed(true);await f.send('CELIKOM_ENABLED_SET',{enabled:true});
 await f.send('CELIKOM_AUTH',{action:'logout'});assert.equal(f.local.enabled,false);
});
test('Stage10 context heartbeat fails open on revoked access; page cannot request popup credentials',async()=>{
 const f=fixture();await f.send('CELIKOM_ENABLED_SET',{enabled:true});f.setAllowed(false);
 const reply=await f.send('CELIKOM_CONTEXT_PING',{}, {id:'worker',url:'https://music.yandex.ru/album/1/track/144530503'});
 assert.equal(reply.ok,true);await new Promise(resolve=>setImmediate(resolve));assert.equal(f.local.enabled,false);
 const forbidden=await f.send('CELIKOM_AUTH',{action:'contribution-access'},{id:'worker',url:'https://music.yandex.ru/'});
 assert.equal(forbidden.error,'invalid_sender');
});

test('worker heartbeat acknowledges before an unresolved server entitlement request',async()=>{
 const f=fixture();f.local.enabled=true;let finish;
 f.auth.entitlement=()=>new Promise(resolve=>{finish=resolve});
 const reply=await f.send('CELIKOM_CONTEXT_PING',{}, {id:'worker',url:'https://music.yandex.ru/'});
 assert.equal(reply.ok,true);assert.equal(f.local.enabled,true);
 await new Promise(resolve=>setImmediate(resolve));finish({allowed:false});
 await new Promise(resolve=>setImmediate(resolve));assert.equal(f.local.enabled,false);
});

test('Start without an account refuses immediately before track detection or trial activation',async()=>{
 const f=fixture();f.setSignedIn(false);
 const result=await f.send('CELIKOM_ENABLED_SET',{enabled:true});
 assert.equal(result.accessError,'sign_in_required');assert.equal(f.trials,0);
 assert.equal(f.local.enabled,false);assert.equal(f.sent.length,0);
});

test('worker accepts green-icon heartbeats only from authorized enabled Yandex connection, including songs without replacements',async()=>{
 const f=fixture();f.local.enabled=true;
 const sender={id:'worker',url:'https://music.yandex.ru/',tab:{id:1}};
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,phase:'OBSERVING',healthy:true},sender);
 await new Promise(resolve=>setImmediate(resolve));assert.match(f.icons.at(-1).path[32],/green/);
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,phase:'READY',healthy:true},sender);
 await new Promise(resolve=>setImmediate(resolve));assert.match(f.icons.at(-1).path[32],/green/);
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,healthy:false},sender);
 await new Promise(resolve=>setImmediate(resolve));assert.match(f.icons.at(-1).path[32],/gray/);
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,phase:'READY',healthy:true,replacementError:true},sender);
 await new Promise(resolve=>setImmediate(resolve));assert.match(f.icons.at(-1).path[32],/gray/);
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,phase:'PREPARING',healthy:true},sender);
 await new Promise(resolve=>setImmediate(resolve));assert.match(f.icons.at(-1).path[32],/green/);
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,phase:'REPLACEMENT_ACTIVE',healthy:true,replacementError:false},sender);
 await new Promise(resolve=>setImmediate(resolve));assert.match(f.icons.at(-1).path[32],/green/);
 await f.send('CELIKOM_AUTH',{action:'logout'});
 await new Promise(resolve=>setImmediate(resolve));assert.match(f.icons.at(-1).path[32],/gray/);
 const g=fixture();g.local.enabled=true;g.setAllowed(false);
 await g.send('CELIKOM_CONTEXT_PING',{enabled:true,phase:'OBSERVING',healthy:true},sender);
 await new Promise(resolve=>setImmediate(resolve));assert.match(g.icons.at(-1).path[32],/gray/);
 const forbidden=await g.send('CELIKOM_CONTEXT_PING',{enabled:true,phase:'OBSERVING',healthy:true},{...sender,url:'https://example.org/'});
 assert.equal(forbidden.ok,false);assert.match(g.icons.at(-1).path[32],/gray/);
});


test('security: untrusted senders cannot read status, start trial or change playback intent',async()=>{
 for(const sender of [{id:'other',url:'chrome-extension://worker/popup/popup.html'},
  {id:'worker',url:'https://music.yandex.ru/'}, {id:'worker',url:'chrome-extension://worker/popup/popup.html?spoof=1'}, {}]) {
  const f=fixture();
  for(const type of ['CELIKOM_STATUS_GET','CELIKOM_ENABLED_SET','CELIKOM_TEST_TRACK_SET','CELIKOM_RESTORE_ORIGINAL','CELIKOM_ADD_TRACK_OPENED','CELIKOM_AUTH']) {
   const result=await f.send(type,{enabled:true,action:'logout'},sender);
   assert.equal(result.error,'invalid_sender');
  }
  assert.equal(f.trials,0);assert.equal(f.local.enabled,false);assert.equal(f.sent.length,0);
 }
});


test('security: delayed Start cannot undo a later manual Stop, Original or logout',async()=>{
 for(const later of ['stop','original','logout']) {
  const f=fixture();let finish;
  f.auth.entitlement=()=>new Promise(resolve=>{finish=resolve});
  const start=f.send('CELIKOM_ENABLED_SET',{enabled:true});
  while(!finish) await new Promise(resolve=>setImmediate(resolve));
  if(later==='stop') await f.send('CELIKOM_ENABLED_SET',{enabled:false});
  else if(later==='original') await f.send('CELIKOM_RESTORE_ORIGINAL');
  else await f.send('CELIKOM_AUTH',{action:'logout'});
  finish({allowed:true,valid_until:new Date(Date.now()+86400000).toISOString()});
  const result=await start;
  assert.equal(f.local.enabled,false);assert.equal(result.enabled,false);
  assert.equal(f.sent.some(m=>m.type==='CELIKOM_REPLACEMENT_RETRY'),false);
 }
});

test('lifetime promo authorizes heartbeat; redemption never overrides manual Stop',async()=>{
 const f=fixture();f.local.enabled=true;
 f.auth.entitlement=async()=>({allowed:true,source:'promo',valid_until:null,reason:'promo_active'});
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,healthy:true},{id:'worker',url:'https://music.yandex.ru/',tab:{id:1}});
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(f.local.enabled,true);assert.equal(f.sent.at(-1).state,'allowed');
 await f.send('CELIKOM_ENABLED_SET',{enabled:false});
 await f.send('CELIKOM_AUTH',{action:'promo-redeem',code:'TEST_CODE'});
 assert.equal(f.local.enabled,false);
});

test('network reconnect revalidates immediately and a stale result cannot suspend the fresh connection',async()=>{
 const f=fixture();f.local.enabled=true;let finish,calls=0,resets=0;
 f.auth.resetTransport=()=>resets++;
 f.auth.entitlement=async()=>{if(++calls===1)return new Promise(r=>finish=r);return {allowed:true,source:'promo',valid_until:null};};
 const sender={id:'worker',url:'https://music.yandex.ru/',tab:{id:1}};
 await f.send('CELIKOM_CONTEXT_PING',{},sender);await new Promise(setImmediate);
 f.network('online');await new Promise(setImmediate);await new Promise(setImmediate);
 assert.equal(resets,1);assert.equal(calls,2);assert.equal(f.sent.at(-1).state,'allowed');
 const before=f.sent.length;finish({allowed:false});await new Promise(setImmediate);
 assert.equal(f.local.enabled,true);assert.equal(f.sent.length,before,'old denial cannot disable or suspend new connection');
 await f.send('CELIKOM_CONTEXT_PING',{},sender);await new Promise(setImmediate);assert.equal(calls,2,'fresh verification remains reusable');
});
test('VPN route change without online event resets stale GET transport and auto-resumes after verified access',async(t)=>{
 t.mock.timers.enable({apis:['Date'],now:1000000});
 const f=fixture();f.local.enabled=true;let calls=0,resets=0,staleRoute=true;
 f.auth.resetTransport=()=>{resets++;staleRoute=false;};
 f.auth.entitlement=async()=>{calls++;if(staleRoute)throw Error('auth_timeout');
   return {allowed:true,source:'promo',valid_until:null,reason:'promo_active'};};
 const sender={id:'worker',url:'https://music.yandex.ru/',tab:{id:1}};
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,healthy:true,suspended:true},sender);
 await new Promise(setImmediate);
 assert.equal(f.sent.at(-1).state,'unavailable');
 assert.equal(resets,0,'ordinary check failure does not thrash transport before cooldown');
 t.mock.timers.tick(5001);
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,healthy:true,suspended:true},sender);
 await new Promise(setImmediate);await new Promise(setImmediate);
 assert.equal(calls,2);assert.equal(resets,1,'next heartbeat retry resets stale VPN transport');
 assert.ok(f.sent.some(m=>m.type==='CELIKOM_ACCESS_STATE'&&m.state==='allowed'&&m.recovered===true));
 assert.equal(f.local.enabled,true,'verified recovery must not toggle user intent');
 assert.equal(f.trials,0,'recovery never restarts trial');
});

test('online hints never enable stopped playback or authorize a revoked account',async()=>{
 const f=fixture();let calls=0;f.auth.entitlement=async()=>{calls++;return {allowed:false};};
 f.network('online');await new Promise(setImmediate);assert.equal(calls,0);assert.equal(f.local.enabled,false);
 f.local.enabled=true;f.network('online');await new Promise(setImmediate);await new Promise(setImmediate);
 assert.equal(calls,1);assert.equal(f.local.enabled,false);
});

test('popup-authoritative connection failure clears green immediately and healthy status restores it',async()=>{
 const f=fixture();f.local.enabled=true;
 await f.send('CELIKOM_STATUS_GET');await new Promise(r=>setImmediate(r));assert.match(f.icons.at(-1).path[32],/green/);
 f.setController({phase:'READY',bridge:{healthy:true}},'receiver-missing');
 const state=await f.send('CELIKOM_STATUS_GET');await new Promise(r=>setImmediate(r));assert.equal(state.phase,'ERROR');assert.match(f.icons.at(-1).path[32],/gray/);
 f.setController({phase:'READY',bridge:{healthy:true}});await f.send('CELIKOM_STATUS_GET');await new Promise(r=>setImmediate(r));assert.match(f.icons.at(-1).path[32],/green/);
});

test('new document after idle or VPN return resets stale GET transport and verifies access without Start',async(t)=>{
 t.mock.timers.enable({apis:['Date'],now:1000000});
 const f=fixture();f.local.enabled=true;let resets=0,calls=0;f.auth.resetTransport=()=>resets++;
 f.auth.entitlement=async()=>{calls++;return {allowed:true,source:'promo',valid_until:null};};
 const sender={id:'worker',url:'https://music.yandex.ru/',tab:{id:1}};
 await f.send('CELIKOM_CONTEXT_PING',{enabled:true,phase:'READY',healthy:true},sender);await new Promise(setImmediate);
 await f.send('CELIKOM_RECOVERY_HINT',{reason:'visible',needsRecovery:false},sender);await new Promise(setImmediate);
 assert.equal(resets,0,'healthy ordinary focus does not interrupt playback');assert.equal(calls,1);
 t.mock.timers.tick(6000);
 const reply=await f.send('CELIKOM_RECOVERY_HINT',{reason:'document',needsRecovery:false},sender);await new Promise(setImmediate);await new Promise(setImmediate);
 assert.equal(reply.rechecking,true);assert.equal(resets,1);assert.equal(calls,2);
 assert.ok(f.sent.some(m=>m.type==='CELIKOM_ACCESS_STATE'&&m.state==='allowed'&&m.recovered===true));assert.equal(f.local.enabled,true);assert.equal(f.trials,0);
});
test('page online recovery replaces an unresolved old check; late denial and duplicate hint cannot override it',async()=>{
 const f=fixture();f.local.enabled=true;let finish,calls=0,resets=0;f.auth.resetTransport=()=>resets++;
 f.auth.entitlement=async()=>{if(++calls===1)return new Promise(r=>finish=r);return {allowed:true,source:'promo',valid_until:null};};
 const sender={id:'worker',url:'https://music.yandex.ru/',tab:{id:1}};
 await f.send('CELIKOM_CONTEXT_PING',{},sender);await new Promise(setImmediate);
 assert.equal((await f.send('CELIKOM_RECOVERY_HINT',{reason:'online'},sender)).rechecking,true);
 await new Promise(setImmediate);await new Promise(setImmediate);assert.equal(resets,1);assert.equal(calls,2);assert.equal(f.sent.at(-1).state,'allowed');
 assert.equal((await f.send('CELIKOM_RECOVERY_HINT',{reason:'online'},sender)).rechecking,false);
 const before=f.sent.length;finish({allowed:false});await new Promise(setImmediate);assert.equal(f.sent.length,before);assert.equal(f.local.enabled,true);
});
test('recovery hints never authorize an untrusted sender, enable Stop, or replay trial activation',async()=>{
 const f=fixture();let resets=0;f.auth.resetTransport=()=>resets++;
 const sender={id:'worker',url:'https://music.yandex.ru/',tab:{id:1}};
 await f.send('CELIKOM_RECOVERY_HINT',{reason:'online',needsRecovery:true},sender);assert.equal(resets,0);assert.equal(f.local.enabled,false);
 f.local.enabled=true;
 for(const invalid of [{...sender,url:'https://example.org/'},{...sender,id:'other'}])assert.equal((await f.send('CELIKOM_RECOVERY_HINT',{reason:'online'},invalid)).ok,false);
 assert.equal(resets,0);assert.equal(f.trials,0);
});
test('Stop while fresh recovery authorization is pending prevents a late allowed response from resuming',async()=>{
 const f=fixture();f.local.enabled=true;let finish;f.auth.entitlement=()=>new Promise(r=>finish=r);
 const sender={id:'worker',url:'https://music.yandex.ru/',tab:{id:1}};
 await f.send('CELIKOM_RECOVERY_HINT',{reason:'online'},sender);await new Promise(setImmediate);
 await f.send('CELIKOM_ENABLED_SET',{enabled:false});const count=f.sent.length;finish({allowed:true,source:'promo',valid_until:null});await new Promise(setImmediate);await new Promise(setImmediate);
 assert.equal(f.local.enabled,false);assert.equal(f.sent.length,count);
});

test("security: legacy upload tabs cannot issue authenticated popup commands", async () => {
 const f=fixture();
 for(const url of [
  "chrome-extension://worker/popup/popup.html#upload",
  "chrome-extension://worker/popup/popup.html#upload-spoof",
  "chrome-extension://worker/popup/popup.html?skip=1#upload",
  "chrome-extension://worker/other.html#upload"
 ]) {
  const denied=await f.send("CELIKOM_AUTH",{action:"contribution-access"},{id:"worker",url});
  assert.equal(denied.error,"invalid_sender");
 }
});

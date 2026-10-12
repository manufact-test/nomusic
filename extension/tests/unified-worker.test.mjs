import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createMusicTabs} from '../dist/unpacked/background/music-tabs.js';
import {createActionIcon} from '../dist/unpacked/background/action-icon.js';
import {readFile} from 'node:fs/promises';
const source=(await readFile(new URL('../dist/unpacked/background/service-worker.js',import.meta.url),'utf8')).replace(/^import .*$/gm,'');
function fixture() {
 let handler,allowed=true,trialStarted=0,localSession=true;
 const local={enabled:false},sent=[],icons=[];
 const commands={getStatus:'CELIKOM_STATUS_GET',setEnabled:'CELIKOM_ENABLED_SET',setTestTrack:'CELIKOM_TEST_TRACK_SET',retryReplacement:'CELIKOM_REPLACEMENT_RETRY',restoreOriginal:'CELIKOM_RESTORE_ORIGINAL'};
 const chrome={action:{setIcon:async value=>icons.push(value),setTitle:async()=>{}},runtime:{id:'worker',getManifest:()=>({version:'0.4.7'}),getURL:p=>'chrome-extension://worker/'+p,onInstalled:{addListener(){}},onStartup:{addListener(){}},onMessage:{addListener:fn=>{handler=fn}}},storage:{local:{get:async()=>({...local}),set:async x=>Object.assign(local,x)}},tabs:{query:async()=>[{id:1,url:'https://music.yandex.ru/'}],sendMessage:async(id,m)=>{sent.push(m);return {ok:true}}}};
 const auth={installationId:async()=>'',perform:async action=>action==='account-preview'?{ok:true,localSession}:{ok:true},withEntitledAccess:async()=>{},entitlement:async activation=>{if(activation)trialStarted++;return {allowed,valid_until:new Date(Date.now()+432000000).toISOString(),reason:allowed?'trial_active':'trial_inactive'}}};
 vm.runInNewContext(source,{chrome,COMMANDS:commands,normalizeEnabled:v=>v===true,createActionIcon,createMusicTabs,createAuthBroker:()=>auth,createApiBroker:()=>async()=>({ok:true}),createControllerBootstrap:()=>({ensure:async()=>({status:{track:{id:'144530503'},player:{mediaId:'1'},phase:'READY',bridge:{healthy:true}}}),ensureOpenTabs:async()=>{}}),Date,URL,Promise});
 const send=(type,more={},sender={id:'worker',url:'chrome-extension://worker/popup/popup.html'})=>new Promise(resolve=>handler({type,...more},sender,resolve));
 return {send,local,sent,icons,auth,setAllowed:v=>allowed=v,setSignedIn:v=>localSession=v,get trials(){return trialStarted}};
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
 await new Promise(resolve=>setImmediate(resolve));assert.match(f.icons.at(-1).path[32],/gray/);
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

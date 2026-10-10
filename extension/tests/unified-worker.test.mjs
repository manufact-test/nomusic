import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
const source=(await readFile(new URL('../dist/unpacked/background/service-worker.js',import.meta.url),'utf8')).replace(/^import .*$/gm,'');
function fixture() {
 let handler,allowed=true,trialStarted=0;
 const local={enabled:false},sent=[];
 const commands={getStatus:'CELIKOM_STATUS_GET',setEnabled:'CELIKOM_ENABLED_SET',retryReplacement:'CELIKOM_REPLACEMENT_RETRY',restoreOriginal:'CELIKOM_RESTORE_ORIGINAL'};
 const chrome={runtime:{id:'worker',getManifest:()=>({version:'0.4.7'}),getURL:p=>'chrome-extension://worker/'+p,onInstalled:{addListener(){}},onStartup:{addListener(){}},onMessage:{addListener:fn=>{handler=fn}}},storage:{local:{get:async()=>({...local}),set:async x=>Object.assign(local,x)}},tabs:{query:async()=>[{id:1}],sendMessage:async(id,m)=>{sent.push(m);return {ok:true}}}};
 const auth={installationId:async()=>'',perform:async()=>({ok:true}),withEntitledAccess:async()=>{},entitlement:async activation=>{if(activation)trialStarted++;return {allowed,valid_until:new Date(Date.now()+432000000).toISOString(),reason:allowed?'trial_active':'trial_inactive'}}};
 vm.runInNewContext(source,{chrome,COMMANDS:commands,normalizeEnabled:v=>v===true,createAuthBroker:()=>auth,createApiBroker:()=>async()=>({ok:true}),createControllerBootstrap:()=>({ensure:async()=>({status:{track:{id:'144530503'},player:{mediaId:'1'},phase:'READY'}}),ensureOpenTabs:async()=>{}}),Date,URL,Promise});
 const send=(type,more={},sender={id:'worker',url:'chrome-extension://worker/popup/popup.html'})=>new Promise(resolve=>handler({type,...more},sender,resolve));
 return {send,local,sent,setAllowed:v=>allowed=v,get trials(){return trialStarted}};
}
test('Stage10 verified Start activates trial before enabling the existing controller',async()=>{
 const f=fixture();const state=await f.send('CELIKOM_ENABLED_SET',{enabled:true});
 assert.equal(f.trials,1);assert.equal(state.enabled,true);assert.equal(f.sent.at(-1).type,'CELIKOM_REPLACEMENT_RETRY');
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
 assert.equal(reply.ok,true);assert.equal(f.local.enabled,false);
 const forbidden=await f.send('CELIKOM_AUTH',{action:'contribution-access'},{id:'worker',url:'https://music.yandex.ru/'});
 assert.equal(forbidden.error,'invalid_sender');
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { initAccessStatus } from '../dist/unpacked/auth/access-status.js';
import { initVersionStatus } from '../dist/unpacked/popup/version-status.js';
const tick = () => new Promise(r => setTimeout(r, 0));
function fixture() {
 const changes = [], listeners = {};
 const node = name => ({textContent:'',hidden:false,title:'',animate(){changes.push(name);return {cancel(){}}}});
 const access = node('access'), version = node('version');
 return {access,version,changes,listeners,document:{querySelector:s=>s==='[data-access-status]'?access:version,addEventListener:(name,fn)=>{const before=listeners[name];listeners[name]=()=>{before?.();fn()}}}};
}
const access = {allowed:true,source:'trial',reason:'trial_active',valid_until:new Date(Date.now()+86400000).toISOString()};
const state = id => ({track:{id},phase:'READY'});
test('known absence of a song collapses the version row immediately on reopen and a real song restores it',async()=>{
 const oldDocument=globalThis.document,oldStorage=globalThis.localStorage,memory=new Map();
 globalThis.localStorage={getItem:k=>memory.get(k),setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)};
 try {
  memory.set('celikom-popup-display-v1:track',JSON.stringify({at:Date.now(),data:{id:null,label:'Откройте Яндекс Музыку'}}));
  memory.set('celikom-popup-display-v1:version',JSON.stringify({at:Date.now(),data:{trackId:'144530503',status:'approved'}}));
  const fx=fixture();globalThis.document=fx.document;
  const refresh=initVersionStatus(async()=>({ok:true,status:'approved'}));
  assert.equal(fx.version.hidden,true,'collapse before the first asynchronous response');
  assert.equal(fx.version.textContent,'','old song cannot reserve an empty row');
  await refresh({phase:'STOPPED',track:null});assert.equal(fx.version.hidden,true);
  await refresh(state('144530503'));assert.equal(fx.version.hidden,false);
  assert.match(fx.version.textContent,/доступна/);
  await refresh({phase:'STOPPED',track:null});assert.equal(fx.version.hidden,true);
 }finally{globalThis.document=oldDocument;globalThis.localStorage=oldStorage}
});
test('reopen keeps saved access but does not present an unverified cached song version',async()=>{
 const oldDocument=globalThis.document, oldStorage=globalThis.localStorage, memory=new Map();
 globalThis.localStorage={getItem:k=>memory.get(k),setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)};
 try {
  const first=fixture();globalThis.document=first.document;
  const send=async m=>m.action==='access-preview'?{}:m.action==='entitlement'?{ok:true,entitlement:access}:{ok:true,status:'approved'};
  await initAccessStatus(send)();await initVersionStatus(send)(state('144530503'));
  const expectedAccess=first.access.textContent, expectedVersion=first.version.textContent;
  const reopened=fixture();globalThis.document=reopened.document;
  let finishAccess,finishVersion;
  const refreshAccess=initAccessStatus(m=>m.action==='access-preview'?Promise.resolve({}):new Promise(r=>finishAccess=r));
  const refreshVersion=initVersionStatus(()=>new Promise(r=>finishVersion=r));
  assert.equal(reopened.access.textContent,expectedAccess,'persisted account expiry may be shown immediately');
  assert.match(reopened.version.textContent,/Проверяем наличие/,'unverified old presence is never claimed');
  const a=refreshAccess(),v=refreshVersion(state('144530503'));await tick();
  assert.equal(reopened.access.textContent,expectedAccess);
  assert.match(reopened.version.textContent,/Проверяем наличие/);
  finishAccess({ok:true,entitlement:access});finishVersion({ok:true,status:'approved'});await Promise.all([a,v]);
  assert.equal(reopened.version.textContent,expectedVersion,'live server status is authoritative');
  assert.deepEqual(reopened.changes,['version'],'only the verified version needs an update');
 }finally{globalThis.document=oldDocument;globalThis.localStorage=oldStorage}
});
test('a changed track cannot borrow the old approved version and delayed old responses cannot overwrite it',async()=>{
 const oldDocument=globalThis.document,oldStorage=globalThis.localStorage;
 globalThis.localStorage={getItem:()=>JSON.stringify({at:Date.now(),data:{trackId:'144530503',status:'approved'}}),setItem(){},removeItem(){}};
 const fx=fixture();globalThis.document=fx.document;
 try {
  const pending=new Map(),refresh=initVersionStatus(m=>new Promise(r=>pending.set(m.track_id,r)));
  const old=refresh(state('144530503')),fresh=refresh(state('38436680'));
  assert.match(fx.version.textContent,/Проверяем наличие/);
  pending.get('38436680')({ok:true,status:'pending'});await fresh;
  pending.get('144530503')({ok:true,status:'approved'});await old;
  assert.match(fx.version.textContent,/на проверке/);
 }finally{globalThis.document=oldDocument;globalThis.localStorage=oldStorage}
});
test('first use keeps explicit loading text; logout clears positive cached presentation',async()=>{
 const oldDocument=globalThis.document,oldStorage=globalThis.localStorage, memory=new Map();
 globalThis.localStorage={getItem:k=>memory.get(k),setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)};
 const fx=fixture();globalThis.document=fx.document;
 try {
  const refresh=initAccessStatus(async m=>m.action==='access-preview'?{}:{ok:true,entitlement:access});
  const version=initVersionStatus(async()=>({ok:true,status:'approved'}));
  assert.match(fx.access.textContent,/Загрузка/);assert.match(fx.version.textContent,/Проверяем наличие/);
  await refresh();await version(state('144530503'));
  fx.listeners['celikom-account-logout']();
  const reopen=fixture();globalThis.document=reopen.document;initVersionStatus(()=>new Promise(()=>{}));initAccessStatus(()=>new Promise(()=>{}));
  assert.match(reopen.access.textContent,/Войдите/);
  assert.match(reopen.version.textContent,/Проверяем наличие/);
 }finally{globalThis.document=oldDocument;globalThis.localStorage=oldStorage}
});
test('sign-in refreshes the current song immediately and ignores a late signed-out response',async()=>{
 const oldDocument=globalThis.document,oldStorage=globalThis.localStorage;
 globalThis.localStorage={getItem:()=>null,setItem(){},removeItem(){}};
 const fx=fixture();globalThis.document=fx.document;
 try {
  const replies=[];let calls=0;
  const refresh=initVersionStatus(()=>{calls++;return new Promise(resolve=>replies.push(resolve))});
  const first=refresh(state('144530503'));replies.shift()({ok:false,error:'invalid_session'});await first;
  assert.match(fx.version.textContent,/Войдите/);
  fx.listeners['celikom-account-login']();
  assert.equal(calls,2,'login bypasses the 15-second cache without a reload');
  replies.shift()({ok:true,status:'approved'});await tick();
  assert.match(fx.version.textContent,/доступна/);
  fx.listeners['celikom-account-logout']();
  const stale=refresh(state('144530503'));
  const oldReply=replies.shift();
  fx.listeners['celikom-account-login']();
  replies.shift()({ok:true,status:'pending'});await tick();
  oldReply({ok:false,error:'invalid_session'});await stale;
  assert.match(fx.version.textContent,/на проверке/,'old account response cannot overwrite sign-in');
 } finally {globalThis.document=oldDocument;globalThis.localStorage=oldStorage}
});

test('stalled version and access checks time out, release their flags and recover on retry',async(t)=>{
 t.mock.timers.enable({apis:['setTimeout','Date']});
 const oldDocument=globalThis.document,oldStorage=globalThis.localStorage;
 globalThis.localStorage={getItem:()=>null,setItem(){},removeItem(){}};
 const fx=fixture();globalThis.document=fx.document;
 try {
  let stalled=true,finishOld;const transport=m=>stalled?new Promise(r=>{finishOld=r;}):Promise.resolve(m.action==='entitlement'?{ok:true,entitlement:access}:{ok:true,status:'none'});
  const v=initVersionStatus(transport),a=initAccessStatus(transport);
  const version=v(state('1944599')),auth=a();
  t.mock.timers.tick(30000);await Promise.all([version,auth]);
  assert.match(fx.version.textContent,/Не удалось проверить/);assert.match(fx.access.textContent,/Нет связи/);
  stalled=false;t.mock.timers.tick(15000);await v(state('1944599'));await a();
  assert.match(fx.version.textContent,/ещё не загружена/);assert.match(fx.access.textContent,/Пробный период/);
  finishOld?.({ok:true,status:'approved'});await Promise.resolve();assert.match(fx.version.textContent,/ещё не загружена/);
 }finally{globalThis.document=oldDocument;globalThis.localStorage=oldStorage}
});

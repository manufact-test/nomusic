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
test('closing and reopening shows saved access and song version synchronously without a loading rewrite',async()=>{
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
  assert.equal(reopened.access.textContent,expectedAccess,'no await before painting the saved expiry');
  assert.equal(reopened.version.textContent,expectedVersion,'no await before painting the saved version');
  const a=refreshAccess(),v=refreshVersion(state('144530503'));await tick();
  assert.equal(reopened.access.textContent,expectedAccess);assert.equal(reopened.version.textContent,expectedVersion);
  finishAccess({ok:true,entitlement:access});finishVersion({ok:true,status:'approved'});await Promise.all([a,v]);
  assert.deepEqual(reopened.changes,[],'identical fresh responses must not animate or rewrite text');
 }finally{globalThis.document=oldDocument;globalThis.localStorage=oldStorage}
});
test('a changed track cannot borrow the old approved version and delayed old responses cannot overwrite it',async()=>{
 const oldDocument=globalThis.document,oldStorage=globalThis.localStorage;
 globalThis.localStorage={getItem:()=>JSON.stringify({at:Date.now(),data:{trackId:'144530503',status:'approved'}}),setItem(){},removeItem(){}};
 const fx=fixture();globalThis.document=fx.document;
 try {
  const pending=new Map(),refresh=initVersionStatus(m=>new Promise(r=>pending.set(m.track_id,r)));
  const old=refresh(state('144530503')),fresh=refresh(state('38436680'));
  assert.match(fx.version.textContent,/Загрузка/);
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
  assert.match(fx.access.textContent,/Загрузка/);assert.match(fx.version.textContent,/Загрузка/);
  await refresh();await version(state('144530503'));
  fx.listeners['celikom-account-logout']();
  const reopen=fixture();globalThis.document=reopen.document;initVersionStatus(()=>new Promise(()=>{}));initAccessStatus(()=>new Promise(()=>{}));
  assert.match(reopen.access.textContent,/Войдите/);
  assert.match(reopen.version.textContent,/Загрузка/);
 }finally{globalThis.document=oldDocument;globalThis.localStorage=oldStorage}
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { initAccessStatus } from '../dist/unpacked/auth/access-status.js';
const tick = () => new Promise(r => setTimeout(r, 0));
const trial = {allowed:true,source:'trial',reason:'trial_active',valid_until:new Date(Date.now()+86400000).toISOString()};
function fixture() {
 const label={textContent:'',title:''}, events={};
 globalThis.document={querySelector:()=>label,addEventListener:(name,fn)=>events[name]=fn};
 return {label,events};
}
test('popup preview stays visible during background checking and is replaced by server refusal',async()=>{
 const old=globalThis.document,fx=fixture();
 try {
  let done; const live=new Promise(r=>done=r);
  const refresh=initAccessStatus(m=>m.action==='access-preview'?Promise.resolve({entitlement:trial}):live);
  const pending=refresh(); await tick(); assert.match(fx.label.textContent,/Пробный период до/);
  done({ok:false,error:'invalid_session'}); await pending; assert.match(fx.label.textContent,/Войдите/);
 }finally{globalThis.document=old}
});
test('late preview cannot overwrite server result; logout prevents an in-flight repaint',async()=>{
 const old=globalThis.document,fx=fixture();
 try {
  let previewDone,liveDone; let n=0;
  const refresh=initAccessStatus(m=>m.action==='access-preview'?new Promise(r=>previewDone=r):++n===1?Promise.resolve({ok:false,error:'invalid_session'}):new Promise(r=>liveDone=r));
  await refresh(); previewDone({entitlement:trial}); await tick(); assert.match(fx.label.textContent,/Войдите/);
  const pending=refresh(); fx.events['celikom-account-logout'](); liveDone({ok:true,entitlement:trial});await pending;
  assert.match(fx.label.textContent,/Войдите/);
 }finally{globalThis.document=old}
});

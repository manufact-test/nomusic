import test from 'node:test';
import assert from 'node:assert/strict';
import { initPromoPanel } from '../dist/unpacked/auth/promo-popup.js';
import { accessLabel } from '../dist/unpacked/auth/access-status.js';
function fixture() {
 const handlers={},events=[];
 const form={addEventListener:(name,fn)=>handlers[name]=fn};
 const code={value:''},button={disabled:false},note={textContent:''};
 const root={hidden:true,querySelector:q=>q==='form'?form:q==='input'?code:q==='button'?button:note};
 const previous=globalThis.document;
 globalThis.document={querySelector:()=>root,dispatchEvent:e=>events.push(e.type)};
 return {root,code,button,note,events,submit:()=>handlers.submit({preventDefault(){}}),restore:()=>globalThis.document=previous};
}
test('promo popup serializes submissions and refreshes access after success',async()=>{
 const f=fixture();let finish,calls=0;
 try{
  const panel=initPromoPanel(()=>{calls++;return new Promise(r=>finish=r)});panel.signed(true);f.code.value='TEST_CODE';
  const pending=f.submit();await f.submit();assert.equal(calls,1);assert.equal(f.button.disabled,true);
  finish({ok:true,already_activated:false,revoked:false});await pending;
  assert.equal(f.code.value,'');assert.equal(f.note.textContent,'Промокод активирован.');assert.deepEqual(f.events,['celikom-promo-activated']);
 }finally{f.restore()}
});
test('logout clears code and ignores a delayed redemption response',async()=>{
 const f=fixture();let finish;
 try{
  const panel=initPromoPanel(()=>new Promise(r=>finish=r));panel.signed(true);f.code.value='TEST_CODE';const pending=f.submit();panel.signed(false);
  finish({ok:true});await pending;assert.equal(f.root.hidden,true);assert.equal(f.note.textContent,'');assert.equal(f.code.value,'');assert.deepEqual(f.events,[]);
 }finally{f.restore()}
});
test('revoked replay is not presented as a fresh grant',async()=>{
 const f=fixture();try{const panel=initPromoPanel(async()=>({ok:true,already_activated:true,revoked:true}));panel.signed(true);await f.submit();assert.match(f.note.textContent,/отозвана/);}finally{f.restore()}
});
test('lifetime and dated promo labels are explicit and incident still takes precedence',()=>{
 assert.equal(accessLabel({allowed:true,source:'promo',valid_until:null,reason:'promo_active'}),'Промокод · доступ навсегда');
 assert.match(accessLabel({allowed:true,source:'promo',valid_until:new Date(Date.now()+86400000).toISOString(),reason:'promo_active'}),/^Промокод до/);
 assert.match(accessLabel({allowed:false,source:'promo',valid_until:null,reason:'service_incident'}),/Сбой интеграции/);
});

 test('Access dates use Moscow even when the computer timezone differs', () => {
  const saved=process.env.TZ;
  try {
    process.env.TZ='America/Los_Angeles';
    const label=accessLabel({allowed:true,source:'promo',valid_until:'2035-10-31T21:00:00Z'});
    assert.match(label,/1 ноября/);assert.match(label,/00:00/);assert.match(label,/Москва/);
  } finally { if(saved===undefined) delete process.env.TZ; else process.env.TZ=saved; }
});

import test from 'node:test';import assert from 'node:assert/strict';
import {initDiagnosticsButton} from '../dist/unpacked/popup/diagnostics-button.js';
const tick=()=>new Promise(r=>setTimeout(r,0));
function setup(show=false){
 const memory=new Map(),listeners={},handlers={},calls=[],pending=[];
 if(show)memory.set('celikom-popup-display-v1:diagnostics-hint',JSON.stringify({at:Date.now(),data:{show:true}}));
 const node={hidden:true,disabled:false,textContent:'Скопировать диагностику',addEventListener:(n,fn)=>handlers[n]=fn};
 globalThis.localStorage={getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v),removeItem:k=>memory.delete(k)};
 globalThis.document={querySelector:()=>node,addEventListener:(n,fn)=>listeners[n]=fn};
 const send=m=>{calls.push(m);return new Promise(resolve=>pending.push(resolve));};
 const controller=initDiagnosticsButton(send);return{node,listeners,handlers,calls,pending,memory,controller};
}
test('remembered owner keeps the footer label visible on reopen but cannot export before fresh permission',async()=>{
 const f=setup(true);assert.equal(f.node.hidden,false);assert.equal(f.node.disabled,true);
 await f.handlers.click();assert.equal(f.calls.length,1,'display hint must not authorize export');
 f.pending.shift()({ok:true,allowed:true});await tick();assert.equal(f.node.hidden,false);assert.equal(f.node.disabled,false);
 const click=f.handlers.click();assert.equal(f.calls.at(-1).type,'CELIKOM_DIAGNOSTICS_GET');
 f.pending.shift()({ok:false});await click;assert.equal(f.node.hidden,true);
});
test('ordinary account stays hidden and late owner response cannot reappear after logout',async()=>{
 const f=setup(false);f.pending.shift()({ok:true,allowed:false});await tick();assert.equal(f.node.hidden,true);await f.handlers.click();assert.equal(f.calls.length,1);
 const p=f.controller.refresh();f.listeners['celikom-account-logout']();f.pending.shift()({ok:true,allowed:true});await p;assert.equal(f.node.hidden,true);assert.equal(f.node.disabled,true);
});
test('network failure keeps remembered owner layout disabled rather than removing/readding it',async()=>{
 const f=setup(true);f.pending.shift()({ok:true,allowed:false,verified:false});await tick();assert.equal(f.node.hidden,false);assert.equal(f.node.disabled,true);
 await f.handlers.click();assert.equal(f.calls.length,1);
});

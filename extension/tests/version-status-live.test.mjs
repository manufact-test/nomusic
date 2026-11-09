import test from "node:test";
import assert from "node:assert/strict";
import {initVersionStatus} from "../dist/unpacked/popup/version-status.js";

test("old persisted pending is not shown before a fresh authoritative lookup",async()=>{
 const data=new Map();
 const now=Date.now();
 data.set("celikom-popup-display-v1:track",JSON.stringify({at:now,data:{id:"48591846",label:"Каменные цветы"}}));
 data.set("celikom-popup-display-v1:version",JSON.stringify({at:now,data:{trackId:"48591846",status:"pending"}}));
 globalThis.localStorage={getItem:key=>data.get(key)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};
 const node={hidden:false,textContent:""};
 globalThis.document={querySelector:()=>node,addEventListener:()=>{}};
 let release;const transport=()=>new Promise(resolve=>{release=resolve;});
 const refresh=initVersionStatus(transport);
 assert.match(node.textContent,/^Версия песни CELIKOM$/);
 assert.doesNotMatch(node.textContent,/на проверке|доступна/);
 const pending=refresh({track:{id:"48591846"},phase:"READY"});
 assert.match(node.textContent,/^Версия песни CELIKOM$/);
 release({ok:true,status:"none"});
 await pending;
 assert.match(node.textContent,/ещё не загружена/);
 assert.doesNotMatch(node.textContent,/на проверке/);
});

test("detected song prefetch is reused by Upload and invalidated after completed submission",async()=>{
 const previousDocument=globalThis.document,previousStorage=globalThis.localStorage;
 const mem=new Map(),node={textContent:"",hidden:false};
 globalThis.document={querySelector:()=>node,addEventListener:()=>{}};
 globalThis.localStorage={getItem:key=>mem.get(key)||null,setItem:(key,value)=>mem.set(key,value),removeItem:key=>mem.delete(key)};
 try {
  let resolves=[],calls=0;
  const transport=()=>{calls++;return new Promise(resolve=>resolves.push(resolve));};
  const refresh=initVersionStatus(transport),id="944530590";
  const initial=refresh({track:{id},phase:"READY"});
  const onClick=refresh.lookup(id);
  assert.equal(calls,1,"badge and upload share the same HTTP request");
  resolves.shift()({ok:true,status:"none"});
  await initial;
  assert.equal(await onClick,"none");
  assert.equal(await refresh.lookup(id),"none");
  assert.equal(calls,1,"warm result is instant");
  refresh.invalidate(id);
  const verified=refresh.lookup(id);
  assert.equal(calls,2,"successful upload invalidates obsolete absence");
  resolves.shift()({ok:true,status:"pending"});
  assert.equal(await verified,"pending");
  // Presence from a lookup is not shown until the next normal badge refresh.
  await refresh({track:{id},phase:"READY"});
  assert.match(node.textContent,/на проверке/);
 }finally{
  globalThis.document=previousDocument;
  globalThis.localStorage=previousStorage;
 }
});

test('fresh same-song display preview never authorizes upload and expires after five minutes',async()=>{
 const now=Date.now(),data=new Map(),node={hidden:false,textContent:''};
 const put=(key,value)=>data.set('celikom-popup-display-v1:'+key,JSON.stringify({at:now,data:value}));
 put('track',{id:'48591846'});put('version',{trackId:'48591846',status:'pending',displayCheckedAt:now});
 globalThis.localStorage={getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};
 globalThis.document={querySelector:()=>node,addEventListener:()=>{}};
 let finish,calls=0;const refresh=initVersionStatus(()=>{calls++;return new Promise(r=>finish=r)});
 assert.match(node.textContent,/на проверке/);
 const view=refresh({track:{id:'48591846'},phase:'READY'}),lookup=refresh.lookup('48591846');let settled=false;lookup.then(()=>settled=true);await Promise.resolve();assert.equal(settled,false);assert.equal(calls,1);
 finish({ok:true,status:'none'});await view;assert.equal(await lookup,'none');assert.match(node.textContent,/ещё не загружена/);
 put('version',{trackId:'48591846',status:'approved',displayCheckedAt:now-300001});initVersionStatus(()=>new Promise(()=>{}));assert.equal(node.textContent,'Версия песни CELIKOM');
});

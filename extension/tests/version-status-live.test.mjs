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
 assert.match(node.textContent,/Проверяем наличие/);
 assert.doesNotMatch(node.textContent,/на проверке|доступна/);
 const pending=refresh({track:{id:"48591846"},phase:"READY"});
 assert.match(node.textContent,/Проверяем наличие/);
 release({ok:true,status:"none"});
 await pending;
 assert.match(node.textContent,/ещё не загружена/);
 assert.doesNotMatch(node.textContent,/на проверке/);
});

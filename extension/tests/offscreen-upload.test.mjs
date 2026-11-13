import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";

const source = (await readFile(new URL("../dist/unpacked/offscreen/upload-worker.js",import.meta.url),"utf8"))
  .replace(/^import .*$/gm,"");
const id = "123e4567-e89b-42d3-a456-426614174000";
const task = {id,trackId:"50163063",durationMs:284400,artist:"Artist",title:"Title",album:"",filename:"sample.mp3",origin:"https://api.example",token:"a".repeat(64)};

function fixture() {
 const messages=[],instances=[],deleted=[];
 let handler=null;
 class XHR {
   constructor(){this.events=new Map();this.upload={addEventListener:(name,fn)=>this.events.set("upload:"+name,fn)};this.status=0;this.responseText="";}
   open(method,url){this.method=method;this.url=url;}
   setRequestHeader(name,value){if(name==="X-Celikom-Upload-Attempt")assert.equal(value,id);}
   addEventListener(name,fn){this.events.set(name,fn);}
   send(data){this.data=data;instances.push(this);}
   abort(){this.events.get("abort")?.();this.events.get("loadend")?.();}
   finish(){this.status=202;this.responseText='{"status":"pending","replacement_id":17}';this.events.get("loadend")?.();}
 }
 const chrome={runtime:{
   id:"ci",getURL:p=>"chrome-extension://ci/"+p,
   onMessage:{addListener:fn=>{handler=fn;}},
   sendMessage:async m=>{messages.push(m);return {ok:true};}
 }};
 vm.runInNewContext(source,{
   chrome,readStagedUpload:async()=>new Blob(["audio-bytes"]),deleteStagedUpload:async k=>{deleted.push(k);},
   fetch:async()=>({json:async()=>({baseUrl:"https://api.example"})}),
   XMLHttpRequest:XHR,FormData,Blob,Date,Promise,setInterval,clearInterval,URL,Math
 });
 const dispatch=(type,more={},sender={id:"ci",url:"chrome-extension://ci/background/service-worker.js"})=>{
   let result;handler({type,...more},sender,value=>{result=value});return result;
 };
 return {messages,instances,deleted,dispatch};
}
async function waitFor(predicate) {
 for(let n=0;n<40;n++){if(predicate())return;await new Promise(resolve=>setTimeout(resolve,5));}
 throw Error("timeout waiting for offscreen test");
}
test("background upload completes after the popup has disappeared",async()=>{
 const f=fixture();
 assert.equal(f.dispatch("CELIKOM_UPLOAD_EXECUTE",{task}).ok,true);
 await waitFor(()=>f.instances.length===1);
 // There is intentionally no popup or tab object in this test environment.
 const xhr=f.instances[0];
 xhr.events.get("upload:progress")({loaded:400,total:1000,lengthComputable:true});
 xhr.events.get("upload:load")();
 xhr.finish();
 await waitFor(()=>f.deleted.includes(id));
 assert.ok(f.messages.some(m=>m.phase==="transferring"&&m.percent===40));
 assert.ok(f.messages.some(m=>m.phase==="server_wait"));
 assert.ok(f.messages.some(m=>m.phase==="completed"));
 assert.equal(f.messages.find(m=>m.phase==="completed").httpStatus,202);
});
test("explicit cancellation stops in-flight offscreen transfer",async()=>{
 const f=fixture();
 f.dispatch("CELIKOM_UPLOAD_EXECUTE",{task});
 await waitFor(()=>f.instances.length===1);
 const denied=f.dispatch("CELIKOM_UPLOAD_INTERRUPT",{id},{id:"ci",url:"https://music.yandex.ru/",tab:{id:2}});
 assert.equal(denied,undefined);
 assert.equal(f.dispatch("CELIKOM_UPLOAD_INTERRUPT",{id}).ok,true);
 await waitFor(()=>f.deleted.includes(id));
 assert.ok(f.messages.some(m=>m.phase==="cancelled"));
});

test('quota rejection preserves retry time and is never automatically uploaded again',async()=>{
 const f=fixture();f.dispatch('CELIKOM_UPLOAD_EXECUTE',{task});await waitFor(()=>f.instances.length===1);
 const xhr=f.instances[0];xhr.status=429;xhr.responseText=JSON.stringify({error:'rate_limited',retry_after_seconds:1800});xhr.events.get('loadend')();
 await waitFor(()=>f.deleted.includes(id));
 const failed=f.messages.find(m=>m.phase==='failed');assert.equal(failed.code,'rate_limited');assert.equal(failed.httpStatus,429);assert.equal(failed.retryAfterSeconds,1800);assert.equal(f.instances.length,1);
});

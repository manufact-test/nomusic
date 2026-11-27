import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import {readFile} from "node:fs/promises";

const source = (await readFile(new URL("../dist/unpacked/offscreen/upload-worker.js",import.meta.url),"utf8"))
  .replace(/^import .*$/gm,"");
const id = "123e4567-e89b-42d3-a456-426614174000";
const task = {id,trackId:"50163063",durationMs:284400,artist:"Artist",title:"Title",album:"",filename:"sample.mp3",origin:"https://api.example",token:"a".repeat(64)};

function fixture(options = {}) {
 const messages=[],instances=[],deleted=[];
 let handler=null;
 class XHR {
   constructor(){this.events=new Map();this.upload={addEventListener:(name,fn)=>this.events.set("upload:"+name,fn)};this.status=0;this.responseText="";}
   open(method,url){this.method=method;this.url=url;}
   setRequestHeader(name,value){if(name==="X-Celikom-Upload-Attempt")assert.match(value,/^[a-f0-9-]{36}$/);}
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
   chrome,readStagedUpload:options.readFile|| (async()=>new Blob(["audio-bytes"])),deleteStagedUpload:async k=>{if(options.deleteFile)await options.deleteFile(k);deleted.push(k);},
   fetch:options.fetch|| (async()=>({json:async()=>({baseUrl:"https://api.example"})})),
   XMLHttpRequest:XHR,FormData,Blob,Date:options.Date||Date,Promise,setInterval:options.setInterval||setInterval,clearInterval:options.clearInterval||clearInterval,URL,Math
 });
 const dispatch=(type,more={},sender={id:"ci",url:"chrome-extension://ci/background/service-worker.js"})=>{
   let result;handler({type,...more},sender,value=>{result=value});return result;
 };
 const request=(type,more={})=>new Promise(resolve=>handler({type,...more},{id:"ci",url:"chrome-extension://ci/background/service-worker.js"},resolve));
 return {messages,instances,deleted,dispatch,request};
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
 assert.equal((await f.request("CELIKOM_UPLOAD_INTERRUPT",{id})).ok,true);
 await waitFor(()=>f.deleted.includes(id));
 assert.ok(f.messages.some(m=>m.phase==="cancelled"));
});

test('quota rejection preserves retry time and is never automatically uploaded again',async()=>{
 const f=fixture();f.dispatch('CELIKOM_UPLOAD_EXECUTE',{task});await waitFor(()=>f.instances.length===1);
 const xhr=f.instances[0];xhr.status=429;xhr.responseText=JSON.stringify({error:'rate_limited',retry_after_seconds:1800});xhr.events.get('loadend')();
 await waitFor(()=>f.deleted.includes(id));
 const failed=f.messages.find(m=>m.phase==='failed');assert.equal(failed.code,'rate_limited');assert.equal(failed.httpStatus,429);assert.equal(failed.retryAfterSeconds,1800);assert.equal(f.instances.length,1);
});

const deferred=()=>{let resolve;const promise=new Promise(r=>{resolve=r});return {promise,resolve}};
for(const stage of ['config','file'])test(`cancel during pending ${stage} prevents POST and immediate explicit retry waits for cleanup`,async()=>{
 const gate=deferred(),cleanup=deferred();let entered=false;
 const f=fixture(stage==='config'?{fetch:async()=>{entered=true;await gate.promise;return {json:async()=>({baseUrl:'https://api.example'})}},deleteFile:()=>cleanup.promise}
  :{readFile:async()=>{entered=true;await gate.promise;return new Blob(['audio'])},deleteFile:()=>cleanup.promise});
 f.dispatch('CELIKOM_UPLOAD_EXECUTE',{task});await waitFor(()=>entered);
 let cancelDone=false;const cancel=f.request('CELIKOM_UPLOAD_INTERRUPT',{id}).then(r=>{cancelDone=true;return r});
 const retry=f.request('CELIKOM_UPLOAD_EXECUTE',{task});
 await new Promise(setImmediate);assert.equal(cancelDone,false);assert.equal(f.instances.length,0);
 assert.equal(f.messages.some(x=>x.phase==='cancelled'),false,'do not enable Retry before old staging is cleaned');
 cleanup.resolve();assert.equal((await cancel).ok,true);assert.equal((await retry).ok,true);
 gate.resolve();await waitFor(()=>f.instances.length===1);
 f.instances[0].finish();await waitFor(()=>f.messages.some(x=>x.phase==='completed'));
 assert.equal(f.instances.length,1,'cancelled preparation must never send its old POST');
});
test('partial transfer idle is stopped without replay and keeps exact final progress',async()=>{
 let now=0,tick;const f=fixture({Date:{now:()=>now},setInterval:fn=>{tick=fn;return 1},clearInterval(){}});
 f.dispatch('CELIKOM_UPLOAD_EXECUTE',{task});await waitFor(()=>f.instances.length===1);const xhr=f.instances[0];
 xhr.events.get('upload:progress')({loaded:130,total:1000,lengthComputable:true});
 now=16000;tick();await waitFor(()=>f.messages.some(x=>x.phase==='waiting'));
 assert.equal(f.messages.find(x=>x.phase==='waiting').percent,13);
 now=31000;tick();await waitFor(()=>f.messages.some(x=>x.phase==='failed'));
 const failure=f.messages.find(x=>x.phase==='failed');assert.equal(failure.code,'stalled');assert.equal(failure.percent,13);assert.equal(failure.sent,130);
 assert.equal(f.instances.length,1);
});
test('actual byte progress, including unchanged percentages, resets idle deadline; server wait is separate',async()=>{
 let now=0,tick;const f=fixture({Date:{now:()=>now},setInterval:fn=>{tick=fn;return 1},clearInterval(){}});
 f.dispatch('CELIKOM_UPLOAD_EXECUTE',{task});await waitFor(()=>f.instances.length===1);const xhr=f.instances[0];
 for(let i=1;i<=6;i++){now=i*20000;xhr.events.get('upload:progress')({loaded:i,total:1000,lengthComputable:true});tick();}
 assert.equal(f.messages.some(x=>x.phase==='failed'),false);
 xhr.events.get('upload:load')();now+=60000;tick();assert.equal(f.messages.some(x=>x.phase==='failed'),false);
 xhr.finish();await waitFor(()=>f.messages.some(x=>x.phase==='completed'));
});
test('duplicate delivery of the active attempt is acknowledged without a second POST',async()=>{
 const f=fixture();f.dispatch('CELIKOM_UPLOAD_EXECUTE',{task});await waitFor(()=>f.instances.length===1);
 assert.equal(f.dispatch('CELIKOM_UPLOAD_EXECUTE',{task}).ok,true);assert.equal(f.instances.length,1);
 f.instances[0].finish();await waitFor(()=>f.messages.some(x=>x.phase==='completed'));
});

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const script=fs.readFileSync(new URL("./dist/renderer.js",import.meta.url),"utf8");
const origin="https://api.celikom.example";
const tick=()=>new Promise(r=>setImmediate(r));
function harness() {
 const clock={now:Date.now()},handlers={},intervals=[];
 class Resource {
   async getFileInfo(p){return {downloadInfo:{trackId:String(p.trackId),url:"https://yandex.example/old"}};}
 }
 class Player {
   reasons=[];urls=[];
   snapshot={queueState:{currentEntity:{value:{entity:{data:{meta:{id:"123"}}}}}},
     playerState:{status:{value:"playing"},progress:{value:{position:77}}}};
   get state(){return this.snapshot;}
   async reloadEntity(reason) {
     this.reasons.push(reason);
     const currentId=String(this.snapshot.queueState.currentEntity.value.entity.data.meta.id);
     const data=await new Resource().getFileInfo({trackId:currentId});
     this.urls.push(data.downloadInfo.url);
   }
 }
 const req=id=>id==="resource"?{Resource}:id===7123?{VE:Player}:null;
 req.m={resource:function factory(){return '"get-file-info"';},7123:function player(){}};
 const chunks=[];chunks.push=p=>{p[2](req);return 1;};chunks.pop=()=>null;
 const window={location:{protocol:"musicapplication:",hostname:"desktop",origin:"null"},
    webpackChunk_N_E:chunks,addEventListener:(name,fn)=>{handlers[name]=fn;}};
 vm.runInNewContext(script,{window,URL,AbortController,
   Date:class extends Date{static now(){return clock.now;}},
   setTimeout,clearTimeout,setInterval:fn=>{intervals.push(fn);return intervals.length;},clearInterval:()=>{},
   console:{info:()=>{}}},{timeout:2000});
 const player=new Player();
 window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
 void player.state;
 for(const fn of intervals) fn();
 return {clock,window,player,handlers};
}
function signedGrant(id="123"){
 const expires=Math.floor((Date.now()+120000)/1000);
 return {trackId:id,approved:true,entitled:true,mimeType:"audio/mpeg",
   audioUrl:origin+"/api/v1/audio/"+id+"?token="+"a".repeat(64)+"&expires="+expires,
   expiresAt:expires*1000};
}
test("W175 cached current Yandex source revalidates only exact approved track after settling",async()=>{
 const r=harness(),w=r.window;
 w.__celikomBridgeNativeCheckDeferred();
 assert.equal(w.__celikomBridgeNativeDrain().length,0);
 assert.deepEqual(r.player.reasons,[]);
 r.clock.now+=4000;
 w.__celikomBridgeNativeCheckDeferred();await tick();
 const pending=w.__celikomBridgeNativeDrain();
 assert.equal(pending.length,1);assert.equal(pending[0].trackId,"123");
 assert.deepEqual(r.player.reasons,[]);
 w.__celikomBridgeNativeReceive(pending[0].requestId,signedGrant());
 for(let i=0;i<8;i++){await tick();for(const p of w.__celikomBridgeNativeDrain())
   w.__celikomBridgeNativeReceive(p.requestId,signedGrant());}
 assert.deepEqual(r.player.reasons,["QUALITY_CHANGE"]);
 assert.ok(r.player.urls[0].startsWith(origin+"/api/v1/audio/123?"));
 assert.equal(r.player.state.playerState.progress.value.position,77);
 r.clock.now+=5000;w.__celikomBridgeNativeCheckDeferred();await tick();
 assert.equal(w.__celikomBridgeNativeDrain().length,0);
 r.handlers.beforeunload();
});
test("W175 unknown song or stopped bridge cannot force initial reload",async()=>{
 const r=harness(),w=r.window;r.clock.now+=4000;
 w.__celikomBridgeNativeCheckDeferred();await tick();
 const p=w.__celikomBridgeNativeDrain();assert.equal(p.length,1);
 w.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
 w.__celikomBridgeNativeReceive(p[0].requestId,signedGrant());
 await tick();await tick();
 assert.deepEqual(r.player.reasons,[]);
 r.handlers.beforeunload();
});

test("W178: next current song with cached original gets exactly one approved source-only reload",async()=>{
 const r=harness(),w=r.window;
 r.clock.now+=4000;
 w.__celikomBridgeNativeCheckDeferred();await tick();
 const initial=w.__celikomBridgeNativeDrain();
 assert.equal(initial.length,1);
 assert.equal(initial[0].trackId,"123");
 w.__celikomBridgeNativeReceive(initial[0].requestId,null);
 for(let i=0;i<4;i++)await tick();
 assert.equal(r.player.reasons.length,0);
 // The first unapproved current song must not suppress a later authorized one.
 r.player.snapshot.queueState.currentEntity.value.entity.data.meta.id="456";
 r.clock.now+=100;
 w.__celikomBridgeNativeCheckDeferred();await tick();
 assert.equal(w.__celikomBridgeNativeDrain().length,0);
 r.clock.now+=4000;
 w.__celikomBridgeNativeCheckDeferred();await tick();
 const pending=w.__celikomBridgeNativeDrain();
 assert.equal(pending.length,1);
 assert.equal(pending[0].trackId,"456");
 w.__celikomBridgeNativeReceive(pending[0].requestId,signedGrant("456"));
 for(let i=0;i<8;i++){
   await tick();
   for(const p of w.__celikomBridgeNativeDrain())
     w.__celikomBridgeNativeReceive(p.requestId,signedGrant("456"));
 }
 assert.deepEqual(r.player.reasons,["QUALITY_CHANGE"]);
 assert.ok(r.player.urls[0].startsWith(origin+"/api/v1/audio/456?"));
 r.clock.now+=10000;
 w.__celikomBridgeNativeCheckDeferred();await tick();
 assert.equal(w.__celikomBridgeNativeDrain().length,0);
 r.handlers.beforeunload();
});
test("W178: absent replacement for the next song never reloads Yandex",async()=>{
 const r=harness(),w=r.window;
 r.clock.now+=4000;w.__celikomBridgeNativeCheckDeferred();await tick();
 for(const p of w.__celikomBridgeNativeDrain())w.__celikomBridgeNativeReceive(p.requestId,null);
 await tick();
 r.player.snapshot.queueState.currentEntity.value.entity.data.meta.id="789";
 r.clock.now+=100;w.__celikomBridgeNativeCheckDeferred();await tick();
 r.clock.now+=4000;w.__celikomBridgeNativeCheckDeferred();await tick();
 const pending=w.__celikomBridgeNativeDrain();
 assert.equal(pending.length,1);
 assert.equal(pending[0].trackId,"789");
 w.__celikomBridgeNativeReceive(pending[0].requestId,null);
 for(let i=0;i<8;i++)await tick();
 assert.deepEqual(r.player.reasons,[]);
 r.handlers.beforeunload();
});

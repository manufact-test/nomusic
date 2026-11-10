import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const bundle = fs.readFileSync(new URL("./dist/renderer.js", import.meta.url), "utf8");
const origin = "https://api.celikom.example";
const expiry = Math.floor((Date.now()+120000)/1000);
const makeGrant = (id="123") => ({
  trackId:id,approved:true,entitled:true,mimeType:"audio/mpeg",
  audioUrl:origin+"/api/v1/audio/"+id+"?token="+"a".repeat(64)+"&expires="+expiry,
  expiresAt:expiry*1000
});
function createRenderer({
  hostname="desktop",protocol="musicapplication:",originValue="null"
}={}) {
  const logs=[],handlers={};
  class Resource {
    async getFileInfo(params) {
      return {
        responseTime:13,
        downloadInfo:{trackId:String(params.trackId),key:"yandex-drm",
          url:"https://official.yandex.example/stream",codec:"aac"}
      };
    }
    async getFileInfoBatch() {
      return {downloadInfos:[
        {trackId:"123",key:"drm",url:"https://official.yandex.example/stream"},
        {trackId:"456",key:"drm",url:"https://official.yandex.example/next"}
      ]};
    }
    pause() {return "YANDEX_PAUSED"}
    seek() {return "YANDEX_SEEKED"}
  }
  const originalPause=Resource.prototype.pause,originalSeek=Resource.prototype.seek;
  const requireFn=id=>id==="native-resource"?{Resource}:null;
  requireFn.m={"native-resource":function resourceFactory(){return '"get-file-info"';}};
  const chunks=[];
  chunks.push=packet=>{packet[2](requireFn);return 1;};
  chunks.pop=()=>null;
  const window={
    location:{hostname,protocol,origin:originValue},
    webpackChunk_N_E:chunks,
    addEventListener:(type,fn)=>{handlers[type]=fn;}
  };
  const context={
    window,console:{info:(...args)=>logs.push(args.join(" "))},
    URL,AbortController,fetch:undefined,
    setInterval:()=>1,clearInterval:()=>{},
    setTimeout,clearTimeout
  };
  vm.runInNewContext(bundle,context,{timeout:2000});
  return {window,Resource,logs,handlers,originalPause,originalSeek};
}
async function tick() {
  await new Promise(resolve=>setImmediate(resolve));
}

test("real bundled renderer integrates one approved source, keeps Yandex pause/seek",async()=>{
  const r=createRenderer();
  assert.equal(typeof r.window.__celikomBridgeNativeSetState,"function");
  assert.ok(r.logs.some(s=>s.includes("Native file-info source connector attached")));
  r.window.__celikomBridgeNativeSetState({
    enabled:true,signedIn:true,apiOrigin:origin
  });
  const player=new r.Resource();
  const pending=player.getFileInfo({trackId:"123"});
  await tick();
  const requests=r.window.__celikomBridgeNativeDrain();
  assert.equal(requests.length,1);
  assert.equal(requests[0].trackId,"123");
  r.window.__celikomBridgeNativeReceive(requests[0].requestId,makeGrant("123"));
  const result=await pending;
  assert.equal(result.responseTime,13);
  assert.equal(result.downloadInfo.url,makeGrant("123").audioUrl);
  assert.equal(result.downloadInfo.key,undefined);
  assert.equal(r.window.__celikomBridgeNativeStatus(),"NATIVE_MAPPING_ACCEPTED");
  assert.strictEqual(r.Resource.prototype.pause,r.originalPause);
  assert.strictEqual(r.Resource.prototype.seek,r.originalSeek);
  assert.equal(player.pause(),"YANDEX_PAUSED");
  assert.equal(player.seek(),"YANDEX_SEEKED");
  r.handlers.beforeunload();
  assert.equal(r.window.__celikomBridgeNativeDrain,undefined);
});
test("native Next with no approved grant returns Yandex original stream",async()=>{
  const r=createRenderer();
  r.window.__celikomBridgeNativeSetState({
    enabled:true,signedIn:true,apiOrigin:origin
  });
  const pending=new r.Resource().getFileInfo({trackId:"456"});
  await tick();
  const req=r.window.__celikomBridgeNativeDrain();
  assert.equal(req.length,1);
  assert.equal(req[0].trackId,"456");
  r.window.__celikomBridgeNativeReceive(req[0].requestId,null);
  const result=await pending;
  assert.equal(result.downloadInfo.url,"https://official.yandex.example/stream");
  r.handlers.beforeunload();
});
test("native batch-first request performs exact-ID source injection",async()=>{
  const r=createRenderer();
  r.window.__celikomBridgeNativeSetState({
    enabled:true,signedIn:true,apiOrigin:origin
  });
  const pending=new r.Resource().getFileInfoBatch({trackIds:["123","456"]});
  await tick();
  const req=r.window.__celikomBridgeNativeDrain();
  assert.deepEqual([...req.map(x=>x.trackId)],["123","456"]);
  for(const item of req) {
    r.window.__celikomBridgeNativeReceive(item.requestId,
      item.trackId==="123"?makeGrant("123"):null);
  }
  const result=await pending;
  assert.equal(result.downloadInfos[0].url,makeGrant("123").audioUrl);
  assert.equal(result.downloadInfos[1].url,"https://official.yandex.example/next");
  r.handlers.beforeunload();
});
test("stop during native relay keeps Yandex source and clears queued requests",async()=>{
  const r=createRenderer();
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  const pending=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  assert.equal(r.window.__celikomBridgeNativeDrain().length,0);
  const output=await pending;
  assert.equal(output.downloadInfo.key,"yandex-drm");
  r.handlers.beforeunload();
});
test("untrusted scheme never installs CELIKOM API into a foreign renderer",()=>{
  const r=createRenderer({hostname:"evil",protocol:"musicapplication:"});
  assert.equal(r.window.__celikomBridgeNativeDrain,undefined);
  assert.equal(r.Resource.prototype.getFileInfo.name,"getFileInfo");
});

test("diagnostic queue reports native mapping as NOT audio verification and never contains a signed URL",async()=>{
  const r=createRenderer();
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  const pending=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  for (const item of r.window.__celikomBridgeNativeDrain())
    r.window.__celikomBridgeNativeReceive(item.requestId,makeGrant(item.trackId));
  await pending;
  const events=r.window.__celikomBridgeNativeDrainDiagnostics();
  const code=events.map(([value])=>value);
  assert.ok(code.includes("RESOURCE_HOOK_ATTACHED"));
  assert.ok(code.includes("RENDERER_STATE_ON"));
  assert.ok(code.includes("SOURCE_MAPPED"));
  assert.ok(code.includes("FILEINFO_NATIVE_KEY_FIELD"));
  assert.ok(code.includes("FILEINFO_NATIVE_CODEC_AAC"));
  assert.ok(events.some(([value,id])=>value==="SOURCE_MAPPED"&&id==="123"));
  assert.ok(events.some(([value,id])=>value==="FILEINFO_NATIVE_KEY_FIELD"&&id==="123"));
  assert.ok(!code.includes("PLAYER_AUDIO_AUDIBLE"),"source mapping must not be called audible playback");
  const serialized=JSON.stringify(events);
  assert.ok(!serialized.includes("token=")&&!serialized.includes("api.celikom.example"));
  r.handlers.beforeunload();
});

test("W48 structural native file-info witness exports only field presence, never crypto values",async()=>{
  const r=createRenderer();
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  const pending=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  const req=r.window.__celikomBridgeNativeDrain();
  for(const item of req) r.window.__celikomBridgeNativeReceive(item.requestId,makeGrant(item.trackId));
  await pending;
  const events=r.window.__celikomBridgeNativeDrainDiagnostics();
  const names=events.map(x=>x[0]);
  assert.ok(names.includes("FILEINFO_NATIVE_KEY_FIELD"));
  assert.ok(names.includes("FILEINFO_NATIVE_CODEC_AAC"));
  assert.ok(!JSON.stringify(events).includes("yandex-drm"));
  assert.ok(!JSON.stringify(events).includes("official.yandex.example"));
  assert.ok(!JSON.stringify(events).includes("token="));
  assert.ok(!names.includes("PLAYER_ENGINE_STARTED"));
  assert.ok(!names.includes("PLAYER_AUDIO_AUDIBLE"));
  r.handlers.beforeunload();
});

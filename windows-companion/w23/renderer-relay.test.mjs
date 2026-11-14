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
  hostname="desktop",protocol="musicapplication:",originValue="null",withPlayer=false
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
  class NativeYandexPlayer {
    constructor({trackId="123",status="playing",position=57.1}={}) {
      this.reloadReasons=[];
      this.mediaSources=[];
      this.snapshot={
        queueState:{currentEntity:{value:{entity:{data:{meta:{id:trackId}}}}}},
        playerState:{status:{value:status},progress:{value:{position}}}
      };
    }
    get state() {return this.snapshot;}
    async reloadEntity(reason) {
      this.reloadReasons.push(reason);
      const id=this.snapshot.queueState.currentEntity.value.entity.data.meta.id;
      const response=await new Resource().getFileInfo({trackId:id});
      this.mediaSources.push(response.downloadInfo.url);
      return response;
    }
  }
  const requireFn=id=>id==="native-resource"?{Resource}:
    id===7123 && withPlayer?{VE:NativeYandexPlayer}:null;
  requireFn.m={"native-resource":function resourceFactory(){return '"get-file-info"';}};
  if(withPlayer)requireFn.m[7123]=function actualYandexPlaybackFactory(){};
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
  return {window,Resource,NativeYandexPlayer,logs,handlers,originalPause,originalSeek};
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
  assert.equal(result.downloadInfo.url,makeGrant("123").audioUrl+"&celikom_native_query_guard=0");
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
  assert.equal(result.downloadInfos[0].url,makeGrant("123").audioUrl+"&celikom_native_query_guard=0");
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
test("W58 real renderer Stop blocks all future grants while already-returned Yandex media source is immutable",async()=>{
  const r=createRenderer(),player=new r.Resource();
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  const prior=player.getFileInfo({trackId:"123"});
  await tick();
  const queue=r.window.__celikomBridgeNativeDrain();
  assert.equal(queue.length,1);
  r.window.__celikomBridgeNativeReceive(queue[0].requestId,makeGrant("123"));
  const resident=await prior;
  assert.equal(resident.downloadInfo.url,makeGrant("123").audioUrl+"&celikom_native_query_guard=0");
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  assert.equal(r.window.__celikomBridgeNativeStatus(),"ORIGINAL");
  const same=await player.getFileInfo({trackId:"123"});
  const next=await player.getFileInfo({trackId:"456"});
  const batch=await player.getFileInfoBatch({trackIds:["123","456"]});
  assert.equal(same.downloadInfo.url,"https://official.yandex.example/stream");
  assert.equal(next.downloadInfo.url,"https://official.yandex.example/stream");
  assert.equal(batch.downloadInfos[0].url,"https://official.yandex.example/stream");
  assert.equal(r.window.__celikomBridgeNativeDrain().length,0);
  assert.equal(resident.downloadInfo.url,makeGrant("123").audioUrl+"&celikom_native_query_guard=0",
    "file-info already delivered to Yandex is not retrospectively changed");
  r.handlers.beforeunload();
});

test("W60 START/STOP re-requests current source through real Yandex position-preserving reload",async()=>{
  const r=createRenderer({withPlayer:true}),player=new r.NativeYandexPlayer();
  const initialGetter=Object.getOwnPropertyDescriptor(r.NativeYandexPlayer.prototype,"state").get;
  assert.ok(r.window.__celikomBridgeNativeDrain);
  // Initial state on Yandex startup must not cause an unrequested second play.
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state; // Yandex UI reads its existing playback observable.
  await tick();
  assert.equal(player.reloadReasons.length,0);
  // The first native source is already approved and has been consumed.
  const first=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  const initial=r.window.__celikomBridgeNativeDrain();
  assert.equal(initial.length,1);
  r.window.__celikomBridgeNativeReceive(initial[0].requestId,makeGrant("123"));
  assert.equal((await first).downloadInfo.url,
    makeGrant("123").audioUrl+"&celikom_native_query_guard=0");
  // STOP must replace the ALREADY-LOADED source, not merely future grants.
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  await tick();
  await tick();
  assert.deepEqual(player.mediaSources,["https://official.yandex.example/stream"]);
  assert.deepEqual(player.reloadReasons,["QUALITY_CHANGE"]);
  assert.equal(player.state.playerState.progress.value.position,57.1);
  assert.equal(player.state.playerState.status.value,"playing");
  assert.equal(r.window.__celikomBridgeNativeStatus(),"ORIGINAL");
  // START must reload the same current track again, now with CELIKOM source.
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  await tick();
  const jobs=r.window.__celikomBridgeNativeDrain();
  assert.equal(jobs.length,1);
  assert.equal(jobs[0].trackId,"123");
  r.window.__celikomBridgeNativeReceive(jobs[0].requestId,makeGrant("123"));
  await tick();
  await tick();
  assert.equal(player.mediaSources.length,2);
  assert.equal(player.mediaSources[1],
    makeGrant("123").audioUrl+"&celikom_native_query_guard=0");
  assert.equal(player.state.playerState.status.value,"playing");
  assert.equal(player.state.playerState.progress.value.position,57.1);
  const diagnosticCodes=r.window.__celikomBridgeNativeDrainDiagnostics().map(x=>x[0]);
  assert.ok(diagnosticCodes.includes("NATIVE_TOGGLE_RELOAD_REQUEST"));
  assert.ok(diagnosticCodes.includes("NATIVE_TOGGLE_RELOAD_OK"));
  r.handlers.beforeunload();
  assert.equal(r.NativeYandexPlayer.prototype.reloadEntity.name,"reloadEntity");
  assert.notStrictEqual(initialGetter,undefined);
});

test("W99 verified CELIKOM source-left schedules one bounded current-track recovery",async()=>{
  const r=createRenderer({withPlayer:true});
  const player=new r.NativeYandexPlayer({trackId:"123",position:82.25});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state;
  const first=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  const initial=r.window.__celikomBridgeNativeDrain();
  assert.equal(initial.length,1);
  r.window.__celikomBridgeNativeReceive(initial[0].requestId,makeGrant("123"));
  assert.ok((await first).downloadInfo.url.includes("/api/v1/audio/123?"));
  assert.equal(r.window.__celikomBridgeNativeRecoverSourceLeft("456"),false,
    "never recover an unrelated/prefetched track");
  assert.equal(r.window.__celikomBridgeNativeRecoverSourceLeft("123"),true);
  const scheduledDiagnostics=r.window.__celikomBridgeNativeDrainDiagnostics();
  assert.ok(scheduledDiagnostics.some(x=>
    x[0]==="SOURCE_LEFT_CURRENT_RECOVERY_SCHEDULED"&&x[1]==="123"),
    "the recovery schedule must be visible before its asynchronous retry");
  assert.equal(r.window.__celikomBridgeNativeRecoverSourceLeft("123"),false,
    "one source-left transition cannot create duplicate recovery timers");
  await new Promise(resolve=>setTimeout(resolve,720));
  // The recovery prime and the subsequent position-preserving Yandex reload
  // can each ask for an exact-ID grant. Drain both bridge turns, not just the
  // first one, before asserting the decoder source.
  for (let i=0;i<4;i++) {
    await tick();
    const retryJobs=r.window.__celikomBridgeNativeDrain();
    for (const job of retryJobs)
      r.window.__celikomBridgeNativeReceive(job.requestId,makeGrant("123"));
    await tick();
  }
  await new Promise(resolve=>setTimeout(resolve,220));
  for (let i=0;i<4;i++) {
    await tick();
    const reloadJobs=r.window.__celikomBridgeNativeDrain();
    for (const job of reloadJobs)
      r.window.__celikomBridgeNativeReceive(job.requestId,makeGrant("123"));
    await tick();
  }
  assert.deepEqual(player.reloadReasons,["QUALITY_CHANGE"]);
  assert.equal(player.mediaSources[0],
    makeGrant("123").audioUrl+"&celikom_native_query_guard=0");
  assert.equal(player.state.playerState.progress.value.position,82.25);
  assert.equal(player.state.playerState.status.value,"playing");
  r.handlers.beforeunload();
});

test("W131 verified source-left invalidates stale mapping before VPN state-off",async()=>{
  const r=createRenderer({withPlayer:true});
  const player=new r.NativeYandexPlayer({trackId:"123",position:82.25});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state;
  const first=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  const initial=r.window.__celikomBridgeNativeDrain();
  assert.equal(initial.length,1);
  r.window.__celikomBridgeNativeReceive(initial[0].requestId,makeGrant("123"));
  assert.ok((await first).downloadInfo.url.includes("/api/v1/audio/123?"));

  // Main-process CDP invokes this only after proving that the current decoder
  // left its previously verified CELIKOM signed source.
  assert.equal(r.window.__celikomBridgeNativeRecoverSourceLeft("123"),true);
  // A VPN/entitlement state transition races the scheduled recovery. Because
  // the decoder is already on the original source, Stop must not issue a
  // second QUALITY_CHANGE reload that would interrupt it with an audible pop.
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  await tick();await tick();
  assert.deepEqual(player.reloadReasons,[]);
  assert.equal(player.state.playerState.progress.value.position,82.25);
  assert.equal(player.state.playerState.status.value,"playing");
  const codes=r.window.__celikomBridgeNativeDrainDiagnostics().map(x=>x[0]);
  assert.ok(codes.includes("SOURCE_LEFT_CURRENT_RECOVERY_SCHEDULED"));
  assert.ok(codes.includes("NATIVE_ORIGINAL_SOURCE_NO_RELOAD"));
  assert.ok(!codes.includes("NATIVE_ORIGINAL_SOURCE_RESTORE"));
  r.handlers.beforeunload();
});

test("W132 VPN A-to-B revalidation keeps a source-left original track untouched",async()=>{
  const r=createRenderer({withPlayer:true});
  const player=new r.NativeYandexPlayer({trackId:"123",position:82.25});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state;
  const first=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  const initial=r.window.__celikomBridgeNativeDrain();
  assert.equal(initial.length,1);
  r.window.__celikomBridgeNativeReceive(initial[0].requestId,makeGrant("123"));
  assert.ok((await first).downloadInfo.url.includes("/api/v1/audio/123?"));

  // CDP has already proved the current decoder returned to Yandex original.
  assert.equal(r.window.__celikomBridgeNativeRecoverSourceLeft("123"),true);

  // VPN A→B: entitlement check temporarily suspends future replacements.
  // It must not reload a decoder that has already returned to original.
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  await tick();await tick();
  assert.deepEqual(player.reloadReasons,[]);
  assert.equal(player.state.playerState.progress.value.position,82.25);
  assert.equal(player.state.playerState.status.value,"playing");

  // VPN B is healthy again. A fresh authenticated resolve says this exact
  // track has no active replacement. Revalidation must leave Yandex in place.
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  await tick();
  const revalidate=r.window.__celikomBridgeNativeDrain();
  assert.equal(revalidate.length,1);
  assert.equal(revalidate[0].trackId,"123");
  r.window.__celikomBridgeNativeReceive(revalidate[0].requestId,null);
  await tick();await tick();
  assert.deepEqual(player.reloadReasons,[]);
  assert.equal(player.state.playerState.progress.value.position,82.25);
  assert.equal(player.state.playerState.status.value,"playing");

  const codes=r.window.__celikomBridgeNativeDrainDiagnostics().map(x=>x[0]);
  assert.ok(codes.includes("SOURCE_LEFT_CURRENT_ALREADY_ORIGINAL"));
  assert.ok(codes.includes("NATIVE_ORIGINAL_SOURCE_NO_RELOAD"));
  assert.ok(!codes.includes("NATIVE_ORIGINAL_SOURCE_RESTORE"));
  assert.ok(!codes.includes("NATIVE_REPLACEMENT_SOURCE_RELOAD"));
  r.handlers.beforeunload();
});

test("W89 unfetched signed source: exactly one current-track native reload, preserve queue, position and pause",async()=>{
  const r=createRenderer({withPlayer:true});
  const player=new r.NativeYandexPlayer({trackId:"123",position:82.25});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state;
  const original=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  const job=r.window.__celikomBridgeNativeDrain();
  assert.equal(job.length,1);
  r.window.__celikomBridgeNativeReceive(job[0].requestId,makeGrant("123"));
  await original;
  assert.equal(r.window.__celikomBridgeNativeRefreshUnfetched("456"),false,
    "never reload an unrelated/preloaded song");
  assert.equal(r.window.__celikomBridgeNativeRefreshUnfetched("123"),true);
  assert.equal(r.window.__celikomBridgeNativeRefreshUnfetched("123"),false,
    "duplicate signed-media observer events cannot cause a reload loop");
  await tick();
  await tick();
  assert.deepEqual(player.reloadReasons,["QUALITY_CHANGE"]);
  assert.equal(player.mediaSources[0],
    makeGrant("123").audioUrl+"&celikom_native_query_guard=0");
  assert.equal(player.state.playerState.progress.value.position,82.25);
  assert.equal(player.state.playerState.status.value,"playing");
  assert.ok(r.window.__celikomBridgeNativeDrainDiagnostics().some(x=>
    x[0]==="SOURCE_UNFETCHED_CURRENT_REFRESH_OK"&&x[1]==="123"));
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  assert.equal(r.window.__celikomBridgeNativeRefreshUnfetched("123"),false,
    "explicit Stop prevents any source-refresh attempt");
  r.handlers.beforeunload();
  assert.equal(r.window.__celikomBridgeNativeRefreshUnfetched,undefined);
});

test("W60 paused native Yandex reload retains pause and position without auto-play",async()=>{
  const r=createRenderer({withPlayer:true});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  const p=new r.NativeYandexPlayer({trackId:"123",status:"paused",position:99.2});
  void p.state;
  const pending=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  const request=r.window.__celikomBridgeNativeDrain();
  assert.equal(request.length,1);
  r.window.__celikomBridgeNativeReceive(request[0].requestId,makeGrant("123"));
  await pending;
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  await tick();await tick();
  assert.equal(p.mediaSources[0],"https://official.yandex.example/stream");
  assert.equal(p.state.playerState.status.value,"paused");
  assert.equal(p.state.playerState.progress.value.position,99.2);
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

test("W50 renderer bundle cannot generate the old false-positive 32-byte audio probe",()=>{
  assert.ok(!bundle.includes("AUDIO_PROBE_STARTED"),"no synthetic audio probe codes in owner bundle");
  assert.ok(!bundle.includes("bytes=0-31"),"no separate diagnostic audio GET");
  assert.ok(bundle.includes("PLAYER_AUDIO_RESOURCE_TIMING_SEEN"),
    "resource timing is attributed to native media or preloading only");
});


test("W76: local bridge timeout recovers already-playing Yandex source without restarting player",async()=>{
  const r=createRenderer({withPlayer:true});
  const nativePlayer=new r.NativeYandexPlayer({trackId:"123",position:67.4});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void nativePlayer.state;
  const first=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  const initial=r.window.__celikomBridgeNativeDrain();
  assert.equal(initial.length,1);
  assert.equal(initial[0].trackId,"123");
  r.window.__celikomBridgeNativeReceive(initial[0].requestId,{transient:true});
  assert.equal((await first).downloadInfo.url,"https://official.yandex.example/stream",
    "first failure must play original, not stall playback");
  await new Promise(resolve=>setTimeout(resolve,760));
  const retries=r.window.__celikomBridgeNativeDrain();
  assert.equal(retries.length,1);
  assert.equal(retries[0].trackId,"123");
  assert.equal(retries[0].recovery,true,
    "only recovery is authorized a longer transport deadline");
  r.window.__celikomBridgeNativeReceive(retries[0].requestId,makeGrant("123"));
  await new Promise(resolve=>setTimeout(resolve,220));
  assert.deepEqual(nativePlayer.reloadReasons,["QUALITY_CHANGE"],
    "native Yandex already-playing entity reloads only its existing source");
  assert.equal(nativePlayer.mediaSources[0],
    makeGrant("123").audioUrl+"&celikom_native_query_guard=0");
  assert.equal(nativePlayer.state.playerState.progress.value.position,67.4);
  assert.equal(nativePlayer.state.playerState.status.value,"playing");
  const codes=r.window.__celikomBridgeNativeDrainDiagnostics().map(x=>x[0]);
  assert.ok(codes.includes("RESOLVE_TRANSIENT"));
  assert.ok(codes.includes("SOURCE_RECOVERY_RELOAD_OK"));
  r.handlers.beforeunload();
});

test("W76: real missing song never schedules background reload",async()=>{
  const r=createRenderer({withPlayer:true});
  const player=new r.NativeYandexPlayer({trackId:"456"});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state;
  const first=new r.Resource().getFileInfo({trackId:"456"});
  await tick();
  const req=r.window.__celikomBridgeNativeDrain();
  assert.equal(req.length,1);
  r.window.__celikomBridgeNativeReceive(req[0].requestId,null);
  assert.equal((await first).downloadInfo.url,"https://official.yandex.example/stream");
  await new Promise(resolve=>setTimeout(resolve,720));
  assert.equal(r.window.__celikomBridgeNativeDrain().length,0,
    "not found remains valid original and does not add recovery load");
  assert.equal(player.reloadReasons.length,0);
  r.handlers.beforeunload();
});

test("W98 VPN state transitions leave a confirmed ORIGINAL current song untouched",async()=>{
  const r=createRenderer({withPlayer:true});
  const player=new r.NativeYandexPlayer({trackId:"456",position:18.4});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state;
  const first=new r.Resource().getFileInfo({trackId:"456"});
  await tick();
  const initial=r.window.__celikomBridgeNativeDrain();
  assert.equal(initial.length,1);
  r.window.__celikomBridgeNativeReceive(initial[0].requestId,null);
  assert.equal((await first).downloadInfo.url,"https://official.yandex.example/stream");
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  await tick();await tick();
  assert.deepEqual(player.reloadReasons,[]);
  assert.equal(player.state.playerState.progress.value.position,18.4);
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  await tick();
  const revalidate=r.window.__celikomBridgeNativeDrain();
  assert.equal(revalidate.length,1);
  assert.equal(revalidate[0].trackId,"456");
  r.window.__celikomBridgeNativeReceive(revalidate[0].requestId,null);
  await tick();await tick();
  assert.deepEqual(player.reloadReasons,[],
    "a fresh authenticated not-found response must not recreate the original decoder");
  const codes=r.window.__celikomBridgeNativeDrainDiagnostics().map(x=>x[0]);
  assert.ok(codes.includes("SOURCE_ORIGINAL"));
  assert.ok(codes.includes("NATIVE_ORIGINAL_SOURCE_NO_RELOAD"));
  r.handlers.beforeunload();
});

test("W76: Stop after temporary failure cancels recovery without touching unknown current source",async()=>{
  const r=createRenderer({withPlayer:true});
  const player=new r.NativeYandexPlayer({trackId:"123"});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state;
  const first=new r.Resource().getFileInfo({trackId:"123"});
  await tick();
  const req=r.window.__celikomBridgeNativeDrain();
  r.window.__celikomBridgeNativeReceive(req[0].requestId,{transient:true});
  await first;
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  await new Promise(resolve=>setTimeout(resolve,730));
  assert.equal(r.window.__celikomBridgeNativeDrain().length,0);
  assert.deepEqual(player.reloadReasons,[],
    "a transient miss is UNKNOWN, not permission to reload an original track");
  assert.deepEqual(player.mediaSources,[]);
  const codes=r.window.__celikomBridgeNativeDrainDiagnostics().map(x=>x[0]);
  assert.ok(codes.includes("NATIVE_UNKNOWN_SOURCE_NO_RELOAD"));
  r.handlers.beforeunload();
});


test("W76: expired signed media 403 callback checks current ID and honestly reports recovery",async()=>{
  const r=createRenderer({withPlayer:true});
  const p=new r.NativeYandexPlayer({trackId:"123",position:24.5});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void p.state;
  assert.equal(r.window.__celikomBridgeNativeRecoverExpired("456"),false,
    "stale prefetched previous song must not force player reload");
  assert.equal(r.window.__celikomBridgeNativeRecoverExpired("123"),true);
  assert.equal(r.window.__celikomBridgeNativeRecoverExpired("123"),false,
    "repeated expired range requests must not start another recovery cycle");
  assert.equal(r.window.__celikomBridgeNativeStatus(),"NATIVE_RECOVERING");
  await new Promise(resolve=>setTimeout(resolve,720));
  const req=r.window.__celikomBridgeNativeDrain();
  assert.equal(req.length,1);
  assert.equal(req[0].trackId,"123");
  assert.equal(req[0].recovery,true);
  r.window.__celikomBridgeNativeReceive(req[0].requestId,makeGrant("123"));
  await new Promise(resolve=>setTimeout(resolve,220));
  assert.deepEqual(p.reloadReasons,["QUALITY_CHANGE"]);
  assert.equal(p.state.playerState.progress.value.position,24.5);
  assert.equal(r.window.__celikomBridgeNativeStatus(),"NATIVE_MAPPING_ACCEPTED");
  r.handlers.beforeunload();
});
test("W76: expired callback cannot wake a stopped or unobserved player",async()=>{
  const r=createRenderer({withPlayer:true});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  assert.equal(r.window.__celikomBridgeNativeRecoverExpired("123"),false,
    "before Yandex state observer attaches it cannot identify current player");
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  assert.equal(r.window.__celikomBridgeNativeRecoverExpired("123"),false);
  r.handlers.beforeunload();
});


test("W77: Kishlak-style transient batch prefetch remains pending until song actually plays",async()=>{
  const r=createRenderer({withPlayer:true});
  const player=new r.NativeYandexPlayer({trackId:"123",position:55.8});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state;
  const batch=new r.Resource().getFileInfoBatch({trackIds:["123","456"]});
  await tick();
  const first=r.window.__celikomBridgeNativeDrain();
  assert.equal(first.length,2);
  for(const req of first) r.window.__celikomBridgeNativeReceive(
    req.requestId,req.trackId==="456"?{transient:true}:makeGrant("123"));
  const result=await batch;
  assert.equal(result.downloadInfos[1].url,"https://official.yandex.example/next",
    "Yandex uses original while next track is merely prefetched");
  assert.equal(r.window.__celikomBridgeNativeCheckDeferred(),false);
  await new Promise(resolve=>setTimeout(resolve,720));
  assert.equal(r.window.__celikomBridgeNativeDrain().length,0,
    "a prefetched next track must never reload while another song plays");
  player.snapshot.queueState.currentEntity.value.entity.data.meta.id="456";
  player.snapshot.playerState.progress.value.position=18.3;
  void player.state;
  assert.equal(r.window.__celikomBridgeNativeCheckDeferred(),true,
    "observed Yandex current song activates the deferred retry");
  assert.equal(r.window.__celikomBridgeNativeStatus(),"NATIVE_RECOVERING");
  assert.equal(r.window.__celikomBridgeNativeCheckDeferred(),false,
    "one retry cycle only even under frequent status polls");
  await new Promise(resolve=>setTimeout(resolve,710));
  const recovery=r.window.__celikomBridgeNativeDrain();
  assert.equal(recovery.length,1);
  assert.equal(recovery[0].trackId,"456");
  assert.equal(recovery[0].recovery,true);
  r.window.__celikomBridgeNativeReceive(recovery[0].requestId,makeGrant("456"));
  await new Promise(resolve=>setTimeout(resolve,220));
  assert.deepEqual(player.reloadReasons,["QUALITY_CHANGE"]);
  assert.equal(player.mediaSources[0],makeGrant("456").audioUrl+
    "&celikom_native_query_guard=0");
  assert.equal(player.state.playerState.progress.value.position,18.3);
  assert.equal(player.state.playerState.status.value,"playing");
  const codes=r.window.__celikomBridgeNativeDrainDiagnostics().map(x=>x[0]);
  assert.ok(codes.includes("SOURCE_DEFERRED_WAITING"));
  assert.ok(codes.includes("SOURCE_DEFERRED_PROMOTED"));
  assert.ok(codes.includes("SOURCE_RECOVERY_RELOAD_OK"));
  r.handlers.beforeunload();
});

test("W77: Stop clears old prefetch failure and forbids future reload",async()=>{
  const r=createRenderer({withPlayer:true});
  const player=new r.NativeYandexPlayer({trackId:"123"});
  r.window.__celikomBridgeNativeSetState({enabled:true,signedIn:true,apiOrigin:origin});
  void player.state;
  const batch=new r.Resource().getFileInfoBatch({trackIds:["123","456"]});
  await tick();
  for(const req of r.window.__celikomBridgeNativeDrain())
    r.window.__celikomBridgeNativeReceive(
      req.requestId,req.trackId==="456"?{transient:true}:null);
  await batch;
  r.window.__celikomBridgeNativeSetState({enabled:false,signedIn:true,apiOrigin:origin});
  await tick();await tick();
  const prior=player.reloadReasons.length;
  player.snapshot.queueState.currentEntity.value.entity.data.meta.id="456";
  void player.state;
  assert.equal(r.window.__celikomBridgeNativeCheckDeferred(),false);
  await new Promise(resolve=>setTimeout(resolve,720));
  assert.equal(r.window.__celikomBridgeNativeDrain().length,0);
  assert.equal(player.reloadReasons.length,prior);
  r.handlers.beforeunload();
});

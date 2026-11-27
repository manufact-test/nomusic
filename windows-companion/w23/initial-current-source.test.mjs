import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const script=fs.readFileSync(new URL("./dist/renderer.js",import.meta.url),"utf8");
const origin="https://api.celikom.example";
const tick=()=>new Promise(r=>setImmediate(r));
function harness() {
 const clock={now:Date.now()},handlers={},intervals=[];
 class FileInfoProvider {
   async getFileInfo(params){
     const id=params?.trackId ?? params?.entity?.data?.meta?.id ??
       params?.entity?.id ?? params?.id;
     return {downloadInfo:{trackId:String(id),url:"https://yandex.example/old"}};
   }
   async getMediaSource(params){return this.getFileInfo(params);}
   async getFileInfoBatchRequest(params){return {fileInfos:[],trackIds:params?.trackIds};}
 }
 class MediaProvider {
   constructor(){this.getFileInfoProvider=new FileInfoProvider();}
   async getMediaSource(params){return this.getFileInfoProvider.getFileInfo(params);}
 }
 class YandexMediaPlayer {
   constructor(){this.mediaProvider=new MediaProvider();}
 }
 class CrossMediaPlayer {
   constructor(){
     this.firstMediaPlayer=new YandexMediaPlayer();
     this.secondMediaPlayer=new YandexMediaPlayer();
     this.currentMediaPlayer=this.firstMediaPlayer;
   }
 }
 class Player {
   reasons=[];urls=[];
   constructor(){
     const cross=new CrossMediaPlayer();
     const currentMediaPlayer={value:cross};
     const mediaPlayersStore={value:{audio:cross}};
     this.mediaController={currentMediaPlayer,mediaPlayersStore};
     this.snapshot={queueState:{currentEntity:{value:{entity:{data:{meta:{id:"123"}}}}}},
       playerState:{status:{value:"playing"},progress:{value:{position:77}}},
       currentMediaPlayer,mediaPlayersStore};
     this.playbackState=this.snapshot;
   }
   get state(){return this.playbackState;}
   async reloadEntity(reason) {
     this.reasons.push(reason);
     const currentId=String(this.snapshot.queueState.currentEntity.value.entity.data.meta.id);
     const cross=this.mediaController.currentMediaPlayer.value;
     const data=await cross.currentMediaPlayer.mediaProvider.getMediaSource({entity:{id:currentId}});
     this.urls.push(data.downloadInfo.url);
   }
 }
 const req=id=>id===7123?{VE:Player}:null;
 req.m={7123:function player(){}};
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

test("W175 Stop while initial grant is pending never reloads the stopped current song",async()=>{
  const r=harness(),w=r.window;
  r.clock.now+=4000;
  w.__celikomBridgeNativeCheckDeferred();await tick();
  const pending=w.__celikomBridgeNativeDrain();
  assert.equal(pending.length,1);
  assert.equal(pending[0].trackId,"123");
  // Yandex Stop happens while the exact-track grant request is still pending.
  r.player.snapshot.playerState.status.value="stopped";
  w.__celikomBridgeNativeReceive(pending[0].requestId,signedGrant("123"));
  for(let i=0;i<8;i++){await tick();for(const p of w.__celikomBridgeNativeDrain())
    w.__celikomBridgeNativeReceive(p.requestId,signedGrant("123"));}
  assert.deepEqual(r.player.reasons,[],
    "the source-only refresh must re-check Yandex playback state after the grant resolves");
  const codes=w.__celikomBridgeNativeDrainDiagnostics().map(x=>x[0]);
  assert.ok(codes.includes("NATIVE_INITIAL_SOURCE_RELOAD_DEFERRED"));
  r.handlers.beforeunload();
});

test("W178: next current song with cached original gets exactly one approved source-only reload",async()=>{test("W178 Stop while next-track grant is pending never reloads the stopped song",async()=>{
  const r=harness(),w=r.window;
  r.clock.now+=4000;
  w.__celikomBridgeNativeCheckDeferred();await tick();
  const initial=w.__celikomBridgeNativeDrain();
  assert.equal(initial.length,1);
  w.__celikomBridgeNativeReceive(initial[0].requestId,null);
  await tick();
  r.player.snapshot.queueState.currentEntity.value.entity.data.meta.id="456";
  r.clock.now+=100;
  w.__celikomBridgeNativeCheckDeferred();await tick();
  r.clock.now+=4000;
  w.__celikomBridgeNativeCheckDeferred();await tick();
  const pending=w.__celikomBridgeNativeDrain();
  assert.equal(pending.length,1);
  assert.equal(pending[0].trackId,"456");
  // Stop after W178 resolves the new current track but before the grant returns.
  r.player.snapshot.playerState.status.value="stopped";
  w.__celikomBridgeNativeReceive(pending[0].requestId,signedGrant("456"));
  for(let i=0;i<8;i++){await tick();for(const p of w.__celikomBridgeNativeDrain())
    w.__celikomBridgeNativeReceive(p.requestId,signedGrant("456"));}
  assert.deepEqual(r.player.reasons,[],
    "W178 must not issue QUALITY_CHANGE after Yandex has stopped playback");
  const codes=w.__celikomBridgeNativeDrainDiagnostics().map(x=>x[0]);
  assert.ok(codes.includes("NATIVE_CURRENT_CATCHUP_RELOAD_DEFERRED"));
  r.handlers.beforeunload();
});


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

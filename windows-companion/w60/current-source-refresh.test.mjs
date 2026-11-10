import test from "node:test";
import assert from "node:assert/strict";
import {createCurrentSourceRefresh} from "./current-source-refresh.mjs";

function harness({status="playing",trackId="123",hasModule=true}={}) {
  class NativeYandexPlayback {
    constructor() {
      this.calls=[];
      this.snapshot={
        queueState:{currentEntity:{value:{entity:{data:{meta:{id:trackId,
          title:"Раскол", artists:[{name:"Исполнитель"}],durationMs:178000}}}}}},
        playerState:{status:{value:status},progress:{value:{position:73.42}}}
      };
    }
    get state() {return this.snapshot}
    async reloadEntity(reason) {this.calls.push(reason)}
    play() {return "OFFICIAL_YANDEX_PLAY"}
    pause() {return "OFFICIAL_YANDEX_PAUSE"}
    seek() {return "OFFICIAL_YANDEX_SEEK"}
  }
  const getter=Object.getOwnPropertyDescriptor(NativeYandexPlayback.prototype,"state").get;
  function webpackRequire(id) {return id===7123 && hasModule ? {VE:NativeYandexPlayback}:null}
  webpackRequire.m=hasModule?{7123:function actualPlayerFactory(){}}:{};
  return {NativeYandexPlayback,webpackRequire,getter};
}

test("W60 signed vendor class observer reloads current source without changing state/controls", async()=>{
  const h=harness(),events=[];
  const r=createCurrentSourceRefresh({onEvent:c=>events.push(c)});
  assert.equal(r.attach(h.webpackRequire),true);
  assert.equal(r.attached,true);
  const player=new h.NativeYandexPlayback();
  const state=player.state;
  assert.strictEqual(state,player.snapshot,"getter identity-preserving return");
  assert.equal(await r.request(),true);
  assert.deepEqual(player.calls,["QUALITY_CHANGE"]);
  assert.equal(player.snapshot.playerState.status.value,"playing");
  assert.equal(player.snapshot.playerState.progress.value.position,73.42);
  assert.equal(player.play(),"OFFICIAL_YANDEX_PLAY");
  assert.equal(player.pause(),"OFFICIAL_YANDEX_PAUSE");
  assert.equal(player.seek(),"OFFICIAL_YANDEX_SEEK");
  assert.ok(events.includes("NATIVE_TOGGLE_RELOAD_OK"));
  assert.ok(events.every(x=>/^[A-Z_]{3,48}$/.test(x)), "no track IDs or URLs logged");
  r.dispose();
  assert.strictEqual(Object.getOwnPropertyDescriptor(h.NativeYandexPlayback.prototype,"state").get,h.getter);
});

test("W60 paused Yandex remains paused and at the same position",async()=>{
  const h=harness({status:"paused"}),r=createCurrentSourceRefresh();
  assert.equal(r.attach(h.webpackRequire),true);
  const player=new h.NativeYandexPlayback();
  void player.state;
  assert.equal(await r.request(),true);
  assert.equal(player.calls.length,1);
  assert.equal(player.snapshot.playerState.status.value,"paused");
  assert.equal(player.snapshot.playerState.progress.value.position,73.42);
  r.dispose();
});

test("W60 no player, unsupported vendor and idle playback are safe no-ops",async()=>{
  const h=harness({hasModule:false}),r=createCurrentSourceRefresh();
  assert.equal(r.attach(h.webpackRequire),false);
  assert.equal(await r.request(),false);
  r.dispose();
  const h2=harness({status:"idle"}),events=[];
  const r2=createCurrentSourceRefresh({onEvent:c=>events.push(c)});
  assert.equal(r2.attach(h2.webpackRequire),true);
  const p=new h2.NativeYandexPlayback();
  void p.state;
  assert.equal(await r2.request(),false);
  assert.deepEqual(p.calls,[]);
  assert.ok(events.includes("NATIVE_TOGGLE_RELOAD_DEFERRED"));
  r2.dispose();
});

test("W60 quick toggles serialize official Yandex reloads and latest state wins",async()=>{
  const h=harness(),r=createCurrentSourceRefresh();
  assert.equal(r.attach(h.webpackRequire),true);
  const player=new h.NativeYandexPlayback();
  let release;
  player.reloadEntity=reason=>{player.calls.push(reason);return new Promise(resolve=>{release=resolve})};
  void player.state;
  const first=r.request();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(player.calls.length,1);
  const second=r.request();
  release();
  await first;
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(player.calls.length,2);
  release();
  assert.equal(await second,true);
  r.dispose();
});

test("W60 pending callbacks cannot revive disposed binding or capture user data",async()=>{
  const h=harness(),r=createCurrentSourceRefresh();
  assert.equal(r.attach(h.webpackRequire),true);
  const player=new h.NativeYandexPlayback();
  void player.state;
  const pending=r.request();
  r.dispose();
  assert.equal(await pending,false);
  assert.equal(player.calls.length,0);
});

test("W60 malicious current-entity getter must not break original playback getter",async()=>{
  const h=harness(),r=createCurrentSourceRefresh();
  assert.equal(r.attach(h.webpackRequire),true);
  const p=new h.NativeYandexPlayback();
  const original=p.snapshot;
  Object.defineProperty(original.queueState.currentEntity,"value",
    {get(){throw Error("vendor entity metadata denied")}});
  assert.strictEqual(p.state,original);
  assert.equal(await r.request(),false);
  r.dispose();
});


test("W62 passive current-song identity is read-only and never a preloaded song",async()=>{
  const h=harness({status:"playing",trackId:"148222333"});
  const r=createCurrentSourceRefresh();
  assert.equal(r.attach(h.webpackRequire),true);
  const player=new h.NativeYandexPlayback();
  assert.equal(r.currentTrackId(),"","no player observed yet");
  void player.state;
  assert.equal(r.currentTrackId(),"148222333");
  assert.deepEqual(player.calls,[],"observing ID does not reload or touch media");
  player.snapshot.playerState.status.value="idle";
  assert.equal(r.currentTrackId(),"","stale paused track is not reported");
  player.snapshot.playerState.status.value="paused";
  assert.equal(r.currentTrackId(),"148222333","paused current entity remains observable");
  r.dispose();
  assert.equal(r.currentTrackId(),"","dispose clears all metadata");
});

test("W63 exact current song yields safe title artist duration without control mutations",()=>{
  const h=harness({trackId:"34483761"}),r=createCurrentSourceRefresh();
  assert.equal(r.attach(h.webpackRequire),true);
  const p=new h.NativeYandexPlayback();
  void p.state;
  assert.deepEqual(r.currentTrack(),{
    id:"34483761",title:"Раскол",artist:"Исполнитель",durationMs:178000
  });
  assert.deepEqual(p.calls,[]);
  p.snapshot.queueState.currentEntity.value.entity.data.meta.title=
    "Name".repeat(150);
  assert.equal(r.currentTrack().title.length,180,"bounded presentation only");
  p.snapshot.queueState.currentEntity.value.entity.data.meta.id="bad";
  assert.equal(r.currentTrack(),null,"cannot expose untrusted identifier");
  r.dispose();
  assert.equal(r.currentTrack(),null);
});

test("W66 song and artist metadata keep uppercase D, digits and Unicode intact",()=>{
  const h=harness({trackId:"34483761"}),r=createCurrentSourceRefresh();
  assert.equal(r.attach(h.webpackRequire),true);
  const p=new h.NativeYandexPlayback();
  const meta=p.snapshot.queueState.currentEntity.value.entity.data.meta;
  meta.title="Город и Туман";
  meta.artists=[{name:"kavabanga Depo kolibri"}];
  void p.state;
  assert.deepEqual(r.currentTrack(),{
    id:"34483761",title:"Город и Туман",
    artist:"kavabanga Depo kolibri",durationMs:178000
  });
  meta.title="TRITIA 10AGE 02468 ABCDFHJLNPRTVXZ";
  meta.artists=[{name:"中文 русский DÉPÔ 0123456789"}];
  assert.equal(r.currentTrack().title,meta.title);
  assert.equal(r.currentTrack().artist,meta.artists[0].name);
  meta.title="D\u0000evil\n";
  assert.equal(r.currentTrack().title,"D evil");
  assert.deepEqual(p.calls,[],"display-only observation never reloads media");
  r.dispose();
});

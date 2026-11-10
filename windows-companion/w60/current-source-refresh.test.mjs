import test from "node:test";
import assert from "node:assert/strict";
import {createCurrentSourceRefresh} from "./current-source-refresh.mjs";

function harness({status="playing",trackId="123",hasModule=true}={}) {
  class NativeYandexPlayback {
    constructor() {
      this.calls=[];
      this.snapshot={
        queueState:{currentEntity:{value:{entity:{data:{meta:{id:trackId}}}}}},
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

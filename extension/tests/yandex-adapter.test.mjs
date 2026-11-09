import assert from "node:assert/strict";
import test from "node:test";

await import("../dist/unpacked/player/core.js");
await import("../dist/unpacked/adapters/yandex-music-adapter.js");

const { createAdapter } = globalThis.__CELIKOM_YANDEX_ADAPTER_V1__;

class FakeMedia extends EventTarget {
  constructor() {
    super();
    this.tagName = "AUDIO";
    this.dataset = {};
    this.id = "";
    this.className = "";
    this.parentElement = null;
    this.isConnected = false;
    this.paused = false;
    this.ended = false;
    this.seeking = false;
    this.currentTime = 12;
    this.duration = 193.283;
    this.playbackRate = 1;
    this.volume = 1;
    this.muted = false;
    this.readyState = 4;
    this.networkState = 2;
    this.currentSrc = "https://strm-rad-25.strm.yandex.net/track";
    this.src = this.currentSrc;
    this.listenerBalance = 0;
  }

  addEventListener(type, listener, options) {
    this.listenerBalance += 1;
    return super.addEventListener(type, listener, options);
  }

  removeEventListener(type, listener, options) {
    this.listenerBalance -= 1;
    return super.removeEventListener(type, listener, options);
  }

  play() {
    this.paused = false;
    return Promise.resolve();
  }

  pause() {
    this.paused = true;
  }

  load() {}
  closest() { return null; }
}

function createEnvironment(media) {
  const windowListeners = new Map();
  const intervals = new Set();
  let timerId = 0;
  const document = {
    title: "Smells Like Teen Spirit — ERCODES, SMOLA",
    hidden: false,
    querySelector: () => null,
    querySelectorAll(selector) {
      if (selector === "audio,video") return Array.isArray(media) ? media : [media];
      return [];
    }
  };
  const environment = {
    window: null,
    document,
    HTMLMediaElement: FakeMedia,
    MutationObserver: null,
    XMLHttpRequest: null,
    navigator: {
      mediaSession: {
        metadata: {
          title: "Smells Like Teen Spirit",
          artist: "ERCODES, SMOLA",
          album: "Smells Like Teen Spirit",
          artwork: [{ src: "https://avatars.yandex.net/get-music-content/20322863/810d39cc.a.43775051-1/400x400" }]
        }
      }
    },
    location: {
      href: "https://music.yandex.ru/landing/main",
      origin: "https://music.yandex.ru",
      pathname: "/landing/main"
    },
    history: {
      pushState() {},
      replaceState() {}
    },
    __STATE_PATCHES__: [[{
      id: "155343370",
      title: "Smells Like Teen Spirit",
      artists: [{ name: "ERCODES" }, { name: "SMOLA" }],
      albums: [{ id: "43775051", title: "Smells Like Teen Spirit", coverUri: "avatars.yandex.net/get-music-content/20322863/810d39cc.a.43775051-1/%%" }],
      durationMs: 193283
    }]],
    addEventListener(type, listener) {
      if (!windowListeners.has(type)) windowListeners.set(type, new Set());
      windowListeners.get(type).add(listener);
    },
    removeEventListener(type, listener) {
      windowListeners.get(type)?.delete(listener);
    },
    getComputedStyle: () => ({ display: "block", visibility: "visible" }),
    setInterval(callback) {
      const id = ++timerId;
      intervals.add(id);
      return id;
    },
    clearInterval(id) { intervals.delete(id); },
    setTimeout: globalThis.setTimeout.bind(globalThis),
    clearTimeout: globalThis.clearTimeout.bind(globalThis),
    queueMicrotask: globalThis.queueMicrotask.bind(globalThis)
  };
  environment.window = environment;
  return { environment, intervals, windowListeners };
}

test("YandexMusicAdapter mounts idempotently, follows SPA track changes and fully unmounts", async () => {
  const media = new FakeMedia();
  const originalPlay = FakeMedia.prototype.play;
  const originalPushState = () => {};
  const { environment, intervals, windowListeners } = createEnvironment(media);
  environment.history.pushState = originalPushState;
  const adapter = createAdapter(environment);
  const snapshots = [];
  const events = [];
  const sink = {
    onSnapshot: (snapshot) => snapshots.push(snapshot),
    onPlayerEvent: (event) => events.push(event)
  };

  adapter.mount(sink);
  adapter.mount(sink);
  assert.equal(adapter.mounted, true);
  assert.equal(intervals.size, 1);
  assert.equal(windowListeners.get("popstate").size, 1);
  assert.equal(media.listenerBalance, 14);
  assert.notEqual(FakeMedia.prototype.play, originalPlay);
  assert.notEqual(environment.history.pushState, originalPushState);
  assert.equal(snapshots.at(-1).track.id, "155343370");
  assert.equal(snapshots.at(-1).player.mediaId, "media-1");

  media.dispatchEvent(new Event("play"));
  assert.equal(events.at(-1).type, "PLAY");
  assert.equal(events.at(-1).trackId, "155343370");

  Object.assign(environment.navigator.mediaSession.metadata, {
    title: "SWERVIN",
    artist: "OISEAU & PAPILLON, onna badvibes",
    album: "SWERVIN",
    artwork: [{ src: "https://avatars.yandex.net/get-music-content/20622967/c3b9f96b.a.44117847-1/400x400" }]
  });
  media.duration = 193.515;
  environment.__STATE_PATCHES__.push([{
    id: "156177669",
    title: "SWERVIN",
    artists: [{ name: "OISEAU & PAPILLON" }, { name: "onna badvibes" }],
    albums: [{ id: "44117847", title: "SWERVIN", coverUri: "avatars.yandex.net/get-music-content/20622967/c3b9f96b.a.44117847-1/%%" }],
    durationMs: 193515
  }]);
  environment.history.pushState({}, "", "/landing/main");
  await Promise.resolve();
  const trackChanged = events.findLast((event) => event.type === "TRACK_CHANGED");
  assert.equal(trackChanged.previousTrackId, "155343370");
  assert.equal(trackChanged.trackId, "156177669");

  adapter.unmount();
  adapter.unmount();
  assert.equal(adapter.mounted, false);
  assert.equal(intervals.size, 0);
  assert.equal(windowListeners.get("popstate").size, 0);
  assert.equal(media.listenerBalance, 0);
  assert.equal(FakeMedia.prototype.play, originalPlay);
  assert.equal(environment.history.pushState, originalPushState);

  adapter.mount(sink);
  assert.equal(media.listenerBalance, 14);
  media.dispatchEvent(new Event("pause"));
  assert.equal(events.at(-1).type, "PAUSE");
  adapter.unmount();
  assert.equal(media.listenerBalance, 0);
});

test("third-party History wrappers survive CELIKOM unmount and remount without recursion or stale snapshots", async () => {
  const media = new FakeMedia();
  const { environment } = createEnvironment(media);
  const calls = { pushState: 0, replaceState: 0 };
  for (const name of Object.keys(calls)) {
    environment.history[name] = function nativeHistory(_state, label) {
      calls[name]++;
      return label;
    };
  }
  const adapter = createAdapter(environment);
  const snapshots = [];
  const sink = { onSnapshot: (snapshot) => snapshots.push(snapshot), onPlayerEvent() {} };
  adapter.mount(sink);
  const externallyWrapped = {};
  for (const name of Object.keys(calls)) {
    const retainedOldWrapper = environment.history[name];
    externallyWrapped[name] = function pageHistoryWrapper(...args) {
      return Reflect.apply(retainedOldWrapper, this, args);
    };
    environment.history[name] = externallyWrapped[name];
  }

  adapter.unmount();
  const whileUnmounted = snapshots.length;
  for (const name of Object.keys(calls)) {
    assert.equal(environment.history[name]({}, name, "/search"), name,
      "retained CELIKOM wrapper must still call its captured original after unmount");
  }
  await Promise.resolve();
  assert.equal(snapshots.length, whileUnmounted, "old wrappers must not schedule work after unmount");

  adapter.mount(sink);
  for (const name of Object.keys(calls)) {
    const before = snapshots.length;
    assert.equal(environment.history[name]({}, name, "/search"), name,
      "new wrapper may delegate through external wrapper then inactive old CELIKOM wrapper");
    await Promise.resolve();
    assert.equal(snapshots.length, before + 1, "only current hook emits a snapshot");
    assert.equal(calls[name], 2, "original browser history called exactly once per navigation");
  }
  adapter.unmount();
  for (const name of Object.keys(calls)) {
    assert.equal(environment.history[name], externallyWrapped[name],
      "never overwrite the third-party History wrapper during cleanup");
  }
});

test("retained media and fetch wrappers use stable originals across unmount and restart", async () => {
  const media = new FakeMedia();
  const { environment } = createEnvironment(media);
  const initialPlay = FakeMedia.prototype.play;
  let networkCalls = 0;
  const nativeFetch = async (url) => {
    networkCalls++;
    return { url: "https://invalid.example/fixture", headers: { get: () => "" }, source: url };
  };
  environment.fetch = nativeFetch;
  const adapter = createAdapter(environment);
  const sink = { onSnapshot() {}, onPlayerEvent() {} };
  try {
    adapter.mount(sink);
    const interceptedPlay = FakeMedia.prototype.play;
    const interceptedFetch = environment.fetch;
    const externalPlay = function pagePlay(...args) {
      return Reflect.apply(interceptedPlay, this, args);
    };
    const externalFetch = function pageFetch(...args) {
      return Reflect.apply(interceptedFetch, this, args);
    };
    FakeMedia.prototype.play = externalPlay;
    environment.fetch = externalFetch;
    adapter.unmount();
    await media.play();
    await environment.fetch("/fixture");
    adapter.mount(sink);
    await media.play();
    await environment.fetch("/fixture");
    assert.equal(networkCalls, 2, "one actual fetch per request across both lifecycles");
    adapter.unmount();
    assert.equal(FakeMedia.prototype.play, externalPlay);
    assert.equal(environment.fetch, externalFetch);
  } finally {
    adapter.unmount();
    FakeMedia.prototype.play = initialPlay;
    environment.fetch = nativeFetch;
  }
});

test("15 ms data audio cannot steal a paused master after a utility media event", () => {
  const master = new FakeMedia(); master.paused = true;
  const utility = new FakeMedia();
  Object.assign(utility, { duration: 0.015, currentTime: 0, currentSrc: "data:audio/wav;base64,fixture", src: "data:audio/wav;base64,fixture", paused: true, isConnected: true });
  const { environment } = createEnvironment([master, utility]);
  const adapter = createAdapter(environment); const snapshots = [];
  adapter.mount({ onSnapshot: (s) => snapshots.push(s), onPlayerEvent() {} });
  const masterId = snapshots.at(-1).player.mediaId;
  utility.dispatchEvent(new Event("volumechange"));
  const next = adapter.getSnapshot();
  assert.equal(next.player.mediaId, masterId);
  assert.equal(next.track.id, "155343370");
  const helper = next.mediaCandidates.find((candidate) => candidate.duration === 0.015);
  assert.ok(helper, JSON.stringify(next.mediaCandidates));
  assert.equal(helper.eligible, false); assert.equal(helper.rejectedReason, "utility-media");
  assert.equal(adapter.getMediaElement(helper.mediaId), null);
  utility.paused = false; utility.dispatchEvent(new Event("play"));
  assert.equal(adapter.getSnapshot().player.mediaId, masterId);
  adapter.unmount();
});

test("track duration stays independent of a mismatched native player clock", () => {
  const master = new FakeMedia(); master.duration = 15;
  const { environment } = createEnvironment(master);
  const adapter = createAdapter(environment);
  adapter.mount({ onSnapshot() {}, onPlayerEvent() {} });
  const snapshot = adapter.getSnapshot();
  assert.equal(snapshot.track.id, "155343370");
  assert.equal(snapshot.track.metadata.durationMs, 193283);
  assert.equal(snapshot.player.duration, 15);
  adapter.unmount();
});

test("network observation failures cannot alter the page fetch response, arguments or original rejection", async () => {
  const { environment } = createEnvironment(new FakeMedia());
  const response = new Response('unchanged page data');
  const args = ['/page-request', {method:'GET'}], originalError = new TypeError('page network failure');
  let calls = 0, reject = false;
  environment.fetch = async function (...received) {
    calls++; assert.equal(this, environment); assert.deepEqual(received, args);
    if (reject) throw originalError;
    return response;
  };
  const original = environment.fetch, adapter = createAdapter(environment);
  adapter.captureJsonResponse = () => { throw new Error('CELIKOM observer failure'); };
  try {
    adapter.installNetworkHooks();
    assert.equal(await environment.fetch(...args), response);
    assert.equal(await response.text(), 'unchanged page data');
    reject = true; await assert.rejects(environment.fetch(...args), error => error === originalError);
    assert.equal(calls, 2, 'each page request reaches the native fetch exactly once');
  } finally { adapter.restoreNetworkHooks(); }
  assert.equal(environment.fetch, original);
});
test("XHR observer listener failure still invokes original send exactly once", () => {
  const { environment } = createEnvironment(new FakeMedia());
  let sent = 0;
  class Xhr {
    open() {}
    send(body) { sent++; return body; }
    addEventListener() { throw new Error('observer listener failure'); }
  }
  environment.XMLHttpRequest = Xhr;
  const original = Xhr.prototype.send, adapter = createAdapter(environment);
  try { adapter.installNetworkHooks(); assert.equal(new Xhr().send('body'), 'body'); assert.equal(sent, 1); }
  finally { adapter.restoreNetworkHooks(); }
  assert.equal(Xhr.prototype.send, original);
});

test('late native ended after element reuse is not emitted as the new track ending',()=>{
 const media=new FakeMedia();const {environment}=createEnvironment(media);const adapter=createAdapter(environment);
 const events=[];adapter.mount({onSnapshot(){},onPlayerEvent:e=>events.push(e)});
 try {
  media.ended=false;media.dispatchEvent(new Event('ended'));
  assert.equal(events.filter(e=>e.type==='ENDED').length,0);
  media.ended=true;media.dispatchEvent(new Event('ended'));
  assert.equal(events.filter(e=>e.type==='ENDED').length,1,'genuine selected-master ending is preserved');
 }finally{adapter.unmount();}
});

test("reused stream cannot identify a new song from the previous Media Session metadata", () => {
  const media = new FakeMedia();
  const { environment } = createEnvironment(media);
  const adapter = createAdapter(environment);
  adapter.mount({ onSnapshot() {}, onPlayerEvent() {} });
  try {
    assert.equal(adapter.getSnapshot().track.id, "155343370");
    media.currentSrc = media.src = "https://strm-rad-25.strm.yandex.net/next-track";
    media.currentTime = 0;
    // The next recording can have the same duration. A duration check cannot
    // establish its identity while Yandex still exposes the previous title.
    const pending = adapter.getSnapshot();
    assert.equal(pending.track.id, null);
    assert.equal(pending.track.evidence, "awaiting-track-refresh");
    assert.equal(adapter.getSnapshot().track.id, null, "polling cannot make stale metadata fresh");
    adapter.ingestTrackPayload({ id: "1944611", title: "Всё пиздато", artists: [{name:"Зануда"}], durationMs: 193283 }, "fixture");
    Object.assign(environment.navigator.mediaSession.metadata, {title:"Всё пиздато",artist:"Зануда",album:"Папиросы",artwork:[]});
    assert.equal(adapter.getSnapshot().track.id, "1944611");
  } finally { adapter.unmount(); }
});

test("conflicting player and Media Session identities suspend replacement until both agree", () => {
  const media = new FakeMedia();
  const { environment } = createEnvironment(media);
  const adapter = createAdapter(environment);
  adapter.mount({ onSnapshot() {}, onPlayerEvent() {} });
  try {
    adapter.ingestTrackPayload({id:"1944611",title:"Всё пиздато",artists:[{name:"Зануда"}],durationMs:193283}, "fixture");
    media.currentSrc = media.src = "https://strm-rad-25.strm.yandex.net/transition-b";
    assert.equal(adapter.getSnapshot().track.id, null);
    adapter.playerDomMetadata = () => ({title:"Всё пиздато",artist:"Зануда",album:"",coverUri:"",durationMs:193283});
    assert.equal(adapter.getSnapshot().track.id, null);
    assert.equal(adapter.getSnapshot().track.evidence, "playback-metadata-conflict");
    Object.assign(environment.navigator.mediaSession.metadata, {title:"Всё пиздато",artist:"Зануда",album:"",artwork:[]});
    assert.equal(adapter.getSnapshot().track.id, "1944611");
    media.currentSrc = media.src = "https://strm-rad-25.strm.yandex.net/transition-c";
    assert.equal(adapter.getSnapshot().track.id, null, "B is now the preceding identity, including after a conflict during A to B");
  } finally { adapter.unmount(); }
});

test("ordinary seek keeps identity; refreshing the same song metadata permits a new stream", () => {
  const media = new FakeMedia();
  const { environment } = createEnvironment(media);
  const adapter = createAdapter(environment);
  adapter.mount({ onSnapshot() {}, onPlayerEvent() {} });
  try {
    media.currentTime = 0; media.seeking = true;
    assert.equal(adapter.getSnapshot().track.id, "155343370");
    media.seeking = false;
    media.currentSrc = media.src = "https://strm-rad-25.strm.yandex.net/refreshed-stream";
    assert.equal(adapter.getSnapshot().track.id, null);
    environment.navigator.mediaSession.metadata = {...environment.navigator.mediaSession.metadata};
    assert.equal(adapter.getSnapshot().track.id, "155343370");
  } finally { adapter.unmount(); }
});

test("metadata setter and native play release stale identity before the next poll", async () => {
  const media = new FakeMedia();
  const { environment } = createEnvironment(media);
  let metadata = environment.navigator.mediaSession.metadata;
  const session = environment.navigator.mediaSession;
  const descriptor = {configurable:true,enumerable:true,get(){return metadata;},set(value){metadata=value;}};
  Object.defineProperty(session, "metadata", descriptor);
  const adapter = createAdapter(environment), seen = [];
  adapter.mount({onSnapshot:s=>seen.push(s),onPlayerEvent(){}});
  try {
    adapter.ingestTrackPayload({id:"1944611",title:"Всё пиздато",artists:[{name:"Зануда"}],durationMs:193283}, "fixture");
    media.currentSrc = media.src = "https://strm-rad-25.strm.yandex.net/next";
    media.currentTime = 0;
    const playing = media.play();
    assert.equal(seen.at(-1).track.id, null, "stale identity is invalidated synchronously before play returns");
    session.metadata = {title:"Всё пиздато",artist:"Зануда",album:"",artwork:[]};
    assert.equal(seen.at(-1).track.id, "1944611", "metadata update does not wait for 500 ms polling");
    await playing;
  } finally { adapter.unmount(); }
  assert.equal(Object.getOwnPropertyDescriptor(session,"metadata").set, descriptor.set);
});

test("duration-only changes cannot refresh the previous identity on a new stream", () => {
  const media = new FakeMedia();
  const { environment } = createEnvironment(media);
  const adapter = createAdapter(environment);
  let durationMs = 193283;
  adapter.playerDomMetadata = () => ({title:"",artist:"",album:"",coverUri:"",durationMs});
  adapter.mount({onSnapshot(){},onPlayerEvent(){}});
  try {
    media.currentSrc = media.src = "https://strm-rad-25.strm.yandex.net/next";
    assert.equal(adapter.getSnapshot().track.id, null);
    durationMs = 193515; media.duration = 193.515;
    assert.equal(adapter.getSnapshot().track.id, null);
    assert.equal(adapter.getSnapshot().track.evidence, "awaiting-track-refresh");
  } finally { adapter.unmount(); }
});

test("A replacement is destroyed before reused native play; only fresh B can start", async () => {
  for (const name of ["sync-engine","replacement-player","fail-open-controller","replacement-controller"]) await import(`../dist/unpacked/player/${name}.js`);
  const {ReplacementController} = globalThis.__CELIKOM_REPLACEMENT_CONTROLLER_V1__;
  for (const delayedCurrentSource of [false,true]) {
  const media = new FakeMedia();
  const {environment} = createEnvironment(media);
  let metadata = environment.navigator.mediaSession.metadata;
  Object.defineProperty(environment.navigator.mediaSession,"metadata",{configurable:true,get:()=>metadata,set:value=>{metadata=value;}});
  const adapter = createAdapter(environment), players = [];
  const bridge = {sessionId:"transition-session",isHealthy:()=>true,getSnapshot:async()=>adapter.getSnapshot(),request:async()=>({snapshot:adapter.getSnapshot()}),post(){}};
  const engine = new ReplacementController(bridge,environment,{
    resolveAsset:async id=>({found:true,trackId:id,durationMs:193283,expiresAt:Date.now()+60000}),
    createPlayer:()=>{
      const player = {audio:{duration:193.283,currentTime:0},destroyed:false,
        async prepare(asset){this.trackId=asset.trackId;},applyState(){},play(){this.playing=true;},pause(){this.playing=false;},destroy(){this.destroyed=true;this.playing=false;}};
      players.push(player);return player;
    }
  });
  const settle = async()=>{for(let i=0;i<40;i++)await Promise.resolve();};
  engine.configure(true, "");
  adapter.mount({onSnapshot:s=>engine.update(s),onPlayerEvent:e=>engine.update(e.snapshot,e.type)});
  try {
    await settle(); assert.equal(players[0].playing,true);
    adapter.ingestTrackPayload({id:"1944611",title:"Всё пиздато",artists:[{name:"Зануда"}],durationMs:193283},"fixture");
    media.src = "https://strm-rad-25.strm.yandex.net/next";
    if(!delayedCurrentSource)media.currentSrc=media.src;
    media.currentTime=0;
    const started=media.play();
    assert.equal(players[0].destroyed,true, "old replacement stops synchronously at the stream transition");
    await started; await settle();
    assert.equal(players.length,1,"old metadata cannot launch another copy of A");
    if(delayedCurrentSource){
      assert.equal(adapter.getSnapshot().track.evidence,"awaiting-media-source");
      media.currentSrc=media.src;
    }
    environment.navigator.mediaSession.metadata = {title:"Всё пиздато",artist:"Зануда",album:"",artwork:[]};
    await settle();
    assert.equal(players.length,2);assert.equal(players[1].trackId,"1944611");assert.equal(players[1].playing,true);
    assert.equal(engine.activationCount,2);
  } finally {engine.destroy();await settle();adapter.unmount();}
  }
});

test("fresh metadata arriving before its stream is not mistaken for stale metadata", () => {
  const media = new FakeMedia();
  const {environment} = createEnvironment(media);
  const adapter = createAdapter(environment);
  adapter.mount({onSnapshot(){},onPlayerEvent(){}});
  try {
    adapter.ingestTrackPayload({id:"1944611",title:"Всё пиздато",artists:[{name:"Зануда"}],durationMs:193283},"fixture");
    Object.assign(environment.navigator.mediaSession.metadata,{title:"Всё пиздато",artist:"Зануда",album:"",artwork:[]});
    assert.equal(adapter.getSnapshot().track.id,"1944611");
    media.currentSrc = media.src = "https://strm-rad-25.strm.yandex.net/next";
    media.currentTime=0;
    assert.equal(adapter.getSnapshot().track.id,"1944611");
  } finally {adapter.unmount();}
});

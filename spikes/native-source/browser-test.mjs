import { createRequire } from "node:module";
import { createServer } from "node:http";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import path from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const fixture = path.resolve(process.env.CELIKOM_NATIVE_FIXTURE || "/tmp/celikom-native-source-fixture");
const extension = path.resolve("spikes/native-source");
const binary = process.env.CELIKOM_BROWSER_BINARY;
if (!binary) throw Error("An explicit actual Chrome or Brave executable is required");
for (const [name, duration] of [["short", 8], ["long", 360]]) {
  const result = spawnSync("ffmpeg", ["-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100", "-t", String(duration), "-ac", "2", "-c:a", "libmp3lame", "-b:a", "128k", "-y", path.join(fixture, name + ".mp3")]);
  if (result.status !== 0) throw Error("Synthetic audio encoder failed: " + result.stderr);
}
const files = {
  "/webpack-fixture.js": [await readFile(path.join(fixture, "webpack-fixture.js")), "application/javascript; charset=utf-8"],
  "/baseline.js": [await readFile("extension/src/player/replacement-player.ts"), "application/javascript; charset=utf-8"],
  "/core.js": [await readFile("extension/src/player/core.ts"), "application/javascript; charset=utf-8"],
  "/adapter.js": [await readFile("extension/src/adapters/yandex-music-adapter.ts"), "application/javascript; charset=utf-8"],
  "/native-metadata.js": [await readFile("spikes/native-source/native-metadata-adapter.js"), "application/javascript; charset=utf-8"],
  "/short.mp3": [await readFile(path.join(fixture, "short.mp3")), "audio/mpeg"],
  "/long.mp3": [await readFile(path.join(fixture, "long.mp3")), "audio/mpeg"]
};
const requests = [], retries = new Map();
const server = createServer(async (request, response) => {
  const url = new URL(request.url, "http://127.0.0.1");
  if (url.pathname === "/") {
    response.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Content-Security-Policy": "default-src 'none'; script-src 'self'; media-src 'self' blob:; connect-src 'self'" });
    return response.end('<!doctype html><meta charset="utf-8"><title>CELIKOM isolated native source fixture</title><script src="/webpack-fixture.js"></script><script src="/baseline.js"></script>');
  }
  const file = files[url.pathname];
  if (!file) { response.writeHead(404); return response.end(); }
  const [bytes, mime] = file;
  if (!request.headers.range) { response.writeHead(200, { "Content-Type": mime, "Content-Length": bytes.length }); return response.end(bytes); }
  requests.push({ path: url.pathname, range: request.headers.range, mode: url.searchParams.get("mode") });
  if (url.searchParams.get("mode") === "denied") { response.writeHead(403); return response.end(); }
  if (url.searchParams.get("mode") === "retry" && !retries.has(url.pathname)) {
    retries.set(url.pathname, true); response.writeHead(503); return response.end();
  }
  const match = /^bytes=(\d+)-(\d*)$/.exec(request.headers.range);
  if (!match) { response.writeHead(416); return response.end(); }
  const from = Number(match[1]), last = match[2] ? Math.min(Number(match[2]), bytes.length - 1) : bytes.length - 1;
  if (from > last) { response.writeHead(416); return response.end(); }
  const body = bytes.subarray(from, last + 1);
  if (url.searchParams.get("mode") === "slow-tail" && from > 0) await new Promise(resolve => setTimeout(resolve, 1800));
  response.writeHead(206, { "Content-Type": mime, "Content-Length": body.length,
    "Content-Range": `bytes ${url.searchParams.get("mode") === "bad-range" ? from + 1 : from}-${last}/${bytes.length}`,
    ETag: '"' + createHash("sha256").update(bytes).digest("hex") + '-1"' });
  response.end(body);
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const origin = "http://127.0.0.1:" + server.address().port;
let browser, context;
const profile = await mkdtemp(path.join(os.tmpdir(), "celikom-native-research-"));
try {
  context = await chromium.launchPersistentContext(profile, { executablePath: binary, headless: true,
    ignoreDefaultArgs: ["--disable-extensions"],
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--enable-unsafe-extension-debugging", "--autoplay-policy=no-user-gesture-required"] });
  browser = context.browser();
  const cdp = await browser.newBrowserCDPSession();
  const installation = await cdp.send("Extensions.loadUnpacked", { path: extension });
  console.log("Installed actual MV3 MAIN-world research extension", installation.id);
  const page = await context.newPage();
  page.on("pageerror", error => console.log("Fixture page error", error.stack));
  page.on("console", message => console.log("Browser fixture", message.text()));
  page.setDefaultTimeout(10000);
  await page.goto(origin, { waitUntil: "load" });
  try {
    await page.waitForFunction(() => window.__CELIKOM_NATIVE_SOURCE_RESEARCH__?.diagnostics().resourceClasses === 2);
  } catch (error) {
    console.log("Fixture state", await page.evaluate(() => ({ api: window.__CELIKOM_NATIVE_SOURCE_RESEARCH__?.diagnostics(), fixture: Boolean(window.__nativeFixture), chunks: Boolean(window.webpackChunk_N_E) })));
    throw error;
  }
  for (const name of ["core.js", "adapter.js", "native-metadata.js"]) await page.addScriptTag({ url: origin + "/" + name });
  const result = await page.evaluate(async origin => {
    const checks = [], check = (value, label) => { if (!value) throw Error(label); checks.push(label); console.log("PASS " + label); };
    const api = window.__CELIKOM_NATIVE_SOURCE_RESEARCH__, req = window.__nativeFixture.req;
    const Source = req(window.__nativeFixture.sourceModule).__testNativeSource;
    const resources = [];
    for (const [id, factory] of Object.entries(req.m)) {
      const s = factory.toString();
      if (!s.includes("getFileInfoBatch") || (!s.includes('"get-file-info"') && !s.includes('"resources/v2/file-info"'))) continue;
      for (const C of Object.values(req(id))) if (typeof C === "function" && C.prototype?.getFileInfo && C.prototype?.getFileInfoBatch) resources.push(C);
    }
    check(resources.length === 2, "actual v1 and v2 Yandex resource classes hooked");
    const download = async (suffix, replacementId = 1) => {
      const holder = { environment: window, destroyed: false, fetchAbort: new AbortController(), streamState: {} };
      return window.__CELIKOM_REPLACEMENT_PLAYER_V1__.ReplacementPlayer.prototype.fetchNativeAsset.call(holder,
        { url: origin + suffix, mimeType: "audio/mpeg", replacementId, version: 1 });
    };
    const start = performance.now(), short = await download("/short.mp3?mode=retry"), long = await download("/long.mp3");
    const shortUrl = URL.createObjectURL(short), longUrl = URL.createObjectURL(long);
    api.register("1001", shortUrl, { expiresAt: Date.now() + 60000, bitrate: 128 });
    api.register("1002", longUrl, { expiresAt: Date.now() + 60000, bitrate: 128 });
    const original = id => ({ trackId: String(id), realId: String(id), codec: "mp3", transport: "encraw", key: "fixture-not-a-secret", quality: "nq", urls: [origin + "/short.mp3"], url: origin + "/short.mp3" });
    function instance(C, kind) {
      const object = Object.create(C.prototype); object.createHttpOptions = x => x;
      object.httpClient = { get: async (path, options) => ({ url: origin + "/file-info", timings: { response: 1 }, json: async () => {
        const ids = String(options.params.trackIds || options.params.trackId).split(",");
        if (path.includes("batch")) return { [kind === "v2" ? "fileInfos" : "downloadInfos"]: ids.map(original) };
        return kind === "v2" ? original(ids[0]) : { downloadInfo: original(ids[0]) };
      } }) }; return object;
    }
    let firstInfo;
    for (const C of resources) {
      const kind = C.prototype.getByteRange ? "v1" : "v2", resource = instance(C, kind);
      const response = await resource.getFileInfo({ trackId: "1001", quality: "nq", codecs: ["mp3"], transports: ["raw"] });
      const info = response.downloadInfo || response.fileInfo; firstInfo = info;
      check(info.urls[0] === shortUrl && !Object.hasOwn(info, "key") && info.transport === "raw", kind + " exact ID native MP3 without encryption key");
      const params = { trackIds: "1001,9999,1002", quality: "nq", codecs: ["mp3"], transports: ["raw"] };
      const batch = await resource.getFileInfoBatch(params), list = batch.downloadInfos || batch.fileInfos;
      check(list.map(x => x.trackId).join(",") === params.trackIds && list[0].urls[0] === shortUrl && list[1].transport === "encraw" && list[2].urls[0] === longUrl, kind + " mixed batch preserves original track and order");
      const ac = new AbortController(); ac.abort();
      const cancelled = await resource.getFileInfo({ trackId: "1001", codecs: ["mp3"], transports: ["raw"] }, { signal: ac.signal });
      check((cancelled.fileInfo || cancelled.downloadInfo).transport === "encraw", kind + " aborted request never substituted");
      resource.httpClient.get = async () => { throw Error("controlled-original-network-failure"); };
      try { await resource.getFileInfo({ trackId: "1001", codecs: ["mp3"], transports: ["raw"] }); throw Error("swallowed-network-error"); }
      catch (e) { check(e.message === "controlled-original-network-failure", kind + " original failure is not bypassed"); }
    }
    const audio = document.createElement("audio"); document.body.append(audio);
    const load = async info => {
      const source = new Source({ data: info, loadingTime: performance.now() });
      source.vsid = "fixture"; source.sourceIndex = 0; source.positionSec = 0;
      const ready = new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(Error("native load timeout")), 8000);
        audio.addEventListener("loadeddata", () => { clearTimeout(timer); resolve(); }, { once: true });
        audio.addEventListener("error", () => { clearTimeout(timer); reject(Error("native decode error " + JSON.stringify({ code: audio.error?.code, message: audio.error?.message, source: audio.src, stage: checks.at(-1) }))); }, { once: true });
      });
      audio.src = source.src; audio.load(); await ready;
      return source.src;
    };
    const expanded = await load(firstInfo);
    check(expanded.includes("?vsid=") && !audio.src.includes("?vsid=") && audio.src.includes("#t=0"), "actual private Yandex source URL parameters normalized only for owned Blob");
    await audio.play();
    const advancingDeadline = performance.now() + 3000;
    while ((audio.paused || audio.currentTime <= 0) && performance.now() < advancingDeadline) await new Promise(r => setTimeout(r, 25));
    check(!audio.paused && audio.currentTime > 0, "single native HTMLAudioElement actually plays");
    audio.pause(); const paused = audio.currentTime; await new Promise(r => setTimeout(r, 150));
    check(audio.paused && Math.abs(audio.currentTime - paused) < 0.02, "native pause holds clock");
    const sought = new Promise(r => audio.addEventListener("seeked", r, { once: true })); audio.currentTime = 5; await sought;
    check(Math.abs(audio.currentTime - 5) < 0.08, "native seek reaches requested position");
    const resource = instance(resources[0], resources[0].prototype.getByteRange ? "v1" : "v2");
    const resolve = async id => { const r = await resource.getFileInfo({ trackId: id, quality: "nq", codecs: ["mp3"], transports: ["raw"] }); return r.fileInfo || r.downloadInfo; };
    await load(await resolve("1002"));
    check(audio.duration > 359 && audio.duration < 361, "six minute native MP3 decoded");
    const tail = new Promise(r => audio.addEventListener("seeked", r, { once: true })); audio.currentTime = 350; await tail; await audio.play();
    check(audio.currentTime >= 350 && !audio.paused, "long track seek beyond first HTTP range plays");
    for (let i = 0; i < 6; i++) { await load(await resolve(i % 2 ? "1001" : "1002")); await audio.play(); }
    check(document.querySelectorAll("audio").length === 1, "rapid next uses exactly one media element");
    api.setEnabled(false); const restored = await resolve("1001");
    check(restored.transport === "encraw" && restored.key === "fixture-not-a-secret", "disabled hook returns original encrypted descriptor untouched");
    await load({ ...restored, codec: "mp3", transport: "raw" }); await audio.play();
    check(audio.currentSrc.startsWith(origin + "/short.mp3") && !audio.paused, "explicit source reacquisition restores original fixture playback");
    audio.pause();
    const baseline = new window.__CELIKOM_REPLACEMENT_PLAYER_V1__.ReplacementPlayer(window, () => {});
    let clock = performance.now();
    await baseline.prepare({ url: origin + "/long.mp3?mode=slow-tail", mimeType: "audio/mpeg", durationMs: 360030 });
    const baselinePreparationMs = Math.round(performance.now() - clock); baseline.destroy();
    clock = performance.now(); const nativeCold = await download("/long.mp3?mode=slow-tail", 2);
    const nativeColdUrl = URL.createObjectURL(nativeCold); api.setEnabled(true);
    api.register("1002", nativeColdUrl, { expiresAt: Date.now() + 60000, bitrate: 128 });
    await load(await resolve("1002"));
    const nativeColdPreparationMs = Math.round(performance.now() - clock);
    clock = performance.now(); await load(await resolve("1002"));
    const nativeWarmPreparationMs = Math.round(performance.now() - clock);
    const preparationComparison = { scope: "controlled decoder preparation only, not signed-in end-to-end latency", continuationDelayMs: 1800,
      baseline073StreamingMs: baselinePreparationMs, nativeColdCompleteFileMs: nativeColdPreparationMs, nativeAlreadyPreparedFileMs: nativeWarmPreparationMs };
    check(nativeColdPreparationMs >= 1600, "cold complete file honestly waits for delayed continuation");
    api.setEnabled(true);api.register("1001", shortUrl, { expiresAt: Date.now() + 50 }); await new Promise(r => setTimeout(r, 75));
    check((await resolve("1001")).transport === "encraw", "expired asset is never assigned to new request");
    for (const mode of ["denied", "bad-range"]) {
      try { await download("/short.mp3?mode=" + mode); throw Error("accepted-invalid-download"); }
      catch (e) { check(e.message !== "accepted-invalid-download", mode + " download rejected before native registration"); }
    }
    const beforeDispose = api.diagnostics(); api.unregister("1001"); api.unregister("1002");
    audio.pause(); audio.removeAttribute("src"); audio.load();audio.remove();URL.revokeObjectURL(shortUrl);URL.revokeObjectURL(longUrl);URL.revokeObjectURL(nativeColdUrl);
    const react = req(53548);
    const rendererModule = Object.keys(req.m).find(id => {
      const src = req.m[id].toString(); return src.includes("createRoot=function") && src.includes("hydrateRoot=function");
    });
    check(Boolean(rendererModule), "actual Yandex React renderer available for discovery test");
    const renderer = req(rendererModule), context = react.createContext(null), mount = document.createElement("div");
    document.body.append(mount);
    let mutationCalls = 0;
    const forbidden = () => { mutationCalls++; throw Error("read-only discovery called engine control"); };
    const engineAudio = document.createElement("audio");
    const core = { getMediaSource: forbidden, reload: forbidden, corePlay: forbidden, core: { setSrc: forbidden },
      currentAudioElement: { value: engineAudio }, hooks: { beforeMediaSourceContentReload: { promise: forbidden }, afterMediaSourceContentReload: { promise: forbidden } } };
    const ActualPlayback = req(window.__nativeFixture.reloadModule).VE;
    const playback = Object.create(ActualPlayback.prototype);
    playback.playbackState = {
      queueState: { currentEntity: { value: { entity: { data: { meta: { id: "1001", durationMs: 8000 } } } } } }, currentMediaPlayer: { value: core }
    };
    check(!playback.queueState && !playback.currentMediaPlayer && playback.state === playback.playbackState,
      "actual Yandex Playback exposes queue and player only through state getter");
    const controller = { getState: forbidden, playbackController: { getPlayback: () => playback } };
    function Consumer() { react.useContext(context); return react.createElement("button", { id: "celikom-react-consumer" }, "context fixture"); }
    const reactRoot = renderer.createRoot(mount);
    reactRoot.render(react.createElement(context.Provider, { value: controller }, react.createElement(Consumer)));
    const mountedDeadline = performance.now() + 3000;
    while (!mount.querySelector("button") && performance.now() < mountedDeadline) await new Promise(r => setTimeout(r, 25));
    check(Boolean(mount.querySelector("button")), "actual React context consumer rendered outside player selectors");
    const discovered = new window.__CELIKOM_NATIVE_ENGINE_PORT__.EnginePort().inspect();
    check(discovered.found && discovered.trackId === "1001" && discovered.shape.playbackState && discovered.mediaEvents && discovered.nativeReload
      && discovered.discovery.matchSource === "fiber-context" && mutationCalls === 0,
      "actual React dependency discovery finds controller without invoking playback");
    const reloadExports = req(window.__nativeFixture.reloadModule), NativeCore = reloadExports.__testReloadCore;
    const nativeAudio = document.createElement("audio"); document.body.append(nativeAudio);
    const nativeCore = Object.create(NativeCore.prototype), entity = { data: { meta: { id: "1001", durationMs: 8000 } }, mediaSourceData: {} };
    const v2 = resources.find(C => !C.prototype.getByteRange), nativeResource = instance(v2, "v2");
    const appliedSources = [];
    const applySource = async ({ source, positionSec = 0 }, play) => {
      appliedSources.push({ requested: positionSec, live: nativeAudio.currentTime, at: performance.now() });
      source.vsid = "native-session-fixture"; source.sourceIndex = 0; source.positionSec = positionSec;
      const loaded = new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(Error("session audio load timeout")), 8000);
        nativeAudio.addEventListener("loadeddata", () => { clearTimeout(timeout); resolve(); }, { once: true });
        nativeAudio.addEventListener("error", () => { clearTimeout(timeout); reject(Error("session audio decode failed")); }, { once: true });
      });
      nativeAudio.src = source.src; nativeAudio.load(); await loaded;
      nativeAudio.currentTime = positionSec;
      if (play) await nativeAudio.play(); else nativeAudio.pause();
    };
    const status = {}, progress = {};
    Object.defineProperty(status, "value", { get: () => nativeAudio.paused ? reloadExports.MT.PAUSED : reloadExports.MT.PLAYING, set: () => {} });
    Object.defineProperty(progress, "value", { get: () => ({ position: nativeAudio.currentTime }) });
    Object.defineProperties(nativeCore, {
      state: { value: { status, progress } },
      currentAudioElement: { value: { value: nativeAudio } },
      hooks: { value: Object.fromEntries(["beforeMediaSourceContentReload", "afterMediaSourceContentReload", "afterError"].map(key => [key, { promise: async () => {} }])) },
      getMediaSource: { configurable: true, writable: true, value: async ({ entity }) => {
        const response = await nativeResource.getFileInfo({ trackId: entity.data.meta.id, quality: "nq", codecs: ["mp3"], transports: ["raw"] });
        return new Source({ data: response.fileInfo, loadingTime: performance.now() });
      } },
      corePlay: { configurable: true, value: args => applySource(args, true) },
      core: { value: { setSrc: args => applySource(args, false) } }
    });
    const nativePlayback = Object.create(ActualPlayback.prototype);
    nativePlayback.playbackState = { queueState: { currentEntity: { value: { entity } } }, currentMediaPlayer: { value: nativeCore } };
    const nativeController = { getState: () => nativePlayback.state, playbackController: { getPlayback: () => nativePlayback } };
    playback.playbackState = nativePlayback.playbackState;
    const metadataPort = new window.__CELIKOM_NATIVE_ENGINE_PORT__.EnginePort(), bindingDeadline = performance.now() + 3000;
    while (metadataPort.binding()?.audio !== nativeAudio && performance.now() < bindingDeadline) await new Promise(r => setTimeout(r, 20));
    check(metadataPort.binding()?.audio === nativeAudio, "actual React context reads updated native Playback state");
    const metadataAdapter = new window.__CELIKOM_YANDEX_ADAPTER_V1__.YandexMusicAdapter(window);
    metadataAdapter.trackCatalog.set("1001", { id: "1001", title: "Fixture song", artist: "Fixture artist", durationMs: 8000 });
    const sessionPort = new window.__CELIKOM_NATIVE_ENGINE_PORT__.EnginePort({ getController: () => nativeController });
    const nativeSession = new window.__CELIKOM_NATIVE_SESSION__.NativeSession({ port: sessionPort, resource: api });
    await nativeCore.reload(entity); await nativeAudio.play(); nativeAudio.currentTime = 0.7;
    const audioCount = document.querySelectorAll("audio").length;
    await nativeSession.configure(true, 1);
    nativeSession.publish({ trackId: "1001", generation: 1, blob: short, durationMs: 8000, expiresAt: Date.now() + 60000 });
    await nativeSession.activate("1001", 1);
    check(nativeSession.inspect().activeTrackId === "1001" && nativeAudio.currentSrc.startsWith("blob:") && nativeAudio.currentTime >= 0.6,
      "actual stock reload applies admitted file through existing native audio and retains position");
    check(document.querySelectorAll("audio").length === audioCount, "native switch creates no second audio element");
    const nativeMetadata = metadataAdapter.trackState(nativeAudio);
    check(nativeMetadata.id === "1001" && !nativeMetadata.ambiguous && nativeMetadata.metadata.title === "Fixture song",
      "existing CELIKOM metadata adapter preserves track ID and upload target after native source change");
    nativeAudio.pause(); const pausedAt = nativeAudio.currentTime; await new Promise(r => setTimeout(r, 120));
    check(nativeAudio.paused && Math.abs(nativeAudio.currentTime - pausedAt) < 0.02, "native pause controls replacement directly");
    nativeAudio.currentTime = 2; await new Promise(r => setTimeout(r, 100));
    check(Math.abs(nativeAudio.currentTime - 2) < 0.1, "native seek controls replacement directly");
    await nativeSession.configure(false, 2);
    check(!nativeSession.inspect().activeTrackId && nativeAudio.currentSrc.startsWith(origin) && nativeAudio.paused,
      "stock reload restores controlled original without starting a paused song");
    await nativeSession.configure(true, 3);
    nativeSession.publish({ trackId: "1001", generation: 3, blob: short, durationMs: 8000, expiresAt: Date.now() + 60000 });
    await nativeSession.activate("1001", 3);
    const nextEntity = { data: { meta: { id: "1002", durationMs: 8000 } }, mediaSourceData: {} };
    nativePlayback.state.queueState.currentEntity.value = { entity: nextEntity };
    await nativeCore.reload(nextEntity);
    await nativeSession.confirmSource(nativeAudio, null, new AbortController().signal);
    check(nativeAudio.currentSrc.startsWith(origin) && sessionPort.inspect().trackId === "1002", "Next does not reuse prior replacement for another ID");
    await nativeSession.configure(false, 4);
    /* Trial A uses the actual stock reload with a delayed file-info request
       while the original audio clock continues advancing. */
    const get = nativeResource.httpClient.get;
    nativeResource.httpClient.get = async function (...args) {
      await new Promise(resolve => setTimeout(resolve, 180)); return Reflect.apply(get, this, args);
    };
    await nativeAudio.play();
    await nativeCore.reload(nextEntity);
    const stale = appliedSources.at(-1), staleRewindMs = Math.round((stale.live - stale.requested) * 1000);
    await sessionPort.reload("1002", { livePosition: true });
    const corrected = appliedSources.at(-1), correctedRewindMs = Math.round((corrected.live - corrected.requested) * 1000);
    check(staleRewindMs >= 100 && Math.abs(correctedRewindMs) < 30,
      "trial A removes stale-position replay under the same delayed stock source load");
    nativeResource.httpClient.get = get;
    /* Trial B reads the actual public queue's derived nextEntity getter,
       including a queue order different from entityList order. */
    const Queue = req(28692).Di, lastEntity = { data: { meta: { id: "1003", durationMs: 8000 } }, mediaSourceData: {} };
    const queue = new Queue({ prevIndex: null, index: 0, nextIndex: 1, entityList: [{ entity: lastEntity }, { entity: nextEntity }],
      order: [1, 0], repeat: req(28692).pM.NONE, shuffle: true, filterParams: {} });
    nativePlayback.playbackState.queueState = queue.state;
    check(queue.state.currentEntity.value.entity === nextEntity && queue.state.nextEntity.value.entity === lastEntity,
      "trial B gets next ID from actual queue state rather than guessing DOM or array order");
    const nextUrl = URL.createObjectURL(short); api.setEnabled(true);
    api.register(String(queue.state.nextEntity.value.entity.data.meta.id), nextUrl, { expiresAt: Date.now() + 60000, bitrate: 128 });
    const sourceCount = appliedSources.length, nextStart = performance.now();
    queue.state.index.value = 1; queue.state.nextIndex.value = null;
    const nextSource = await nativeCore.getMediaSource({ entity: queue.state.currentEntity.value.entity });
    await nativeCore.corePlay({ source: nextSource, positionSec: 0 });
    const preparedNextMs = Math.round(performance.now() - nextStart);
    check(nativeAudio.currentSrc.startsWith("blob:") && appliedSources.length === sourceCount + 1 && sessionPort.inspect().trackId === "1003",
      "trial B prepared next track uses one native source assignment without late replacement reload");
    const legacyWarmSamples = [];
    for (let i = 0; i < 3; i++) {
      const legacy = new window.__CELIKOM_REPLACEMENT_PLAYER_V1__.ReplacementPlayer(window, () => {}), began = performance.now();
      await legacy.prepare({ url: origin + "/short.mp3", mimeType: "audio/mpeg", durationMs: 8000 });
      legacyWarmSamples.push(Math.round(performance.now() - began)); legacy.destroy();
    }
    const trials = { position: { sourceDelayMs: 180, staleRewindMs, correctedRewindMs }, preparedNext: {
      nativeMs: preparedNextMs, legacy073PrepareSamplesMs: legacyWarmSamples,
      scope: "controlled prepared-file path, not signed-in end-to-end playback",
      limitations: ["exact next entity must already exist", "fresh admission and cancellation are not wired into this laboratory next registration"] } };
    nativeAudio.pause(); nativeAudio.remove(); api.unregister("1003"); URL.revokeObjectURL(nextUrl);
    api.dispose();
    check(api.diagnostics().stopped && api.diagnostics().assets === 0, "dispose restores owned prototype hooks and removes registry");
    reactRoot.unmount(); mount.remove();
    return { checks, beforeDispose, preparationComparison, trials, experimentElapsedMs: Math.round(performance.now() - start), limitations: ["controlled resource responses; not a signed-in Yandex listening session", "stock reload tested with real audio; actual encrypted decryption is not tested", "no measured end-to-end speed advantage"] };
  }, origin);
  let liveProbe;
  const livePage = await context.newPage();
  try {
    const response = await livePage.goto("https://music.yandex.ru/", { waitUntil: "domcontentloaded", timeout: 45000 });
    await livePage.waitForFunction(() => window.__CELIKOM_NATIVE_SOURCE_RESEARCH__?.diagnostics().resourceClasses === 2, undefined, { timeout: 15000 });
    liveProbe = { status: response.status(), diagnostics: await livePage.evaluate(() => window.__CELIKOM_NATIVE_SOURCE_RESEARCH__.diagnostics()),
      engine: await livePage.evaluate(() => new window.__CELIKOM_NATIVE_ENGINE_PORT__.EnginePort().inspect()), signedInPlaybackTested: false };
  } catch (error) {
    liveProbe = { unavailable: true, reason: error.name, signedInPlaybackTested: false };
  } finally { await livePage.close(); }
  console.log(JSON.stringify({ browser: await browser.version(), extensionId: installation.id, ...result, liveProbe, httpRanges: requests }, null, 2));
  await writeFile(path.join(fixture, path.basename(binary) + "-results.json"), JSON.stringify({ browser: await browser.version(), ...result, liveProbe, httpRanges: requests }, null, 2) + "\n");
} finally {
  await context?.close();
  await rm(profile, { recursive: true, force: true });
  await new Promise(resolve => server.close(resolve));
}

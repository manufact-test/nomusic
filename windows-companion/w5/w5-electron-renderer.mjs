/*
 * W5 isolated Electron renderer: actual pinned public Yandex resource/source
 * factories with synthetic MP3. NOT logged-in/installed Yandex Music.
 */
import { createWindowsSourceBridge } from "/bridge.mjs";

const checks = [];
const assert = (condition, description) => {
  if (!condition) throw Error("FAIL " + description);
  checks.push(description);
};
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const req = window.__nativeFixture?.req;
let bridge, player;
const blobs = [];

async function run() {
  assert(typeof req === "function", "pinned public Yandex Webpack fixture loaded");
  const Source = req(window.__nativeFixture.sourceModule).__testNativeSource;
  assert(typeof Source === "function", "actual private Yandex source class exposed only in fixture");

  const classes = [];
  for (const [moduleId, factory] of Object.entries(req.m)) {
    const text = Function.prototype.toString.call(factory);
    if (!text.includes("getFileInfoBatch") ||
        (!text.includes('"get-file-info"') && !text.includes('"resources/v2/file-info"')))
      continue;
    try {
      for (const value of Object.values(req(moduleId))) {
        if (typeof value === "function" && typeof value.prototype?.getFileInfo === "function" &&
            typeof value.prototype?.getFileInfoBatch === "function" &&
            !classes.includes(value)) classes.push(value);
      }
    } catch { /* only explicitly matching class exports accepted */ }
  }
  assert(classes.length === 2, "genuine v1 and v2 Yandex file-info resources discovered");

  const ticket = async (id, ttl = 120) => {
    const response = await fetch("/ticket/" + id + "?ttl=" + ttl);
    assert(response.status === 200, "test-only signed ticket for " + id);
    return response.json();
  };
  const one = await ticket("1001"), two = await ticket("2002");
  const range = await fetch(one.url, { headers: { Range: "bytes=0-1023" } });
  assert(range.status === 206 &&
    (range.headers.get("Content-Range") || "").startsWith("bytes 0-1023/"),
    "synthetic authorized Range returns HTTP 206");
  assert((await range.arrayBuffer()).byteLength === 1024, "Range bytes match expected amount");
  const invalidRange = await fetch(one.url, { headers: { Range: "bytes=999999999-" } });
  assert(invalidRange.status === 416, "out-of-range request returns 416");
  assert((await fetch("/audio/1001")).status === 403, "unsigned audio denied");
  const oldTicket = await ticket("1001", -1);
  assert((await fetch(oldTicket.url)).status === 403, "expired signed audio denied");

  const fetchPreparedMp3 = async t => {
    const response = await fetch(t.url);
    assert(response.status === 200 && response.headers.get("content-type") === "audio/mpeg",
      "authorized synthetic MP3 completely prepared");
    const bytes = await response.arrayBuffer();
    const url = URL.createObjectURL(new Blob([bytes], { type: "audio/mpeg" }));
    blobs.push(url);
    return url;
  };
  const [a, b] = await Promise.all([fetchPreparedMp3(one), fetchPreparedMp3(two)]);
  bridge = createWindowsSourceBridge({ origin: location.origin });
  for (const C of classes) bridge.install(C.prototype);
  assert(bridge.diagnostics().installed === 2, "W4 adapter attached to two actual Yandex resource prototypes");
  bridge.setEnabled(true);
  bridge.setTrack("1001");
  for (const [trackId, url] of [["1001", a], ["2002", b]])
    bridge.registerPreparedAsset({ trackId, url, expiresAt: Date.now() + 100000,
      bitrate: 128, approved: true, entitled: true, durationMatched: true,
      audioValidated: true });

  const originals = new Map([["1001", one.url], ["2002", two.url]]);
  const initial = trackId => ({ trackId: String(trackId), realId: String(trackId),
    quality: "nq", codec: "mp3", bitrate: 128, transport: "raw",
    url: originals.get(String(trackId)) || originals.get("1001"),
    urls: [originals.get(String(trackId)) || originals.get("1001")] });

  const resources = classes.map(C => {
    const kind = C.prototype.getByteRange ? "v1" : "v2";
    const instance = Object.create(C.prototype);
    instance.createHttpOptions = x => x;
    instance.httpClient = {
      get: async (resourcePath, options) => ({
        url: location.origin + "/file-info-fixture",
        timings: { response: 1 },
        json: async () => {
          const ids = String(options?.params?.trackIds || options?.params?.trackId || "").split(",");
          if (resourcePath.includes("batch"))
            return { [kind === "v1" ? "downloadInfos" : "fileInfos"]: ids.map(initial) };
          return kind === "v1" ? { downloadInfo: initial(ids[0]) } : initial(ids[0]);
        }
      })
    };
    return { instance, kind };
  });

  const get = async (resource, trackId) => {
    const result = await resource.getFileInfo({
      trackId, quality: "nq", codecs: ["mp3"], transports: ["raw"]
    });
    return result?.downloadInfo || result?.fileInfo;
  };
  for (const { instance, kind } of resources) {
    const info = await get(instance, "1001");
    assert(info?.url === a && info.transport === "raw" && info.codec === "mp3",
      "actual " + kind + " resource yields W4 chosen Blob");
    const mixed = await instance.getFileInfoBatch({
      trackIds: "1001,9999,2002", quality: "nq", codecs: ["mp3"], transports: ["raw"]
    });
    const batch = mixed.downloadInfos || mixed.fileInfos;
    assert(batch?.length === 3 && batch[0].url === a &&
      batch[1].url === originals.get("1001") && batch[2].url === two.url,
      "actual " + kind + " batch preserves original/unselected tracks and order");
  }

  const nativeSourceUrl = data => {
    const native = new Source({ data, loadingTime: performance.now() });
    native.vsid = "celikom-w5-fixture";
    native.sourceIndex = 0;
    native.positionSec = 0;
    const raw = native.src;
    if (typeof raw !== "string") throw Error("native Yandex source URL not produced");
    // Private Yandex getter adds vsid/source_index to Blob URLs.
    // Normalize ONLY the exact already validated CELIKOM-owned Blob.
    for (const owned of blobs) {
      if (!raw.startsWith(owned + "?")) continue;
      const fragment = raw.indexOf("#", owned.length);
      return { raw, playable: owned + (fragment < 0 ? "" : raw.slice(fragment)), owned: true };
    }
    // The real Yandex getter appends '?vsid=...' even when a fixture URL
    // already has HMAC query parameters. That invalidates a signed test URL.
    // Normalize ONLY these two fixture-origin tickets; never rewrite actual
    // third-party Yandex URLs, and retain the exact signed capability.
    for (const ticketUrl of originals.values()) {
      if (!raw.startsWith(ticketUrl + "?")) continue;
      const fragment = raw.indexOf("#", ticketUrl.length);
      return { raw, playable: ticketUrl + (fragment < 0 ? "" : raw.slice(fragment)),
        owned: false, signedFixtureNormalized: true };
    }
    return { raw, playable: raw, owned: false, signedFixtureNormalized: false };
  };

  player = document.createElement("audio");
  player.muted = true; // real Chromium decoding, no audible output on CI host
  player.preload = "auto";
  document.body.append(player);
  assert(document.querySelectorAll("audio,video").length === 1,
    "only one Electron native media element is created");

  const loadNative = async data => {
    const urls = nativeSourceUrl(data);
    const loaded = new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        cleanup();
        reject(Error("native decoder load timeout"));
      }, 20000);
      const success = () => { cleanup(); resolve(); };
      const failed = () => {
        cleanup();
        reject(Error("native decoder failed code " + (player.error?.code ?? "unknown")));
      };
      const cleanup = () => {
        clearTimeout(timer);
        player.removeEventListener("loadeddata", success);
        player.removeEventListener("error", failed);
      };
      player.addEventListener("loadeddata", success);
      player.addEventListener("error", failed);
    });
    player.pause();
    player.src = urls.playable;
    player.load();
    await loaded;
    return urls;
  };
  const firstInfo = await get(resources[0].instance, "1001");
  const firstUrls = await loadNative(firstInfo);
  assert(firstUrls.owned && firstUrls.raw.includes("?vsid=") &&
    player.currentSrc.startsWith(a), "real Yandex source getter + narrowly normalized Blob reaches native decoder");
  assert(player.duration > 8.5 && player.duration < 9.5, "synthetic MP3 duration decoded in real Electron");
  await player.play();
  await sleep(350);
  assert(!player.paused && player.currentTime > 0.05,
    "native Electron playback clock advances without second player");
  player.pause();
  const timeOnPause = player.currentTime;
  await sleep(250);
  assert(player.paused && Math.abs(player.currentTime - timeOnPause) < 0.03,
    "native pause holds one playback clock");
  player.currentTime = 6;
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(Error("seek timeout")), 10000);
    player.addEventListener("seeked", () => { clearTimeout(timeout); resolve(); }, { once: true });
  });
  assert(Math.abs(player.currentTime - 6) < 0.2,
    "native seek reaches requested position on alternate source");

  bridge.setTrack("2002");
  const secondInfo = await get(resources[1].instance, "2002");
  const secondUrls = await loadNative(secondInfo);
  assert(secondUrls.owned && secondInfo.url === b, "Next replaces source on exact new track");
  assert(player.duration > 35 && player.duration < 37,
    "36-second alternate MP3 decoded by same native media element");
  player.currentTime = 30;
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(Error("late seek timeout")), 10000);
    player.addEventListener("seeked", () => { clearTimeout(timer); resolve(); }, { once: true });
  });
  await player.play();
  assert(player.currentTime >= 29.8 && !player.paused,
    "late seek and playback after Next remain native");
  assert(document.querySelectorAll("audio,video").length === 1,
    "Next does not spawn a second decoder");

  // Delay a real resource instance's mocked HTTP response; ensure W4 fences it.
  const slow = resources[0].instance;
  const oldHttp = slow.httpClient.get;
  let release;
  const blocker = new Promise(resolve => { release = resolve; });
  slow.httpClient.get = async (...args) => {
    await blocker;
    return oldHttp(...args);
  };
  bridge.setTrack("1001");
  const pending = get(slow, "1001");
  bridge.setTrack("2002");
  release();
  const late = await pending;
  assert(late.url === one.url, "stale source response after Next remains original");
  slow.httpClient.get = oldHttp;

  bridge.original();
  const restored = await get(resources[1].instance, "2002");
  assert(restored.url === two.url, "Original selects native original source on next acquisition");
  const originalUrls = await loadNative(restored);
  assert(!originalUrls.owned && originalUrls.signedFixtureNormalized &&
    player.currentSrc.startsWith(two.url),
    "Yandex getter appended URL query; fixture signer preserved for native original");
  await player.play();
  await sleep(180);
  assert(!player.paused && player.currentTime >= 0,
    "original synthetic source plays after explicit reacquisition");
  bridge.stop();
  assert((await get(resources[1].instance, "2002")).url === two.url,
    "Stop prevents subsequent source substitutions");
  assert(document.querySelectorAll("audio,video").length === 1,
    "Stop does not create overlay player");
  bridge.dispose();
  assert(bridge.diagnostics().disposed, "adapter unhooks after experiment");
  return { passed: true, assertions: checks.length, checks };
}

run()
  .then(result => { window.__CELIKOM_W5_RESULT__ = result; })
  .catch(e => {
    window.__CELIKOM_W5_RESULT__ = {
      passed: false, error: String(e?.message || e), assertions: checks.length, checks
    };
  })
  .finally(() => {
    try { player?.pause(); player?.removeAttribute("src"); player?.load(); player?.remove(); } catch {}
    try { bridge?.dispose(); } catch {}
    for (const u of blobs) URL.revokeObjectURL(u);
  });

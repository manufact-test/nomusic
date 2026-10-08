import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

await import("../dist/unpacked/player/core.js");
const core = globalThis.__CELIKOM_PLAYER_CORE_V1__;
const cases = JSON.parse(await readFile(new URL("./fixtures/yandex-player-cases.json", import.meta.url), "utf8"));

test("production core exposes a versioned closed protocol", () => {
  assert.equal(core.VERSION, "0.4.2");
  assert.equal(core.PROTOCOL_VERSION, 1);
  assert.equal(core.CHANNEL, "CELIKOM_PLAYER_V1");
  assert.equal(Object.isFrozen(core), true);
});

test("Track ID parsing supports player routes and API variants", () => {
  const urls = [
    "https://music.yandex.ru/album/192577/track/1944599",
    "https://api.music.yandex.net/tracks/1944599",
    "https://music.yandex.ru/play?trackId=1944599"
  ];
  for (const url of urls) assert.equal(core.parseTrackIdFromUrl(url), "1944599");
  for (const url of ["", "https://music.yandex.ru/landing/main", "javascript:track/123"]) {
    assert.equal(core.parseTrackIdFromUrl(url), null);
  }
});

test("catalog matching resolves exact tracks on album and landing variants", () => {
  for (const fixture of [cases.albumRoute, cases.landingFetch]) {
    const result = core.pickTrackFromCatalog(fixture.catalog, fixture.metadata, 100);
    assert.equal(result.ambiguous, false);
    assert.equal(result.selected?.id, fixture.expectedId);
    assert.ok(result.selected.score >= 240);
  }
});

test("candidate selection fails closed when two Track IDs are equally plausible", () => {
  const result = core.pickBestTrackCandidate(cases.ambiguousQueue.candidates, 70);
  assert.equal(result.ambiguous, true);
  assert.equal(result.selected, null);
});

test("detached playing audio outranks a short Yandex ad video", () => {
  const video = {
    isMedia: true,
    tag: "video",
    source: "https://strm.yandex.ru/ad",
    connected: true,
    paused: false,
    duration: 15.997,
    currentTime: 6.5,
    readyState: 4,
    hasSource: true
  };
  const audio = {
    isMedia: true,
    tag: "audio",
    source: "https://strm-rad-24.strm.yandex.net/track",
    connected: false,
    paused: false,
    duration: 238.051,
    currentTime: 15.356,
    readyState: 4,
    hasSource: true
  };
  video.knownAd = core.isYandexAdMediaCandidate(video);
  audio.knownAd = core.isYandexAdMediaCandidate(audio);
  assert.equal(video.knownAd, true);
  assert.equal(audio.knownAd, false);
  assert.equal(core.scoreMediaCandidate(video), Number.NEGATIVE_INFINITY);
  assert.ok(core.scoreMediaCandidate(audio) > 200);
});

test("native player events normalize to the stable PlayerEvent contract", () => {
  const expected = {
    play: "PLAY",
    playing: "PLAY",
    pause: "PAUSE",
    seeking: "SEEK",
    seeked: "SEEK",
    timeupdate: "TIME_UPDATE",
    volumechange: "VOLUME_CHANGED",
    ratechange: "RATE_CHANGED",
    loadedmetadata: "METADATA_CHANGED",
    ended: "ENDED",
    error: "ERROR"
  };
  for (const [nativeEvent, normalized] of Object.entries(expected)) {
    assert.equal(core.normalizeNativeEventType(nativeEvent), normalized);
  }
  assert.equal(core.normalizeNativeEventType("canplay"), null);
});

test("utility media exclusion leaves full-length data audio and short streamed audio available", () => {
  assert.equal(core.isUtilityMediaCandidate({ tag: "audio", source: "data:audio/wav;base64,fixture", duration: 0.015 }), true);
  assert.equal(core.isUtilityMediaCandidate({ tag: "audio", source: "data:audio/wav;base64,fixture", duration: NaN }), true);
  assert.equal(core.isUtilityMediaCandidate({ tag: "audio", source: "data:audio/mp3;base64,fixture", duration: 201 }), false);
  assert.equal(core.isUtilityMediaCandidate({ tag: "audio", source: "https://strm-rad-24.strm.yandex.net/track", duration: 0.5 }), false);
});

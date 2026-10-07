"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("../src/shared/core.js");

test("extracts an exact Track ID from supported URL shapes", () => {
  assert.equal(core.parseTrackIdFromUrl("https://music.yandex.ru/album/12/track/987654"), "987654");
  assert.equal(core.parseTrackIdFromUrl("https://music.yandex.ru/track/123456/"), "123456");
  assert.equal(core.parseTrackIdFromUrl("https://example.test/api/tracks/456789?token=secret"), "456789");
  assert.equal(core.parseTrackIdFromUrl("https://example.test/player?trackId=321"), "321");
});

test("rejects non-exact or unsafe Track IDs", () => {
  assert.equal(core.parseTrackIdFromUrl("https://music.yandex.ru/album/12"), null);
  assert.equal(core.parseTrackIdFromUrl("javascript:alert(1)"), null);
  assert.equal(core.normalizeTrackId("12a3"), null);
  assert.equal(core.normalizeTrackId(""), null);
});

test("selects the strongest unambiguous Track ID candidate", () => {
  const result = core.pickBestTrackCandidate([
    { id: "111", score: 25, source: "route" },
    { id: "222", score: 135, source: "player" },
    { id: "222", score: 95, source: "duplicate" }
  ]);
  assert.equal(result.selected.id, "222");
  assert.equal(result.ambiguous, false);
});

test("fails closed for ambiguous Track ID evidence", () => {
  const result = core.pickBestTrackCandidate([
    { id: "111", score: 120, source: "player-a" },
    { id: "222", score: 114, source: "player-b" }
  ]);
  assert.equal(result.selected, null);
  assert.equal(result.ambiguous, true);
});

test("computes drift and correction target", () => {
  assert.deepEqual(core.computeDrift(10, 10.2, 350, 600), {
    driftMs: 200,
    shouldCorrect: false,
    targetTime: 10
  });
  assert.deepEqual(core.computeDrift(10, 10.5, 350, 600), {
    driftMs: 500,
    shouldCorrect: true,
    targetTime: 10
  });
  assert.deepEqual(core.computeDrift(125, 25.1, 350, 100), {
    driftMs: 100,
    shouldCorrect: false,
    targetTime: 25
  });
});

test("projects a playing master between bridge snapshots", () => {
  assert.equal(core.projectMediaTime({
    currentTime: 10,
    duration: 200,
    playbackRate: 1,
    paused: false,
    ended: false,
    seeking: false
  }, 1000, 1500), 10.5);

  assert.equal(core.projectMediaTime({
    currentTime: 10,
    duration: 200,
    playbackRate: 1,
    paused: true
  }, 1000, 1500), 10);

  assert.equal(core.projectMediaTime({
    currentTime: 199.8,
    duration: 200,
    playbackRate: 1,
    paused: false
  }, 1000, 2000), 200);
});

test("wraps only the synthetic replacement asset when it is shorter", () => {
  assert.equal(core.safeReplacementTime(30, 100), 30);
  assert.equal(core.safeReplacementTime(125, 100), 25);
  assert.equal(core.safeReplacementTime(-10, 100), 0);
});

test("sanitizes user-controlled settings", () => {
  assert.deepEqual(core.sanitizeSettings({
    enabled: false,
    automaticReplacement: true,
    testTrackId: " 123 ",
    driftThresholdMs: 99999,
    showOverlay: false
  }), {
    enabled: false,
    automaticReplacement: true,
    testTrackId: "123",
    driftThresholdMs: 2000,
    showOverlay: false
  });
});

test("normalizes Yandex artwork URLs across template and rendered sizes", () => {
  assert.equal(
    core.normalizeArtworkKey("avatars.yandex.net/get-music-content/42108/33aed17a.a.192577-1/%%"),
    "avatars.yandex.net/get-music-content/42108/33aed17a.a.192577-1"
  );
  assert.equal(
    core.normalizeArtworkKey("https://avatars.yandex.net/get-music-content/42108/33aed17a.a.192577-1/100x100?webp=false"),
    "avatars.yandex.net/get-music-content/42108/33aed17a.a.192577-1"
  );
});

test("matches the current Yandex player metadata to its exact state Track ID", () => {
  const catalog = [
    {
      id: "1944599",
      title: "Папиросы",
      durationMs: 200820,
      coverUri: "avatars.yandex.net/get-music-content/42108/33aed17a.a.192577-1/%%",
      artists: [{ id: "401402", name: "Зануда" }],
      albums: [{ id: 192577, title: "Папиросы" }]
    },
    {
      id: "17887612",
      title: "Папиросы",
      durationMs: 238840,
      coverUri: "avatars.yandex.net/get-music-content/6021799/8be0f804.a.22517447-1/%%",
      artists: [{ name: "Чиж & Co" }]
    }
  ].map(core.trackCatalogEntryFromValue);

  const result = core.pickTrackFromCatalog(catalog, {
    title: "Папиросы",
    artist: "Зануда",
    durationMs: 201000,
    coverUri: "https://avatars.yandex.net/get-music-content/42108/33aed17a.a.192577-1/50x50"
  });

  assert.equal(result.selected.id, "1944599");
  assert.equal(result.selected.source, "state-track-catalog");
  assert.ok(result.selected.score >= 240);
  assert.equal(result.ambiguous, false);
});

test("fails closed when state contains indistinguishable duplicate Track IDs", () => {
  const catalog = ["111", "222"].map((id) => ({
    id,
    title: "Same recording",
    artists: ["Same artist"],
    album: "Same album",
    durationMs: 180000,
    coverUri: "https://example.test/cover/100x100"
  }));

  const result = core.pickTrackFromCatalog(catalog, {
    title: "Same recording",
    artist: "Same artist",
    album: "Same album",
    durationMs: 180000,
    coverUri: "https://example.test/cover/50x50"
  });

  assert.equal(result.selected, null);
  assert.equal(result.ambiguous, true);
});

test("does not trust title and duration without artist, artwork, or album identity", () => {
  const result = core.pickTrackFromCatalog([{
    id: "333",
    title: "Common title",
    artists: ["Different artist"],
    durationMs: 180000,
    coverUri: "https://example.test/different/100x100"
  }], {
    title: "Common title",
    artist: "Expected artist",
    durationMs: 180000,
    coverUri: "https://example.test/expected/100x100"
  });

  assert.equal(result.selected, null);
  assert.equal(result.ranked.length, 0);
});

test("rejects empty and known advertising media as the master player", () => {
  assert.equal(core.scoreMediaCandidate({
    isMedia: true,
    tag: "video",
    paused: true,
    connected: true,
    readyState: 0,
    networkState: 0,
    duration: null,
    currentTime: 0,
    hasSource: false
  }), Number.NEGATIVE_INFINITY);

  assert.equal(core.scoreMediaCandidate({
    isMedia: true,
    knownAd: true,
    tag: "video",
    paused: false,
    readyState: 4,
    duration: 30,
    hasSource: true
  }), Number.NEGATIVE_INFINITY);
});

test("recognizes the observed Yandex short video stream as advertising media", () => {
  assert.equal(core.isYandexAdMediaCandidate({
    tag: "video",
    source: "https://strm.yandex.ru/example",
    duration: 15.997,
    connected: true
  }), true);
  assert.equal(core.isYandexAdMediaCandidate({
    tag: "audio",
    source: "https://strm-rad-24.strm.yandex.net/example",
    duration: 238.051,
    connected: false
  }), false);
});

test("manual bypass applies only to the exact current Track ID", () => {
  assert.equal(core.isTrackBypassed("155194611", "155194611"), true);
  assert.equal(core.isTrackBypassed("155194611", "156177669"), false);
  assert.equal(core.isTrackBypassed("", "155194611"), false);
});

test("prefers a playing audio element over a paused usable candidate", () => {
  const pausedScore = core.scoreMediaCandidate({
    isMedia: true,
    tag: "audio",
    paused: true,
    connected: false,
    readyState: 4,
    networkState: 1,
    duration: 201,
    currentTime: 12,
    hasSource: true
  });
  const playingScore = core.scoreMediaCandidate({
    isMedia: true,
    tag: "audio",
    paused: false,
    connected: false,
    readyState: 4,
    networkState: 1,
    duration: 201,
    currentTime: 12,
    hasSource: true,
    recentEvent: true
  });

  assert.ok(Number.isFinite(pausedScore));
  assert.ok(playingScore > pausedScore);
});

test("playing audio outranks a recently active video candidate", () => {
  const audioScore = core.scoreMediaCandidate({
    isMedia: true,
    tag: "audio",
    paused: false,
    connected: false,
    readyState: 4,
    duration: 193,
    currentTime: 12,
    hasSource: true
  });
  const videoScore = core.scoreMediaCandidate({
    isMedia: true,
    tag: "video",
    paused: false,
    connected: true,
    readyState: 4,
    duration: 16,
    currentTime: 12,
    hasSource: true,
    recentEvent: true
  });

  assert.ok(audioScore > videoScore);
});

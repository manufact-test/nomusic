# Native Yandex source research — 2026-11-08

Status: isolated feasibility prototype; not a release. Accepted CELIKOM 0.4.73 remains unchanged.

## Scope and source of truth

Base: `archive/desktop-0.4.73-accepted-20261104`, commit `63d8cd891e1db82e0245122391fd4ab5cdd323be`.
Experiment: `experiment/desktop-native-source-20261108`.
Only `spikes/native-source/`, research documents/results and a dedicated test workflow are added.
No changes to extension production sources/manifest, Android, server, deployment or the accepted archive.

## What the four projects actually do

| Source inspected | Mechanism | Browser relevance | License |
| --- | --- | --- | --- |
| [Hazzz895/FckCensor](https://github.com/Hazzz895/FckCensor/tree/64ccdfc714d780bd1fc4497ff63427443c1b150a) | `src/sdk/bridge.ts`: PulseSync SDK `api.client.setTrackReplacements`, resource hooks, player snapshot / `onTrackChange`; generation fencing and serialized change propagation | That SDK is supplied by the modified client, not by the Yandex website or Chrome. Transfer the idea of registration and ownership, not the API call | MIT, Copyright 2026 Haz |
| [S4YN3X/FkCensor](https://github.com/S4YN3X/FkCensor/tree/c1b142c03868d0513d48fcb090c7b0564559545b) | `assets/inject.js`: Electron injects a renderer script; searches Webpack factories by endpoint strings, patches `getFileInfo` / batch methods, supplies `mp3` / `raw` / replacement URLs without encryption key | The renderer resource seam exists on the website too; Electron injection, filesystem and process integration do not transfer | MIT, Copyright 2026 S4YN3X |
| [mrvokintos/YandexMusicMod](https://github.com/mrvokintos/YandexMusicMod/tree/b383940260cd2ef61718f98542ca605e2d6a7fe5) | `src/mod/features/ym-liberty/ym-liberty.ts`: private dependency container → `GetFileInfoResource`, then `getLocalFileDownloadInfo` and `isTrackDownloaded`, local IndexedDB assets | Relies on a desktop/local-download route. Minified DI export names are particularly brittle; no evidence that the website has that local route | MIT, Copyright 2026 gagayhhad-tech |
| [aeviww/yandex-music-client](https://github.com/aeviww/yandex-music-client/tree/08d514a43a295b6fc31c970e7642da3357319a5e) | Own Vue/Tauri player (not Electron), direct source selection by exact ID, next-track prefetch, Rust Range proxy/cache | Useful design ideas; its own player and native proxy cannot be transplanted into a browser extension as-is | GPL-3.0; no code incorporated |

No competitor implementation is copied into the prototype. Field names are Yandex protocol compatibility requirements. MIT code reuse would require preserving its copyright/license notices. GPL implementation reuse needs a separate compatibility decision; public source does not imply unrestricted proprietary reuse. This is a source license review, not a determination of Yandex terms or audio redistribution rights.

## Current public website evidence

Anonymous homepage fetched successfully (HTTP 200). Frontend build: `v4.1726.0`.
The public JavaScript contains BOTH resource classes:

- Module 39968: `get-file-info`, `get-file-info/batch` → `downloadInfo` / `downloadInfos`.
- Module 72882: `resources/v2/file-info`, batch → `fileInfo` / `fileInfos`.
- Resource requests carry explicit `trackId` / `trackIds`. A batch is a set of requested/preloaded tracks, **not proof of the currently audible track**. Do not relabel CELIKOM UI/current ownership from every request.
- Player provider supports cached `mediaSourceData`, batched preloading, raw and encrypted transports.
- Its native source class is PRIVATE inside a factory, not a public SDK export.
- Its source getter appends `vsid`, `source_index` and `#t=position` to the URL.

Relevant assets:

| Public asset | SHA-256 |
| --- | --- |
| `34497-e56b7089abb5601b.js` | `b4bae3fc37e72e0a7439a5059f92595c4dbd748fdbbedcfa4ad814e28af6fc1a` |
| `81814-555ff279a2b975f5.js` | `87bfda81feef3272bfd6d27dc9b37c553cfd3c1040ce584d600bab91d1816e8e` |

URL prefix: `https://yastatic-net.ru/s3/music-frontend-static/music/v4.1726.0/_next/static/chunks/`.
`spikes/native-source/asset-manifest.json` pins 76 public chunk URLs and SHA-256 hashes from this observed build. CI downloads them into a transient fixture and verifies the hashes; it does not depend on a fresh homepage for every test. `CELIKOM_NATIVE_LIVE_ASSETS=1` optionally examines the current public homepage instead. Third-party bundles are not committed or distributed with CELIKOM.

Chrome supports `MAIN` content scripts at `document_start`; accepted CELIKOM already uses this. DNR is not a JSON response-body rewriting API. The experiment patches narrowly selected JavaScript resource methods rather than requiring Electron or modifying Chrome network response bodies.

Official references: [content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts), [DNR](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest), [CDP extension installation for isolated tests](https://chromedevtools.github.io/devtools-protocol/tot/Extensions/).

## Minimal prototype

`spikes/native-source/manifest.json` loads a separate research extension. It has no production account integration, no privileged broker, no remote executable code and no automatic install/update path. It must never replace the accepted manifest or be sent as a normal customer build.

1. Discover only resource factories with the endpoint/method signatures. Do not execute every Webpack module or patch minified DI export names.
2. Preserve successful native resource responses and substitute only an explicitly registered exact ID. Missing/failed/aborted/expired requests retain original behavior; do not turn original failures into synthetic successful responses.
3. Preserve batch order and untouched entries; do not append invented absent tracks.
4. Pass an already completely downloaded native MP3 Blob to the Yandex source descriptor (`codec=mp3`, `transport=raw`, no encryption key). No second playing decoder or sync clock, no incomplete MediaSource handoff.
5. Strip Yandex-added query parameters ONLY from the exact owned Blob URL at the native media `src` setter / media `setAttribute`; preserve the `#t=` fragment. Ordinary URLs are untouched. This additional prototype hook is necessary because the source class is private; it needs careful compatibility coverage before any integration.
6. Bound registry to two assets and at most five-minute admission lifetime. Disable/dispose prevents new assignments and restores only prototype methods still owned by this experiment.

The existing, unchanged 0.4.73 complete-file downloader supplies bytes in the fixture: real 206 responses, MIME/content-range/size/ETag validation, one sequential continuation, 30 MiB cap, signed-first-request cache gate and existing transient retry behavior. Fixture URLs/data are synthetic, not production signed credentials. No token is put into MAIN.

## Tests and limits

Dedicated workflow: `.github/workflows/desktop-native-source-research.yml`.
It installs official Chrome/Brave, loads this actual unpacked MV3 extension via CDP into fresh regular profiles, and runs synthetic audio against current downloaded Yandex resource/source classes. The private source class receives a TEST-ONLY export in the transient fixture; its class body remains unchanged. HTTP responses to resource API calls are controlled. This is more than a hand-written fake player, but is **not a logged-in end-to-end listening test**.

Cases: v1/v2, mixed prefetch batches, exact-ID/abort/original-error fences, actual native MP3 playback, pause, seek, six-minute track and late seek, rapid Next, explicit original reacquisition, expiry, HTTP 503 retry, access denial, invalid ranges and hook cleanup.

### Verified results

- Functional experiment commit: `374f48db24cdad0ea89b52506fbf3609c9eb86bc`.
- [CI run 42478508631](https://github.com/manufact-test/nomusic/actions/runs/42478508631), job `128725094171`: SUCCESS.
- Actual Chrome `156.0.8078.79`: **23 checks passed**.
- Actual Brave `157.1.99.55` (Chromium `157.0.8103.39`): **23 checks passed**.
- Accepted extension regressions: **360 passed, 0 failed**.
- Separate read-only probes on the actual anonymous Yandex website: HTTP 200, two real resource classes discovered in BOTH browsers, zero replacements and no registered assets. This establishes current browser access to the seam, not authenticated playback compatibility.
- Machine-readable results: [NATIVE-SOURCE-VERIFIED-20261108.json](NATIVE-SOURCE-VERIFIED-20261108.json). Full asset provenance and test outputs are also attached to the CI run.

Controlled preparation comparison (synthetic six-minute MP3; server delays every continuation by 1800 ms):

| Browser | Accepted .73 streaming decoder ready | Cold complete file + native decoder ready | Already prepared native file + decoder ready |
| --- | ---: | ---: | ---: |
| Chrome | 28 ms | 1844 ms | 2 ms |
| Brave | 12 ms | 1845 ms | 3 ms |

These are single controlled decoder-preparation measurements, **not** user-perceived account lookup/start latency, statistical percentiles, or a general speedup. The warm-file case excludes the preceding complete transfer and account/descriptor admission. It cannot justify bypassing their checks in a real integration. The cold result demonstrates why unconditional full-file substitution would regress startup.

Earlier harness runs failed on fixture encoding and an HTTP fixture that rejected native open-ended `bytes=0-` requests. Final fixture serves UTF-8 explicitly and accepts open-ended native media ranges. A temporary homepage network failure also motivated pinned, hash-checked asset downloads. These failures are preserved in CI history; do not describe them as product fixes. No skipped audio assertions in the final passing run.

Never infer absence of clicks, zero missing words, indefinite playback stability or live account compatibility solely from these tests. Play/Pause/Seek here exercise the native media element through an actual source descriptor, not authenticated Yandex UI buttons. Automatic restore after active decoder failure remains unimplemented.

## Comparison with accepted 0.4.73

| Aspect | Accepted 0.4.73 | Native-source experiment |
| --- | --- | --- |
| Clock/control | Original plus replacement; carefully guarded handoff and ongoing synchronization | One native playing media element; native play/pause/seek |
| Initial MP3 bytes | Ordinary streaming can start from first 64 KiB; approved mid-song joins use complete native file | Prototype requires complete file before substitution; cold start can be SLOWER without advance prefetch |
| ID timing | Catalog/DOM/media metadata confidence fences | Resource request ID is exact and may arrive earlier, including prefetch; not synonymous with current track |
| Caching | Existing limited validated replacement cache | Must also respect/invalidate Yandex's `mediaSourceData` cache |
| Authorization | Existing broker, entitlement and lifecycle fences | Not integrated; admission registry is for tests only |
| Stop / errors / approval | Owner-accepted restoration and complete-file live-approval path | Next resource request restores original when disabled; immediate automatic active-source restore and live approval are NOT implemented |
| Audio gain | CELIKOM's accepted gain chain | Per-track CELIKOM gain is not integrated into native Yandex graph |
| Compatibility | Accepted fallback survives private resource absence | Depends on private frontend resource/source shapes; feature detection and a safe per-track fallback are mandatory |

There is no measured end-to-end speed advantage yet. Two-clock drift is structurally removed in the native fixture; network availability, original get-file-info latency, decoder behavior and unknown-next-track cold starts do not disappear.

## Recommendation / next bounded step

Continue this as an optional native backend in a separate experiment, not a rewrite and not a replacement release. First integrate only already authenticated, duration-checked, completely downloaded, prefetched MP3s. Keep account tokens and privileged fetch authority in ISOLATED/background; expose only revocable in-memory bytes/handles. Never allow both CELIKOM's old engine and native backend to own the same track.

Before promotion: prove logged-in native engine use (not just classes), safe engine-cache invalidation, Stop/Original/access-loss behavior for an already-playing Blob, decoding-error recovery to original without loops, approval mid-song, exact source ownership across rapid Next/seek, per-track gain and account switching. Registry TTL alone cannot revoke bytes already assigned to a decoder. Need explicit lifecycle/engine restoration. Do not make a production promise from this spike.

Even if native backend is rejected later, the narrow early resource observer can help the existing architecture: pre-resolve exact requested IDs and bounded next-track assets behind existing entitlement/duration/version fences. Do not fetch an entire batch or make requested IDs authoritative for current playback. Serialized generation fencing already exists in CELIKOM; do not reintroduce a second competing state machine.

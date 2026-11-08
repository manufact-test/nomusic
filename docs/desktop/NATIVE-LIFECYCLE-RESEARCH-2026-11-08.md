# Native source: authority, engine reload and manual boundary

Date: 2026-11-08. Branch: `experiment/desktop-native-lifecycle-20261108`.
Base: verified prototype `32a433f78b6b858af2b1e0955b2701260b89ee37` on `experiment/desktop-native-source-20261108`.
Accepted 0.4.73 archive, production extension sources, server and Android remain untouched.

## Actual next implementation

`spikes/native-source/desktop-prefetch-adapter.js` connects the experimental coordinator to the EXISTING isolated engine `resolveAsset` callback and unchanged `ReplacementPlayer.fetchNativeAsset`. It creates no audio element. MP3 inspection uses the existing `mp3DurationMs` parser; publication contains only a bounded complete Blob, exact ID, duration, expiry and generation, never a Bearer or signed audio URL.

`prefetch-coordinator.js` serializes authority resets, aborts pending byte reads on Stop/access loss, limits pending work to one download and two ready entries, rejects non-MP3/nonzero gain/duration mismatches, and requires fresh broker admission before a cached prepared asset can be used. Revocation/version changes invalidate prepared entries. Late-publication cleanup is scoped to the OLD generation so it cannot clear a newly authorized session.

This adapter/coordinator is NOT connected to normal product startup or popup Start yet. Running a second playback owner alongside accepted 0.4.73 would be unsafe; exclusive ownership and native restoration must be demonstrated first. It is tested through the real broker code with controlled authority/API responses, not through a real account session.

## Why native restoration needs the Yandex engine

Original Yandex `downloadInfo` can use `transport=encraw` and an encryption key. Reassigning its URL to a plain HTMLAudioElement cannot restore that original safely. A successful raw-MP3 fixture restore did not prove encrypted restoration.

Current public frontend has a native core `reload(entity)` method. It requests `getMediaSource({entity, disableCache:true})`, retains position/status, handles the native encrypted source through its normal core, and selects play or paused setSrc accordingly. The public source is pinned in the existing fixture asset manifest. In tests, a private export exposes the UNCHANGED reload class just like the earlier private source class; downloaded third-party bundles are not committed.

`engine-port.js` discovers the native controller through bounded React provider ancestry under the player bar, not minified module numbers or arbitrary recursive enumeration of the page. `getPlayback()` in the inspected frontend only reads its playback map and throws if absent; it does not create a new playback.

Reload is bound to the exact controller, playback, queue pair, entity, native player/core and media element. The source read, final `corePlay` and `setSrc` are fenced. A delayed response or asynchronous before-reload hook cannot apply the old song after Next, new media ownership, user pause/seek, cancellation or authority loss. Requests coalesce per binding; there is no automatic retry loop. Cleanup restores only methods still owned by the operation.

The normal source-selection and encrypted decoder remain Yandex's. Tests verify exact reload implementation dispatch and the preserved key with controlled core callbacks. They do not establish encrypted audio decoding in the user's live player, its account-specific experiments, or reliable access to that player from every current frontend profile.

## Validation

- Local lifecycle suite: **23 passed** against current downloaded Yandex reload code, real compiled CELIKOM API broker/downloader and MP3 inspector.
- Cases include native paused/playing reload, bypassing source cache, delayed before-reload hook, stale Next/player/intent/authority, no duplicate reload/retries, method ownership, login/entitlement/403 denial, exact duration, nonzero-gain refusal, fresh access/version admission, cancellation and generation-scoped late cleanup.
- [Workflow 42480354427](https://github.com/manufact-test/nomusic/actions/runs/42480354427): **SUCCESS**. Actual Chrome and Brave each passed the 23 MV3/native media fixture checks; all 23 new lifecycle/authority checks and all 360 accepted desktop regressions passed. Read-only probe builder succeeded too.
- One first Chrome fixture run observed a zero native clock at the old fixed 180 ms check. The harness now waits for ACTUAL clock advance within 3 seconds and still requires it; no playback assertion was removed. This is not evidence of an owner-visible product regression or a new performance fix.

## Required live check before activation

Anonymous CI page probes can find resource classes but do not expose an active authorized playback/controller binding. A current playing, signed-in user tab is needed to verify the React/provider/player shape. Do not compensate for missing evidence by enabling a native backend or copying desktop globals from a modified client.

`spikes/native-source/probe/` plus `build-probe.mjs` produces a tiny separate unpacked extension, **CELIKOM — проверка движка**. It does not replace or change 0.4.73 and does not require a Yandex refresh. The user opens it on the already-playing Yandex tab and copies the result.

The generated MAIN reader contains ONLY shared discovery/binding/inspection code. It exposes no reload method, installs no media/resource hooks, has no timers/listeners, makes no audio/network request and does not read cookies, tokens or account identifiers. The builder rejects playback mutation call patterns. The popup uses activeTab + scripting for the user-selected tab; it requests no blanket host access. Only timestamp and whitelisted engine shape/track/duration booleans are copied.

Manual steps: unzip to a separate folder → Brave `brave://extensions` → developer mode → Load unpacked → select folder. Leave the existing CELIKOM installed/enabled. With a song playing on music.yandex.ru, click the check extension and “Скопировать результат”; send that one result to the chat. Remove this check extension afterward if desired.

Delivered probe: `CELIKOM-Engine-Check.zip`, 3792 bytes, SHA-256 `a546090230006c68b28631c8ee29aa6f6c59ccd13fb5cf167cc783c998588d57`, persistent artifact `libfile_6fcfc601349881919dc743c12ac355e3`. The final reader also reports event/guard-method compatibility so one owner check can validate the required interfaces together. This is a separate read-only extension, not a new CELIKOM playback release. Do not rebuild/overwrite that artifact merely to regenerate ZIP timestamps.

Next after a confirmed binding: combine fresh admission, scoped native registration/revocation and this fenced engine reload under a SINGLE per-track owner. Then test Stop/Original/error/approval/access expiry in a full real native session. Do not enable alongside the old controller. Nonzero per-track gain and cache/late-source handling remain parity requirements before replacing the accepted backend.

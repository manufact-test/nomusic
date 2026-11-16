# CELIKOM Android A1 — CURRENT HANDOFF

**Updated:** 16 November 2026  
**Read this file first.** It is the single canonical current-state handoff. Do not append another history dump to it.

## Checkpoint

- Repository: `manufact-test/nomusic`
- Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- Last code checkpoint: `27ccbe8348d598fead0386e70ef68573b04270c4`
- Code backup: `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116` @ same SHA
- Last runtime-hook change: `a655712d210189f3bc611847235de3ed4d985c1a`; no later hook changes
- CI #229: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139), signed Yandex 2025.10.4 #120.1gpr, 16 splits / 6 DEX, read-only
- CI #230: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101), compact summary only. Log reduced from 2,517,490 to 68,361 bytes (~97.3%); full report is temporary and deleted
- Documentation hygiene backup before this update: `backup/android-a1-context-hygiene-final-20261116` @ `12fe3ea2a79378de344ad75b484cecba06edcdd1`

No APK was built, patched, installed, or released during this investigation.

## First task for the next chat — establish the actual Yandex target build

Do **not** immediately continue tracing obfuscated classes.

The CI specimen is Yandex Music **2025.10.4 #120.1gpr**. The owner's phone was previously reported as **2026.09.5 #167gpr**. The CI specimen, the app/package CELIKOM A1 is actually built around, and the Yandex app installed on the phone may be three different things. Do not assume they match.

1. Inspect the repository's current Android packaging/build configuration, pinned package metadata, workflows and existing verified hashes. Establish which exact Yandex build CELIKOM A1 is intended to target (embedded/loaded runtime target, not merely the test phone's installed app).
2. If repository evidence does not resolve that, ask the owner one short question: should the investigation target the pinned 2025.10.4 specimen or the phone's 2026 build?
3. Once the target is known, use only the exact original package for that build. Verify publisher signature, version, complete split set, package metadata and SHA-256 before analysis. Prefer owner/officially obtained package evidence; third-party mirror version pages are not proof of provenance.
4. Do not transfer obfuscated class/method findings between 2025 and 2026 builds.

The previous public version-page checks were inconsistent and are not authoritative. Do not spend another long research pass comparing mirror version lists.

## Research conclusions already established

Read [ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md](ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md) only if needed. Important findings:

- Official Media3 supports direct ExoPlayer playlist APIs that accept `MediaSource` objects. A valid handoff need not pass through a `MediaItem` getter/factory path.
- Keep the possible source boundary broad enough to include `MediaSource → MediaPeriod → DataSource → Extractor`, as well as Player APIs. This is a search boundary from the public Media3 contract, **not** proof of Yandex's internal implementation.
- Public YaMuLite / yt-dlp Yandex projects describe their own unofficial stream-resolution flows. They do not reveal the official Yandex Android call graph. Do not copy their auth, URLs, keys, or transport behavior.
- Yandex support documents VPN/network/battery/background-data causes for playback interruptions. That is useful for device-level dropout diagnosis, not proof of Track-to-decoder identity.

## Current static evidence

Stage A / NAV17: PASS by owner confirmation.  
Stage B: NOT CONNECTED / NO-GO. Keep `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.

CI #229 proves same-object TrackWrapper handoffs:

`LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>`

- `Lqj8` is an abstract interface with one direct implementer, `Lxj8`.
- `Lxj8.if` passes the same service and TrackWrapper into `Lvj8`; `Lvj8` stores/reads both and passes them to `Lxj8.for`.
- The bounded `Lxj8.for` trace passes the same TrackWrapper into `LfT2.<init>` at two callsites.
- `LfT2.<init>` stores that exact TrackWrapper on its instance.
- The exact `LfT2.invokeSuspend(Object):Object` body was not found. No same-object handoff from this route to a source, Player, or audio sink is proven.
- `LfT2` has 9 direct constructor callsites across 8 caller methods. Do not infer playback purpose from caller names or compatible types; only the current `Lxj8.for` route has the proven identity described above.

Detailed proof and next bounded trace: [ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md](ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md).

## Second task — only after target build is verified

Inspect the exact `LfT2;` class in the verified target's signed DEX:

1. Resolve class flags, superclass, interfaces and declared method descriptors.
2. Determine whether its executable continuation entry exists under another signature, is inherited, or whether this is not the expected coroutine object. Do not assume `invokeSuspend` exists.
3. Trace only reads of its stored TrackWrapper and immediate calls receiving that same object.
4. Follow only identity-proven calls into `MediaSource`, `MediaPeriod`, `DataSource`, `Extractor` or Player.
5. If no executable same-object source/player handoff exists, close this candidate. No global scan and no restart of the already proven `LIEa → Lqj8 → Lxj8.if → Lvj8 → Lxj8.for` chain.

## Closed routes — do not reopen

- `LiLb`: holder constructor/getter route has no direct Player handoff; closed in CI #216. [Closure](ANDROID-A1-LILB-PLAYER-HANDOFF-CLOSURE-20261116.md)
- `LXk6`: inner List.get → MediaItem → Player mutator exists, but outer caller/runtime dispatch and List element provenance are unresolved; closed. [Closure](ANDROID-A1-PLAYLIST-CALLBACK-ROUTE-CLOSURE-20261116.md)
- Current-item getter / Player mutator evidence: [MediaItem/Player handoff](ANDROID-A1-MEDIAITEM-PLAYER-PLAYLIST-HANDOFF-20261116.md)
- ByteBuffer → native sink is a separate path; no current-item identity reaches it. [Renderer census](ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md)

Reference docs are not startup reading. Open one only when the active task requires it.

## Hard constraints

- Android CELIKOM A1 only; no Windows or browser-extension work.
- No architecture changes, vendor changes, runtime-hook changes, APK changes or edits to original Yandex.
- No second Player, decoder or AudioTrack.
- Do not read/export Track/Album IDs, titles, URLs, DataSpec, tokens, account data, private field names/values or audio bytes.
- Do not touch NAV17, Test.50, frozen A1/LSPatch baseline, Windows, extension, backend/API/DB or production.
- Static inspection remains bounded, read-only and fail-closed.
- Work in one substantial block. No progress narration or repetitive reports.

## Documentation rule

Follow [ANDROID-DOCUMENTATION-HYGIENE.md](ANDROID-DOCUMENTATION-HYGIENE.md). The [archive index](archive/README.md) identifies superseded and oversized historical notes. Replace this handoff instead of appending; never load the archive or legacy handoffs for routine continuation.

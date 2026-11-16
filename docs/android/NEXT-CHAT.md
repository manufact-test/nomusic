# CURRENT HANDOFF — CELIKOM Android A1 — 16.11.2026

**Read this file first. It replaces the accumulated handoff below; historical details were preserved, not deleted.**

## 1. Current checkpoint

- Product: Android CELIKOM A1 only.
- Repository: `manufact-test/nomusic`.
- Only working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Last code checkpoint: `27ccbe8348d598fead0386e70ef68573b04270c4`.
- Exact code backup: `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116` @ `27ccbe8348d598fead0386e70ef68573b04270c4`.
- Documentation/context-hygiene backup: `backup/android-a1-context-hygiene-20261116` @ `feefeb14fc613a42b1c31009448a9777b0f12cc7`.
- CI #229: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139), pinned issuer-signed Yandex Music 2025 XAPK, 16 splits / 6 DEX, read-only.
- CI-log compaction workflow change: `723c71caeb0a9244e89eefd1f8c91e597e5bce00`; [CI #230 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101). The job log fell from 2,517,490 bytes in #229 to 68,361 bytes in #230 (about 97.3% smaller). The compact summary retains route verdicts/counts; the full JSON is temporary and deleted, with no artifact upload.
- Last runtime-hook change: `a655712d210189f3bc611847235de3ed4d985c1a`. No runtime hooks changed after it.
- No APK was built, patched, installed, or released during this static investigation.

**Build scope gate:** the static audit asset is Yandex Music 2025.10.4 #120.1gpr. The owner's phone was previously reported as 2026.09.5 #167gpr. APKPure's opened version page lists 2026.10.3 #170gpr as latest and also has #167 variants; other mirror snippets disagree, so these listings are not reliable proof of the installed build. Before another long trace, establish the exact intended runtime target. If it is 2025.10.4, continue LfT2 there; if it is a 2026 build, first obtain the exact original split package and verify publisher signature, split set, size, and SHA-256. Do not trust a mirror file or transfer obfuscated findings across versions without verification. Details: [external research](ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md).

## 2. Product gates

- Stage A / NAV17: PASS by owner confirmation.
- Stage B: NOT CONNECTED / NO-GO.
- Keep `active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`.
- No current Track-to-decoder identity chain has been established.

## 3. Latest proven chain — stop at LfT2

CI #229 proves same-object TrackWrapper handoffs:

`LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>`

- `Lqj8` is an abstract interface with one direct implementer, `Lxj8`.
- `Lxj8.if` passes the same service and TrackWrapper into `Lvj8`.
- `Lvj8` stores and reads those same references, then passes both into `Lxj8.for`.
- The bounded `Lxj8.for` trace is complete and passes the same TrackWrapper to `LfT2.<init>` at two callsites.
- `LfT2.<init>` stores that exact TrackWrapper on its own instance.
- The exact `LfT2.invokeSuspend(Object):Object` body was not found. No downstream source, MediaItem, Player, or audio-sink handoff is proven.
- Verdict: `SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY`.

Full current evidence and exact next task: [ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md](ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md).

## 4. One next task only

Inspect the exact `LfT2;` class in the same six signed DEX:

1. Resolve class flags, superclass, interfaces, and declared method descriptors.
2. Determine whether the continuation entry exists under another exact method/signature, is inherited, or whether this is not the expected coroutine object. Do not assume `invokeSuspend` exists.
3. Trace only the stored TrackWrapper field's exact read sites and immediate calls receiving that same object.
4. Follow only identity-proven calls into `MediaSource`, `MediaPeriod`, `DataSource`, `Extractor`, or Player.
5. If no executable same-object source/player handoff exists, close this candidate. Do not start a global scan.

Do not repeat `LIEa → Lqj8 → Lxj8.if → Lvj8 → Lxj8.for`; it is already proven.

## 5. Useful external research

The official Media3 contract allows a direct `MediaSource` playlist path; not every source handoff must pass through a `MediaItem` factory. `MediaSource` supplies Timeline/MediaPeriod; MediaPeriod loads data for renderers; DataSource requests bytes; Extractor parses access units. This is a search-boundary clue, not proof that Yandex uses a particular path.

Public third-party Yandex clients describe their own download-info → CDN URL resolution and Media3 playback, but do not reveal the official app's internal call graph. Yandex's support article lists VPN/network/battery/background-data causes for playback interruptions; it does not explain our static identity gap.

Details and source links: [ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md](ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md).

## 6. Closed routes — do not reopen

- `LiLb`: constructor/getter holder path has no direct Player handoff; CI #216 closure is complete. [Closure](ANDROID-A1-LILB-PLAYER-HANDOFF-CLOSURE-20261116.md).
- `LXk6`: inner List.get → MediaItem → Player mutator exists, but outer caller/runtime dispatch and List element provenance are unresolved; route closed. [Closure](ANDROID-A1-PLAYLIST-CALLBACK-ROUTE-CLOSURE-20261116.md).
- Current-item getter and Player mutator forwarding evidence is documented here: [MediaItem/Player handoff](ANDROID-A1-MEDIAITEM-PLAYER-PLAYLIST-HANDOFF-20261116.md).
- ByteBuffer → native sink path is separate; no current-item identity reaches it. [Renderer census](ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md).

These are reference documents only. Read one only if the exact next task needs it.

## 7. Hard constraints

- Android CELIKOM A1 only; no Windows or browser-extension work.
- Do not change architecture, vendor behavior, runtime hooks, APK, or original Yandex app.
- Do not add a second Player, decoder, or AudioTrack.
- Do not read/export Track/Album IDs, titles, URLs, DataSpec, tokens, account data, private field names/values, or audio bytes.
- Do not touch NAV17, Test.50, frozen A1/LSPatch baseline, Windows, extension, backend/API/DB, or production.
- Keep all static inspection bounded, read-only, and fail-closed.
- Work in one substantial block. No progress narration or repetitive reports.

## 8. Context and document hygiene

- Read only this file and the LfT2 handoff at startup. The external research note is optional.
- The old 71 KB accumulated `NEXT-CHAT.md` is preserved at [archive/NEXT-CHAT-ACCUMULATED-BEFORE-CLEANUP-20261116.md](archive/NEXT-CHAT-ACCUMULATED-BEFORE-CLEANUP-20261116.md). Do not load it for routine continuation.
- Other historical documents remain in place. Nothing useful was bulk-deleted.
- Do not fetch or paste full CI logs. Use workflow job step summaries and extract only the exact report fields needed. The workflow change in CI #230 redirects the full diagnostic JSON to a temporary runner file, prints a small safe summary, then deletes the file. It does not upload an artifact or persist the full report.
- The audit parser and its unit-test file are very large. Never fetch either file in full; use exact line ranges around the one function/test being changed. Never print the full diagnostic JSON into chat.
- The pre-cleanup start message is preserved at [archive/NEXT-CHAT-START-MESSAGE-BEFORE-CLEANUP-20261116.md](archive/NEXT-CHAT-START-MESSAGE-BEFORE-CLEANUP-20261116.md).

# CELIKOM Android A1 — FIRST REAL OWNER MUSIC SUCCESS, preserve NAV17; next native CELIKOM replacement source (14 Nov 2026)

## Absolute current truth

**OWNER-VERIFIED POSITIVE AFTER NAV17.** The owner installed the signed NAV17 APK and explicitly reported that CELIKOM opens the user's real Yandex Music account, shows owned albums, My Wave and plays original Yandex Music tracks on the actual phone. The original CELIKOM replacement versions are **not yet present/audible**. The user supplied **`CELIKOM-A1-Diagnostics-1794687390507.txt`** (1495 lines, 102234 bytes), preserved in Library at `/CELIKOM/CELIKOM-A1-NAV17-Owner-Real-Music-Success-Diagnostics-1794687390507.txt`.

The file begins with an old NAV16 retained segment; the authoritative NEW session starts `DIAGNOSTIC_BUILD NAV_V17_PASSPORT_PROVIDER_AUTHORITY_FIX` at file line 246. The essential original Yandex runtime evidence:
- line 419 `LOGIN_PIPELINE_SOURCE ENTRY AUTOLOGIN_UID_RESULT` — saved-account auto-login used, no simulated authentication.
- line 421 `LOGIN_TOKEN_OUTCOME ENTRY WRAPPED_STRING`, line 422 after token request no failure.
- line 476 `LOGIN_PIPELINE_RESULT AFTER_USERINFO_REQUEST NONTERMINAL_OR_OTHER`.
- line 513 `LOGIN_PIPELINE_RESULT AFTER_SYNC USERINFO_READY`.
- line 514 `LOGIN_FLOW_RESULT ENTRY USERINFO_READY`.
- line 517 `POSTLOGIN_PUBLISH ENTRY REAL_USERINFO_SUCCESS`.
- line 563 `POSTLOGIN_MAIN_ROUTE ENTRY MAIN_REQUESTED`.
- lines 583–585 `MAIN_ACTIVITY CREATED/STARTED/RESUMED` in the own clone, then lines 622–624 and elsewhere real `VENDOR_ACTIVITY CREATED/STARTED/RESUMED`.
- line 900 original Passport `ACCOUNT_ADD CLONE_OWN ADDED`, master-token reads PRESENT/decrypt NO_EXCEPTION repeatedly.
- There are multiple `METRICA_EXCEPTION MUSIC_APP EXC_OTHER` events in playing-app navigation. These are generic reporter classifications, **NOT** evidence of a fatal application crash. Do not chase them as a new blocker without a correlated user-visible failure.
- File is `LOG_TRIMMED KEEP_LAST_32KB`; retained chunks combine historical and current startup. No `CELIKOM_REPLACEMENT_APPLIED` or verified swapped-audio proof in this TXT. The actual original playback is OWNER-REPORTED rather than verifiable by the current log instrumentation.

**Stage A acceptance status:** The previously blocking *real owner Yandex Passport -> token -> userinfo -> native Music UI + audible original Music* boundary is **passed** on NAV17. This authorizes **starting Stage B development**, not final product release or a claim that CELIKOM replacements already work. Maintain the release gate: owner must personally test a real CELIKOM replacement, Start/Stop, My Wave/Next, album edition correctness, seek/pause/resume, fallback and original song parity.

## Frozen known-good baseline

Repo `manufact-test/nomusic`, only Android A1 working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Before recording this owner proof, exact HEAD **`d4c0887028b2bfbad7ed59f63ec88a4770f3595d`**, protected backup **`backup/android-a1-nav17-owner-real-userinfo-main-music-audible-20261114`** at that SHA. This backup preserves actual NAV17 known-good source with the previous Passport provider fix. The verified signed NAV17 APK **`/CELIKOM/CELIKOM-A1-NAV17-PassportProviderFix-20261114.apk`** remains available in Library, SHA256 `8d7c1570367360c12ba11f3972fa72477aca4dcc33f30dce78b381aee939b20d`, owner signer SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`. **Do not replace or mutate this archive/signing identity.** Avoid any unrelated AppMetrica, Passport, onboarding or original vendor APK changes. Never require uninstall, clear data, repeated Passport codes, competitor architecture, a parallel player, Windows/main edits or new active Android branch.

## Stage B: actual missing component, not another login investigation

Inspected live branch source:
- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/ExitCallsiteWitness.java`: on-host read-only `MediaDataSource.readAt` and exact `MediaExtractor.setDataSource(MediaDataSource)` observers, static source-identity targets and successful native boot/login witness. **No connected CELIKOM catalogue/resolve grants, approved media replacement source, or proven native source swap.** Do not claim a missing CELIKOM feature was fixed by login.
- `android/native-audio-contract/source-contract.mjs` + `source-contract.test.mjs`: separate pure source selection contract (B42) with identity, album + edition attestations, entitlement, signed normalized grant, HEAD/Range, generation/Next/MyWave, abort and fallback. **It is not wired into the native Yandex player.**
- `android/native-audio-contract/server-byte-range-compat.test.mjs` and existing PHP `server/src/Application/ResolveService.php`, `server/src/Http/AudioController.php`: source / server HTTP Range contract. Do not bypass rights/approval or fabricate server access.
- Historical Test.50 source is the owner-approved earlier Android companion audio behavior reference, NOT an instruction to change the A1 single native-player architecture. No second player or microphone audio mix.

**Ordered, large work blocks:**
1. Read exact 2025 read-only source-before-decoder inventory and test `android/native-yandex-hooklab/ci/a1_private_2025_audio_entrypoints.py`, existing on-host readAt/MediaExtractor observers and `docs/android/ANDROID-A1-2025-MEDIADATASOURCE-READAT-HANDOFF-20261113.md`. Tie actual *current Yandex track ID, album ID, edition ID and duration* to the one native source instance for that play (not just `readAt` counts, guessed track titles or content URI). The user's NAV17 fresh log does not contain audio-source events; hot-path logs are logcat-only and not copied into exported TXT. Add bounded, privacy-safe on-phone **summary counters / categories** outside hot path if needed for next owner verification. Preserve original audio in absence of attested identity.
2. Connect existing trusted CELIKOM server session/catalogue lookup and rights/entitlement validation to the source selector. Correct version, exact ID and album+edition gate, signed URL, expiry and MIME. Missing or unverifiable context must stay ORIGINAL, never silently swap a related edition.
3. Implement **source selection inside the same native player before decoder/read**, via the already audited source surface. Keep native Yandex UI, queue and original transport. No second decoder/MediaPlayer/AudioTrack, no bypass of Android AccountManager, no reflection across issuer credentials, no unverified stream URL. Abort superseded resolve on Next/My Wave; preserve seek/pause and seamless fallback.
4. Unit and native ARM13 CI: prove unchanged original publisher artifact, owner signature, original playback baseline, no crash/regression, exact track only source replacement with synthetic mock media grants on disposable CI (NO real owner account or production traffic); then export **one** signed in-place owner test APK after full green. Do NOT issue many successive speculative APKs or tell user to manually run Actions.
5. Owner stage: test actual CELIKOM replacement on one approved track and a negative original, Next/My Wave, pause/seek, Stop, unknown/expired URL fallback. Only then claim CELIKOM audio integration works.

**Immediate current request:** owner is celebrating the first real native Yandex Music success and reports original songs only. Preserve the win, continue Stage B. Do NOT confuse originals playing with our replacements playing. No need to send a new APK before one actual source integration is ready.


## Superseding technical checkpoint — 15 Nov 2026 (AudioTrack / ByteBuffer)

**Stage A = PASS on NAV17 owner verification. Stage B = IN PROGRESS.** NAV17 established the real owner flow; the owner reported audible original Yandex playback after login, with albums and My Wave visible. The diagnostic TXT does not independently verify the audio output. CELIKOM replacement tracks were not present/audible. This research does not change that owner result and does not claim replacement integration.

- Static audit code: `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Audit CI: [#43712507031](https://github.com/manufact-test/nomusic/actions/runs/43712507031) **SUCCESS**, 40/40 focused tests; verdict `SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY`.
- Exact CI-green code backup: `backup/android-a1-audio-buffer-identity-ci-green-20261115` @ `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`.
- Pre-fix rollback: `backup/android-a1-wide-invoke-map-pre-final-audit-fix-20261115` @ `8e121e50712c2f65f0b703e7beeb91688727b764`.
- Last runtime Java hook change remains `a655712d210189f3bc611847235de3ed4d985c1a`. This pass changed only the read-only static audit and its tests; no runtime hook, APK, account, phone or production component changed.

### Exact signed-DEX findings

- `LbJ2` implements `Lpk0` and declares typed `AudioTrack` and `ByteBuffer` fields. Its `native(ByteBuffer, long, int)` method is the concrete native audio-buffer entry candidate; the same owner also exposes the AudioTrack construction/control path (`play`, `pause`, `flush`, AudioTrack factory methods).
- Two direct class callsites pass the caller's exact ByteBuffer parameter to `LbJ2.native`: `LcLb.O(..., ByteBuffer, ...)` at ordinal 43 and `Lbd6.O(..., ByteBuffer, ...)` at ordinal 38. Both use the same caller parameter register (v6); the bounded register-write census found no write to it, and the invoke word map correctly accounts for the wide `long` argument occupying two register words. This is a static same-register provenance result, not runtime playback proof.
- `LEF2.j()` calls the exact `Lpk0.native(ByteBuffer, long, int)` interface reference and passes a ByteBuffer read from a typed field. `LbJ2` implements `Lpk0`, but the audit does not infer the runtime interface receiver/dispatch or prove that this is the same object as either direct class callsite.
- Branch handling now preserves a caller ByteBuffer parameter only when its original register is not written anywhere in the method (including the second word of wide writes). Other aliases are discarded at branch joins; the audit deliberately prefers false negatives over path-insensitive identity claims.
- Invoke mapping now expands `J`/`D` into two register words and reports both logical argument positions and register-word positions. Static and instance/interface invocation fixtures are separately tested.

### What remains unproven

`active_selected_item_proven=false` and `same_native_item_to_decoder_proven=false`. We have not connected this ByteBuffer to the current selected Track, its Album, edition/generation, or the exact same item observed at the native decoder/audio renderer. No CELIKOM source resolver is wired into this path; no replacement source is selected. The audit does not read ByteBuffer contents, Track/Album field values, names/IDs, URLs, DataSpec, account data, tokens or audio bytes.

### Next work

1. Trace the actual caller/owner path into `LcLb.O` and `Lbd6.O`; distinguish active playback from queue, prefetch and download. Keep virtual/interface dispatch and coroutine resume uncertainty explicit.
2. Join the proven audio-buffer sink path to the exact Track/Album identity only by bounded Java object identity. Do not infer it from method names, timing or matching types.
3. Establish a distinct edition/generation identity for that same selected item. Numeric fields and collection fields alone are not semantics.
4. Require the same selected identity at the decoder/audio renderer. Only then connect the existing authorized CELIKOM resolve/entitlement contract before decoder input, preserving the single native player and original fallback.
5. Do not ask the owner for another login, APK install or manual diagnostic until a concrete read-only measurement is identified.


# CELIKOM Android A1 — NAV24 exact type-1/state-2 renderer read diagnostic (18 Nov 2026)

## Owner task and accepted baseline

Owner's native 2025 Yandex Music clone plays and controls normally (Next/pause/seek); **no user-observed playback bugs**. CELIKOM alternative stream replacement is the only outstanding product capability, and Stage B remains **NOT_CONNECTED/NO-GO**. Do not speculate about failure from AppMetrica exception-constructor counters.

**Authoritative prior phone report:** [NAV23 real-phone holder array and renderer read proof](ANDROID-A1-NAV23-OWNER-REALPHONE-ENGINE-HOLDER-MATCH-20261118.md). NAV23: `ENGINE_HOLDER_STREAM_ARRAY_MATCH=MANY`, no mismatches/unavailable, `ENGINE_HOLDER_READ_RETURN_MINUS4=MANY`, -5 FEW, -3 MANY, no lost links. Exact `e.break` queue SLOT_B to `e.catch` field+reference CFG check is signed CI #44185115155 SUCCESS (2 strict scenarios, one unproven PC510). This does **not** yet establish active audio track, selected edition or PCM output.

## Signed exact 2025 static method proof

The exact publisher-signed 2025.10.4 XAPK (16 original splits, six DEX, no 2026 symbols) was checked with `android/native-yandex-hooklab/ci/renderer_active_audio_owner_exact.py` and isolated workflow `android-a1-nav24-active-audio-renderer-static-proof.yml`:

- CI #44187962678 **SUCCESS** (following initial fail-closed #44187446993 due to generic `getTrackType()` method name absent in obfuscated publisher build).
- In concrete `Landroidx/media3/exoplayer/b;`, original `default()I` is exactly `iget` of the base renderer `int` field → `return`; constructor `b.<init>(I)V` stores its unchanged direct incoming `int` parameter into the **same exact field ID**. This is a faithful per-renderer type code, not an invented `getTrackType()`.
- In the same base `b`, original `getState()I` is one `iget` of another int field → return. The engine `e.break` invokes `k.getState()I` at signed PCs 494, 833, 1448, 1582 and 1616, and `k.default()I` at PC 932.
- Exactly one `e` → `h` queue field identity was resolved in the inspected engine path and reset path. Queue SLOT_B `Lxh6` field ID is the same at `e.break` PCs 547 and 1051 and `e.class([ZJ)V` PC 2. Still **no runtime queue-field-to-current-output confirmation**.
- Static gate deliberately reports `runtime_named_method_gate_ready=false` for generic `getTrackType`; the code uses exact obfuscated `default` method only. No old 2026 signatures and no general method search.

## NAV24 source change, tightly scoped

On the **same original read-only `b.g(iA9,RF2,int)` witness** already present in NAV23, only when sampling the unchanged returned result, invoke exact 2025 `b.default()I` and `b.getState()I` *after* `chain.proceed()`. If either reflective accessor does not resolve, the older read hook still works and the new access is marked `NO_HOOK`; no skip, replacement, fabricated result or sound modification. Additional `NativeRendererStreamEvidence.onRendererTypeStateRead` verifies an independently proven **same holder/renderer/stream** engine link plus the current attached stream alias before counting anything.

New finite, privacy-safe categories:
- `AUDIO_NATIVE_RENDERER_HOOK_STATUS;origin=RENDERER_TYPE_STATE_ACCESS`
- `ENGINE_HOLDER_RENDERER_TYPE1` or `ENGINE_HOLDER_RENDERER_TYPE_OTHER`
- `ENGINE_HOLDER_TYPE1_STATE2` or `ENGINE_HOLDER_TYPE1_STATE_NOT2`
- `ENGINE_HOLDER_TYPE_STATE_UNAVAILABLE`
- `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4/MINUS5/MINUS3/OTHER`

`TYPE1` is the canonical Media3 audio track type and `STATE2` its started state convention, but **the numeric values and `b.g` return are not proof of the current audible media item or decoded PCM**. No raw objects, field names, user identifiers, titles, editions, audio, tokens or URLs exported. Earlier `QUEUE_SCOPED`, `UNSCOPED`, NAV22 secondary and NAV23 holder categories remain unchanged. `IDENTITY_STATUS` still `STRUCTURAL_ONLY`.

Six additional independent JVM fail-closed regression cases cover exact same-reference positive, type 2 not counted as audio, type1 state1 not counted as state2, wrong stream/detach, missing reflection and throw/failure. Existing checks remain. **JVM CI #44188648112 SUCCESS**.

## State, backups, release gate

- Only working branch `manufact-test/nomusic` / `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Protected pre-NAV24 baseline: `backup/android-a1-nav23-owner-accepted-pre-nav24-active-audio-20261118` @ `f1fe9e052660d62eaa9cacb447eca4e577b291cd`.
- Same preserved original signed publisher Yandex 2025.10.4 base SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`.
- NAV23 accepted Library APK `/CELIKOM/Android/Native/CELIKOM-A1-NAV23-Engine-Holder-Stream-ReadOnly-20261118.apk`, SHA-256 `376d3212a3802cf40e905eb434699d6999202086129eb9affc0c66bd4f8ea6a8`, left untouched.
- NAV24 original-publisher-first native Android13 ARM + persistent owner signer **CI #44188930346 SUCCESS**, exact signed source commit `230ad06e91b7b2fc8e77eedfb0686eff92caf228`. The original native version 2025.10.4 16 publisher-signed splits were verified in CI. Original embedded `assets/lspatch/origin.apk` was independently extracted from the signed NAV24 owner APK and SHA-256 checked against NAV23: `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`, unchanged.
- Owner signing certificate from CI: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`, **owner_apk_signer_verified=true**, matches accepted NAV17–NAV23 in-place update certificate. Native CI verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO` is NOT acoustic replacement proof.
- Exact signed APK **71,471,084 bytes**, SHA-256 `b1cd871c76b9e514b212d67eab19314e23b73fb09ca5e7f24e3fd18b26eb74ac`. The signed artifact was extracted, checked against CI SHA/bytes, uploaded to personal ChatGPT Library, independently listed and materialized back. **LIBRARY_NAV24_BYTES_IDENTICAL**, byte-for-byte comparison successful.
- Exact personal ChatGPT Library entries: `/CELIKOM/Android/Native/CELIKOM-A1-NAV24-Audio-Renderer-Type1-State2-ReadOnly-20261118.apk` and `/CELIKOM/Android/Native/CELIKOM-A1-NAV24-Инструкция.txt`. Do not provide a GitHub Actions download or sandbox link in owner-facing answers.
- Protected source backup `backup/android-a1-nav24-audio-type1-state2-owner-ci-green-20261118` @ `230ad06e91b7b2fc8e77eedfb0686eff92caf228`. Previous NAV23 backup and Library APK preserved untouched. **NAV24 NOT YET TESTED ON OWNER PHONE; CELIKOM REPLACEMENT STILL NOT_CONNECTED**.
- **Owner next:** install Library NAV24 APK **in place over NAV23**, do not uninstall/clear data. Listen to a few songs normally, export private TXT. Confirm original playback and classify `RENDERER_TYPE_STATE_ACCESS`, `ENGINE_HOLDER_RENDERER_TYPE1`, `ENGINE_HOLDER_TYPE1_STATE2`, `ENGINE_AUDIO_TYPE1_STATE2_RETURN_*`. Numeric observations are still not selected-track/edition/PCM proof. No speculative audio source switching.

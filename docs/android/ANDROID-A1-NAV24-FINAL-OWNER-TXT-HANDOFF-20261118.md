# CELIKOM Android A1 — NAV24 signed owner release; waiting for owner diagnostic TXT (18 Nov 2026)

## Authoritative handoff — no work should be restarted

**Product:** Android CELIKOM A1, not Windows, extension or Test.50. Repo `manufact-test/nomusic`, the **only working branch** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Preserve original architecture and backups. **User confirmed ordinary native Yandex Music operates normally** (playback, Next, seek, pause); **NO playback bugs to fix**. The only missing functionality is CELIKOM alternative-audio substitution. The user will send a new owner real-phone **NAV24 diagnostic TXT as the first follow-up in the NEXT chat**. Do not request another NAV23 file, do not start from zero, do not produce speculative APK before interpreting that TXT.

## Signed NAV24 that owner is testing

- Native Android13/ARM publisher-first and owner signed CI **#44188930346 SUCCESS**. JVM observer CI **#44188648112 SUCCESS**; exact original 2025.10.4 six-DEX audio/queue method source audit CI **#44187962678 SUCCESS**; strict `h.SLOT_B → e.catch` CFG audit **#44185115155 SUCCESS**.
- **Exact signed NAV24 code/workflow commit** `230ad06e91b7b2fc8e77eedfb0686eff92caf228`; follow-up commits only docs.
- Persisted owner signing certificate SHA-256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`; embedded original publisher signed Yandex `assets/lspatch/origin.apk` SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`, verified unchanged.
- **Signed owner NAV24 APK**: 71,471,084 bytes, SHA-256 `b1cd871c76b9e514b212d67eab19314e23b73fb09ca5e7f24e3fd18b26eb74ac`.
- Uploaded to **personal ChatGPT Library**, independently listed and downloaded; **LIBRARY_NAV24_BYTES_IDENTICAL**. Exact entries: `/CELIKOM/Android/Native/CELIKOM-A1-NAV24-Audio-Renderer-Type1-State2-ReadOnly-20261118.apk` and `/CELIKOM/Android/Native/CELIKOM-A1-NAV24-Инструкция.txt`. Owner's NAV23 Library APK preserved. Always provide verified Library entries for owner binaries; never substitute GitHub Actions artifact / sandbox link.
- Prior protected native exact code snapshot `backup/android-a1-nav24-audio-type1-state2-owner-ci-green-20261118` @ `230ad06e91b7b2fc8e77eedfb0686eff92caf228`.
- Prior verified source-and-docs final NAV24 reserve `backup/android-a1-nav24-owner-signed-library-verified-final-20261118` @ `27e3c3f0b323d61f9b89b9b21de4c56b90c66886`.
- Additional separate latest handoff reserve should be referenced in `NEXT-CHAT.md` upon creation. It changes only documentation.

## Proven before NAV24 — real phone NAV23

The last **actually analyzed phone file**, `CELIKOM-A1-Diagnostics-1794952135309.txt` (private owner TXT; do not commit raw), has all six native 2025 witness hooks REGISTERED:
- `ENGINE_HOLDER_STREAM_ARRAY_MATCH=MANY`, `ENGINE_HOLDER_STREAM_ARRAY_DIFFERENT=NONE`, `UNAVAILABLE=NONE`
- `ENGINE_HOLDER_READ_RETURN_MINUS4=MANY`, `MINUS5=FEW`, `MINUS3=MANY`
- `SECONDARY_CALLER_ENTER=MANY`, `SECONDARY_CALLER_STREAM_MATCH=MANY`, `READ_RETURN_LINK_LOST=NONE`
- older helper `QUEUE_SCOPE_ENTER=NONE` (a distinct path; **not a playback problem**)
- `IDENTITY_STATUS=STRUCTURAL_ONLY` and `CELIKOM_REPLACEMENT=NOT_CONNECTED` / Stage B NO-GO.
- Signed original source confirms `e.break` PC1051→1183 and `e.class` PC2→51 pass same exact queue `h.SLOT_B Lxh6` object reference into `e.catch` on audited paths. One `e.break` PC510 origin is **not** proved from SLOT_B.

## What NAV24 adds and how to interpret user's pending TXT

Only new passive observation on the original unchanged bounded `androidx.media3.exoplayer.b.g(iA9,RF2,int)` read-result hook: after original `chain.proceed()`, read exact obfuscated 2025 `b.default()I` (renderer track-type code inherited from `b.<init>(I)`) and `b.getState()I`. Original Yandex `getTrackType` method name is NOT present; avoid speculative reflection. Attach/holder/stream same-reference proofs and old bins stay intact.

**Parse live NAV24 (not rotated historical NAV23 marker) from the latest export**:
1. `DIAGNOSTIC_BUILD=NAV_V24_EXACT_AUDIO_TYPE1_STATE2_ENGINE_HOLDER_READONLY`; original native `RENDERER_TYPE_STATE_ACCESS=REGISTERED` (or NO_HOOK, then investigate reflection type without claiming playback bug).
2. `ENGINE_HOLDER_STREAM_ARRAY_MATCH` vs `DIFFERENT/UNAVAILABLE` and old `ENGINE_HOLDER_READ_RETURN_*` to ensure NAV23 structural link still holds.
3. `ENGINE_HOLDER_RENDERER_TYPE1` vs `ENGINE_HOLDER_RENDERER_TYPE_OTHER`.
4. `ENGINE_HOLDER_TYPE1_STATE2` vs `ENGINE_HOLDER_TYPE1_STATE_NOT2` and `ENGINE_HOLDER_TYPE_STATE_UNAVAILABLE`.
5. `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4/MINUS5/MINUS3/OTHER`, with `READ_RETURN_LINK_LOST`, prior `UNSCOPED` vs `QUEUE_SCOPED`.
6. `CELIKOM_REPLACEMENT` stays `NOT_CONNECTED`. **Even TYPE1 + STATE2 + matching stream != proven decoded audible sample, current selected track/album/edition or authorized replacement.** Continue narrowing the actual selected song identity and lifecycle after analyzing the new TXT; do not enable Stage B based only on aggregate counters.

**Do not diagnose AppMetrica `MUSIC_APP/MANY` exception-constructor counters as crashes** unless owner reports a failure and independent evidence ties it to our code. No unnecessary user questions about pause/seek. No changes to stock Yandex, A1 architecture, Test.50, Windows, extension, backend or original sound.

## Source-of-truth reading order

1. `docs/android/NEXT-CHAT.md` top CURRENT section (newest; archive below is history).
2. This handoff.
3. `docs/android/ANDROID-A1-NAV24-EXACT-AUDIO-RENDERER-STATE-20261118.md` (signed static evidence, JVM/native checks, release).
4. `docs/android/ANDROID-A1-NAV23-OWNER-REALPHONE-ENGINE-HOLDER-MATCH-20261118.md` (last phone proof).
5. `docs/android/ANDROID-A1-NAV22-OWNER-PHONE-RESULT-SECONDARY-CALLER-20261118.md` (secondary route history).

**No new code change or owner APK created by this handoff. The user's NAV24 TXT is not yet received.**

# CELIKOM Android A1 — NAV19 real-owner diagnostic release (17 November 2026)

## Current verified state
- Working branch ONLY: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. No architecture change, no new player, no changed server/extension/Windows/Test.50 or Yandex publisher APK. Original accepted NAV17 APK preserved.
- Latest handset evidence is **NAV18 owner TXT**, analyzed in `ANDROID-A1-NAV18-OWNER-TXT-READONLY-OBSERVATION-20261117.md`. Owner has **not yet tested NAV19**.
- NAV18 owner TXT: marker `NAV_V18_NATIVE_RENDERER_STREAM_READONLY`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `QUEUE_SCOPE_ENTER=NONE`, `QUEUED_HOLDER_ATTACHED=NONE`, `UNSCOPED_ATTACH=FEW`, `ATTACHED_STREAM_READ_MATCH=NONE`, `READ_NO_MATCHED_ATTACHMENT=FEW`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. No active-audio queue/renderer identity proof; read-only tests cannot play CELIKOM audio.
- Stage A NAV17 PASS (native Yandex UI, account, original playback, albums, My Wave confirmed on owner HONOR 50 Android13). Stage B CELIKOM alternative audio still **NO-GO**. Static signed-2025 chain to `LR29.throw` already proven, do not repeat.

## Exact diagnostic-only NAV19 changes
- Weak, independent `UNSCOPED_ATTACHED_STREAM_READ_MATCH` and `..._DIFFERENT` observations for native renderer attach/read, always separate from the stronger queued-holder/renderer same-instance proof.
- `AUDIO_NATIVE_RENDERER_HOOK_STATUS`: `QUEUE_SCOPE`, `STREAM_ATTACH`, `SAMPLE_READ`, `STREAM_DETACH` registration state survives trimmed event logs (REGISTERED/NO_HOOK/NOT_SEEN).
- Per-valid-unscoped-attach read-budget reset; exact-bounded max unchanged. No audio access, stream contents, URLs, track IDs, private account data, or second Player; no bypass of original `chain.proceed`.
- Exact marker: `NAV_V19_RENDERER_HOOK_STATUS_UNSCOPED_READONLY`. Guard remains original signed Yandex **2025.10.4 #120.1gpr** `versionCode=24025542`; do not reuse `HookSpec.java` 2026.10.3 obfuscated symbols.
- Scope includes only observer, tests, Russian owner README and one-shot export workflow. Old NAV18 owner APK and NAV17 accepted baseline unchanged.
- Protected before-fix backup `backup/android-a1-nav18-owner-diagnostics-before-observer-fix-20261117` @ `a8d6dbc9...`; after initial JVM-green changes `backup/android-a1-nav18-owner-txt-readonly-observer-jvm-green-20261117` @ `971aef7...`.

## CI and independently checked release
- New Java JVM observer model **#44129950827 SUCCESS**. Older ARM13 clone-alone **#44129887105 SUCCESS**, AppMetrica native ARM13 **#44129886883 SUCCESS**.
- First NAV19 owner export **#44132173158 FAILED CLOSED**: existing post-login source assertions still expected NAV18 marker; no owner artifact published. Updated *only two obsolete test assertions*. Do not report this as runtime failure.
- Corrected additional AppMetrica native ARM13 **#44132738954 SUCCESS**.
- **Final owner-signed NAV19 ARM13 export CI #44132767915 SUCCESS**, native publisher-first, no-suppression 75s, signed export on **in-place-only** gate. Private artifact #14351192314 was independently downloaded and extracted; not a GitHub Actions user download link.
- Extracted NAV19 APK **71,466,988 bytes**. Exact SHA-256 **`d55d7194c1c490481bfc4c184030e198f28827caa18ebf0aa2d116de6932e561`**. APK signing scheme v2 and v3 each contain exactly one X509 cert SHA256 **`048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`**, the same as NAV17/NAV18.
- Nested original `assets/lspatch/origin.apk` SHA256 **`1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`** = unchanged signed publisher Yandex 2025 original.
- Independently opened nested module `assets/lspatch/modules/pro.celikom.a1exitwitness.apk`: DEX contains exact NAV19 marker, `AUDIO_NATIVE_RENDERER_HOOK_STATUS`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH`. Direct cert/origin/module hashes independently verified, not just workflow's claimed success.
- Exact verified personal ChatGPT Library items:
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV19-Renderer-HookStatus-ReadOnly-20261117.apk`; library ID `libfile_2b302dba29688191a8e833e56301d955`.
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV19-Инструкция.txt`; library ID `libfile_f87cda3e1a2081919fdbb15b17a206ba`.
  - Original accepted NAV17 and NAV18 are still in the same personal Library folder. Both new files were re-listed in Library after upload; exact APK size matched.

## Owner trial — NEXT ACTION
1. Download the APK from personal ChatGPT Library (not GitHub Actions temporary URL), **install over existing NAV18/NAV17**. Never uninstall, wipe data, request new account login, or disable Play Protect. If an in-place update is rejected, stop, do not delete the working app.
2. Listen ordinary original Yandex songs 15–20 s, Next several times, pause/resume, seek, then My Wave 2–3 songs; report any crashes, forced app reloads, audio glitches or delays. The replacement is still off intentionally.
3. Tap «Сохранить диагностику» and send **new NAV19 TXT** from `Загрузки/CELIKOM A1`, and owner playback notes. Parse **latest** `DIAGNOSTIC_BUILD=NAV_V19_RENDERER_HOOK_STATUS_UNSCOPED_READONLY;ACTIVE`.
4. Check persisted `AUDIO_NATIVE_RENDERER_HOOK_STATUS/QUEUE_SCOPE` and `AUDIO_NATIVE_RENDERER_SUMMARY`: `QUEUED_HOLDER_ATTACHED`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH/DIFFERENT`, `ATTACHED_STREAM_READ_MATCH/DIFFERENT`, `READ_NO_MATCHED_ATTACHMENT`, `IDENTITY_STATUS`. Values NONE/ONE/FEW/MANY are bins only.
5. If `QUEUE_SCOPE=NO_HOOK`: exact 2025 method-reflection/registration mismatch diagnosis. If `REGISTERED` but scope `NONE`: active queue dispatch may be distinct. If unscoped attach/read matches: same renderer and stream have read entry, still NOT selected audible track/PCM or CELIKOM replacement proof. Make next diagnostic or replacement change only on grounded identity and rights/entitlement/fallback checks.
6. Keep accepted NAV17 as rollback, do not modify original Yandex, Test.50, Windows, extension, server or architecture. Do not repeat signed-2025 static renderer research.

**Do not manufacture NAV20 until the owner's NAV19 TXT provides an actual problem/gate.**

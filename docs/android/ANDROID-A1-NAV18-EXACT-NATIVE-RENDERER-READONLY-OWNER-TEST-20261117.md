# CELIKOM Android A1 — NAV18 native renderer read-only owner test (17 November 2026)

**FINAL: owner diagnostic NAV18 APK verified and delivered to ChatGPT Library.** Native signed ARM13 CI #44122921119 SUCCESS. The user approved one controlled test on HONOR 50. Stage B replacement remains NO-GO until actual owner playback and alternate-audio evidence.

## Immutable NAV17 baseline and scoped work

- Only working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Before-work backup: `backup/android-a1-pre-live-readonly-witness-20261117` @ `4a1caf93bff6e06fb99669693fc346321b89d509`.
- Independently downloaded previously **owner-accepted NAV17** GitHub artifact ZIP #14129665593 from signed workflow #43633688595 and locally verified its extracted 71,450,604 byte APK SHA-256 **`8d7c1570367360c12ba11f3972fa72477aca4dcc33f30dce78b381aee939b20d`**. Its embedded `assets/lspatch/origin.apk` SHA-256 is **`1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`** = signed Yandex Music **2025.10.4 #120.1gpr** (code 24025542).
- Parsed baseline APK v2 and v3 signing blocks independently, both have **one and only one X509 SHA-256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`**. Saved the original exact APK to personal Library `/CELIKOM/Android/Native/CELIKOM-A1-NAV17-OWNER-ACCEPTED-BACKUP-20261114.apk`; checked presence.
- No changes to publisher APK, NAV17 baseline, original official Yandex, Test.50, server, windows or browser. No audio replacement or second Player.

## Read-only native renderer witness implemented

- Pure-Java weak-ref, finite-count identity model `exit-callsite-witness-module/.../NativeRendererStreamEvidence.java`: `mQ8.catch(k,xh6,RFa,LL2)` stack scope → exact `b.package([Sr4,R29,J,J,Sl6$b)` native renderer attachment → `b.g(iA9,RF2,int)` stream sample-read **method entry** → `b.case()` detach. Up to 12 weak refs, 8 read observations per attachment, 256 read checks max per process, zero data/audio/field contents/IDs/URLs/tokens/track titles exported. The attached LR29 is compared using `==` to the stream returned by signed-exact `b.while()`. No extra Player, IO, buffer capture or read interception that skips the original.
- Scoped passive LibXposed hooks added in **existing NAV17 owner clone** module `ExitCallsiteWitness.java`; only main process `pro.celikom.yandex.nativeclonelab`, package version **24025542**, exact 2025 method parameter types, original `chain.proceed()` **once** and unchanged on each method. Registration and bounded summary categories go to the pre-existing explicit owner-save diagnostic TXT. `DIAGNOSTIC_BUILD` now `NAV_V18_NATIVE_RENDERER_STREAM_READONLY`.
- Hook registration marker categories: `AUDIO_NATIVE_RENDERER_HOOK` / `QUEUE_SCOPE`, `STREAM_ATTACH`, `SAMPLE_READ`, `STREAM_DETACH`. Owner export finite categories: `AUDIO_NATIVE_RENDERER_SUMMARY` with `QUEUED_HOLDER_ATTACHED`, `ATTACHED_STREAM_READ_MATCH`, `ATTACHED_STREAM_READ_DIFFERENT`, `READ_NO_MATCHED_ATTACHMENT`, `STREAM_REATTACH_TRANSITION`, etc. **These are code-path observations, not confirmed decoded buffers or audible replacement.**
- Separate 4-case Java17 reference/Next/stale/lifetime/privacy tests `tests/src/pro/celikom/a1exitwitness/NativeRendererStreamEvidenceTest.java`; isolated CI **#44120467198 SUCCESS**. The native build/launcher gates use the existing signed original ARM13 test rig; no owner Yandex account in CI.
- Owner instructions updated in `device-audio-trial/README-RU.txt`: in-place update only; play original tracks, Next, pause/seek, My Wave; save one TXT via in-app button. Do not uninstall, reset data, or disable Play Protect.
- One-shot test-and-private-export workflow `.github/workflows/android-a1-nav18-owner-renderer-diagnostic-export-once.yml` triggers only on **changes to its own workflow file**, reuses the full original 2025 publisher-first ARM13 run, verifies independent persistent owner signing, never permits fresh clone install, exports only on full native 75s acceptance. This is a **separate one-time workflow**, not a permanent automatic Android release.
- Previous one-shot CI **#44121652525** stopped correctly at `OWNER_INSTALL_MODE_NOT_AUTHORIZED` because repo variable for installed cert was empty (not a runtime/startup failure). Since NAV17 signer was independently parsed above, the one-shot workflow pins that verified installed cert for an **in-place-only** comparison. Re-run by workflow-file update commit **`ec559b537d52b5c9335452d7a24b7111e423f364`**, full native run **#44122921119 SUCCESS**; owner APK exported and independently verified.

## Release checks — completed

1. **One-shot workflow #44122921119 SUCCESS**, including all source guards, native original 75s baseline + own clone 75s, owner signing and exporter acceptance. No bypass or fresh install.
2. Retrieve its artifact ZIP through authenticated GitHub connector, extract only APK + instructions, verify outer APK v2/v3 owner certificate exactly equals baseline `048d76...`; original embedded vendor APK hash identical to baseline `1d0527...`, version/package identical, embedded module changed as expected. No official vendor content alteration.
3. Upload **new signed APK as own file** and instruction TXT into personal ChatGPT Library `/CELIKOM/Android/Native/`. Verify Library records before telling user to install. Never give expired GitHub Actions or sandbox links as the download link.
4. Only then ask owner to perform ONE NAV18 controlled trial with saved existing Yandex login, normal original music/Next/seek/My Wave and diagnostics TXT. Interpret matching stream reads as method entry until runtime return/status and decoder audio proven. **Stage B still NO-GO; alternative CELIKOM audio is not switched on.**

### Caution

The retained `HookSpec.java` in another module is for Yandex **2026.10.3** and must NOT supply method names here. All NAV18 targets are pinned to **signed 2025.10.4** proven in the earlier 17 Nov `ANDROID-A1-CONCRETE-RENDERER-ATTACHED-STREAM-20261117.md` and prior static chain. No broad renderer scan or ByteBuffer sweep.

## Verified final owner APK — 17 November 2026

- **[Final native CI #44122921119 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44122921119)**. Verified publisher original 16 splits, stable native Android 13 original-first and own clone; `verdict=METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, `owner_apk_signer_verified=true`, `owner_apk_install_mode=UPDATE_EXISTING`, `owner_phone_diagnostic_artifact.exported=true`.
- Downloaded actual private CI artifact #14347510393, extracted signed APK and instructions and verified independently, not relying only on GitHub job report.
- NAV18 APK: **71,466,988 bytes**, SHA256 **`647cbbc348e128ff10e79f50a6a04964cf9253a5e4cacd08f5949fe892793212`**. APK Signature Scheme v2 and v3 have exactly one cert SHA256 each, both **`048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`**, identical to owner-accepted NAV17.
- Embedded signed original `assets/lspatch/origin.apk` SHA256 **`1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`** = unchanged NAV17 original. Embedded observer module is *different* from NAV17 as intended; its `classes2.dex` contains actual `NAV_V18_NATIVE_RENDERER_STREAM_READONLY`, `installExact2025NativeRendererReadWitness`, `AUDIO_NATIVE_RENDERER_SUMMARY`.
- Verified present in **personal ChatGPT Library**:
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV18-NativeRenderer-ReadOnly-20261117.apk` (Library ID `libfile_cce835526c9c81918c87d27981bc55a7`);
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV18-Инструкция.txt` (Library ID `libfile_7a83f5e9aa7481919953a607dc538d69`);
  - accepted NAV17 rollback `/CELIKOM/Android/Native/CELIKOM-A1-NAV17-OWNER-ACCEPTED-BACKUP-20261114.apk` (Library ID `libfile_54ce63c3f10481919b730be1614219fd`).
- **User test**: install NAV18 over NAV17 without deleting data, start 15–20 seconds of one original track, Next 2–3, pause/resume/seek, My Wave 2–3, tap «Сохранить диагностику»; send TXT from `Загрузки/CELIKOM A1` and report interruptions/restarts.
- Matching attached-stream read event is **sample-read entry only**, not proof of successful decoding/current selected album+edition or audible CELIKOM replacement. Do not alter source on its basis.

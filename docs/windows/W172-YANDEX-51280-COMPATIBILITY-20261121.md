# W172 — Yandex Music 5.128.0 compatibility and CELIKOM 0.24.53 owner build

Date: 21 November 2026

## Repository and safety

- Repository: `manufact-test/nomusic`
- W172 branch: `experiment/windows-w172-yandex-51280-compat-20261121`
- Exact pre-W172 rollback branch: `backup/windows-w172-pre-yandex-51280-20261121` @ `6ce4cc21352912ab31578190007042397e083f64`
- Parent owner-review line: `experiment/windows-w170-mainline-20261121`; W170 PR #65 remains draft and separate.
- `main` was not changed.
- Target app and supervisor: **0.24.53.0**; native host/module source remains **0.24.32**.
- Installer is internal and unsigned. No production release, signing, stable feed publication, server deployment or Yandex binary redistribution.

## Verified official Yandex 5.128.0

The official Yandex Windows installer was downloaded from the Yandex stable S3 origin in disposable Windows CI. Its Authenticode publisher signature and the inner Yandex executable signature were valid and matched YANDEX LLC. The extracted inner executable version is `5.128.0.r22145392`.

- Installer SHA256: `2f931b7e6fc340e7a6a0d67888c2f963e2547f4c393703424956487af3af73e7`
- Inner `Яндекс Музыка.exe` SHA256: `0fdd7b7b25fed66701a61eda514767e15f735893782b331a05f830ad36f45f3d`
- `app.asar` SHA256: `b50abc625d3f426aa140b17861f8075eff3e17d71b2038e48ded1b6592cb8d0b`

The exact version and both file hashes were added as a new immutable entry to `OfficialYandexCatalog` and `official-yandex-builds-v2.json`. Previous verified 5.126.1 and 5.127.0 entries were retained unchanged.

## What changed

1. CELIKOM recognizes the exact signed Yandex 5.128.0 EXE/ASAR pair.
2. The existing vendor-update lifecycle remains in use: the new integration image is staged and checked before writes; the prior snapshot is archived under `previous-*`; the new original vendor files receive a separate snapshot.
3. A previously ACTIVE owner-approved integration can reconnect to this exact verified vendor update without a second consent dialog.
4. The W170 MP3 upload compatibility changes remain included in the 0.24.53 branch.
5. No W23 playback/audio source code was changed for this compatibility update. No Yandex installer or vendor binary is bundled in CELIKOM.

## Verification

- W172 official Yandex candidate and real vendor sandbox: [run 44892009619](https://github.com/manufact-test/nomusic/actions/runs/44892009619) — SUCCESS.
  - Valid Yandex installer and inner EXE signatures.
  - Native image construction against the actual 5.128.0 EXE/ASAR.
  - Real vendor pair install/restore sandbox passed; exact original vendor bytes restored.
  - W24 native image builder: **20 passed** in the general contract step; the actual vendor sandbox emitted `W81_2026_REAL_NATIVE_SANDBOX_PASS version=5.128.0.r22145392`.
  - W21 recovery contract: **41 passed**.
  - W15 native/Start contract: **467 passed**.
  - GUI build with warnings as errors passed.
- W20 installer staging: [run 44892155319](https://github.com/manufact-test/nomusic/actions/runs/44892155319) — **in progress at this documentation checkpoint**. Update this file with the final artifact ID, EXE/ZIP hashes and conclusion after it finishes.

CI proves official vendor provenance, image construction and reversible install/restore in a disposable Windows sandbox. It does **not** prove audible replacement on the owner's PC. Owner playback and real MP3 upload remain the final field checks.

## Owner test after package is ready

1. Install the single 0.24.53 installer over the existing CELIKOM installation; keep the same AppId and install path. Saved login/settings must remain.
2. Keep official Yandex Music 5.128.0 installed. Do not uninstall or downgrade Yandex.
3. Press CELIKOM Start. A previously active integration should reconnect without another consent dialog.
4. Test mapped replacement playback and the upload flow with a real MP3.
5. If anything fails, export the CELIKOM diagnostic and send it unchanged. Do not manually edit or replace Yandex files.

No claim of owner acceptance until these real-machine checks pass.

# CELIKOM Android A1 — first real own-signed native Yandex launch with LSPatch 2

**Date:** 2026-11-12. **Status:** a genuine native Android13 arm64/armv7 75s lifecycle PASS for a research build; **NOT a ready CELIKOM app**, no alternate audio, account or user acceptance yet. The owner explicitly authorized testing LSPatch signature-compatibility after retiring an older self-imposed level0-only research constraint.

## Exact source and safe setup

- Existing privately uploaded and unpublished publisher-signed Yandex Music `2025.10.4 #120.1gpr`, 16 split APKs, source XAPK SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, all cryptographically issuer-verified.
- Pinned independent LSPatch v1.2-487 jar SHA256 `d238fdc414d121b7fa454d8b4ccf420df3a8c97d563761861ff92bd9c5da2165`, **`-l 2`**. The upstream signature-compatibility feature was used as-is; no competitor module, certificate, music, bytes or credentials copied.
- Disposable GitHub native ARM Android13 guest, Android user0; no owner HONOR, user session, subscription, audio, DRM or installed Yandex altered. Original 16 publisher splits installed as positive control 75s; cleanly uninstalled in guest. Our output has independently generated own app-signing key for all 16 splits, always deleted after test. Original genuine bytes stay in unpublished draft and are not released as GitHub Actions artifacts.
- Code: `android/native-yandex-hooklab/ci/owner_2025_lspatch2_resigned_native_arm13.py`; workflow: `.github/workflows/android-a1-2025-uploaded-lspatch2-native-arm13.yml`. Explicitly gates cryptographic source, 16 splits, own signer, nested host DEX/native byte parity, LSPatch loader level 2, signed outer, exact package/version, real installed count and same exact native MAIN PID + resumed 25/25 for 75s.
- Existing tightly bounded `recover_stored_origin_crc.py` was reused when pinned upstream LSPatch wrote stale CRC in embedded stored origin; repair only ZIP container metadata, zipalign, re-sign with independent own key, not publisher key.

## Three concrete runtime checks

| CI | Input passed to LSPatch level2 | Verified result |
|---|---|---|
| [43190471508](https://github.com/manufact-test/nomusic/actions/runs/43190471508) | Independently own-signed original-name 2025 base | Packaging issue: nested `origin.apk` ZIP CRC, native execution not reached |
| [43191033070](https://github.com/manufact-test/nomusic/actions/runs/43191033070) | Same own-signed base, CRC repaired | 16/16 signed/installed. Publisher original native 75s PASS. Own LSPatch2 75s **FAIL**, Java `IllegalStateException` on MAIN with `SIGNATURE` marker |
| **[43191788591 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43191788591)** | **Cryptographically verified untouched publisher-signed base APK**, not our own-signed base | **Both original native and independently own-signed LSPatch2 build 75s PASS**, 16/16 splits installed, exact MAIN stable 25/25 observations. `lspatch2_input_is_verified_unmodified_publisher_base=true`, `independent_native_75s=true`, `issuer_native_75s=true`. |

**Actual causal discovery:** `sigBypassLevel=2` alone is NOT sufficient when the wrapper is built from an already independently signed original-name APK. Feeding the **genuine publisher-signed source base** to LSPatch while signing the outer with our independent own key makes a stable native MAIN possible in the same Android13 environment. This **does not** establish which internal signing compatibility mechanism is necessary, but it is a working reproducible construction.

## Next product blockers — do not misstate

- This lab A/B retained Android original package name `ru.yandex.music` for same guest conditions. It does **not coexist** with an installed original and involves **16 split APKs**, not the required **one independently installable `pro.celikom.*` APK**.
- No full Yandex screen-by-screen UI, account/login, MyWave, background playback, source substitution, actual Yandex MediaCodec/decoder, pause/seek, install on HONOR or Play Protect has been proved.
- The separate B42 client/audio HTTP contract remains prepared and tested but is not hooked into this host.
- Next technical work: derive a **clone-namespaced** own-signed outer keeping genuine publisher source/signature metadata; prove single-APK split assembly and side-by-side install with official Yandex, then own minimal scoped LSPatch module before audio `prepare`. Do not ship until original remains untouched and real owner playback is heard.
- The old frozen A1 branch `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743` and accepted Test.50 are unchanged. Stage A still **NO-GO**; Stage B locked until audible owner acceptance.

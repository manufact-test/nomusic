# CELIKOM Android A1 — verified owner-supplied publisher-signed 2025 GPR (11 Nov 2026)

## Original file
- Stored in the existing UNPUBLISHED GitHub Release draft tag a1-yandex-2025-gpr-private-test, release ID 442137464, asset ID 736739728. Never commit/publish/upload the binary as an Actions artifact.
- Asset: yandex-music-2025-10-4-120-1gpr.xapk; 45,961,661 bytes; SHA256 8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053.
- Exactly 16 intact APKs: one BASE 2025.10.4 #120.1gpr versionCode 24025542; 15 named configuration splits with Android-standard EMPTY versionName and identical package/versionCode.
- Each of the 16 APKs is cryptographically authenticated by apksigner v2/v3, with exactly the pinned original Yandex publisher signer SHA256 aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba. Signature validation is per split, not an assertion based on file names.
- [Strict original provenance CI 43090872523](https://github.com/manufact-test/nomusic/actions/runs/43090872523) SUCCESS; 16/16 synthetic tests PASS and real 16/16 APK signatures checked. Earlier failed runs exposed an overly restrictive parser of *named* config splits with empty versionName, corrected without weakening base manifest or signer checks.

## Native real ARM Android13 (not an emulator masquerading as ARM)
[Native guest control CI 43091414430](https://github.com/manufact-test/nomusic/actions/runs/43091414430): SUCCESS.
- Clean ARM64 Linux/Android13 API33 Redroid with both native arm64-v8a and armeabi-v7a.
- Unmodified publisher-signed 16-split original successfully installed (16 installed paths), original ru.yandex.music launcher accepted.
- Stable same exact MAIN process PID in all **25/25** observations across **75 seconds**; currently resumed original Activity **25/25**.
- Window focus first/last count = 0. **Do not claim window focus, UI pixels, login, playback, audio, DRM behavior, Play Protect or owner device acceptance**. All of those remain untested.
- Signed source and temporary guest data were deleted from the disposable runner; draft stays unpublished; owner's HONOR 50, original installed Yandex, main CELIKOM A1, Android Test.50, Windows W61, production unchanged.

## Interpretation
This is the first AUTHENTIC publisher-signed 2025 GPR native startup control, distinct from competitor-modified, re-signed 2025 RUR nested origin. It does not solve the independent CELIKOM native clone's signature-associated EXIT_SELF(0); it only establishes that authentic publisher-signed 2025 original on stock package identity can survive ARM13 native startup.

**Stage A NO-GO, Stage B locked.** Next useful independent test: compare this pristine 2025 signed-original baseline to an explicitly separate 2025 CELIKOM *lab-signed, distinct-package* no-bypass lifecycle experiment while preserving DEX/native payloads, using only disposable CI. Do not import competitor modules/sigBypassLevel, contact Yandex without permission, or present a test APK to the owner before actual UI/audio proof.

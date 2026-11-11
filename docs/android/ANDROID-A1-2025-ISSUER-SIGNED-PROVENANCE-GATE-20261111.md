# CELIKOM Android A1 — 2025.10.4 #120.1rur issuer-signed provenance gate

Date: 11 Nov 2026. **Product Stage A: NO-GO**. This is a candidate-verification gate, not a working APK or a real 2025 audio/runtime test.

## Prior, independently proven boundaries

- Main A1 frozen at experiment/android-native-a1-lspatch-clone-loader0-20261111 @ cc4cb0f93489168db21502f3ef195855ae9fb743.
- Real publisher-signed 2026.10.3 #170gpr Yandex MAIN is alive on native ARM13; our separately signed CELIKOM 2026 MAIN has a signature-associated IllegalStateException followed by EXIT_SELF(0). Refer to ANDROID-A1-20261111-SIGNATURE-TRUST-LIVE-NO-GO.md.
- Exact full ChromaSync stayed same MAIN PID/resumed Activity for 25/25 over 75 seconds (CI 43081123928). Its **competitor-modified/re-signed** embedded 2025 origin alone crashes with Java APPLICATION_STATE. This is a DIFFERENT observed failure and is not a publisher-signed 2025 control. Neither finding proves which outer wrapper factor is essential; do not copy sigBypassLevel 2 or foreign modules.

## Historical sample lookup and trust caveat

4PDA post #29718, 31 Oct 2025, lists Yandex Music 2025.10.4 #120.1rur:
- Version code: 24025542; expected package ru.yandex.music.
- Historical reported size: 59,498,960 bytes.
- Historical reported third-party MD5: 710b04ac0cc784f2576710343d4c37c1.
- Historic post: https://4pda.to/forum/index.php?showtopic=465231&st=29700 .

The uploader's historical MD5 and filename do **not** attest publisher origin. Neither a verifiable 2025 original APK nor a proven official historical download URL was obtained. The RuStore public application API previously tested in this repository provides CURRENT metadata, not proof of an old-version download. Official catalog: https://www.rustore.ru/catalog/app/ru.yandex.music ; official distributor list: https://www.yandex.ru/support/music/ru/supported-devices .

Previously verified **issuer reference** from official RuStore 2026.10.3 #170rur inventory, in tools/android-native-gate1/audit_rustore_host_once.py:
cert SHA256: aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba.
This certificate fingerprint is an independently anchored comparator, not standalone proof. Cryptographic Android APK Signature Scheme v2/v3 verification MUST succeed separately.

## What changed (isolated research branch only)

- Working branch: experiment/android-a1-2025-issuer-provenance-gate-20261111.
- Precise pre-change backup: backup/android-a1-pre-2025-issuer-control-20261111 @ 779780d6113a6c24f110d8f53ad2dbbc4e72d313.
- android/native-yandex-hooklab/ci/publisher_2025_provenance_gate.py: offline read-only Android SDK aapt/apksigner check, strict version/package/signature and certificate pin, calculate SHA256, compare historical MD5+size as **non-authoritative corroboration**. Wrong or missing signer, invalid signature, modified manifest, no valid v2/v3, missing file are rejected. No installation/execution/repackaging.
- android/native-yandex-hooklab/tests/test_publisher_2025_provenance_gate.py: 14 synthetic tests for acceptance and fail-closed rejection.
- android/native-yandex-hooklab/ci/official_2025_store_metadata_probe.py: current public RuStore HTTPS metadata only; no binary or login, no invented historical archive availability.
- .github/workflows/android-a1-2025-issuer-provenance.yml: public GitHub Actions, branch scoped, only synthetic tests + official metadata and a no-APK blocked verdict. CI success is NOT a true Android13 host run.
- No secrets, private binary, vendor code, competitor content or logs are stored/published. No modifications to main A1, Test.50, Windows, extension, backend/production, user HONOR, official Yandex or unpublished competitor draft.

## Verified new public CI result

- [GitHub Actions run #43083139558](https://github.com/manufact-test/nomusic/actions/runs/43083139558), code and workflow HEAD **19f396b22d4bffc78b43ded86de083d9b76de44f**: 14/14 synthetic issuer/version/signer/no-candidate regression tests **PASS**.
- Actual HTTPS official RuStore metadata response in that CI: **2026.10.3 #170rur** is current for package ru.yandex.music; verdict CURRENT_STORE_METADATA_NOT_TARGET_2025_RELEASE. This proves **only current metadata mismatches** target, not that archived official files cannot exist anywhere.
- Fail-closed no-APK control emitted PUBLISHER_SIGNED_2025_SAMPLE_NOT_YET_OBTAINED, native_2025_test_permitted=false; no APK uploaded/installed/launched; no ARM13 native 2025 runtime test, no CELIKOM boot/audio fix. **CI SUCCESS is provenance tooling validation, product NO-GO.**

## Next gate, only when legitimate bytes are available

1. Find independently attributable original publisher-signed 2025.10.4 #120.1rur through a lawful trustworthy source. Do not silently substitute any ChromaSync inner host or random MOD.
2. Keep bytes ephemeral and private. Run publisher_2025_provenance_gate.py with --apk pointing to a local candidate on disposable CI. Reject before installation unless issuer signing, exact version and integrity verify. Historic MD5 alone cannot authorize installation.
3. **Only after** a trustworthy original passes provenance and issuer checks, perform clean ARM13 native MAIN lifecycle A/B: unchanged publisher-signed 2025 vs unchanged publisher-signed 2026 in independent guests. This isolates release-year behavior, not changed package/signing trust of an independent clone.
4. For CELIKOM 2026 EXIT_SELF(0), if issuer trust/authorization is a hard condition, preserve as an explicit unresolved blocker. No security/DRM/Passport/Play Protect bypass, no publisher contact without owner approval.

**NO-GO remains:** no verified full CELIKOM native Yandex UI, authorized login, MyWave, decoder-source choice, audible replacement, pause/seek/Next, Play Protect or owner acceptance. Stage B stays locked.


## Follow-up public catalog check — NO issuer-signed 2025 obtained

- Scoped new metadata-only probe: android/native-yandex-hooklab/ci/aptoide_2025_documented_metadata_probe.py. It uses **documented public** Aptoide API endpoints only, two published host names ws75/ws2, NO API keys/login/private endpoint, no APK download, and does not treat store metadata as cryptographic signing evidence. Includes 8 metadata classifier tests.
- [CI #43084564576](https://github.com/manufact-test/nomusic/actions/runs/43084564576) source 696289bc5dceab1a18f9ae56374abf623ef423da: total **22/22** regression tests PASS (14 issuer + 8 discovery). Metadata requests for old code 24025542 to BOTH documented Aptoide public hosts returned HTTP 404. Package-only and public version-list requests return responses but **no verified matching target**. This does **not** prove no old APK is available elsewhere, and no private Aptoide authentication was attempted. Current publisher RuStore still reports 2026.10.3 #170rur.
- Secondary public catalog observation: APKMirror lists a historical 2025.10.4 #120.1gpr beta from October 25, 2025, while the exact desired control is #120.1rur. Neither an APKMirror listing nor a known version name establishes cert/signature authenticity. No binary was fetched from that catalog in this cycle.
- All successful CI jobs are **source discovery / fail-closed logic**, NOT an ARM13 2025 guest run, CELIKOM native boot success, or audio substitution. The existing EXIT_SELF(0) remains unresolved and must be handled as a publisher trust limitation rather than bypassed.

**Engineering stop condition on discovery loops:** no more speculative nonpublisher mirror/API scrapes for the same version unless a *new genuinely download-accessible, authorized and independently signature-verifiable source* is identified. Keep work pointed at new evidence, not endless metadata tests.

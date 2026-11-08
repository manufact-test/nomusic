# CELIKOM — final source import closure and production state, 2026-11-08

## Scope and authority

Source `Hazzz895/FckCensorData`, pinned commit `10187b7af56f311fe141a3c9b75483798bf0f589`; CELIKOM repository `manufact-test/nomusic`, isolated branch `feature/blur-batch1000-20261108`. No changes to main, Android, Windows, browser extension, or other developer branches. No autoapproval or rights confirmation.

## Actual production result (independent READ ONLY audit)

**Audit GitHub Actions: https://github.com/manufact-test/nomusic/actions/runs/42518290094 — SUCCESS**

- `yandex_tracks=1426`.
- `replacement_versions_total=1431` (includes two rejected and three disabled).
- `approved:1=1108` / active catalogue tracks `1108`.
- `pending:0=318`, all imported this chat and pending owner moderation.
- `private_audio_assets=1429`, `distinct_storage_keys=1429`.
- `private_audio_bytes=8994078129`, about 8.99 GB decimal.
- `open_yandex_requests=28`, `yandex_tombstones=0`, `writes=0`.

## This chat's import, tracked separately from physical assets

1. Previous batch (replacement IDs `918–1117`) audited as **200/200 already approved and active** at start: https://github.com/manufact-test/nomusic/actions/runs/42515169858.
2. New batch (replacement IDs `1118–1317`): **200 newly created pending track mappings**, 4x50, 1253877244 bytes of source MP3s, all per-batch audits PASSED. Import https://github.com/manufact-test/nomusic/actions/runs/42515690727; separate independent 200-file read-only audit https://github.com/manufact-test/nomusic/actions/runs/42516451573.
3. Final residual (replacement IDs `1318–1435`): **118 newly created pending track mappings** in groups 50+50+18, all 118 source MP3s unique, 761451096 bytes. Initial attempt imported 100 and stopped due fixed-50 manifest guard; fixed the isolated importer and safe re-run resumed 100 pending matches and imported remaining 18. Import https://github.com/manufact-test/nomusic/actions/runs/42517431248; separate independent 118-file read-only audit https://github.com/manufact-test/nomusic/actions/runs/42518290094.
4. Total newly added **318 pending track mappings**. Physical registered audio assets rose from **1112 to 1429**, meaning **317 new distinct private audio assets** (one source MP3 is shared by two distinct Track IDs). No automatic approvals. Source collection imports historically: 975 + 200 + 118 = **1293 source track mappings** imported over all sessions, not necessarily 1293 unique audio byte hashes.

## Confirmed content collision requiring OWNER review BEFORE mass approval

- Yandex Track ID `29508047`, source label `PHARAOH — RAW`.
- Yandex Track ID `29508038`, source label `PHARAOH — Флора`.
- The source Git blob matches byte-for-byte for both (`2c3c910dfc1d853d368dc240822d629d5a964b1d`). Both MP3 embedded ID3 tags explicitly say `title=Флора`, `artist=PHARAOH`, `album=PHLORA`. Therefore `RAW` is potentially incorrectly mapped and should NOT be bulk-approved without owner review.
- Read-only source inspection https://github.com/manufact-test/nomusic/actions/runs/42517443298. Neither mapping was autoapproved, deleted, or altered.
- Source content duplicates from other historical batches and one excluded final candidate are listed in `BLUR-CONTENT-DUPLICATES.csv`. Final candidate `106479320` had the same source blob as prior `105630453`; it was not uploaded twice.

## Complete accounting of source 1526 track files

The original audited manifest had 1442 candidate entries; the source tree contains 1526 source files. After this operation:

| Disjoint bucket | Source files |
|---|---:|
| Previously skipped/existing/conflict (includes earlier 175 source imports) | 835 |
| Last pre-handoff batch of 200 | 200 |
| New 200 batch in this chat | 200 |
| Final 118 batch in this chat | 118 |
| Cumulative technical rejects recorded in `BLUR-REJECTED-CUMULATIVE.csv` | 138 |
| One excluded duplicate blob `106479320` | 1 |
| Outside original source candidate manifest (separately inventoried) | 34 |
| **Total** | **1526** |

The complete manifest pool has **0 not-yet-checked candidates**; the 34 outside-manifest files were independently inventoried, not silently dropped.

## The 34 outside-manifest source files

Read-only byte-hash, MIME, ID3 analysis: https://github.com/manufact-test/nomusic/actions/runs/42517724989; `BLUR-SOURCE-GAPS-FOUND-TAGS.csv`.
- 28 source files had no trusted artist/title mapping in upstream README, and thus were never in initial candidate manifest.
- Among those 28, **27 are genuine MP3** and **1 is HTML**, specifically `107972749`.
- Of the 27 MP3s, **26 have embedded ID3 title + artist**, **1 has no useful tags**, `50400505`.
- The 26 ID3 labels **do not independently prove Yandex Track ID mapping**. Source collision RAW/Флора demonstrates why ID3 alone cannot be treated as a reliable matching authority. Anonymous Yandex metadata API returned HTTP 451 and public page provided no usable metadata: https://github.com/manufact-test/nomusic/actions/runs/42518018499. Do not autoimport these 27 without matching against authoritative Yandex ID metadata.
- Other 6 files fail current importer size limits: two zero-byte, two too small, two over 25 MB. See `BLUR-SOURCE-GAPS.csv`.
- Potentially recoverable but **unverified**: 26 ID3-labelled MP3 plus 1 MP3 without tags. Not guaranteed valid/importable and not counted as uploaded. The 138 CSV technical rejects are separate from the 34 exceptions.

## Operational recommendations

- Owner can manually moderate 318 new pending track mappings. Review `RAW` vs `Флора` BEFORE any bulk approval; never auto-confirm rights.
- Do not repeatedly scan the already exhausted 1442-source candidate manifest. Resume only if the owner provides reliable metadata verification for the 27 outside-manifest MP3s, or chooses to investigate rejected/oversized sources separately.
- Keep changes on this isolated branch; do not merge to main automatically.

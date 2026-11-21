# W173 — stable Start presentation and owner upload audit

Date: 21 November 2026

## Repository and baseline

- Repository: `manufact-test/nomusic`
- Work branch: `experiment/windows-w172-yandex-51280-compat-20261121`
- W173 package commit: `0fe5729f3e6f51e2679bf1cbec2dc6cedb81c27d`
- W172 official Yandex 5.128.0 baseline retained unchanged.
- App and Update Supervisor: **0.24.54.0**
- Embedded native host/module marker: **0.24.31** (unchanged from the accepted W170/mainline baseline used by this package).
- W170 upload changes remain included.
- Internal unsigned stage only. No production release, signing, stable-feed publication, server deployment, or PR merge.

## Owner-visible Start fix

The owner reported that after Yandex updated, CELIKOM displayed a separate red message asking the user to press Start again. The Start request could also be invalidated when the asynchronous host probe detected the verified vendor update.

W173 changes:

1. Keep the standard connection message throughout Start, entitlement validation and native integration preparation: `Подождите, идёт подключение к Яндекс Музыке.`
2. If the already-approved installation detects an exact verified Yandex vendor update while Start is in progress, disable the old bridge but preserve the current Start generation. The same Start flow continues into the existing safe install/reconnect path.
3. A verified update detected in the background no longer leaves a separate red vendor-update message in the normal popup. The next manual Start shows the ordinary connection message.
4. Unknown or modified Yandex files remain fail-closed and retain the existing safety warning. This does not weaken signature/hash checks or snapshot handling.
5. Removed intermediate “Проверяем пробный период или подписку…” presentation changes from the normal Start path to avoid unnecessary message/layout flicker.

No audio playback, volume, VPN, routing, native host, Android, browser extension, account, access, or server behavior was changed.

## Verification

- W172 exact official Yandex 5.128.0 signed EXE/ASAR candidate and reversible native install/restore sandbox: [run 44894403337](https://github.com/manufact-test/nomusic/actions/runs/44894403337) — **SUCCESS**.
- W15 native/Start contract: **469 passed**.
- W21 recovery contract: **41 passed**.
- W24 native image builder: **20 passed**.
- GUI compiled with warnings as errors.
- W20 internal installer staging: [run 44894407351](https://github.com/manufact-test/nomusic/actions/runs/44894407351) — **SUCCESS**.
- Disposable per-user install, same-AppId in-place upgrade, uninstall, ZIP metadata and anti-downgrade checks passed.

## Internal owner package

- Installer: `CELIKOM-W173-START-UX-02454-UNSIGNED.exe`
- ZIP: `CELIKOM-Windows-0.24.54.zip` (exactly one root installer; byte-identical to standalone EXE)
- Installer SHA256: `da5877bb01dca6048ce85cb07881f663c3a16cb81ec1f3b16074837bf9b60f33`
- ZIP SHA256: `d719af9688d74230440887707b9a6cd1c8e2b08af6026cd406c909fd4d3fb4b3`
- GitHub Actions artifact: [14703029534](https://github.com/manufact-test/nomusic/actions/runs/44894407351/artifacts/14703029534)
- Artifact expires **1 December 2026, 10:30 UTC**.
- Package is unsigned and internal only.

## Live read-only owner upload audit

The prior audit ended at 2026-11-21 09:36:30. The updated audit connected through the existing pinned SSH workflow and inspected the latest owner submissions and stored MP3 bytes. It did not write to the database or deploy server code.

Audit runs:
- [44894468621](https://github.com/manufact-test/nomusic/actions/runs/44894468621)
- [44894611523](https://github.com/manufact-test/nomusic/actions/runs/44894611523) — includes a read-only probe of the previously reported Track ID 48591846.

Five new owner submissions were found:

| Replacement | Track ID | Track | Status | Server duration vs Yandex | Difference |
|---:|---:|---|---|---:|---:|
| 1546 | 124387571 | Татем — А её улыбка | approved / active | 157727 / 157680 ms | 47 ms |
| 1547 | 129773110 | INSPACE, aikko — перелом | pending | 221414 / 221370 ms | 44 ms |
| 1548 | 125157964 | Поколено — Смысл жизни | pending | 128496 / 128280 ms | 216 ms |
| 1549 | 122765640 | T.JHAY, MAYOT — Наполовину пуст | pending | 128000 / 127930 ms | 70 ms |
| 1550 | 134308745 | tuborosho, Anonymous Ember — А я Курю и Плачу | pending | 123089 / 123140 ms | 51 ms |

All five:
- have valid stored-file SHA256 and exact size;
- are stored as `audio/mpeg`;
- have no MP3 metadata parse errors;
- have server-inspector duration matching the stored asset duration;
- are within the 1500 ms upload tolerance.

Four remain pending and inactive; one is approved and active. The original approved audio asset remains intact.

**Correction — the metadata classification above is not evidence about the original uploads.** That script inspected files already stored after the 0.4.78 server-side cleanup. The absence of tags in a canonical stored MP3 does not mean the incoming file had no metadata; the cleanup may already have removed it. The database keeps the canonical digest and does not retain the raw upload or per-upload removed-tag counters. Therefore it is impossible to identify retrospectively which of replacements 1546–1550 required cleanup. The earlier wording implying that these source files lacked the special patterns is withdrawn.

The correct follow-up audit covers every replacement created since the 0.4.78 activation, not just the five newest rows:
- [Private read-only upload receipt check 44895271863](https://github.com/manufact-test/nomusic/actions/runs/44895271863) — **13 total; 13 checked; 13/13 stored hash, size, duration, canonical-normalizer and full-decode checks passed; 9 approved, 4 pending; 0 failed checks**.
- Active release during this audit: `admin-rejected-cleanup-1b532497bf6e`. The audit successfully loaded and ran the cleanup normalizer and full decoder from that active release, confirming the feature survived the later server release.
- This proves the stored results are canonical and fully decodable. It does **not** prove which original uploads contained removable metadata or how many bytes were removed.

The actual 0.4.78 upload pipeline normalizes the authenticated raw MP3 in a private temporary file before measuring, decoding, hashing and storing it. The original upload bytes are not retained.

**Owner decision: do not add a cleanup journal, per-song removal counters, telemetry, or retention of original MP3 files.** The product requirement is that valid songs are cleaned, fully decoded and stored correctly, while damaged files are rejected. The existing server pipeline already does this. Recording which tags were removed adds no user-facing value and is not required for acceptance. Reopen this only if a real upload failure demonstrates a concrete diagnostic need; do not add it speculatively.

The previously reported “Каменные цветы” sample (Track ID `48591846`, replacement `30`) is present and approved/active. Its stored MP3 has two leading ID3v2.4 headers and one Info/Xing frame; the stored hash is valid and the live server inspector returns 277969 ms. This upload dates to 18 October, so it is a useful legacy sample but not a new W173 owner upload. The 0.24.51 baseline parser already handled consecutive leading ID3 tags; this sample does not prove the W170-only interleaved Info/Xing or extended UTF-8 ID3v1 cases.

## Owner acceptance

The owner installed the exact 0.24.54.0 W173 package, checked it on the target machine, and confirmed that it works and is accepted. This exact source/package is the production candidate to promote to `main`; no repeat installation, broad runtime test, or rebuild is required for this repository consolidation.

PR #65 is an older W170 draft pointing at the 0.24.52 branch, not this W173 0.24.54 candidate. Do not merge it as-is. The owner has requested W173 become canonical on `main`; follow the reviewed mainline-consolidation sequence in `docs/windows/NEXT-CHAT.md`.

## Mainline promotion completed

W173 **0.24.54.0** was promoted to the canonical Windows production line on GitHub `main`.

- PR: [#67](https://github.com/manufact-test/nomusic/pull/67) — merged successfully by squash.
- W173 code-promotion squash-merge commit: `aa713b99824f20abbe7c239bf06e356cf3f7f367`. Handoff documentation was committed afterward; resolve the live `main` ref before any future ref operation.
- Pre-merge backup: `backup/windows-main-pre-w173-consolidation-20261121` @ `affb7b225d2e7eb2835f53294e975a1e60bb758b`.
- PR general CI [44898409654](https://github.com/manufact-test/nomusic/actions/runs/44898409654) and Windows integration CI [44898409698](https://github.com/manufact-test/nomusic/actions/runs/44898409698): SUCCESS.
- Main general CI [44898706705](https://github.com/manufact-test/nomusic/actions/runs/44898706705), Windows integration CI [44898706600](https://github.com/manufact-test/nomusic/actions/runs/44898706600), and W20 safe installer stage [44898706605](https://github.com/manufact-test/nomusic/actions/runs/44898706605): SUCCESS.
- Main W20 internal artifact: [14705515606](https://github.com/manufact-test/nomusic/actions/runs/44898706605/artifacts/14705515606).

The owner explicitly asked to postpone repository cleanup until after migration to a separate owner-controlled server. No old Windows branches or PRs were deleted or closed. PR #65, #62 and #66 remain untouched; preserve all backup, Android, server and extension refs.

Current authoritative handoff: `docs/windows/NEXT-CHAT.md`. Completed promotion record: `docs/windows/W174-MAINLINE-CONSOLIDATION-20261121.md`.

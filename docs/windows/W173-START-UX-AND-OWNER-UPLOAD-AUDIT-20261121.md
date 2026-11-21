# W173 — stable Start presentation and owner upload audit

Date: 21 November 2026

## Repository and baseline

- Repository: `manufact-test/nomusic`
- Work branch: `experiment/windows-w172-yandex-51280-compat-20261121`
- W173 package commit: `0fe5729f3e6f51e2679bf1cbec2dc6cedb81c27d`
- W172 official Yandex 5.128.0 baseline retained unchanged.
- App and Update Supervisor: **0.24.54.0**
- Native host/module: **0.24.32**
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

Metadata observations in this new batch:
- Four files have no detected ID3/APE/Info-Xing tail metadata.
- “Наполовину пуст” has one ordinary Info/Xing frame.
- None has duplicate Info/Xing frames separated by an interleaved ID3 tag or the extended UTF-8 ID3v1 tail. Therefore this batch confirms ordinary upload acceptance and storage integrity, but does not field-prove those two W170-specific edge patterns.

The previously reported “Каменные цветы” sample (Track ID `48591846`, replacement `30`) is present and approved/active. Its stored MP3 has two leading ID3v2.4 headers and one Info/Xing frame; the stored hash is valid and the live server inspector returns 277969 ms. This upload dates to 18 October, so it is a useful legacy sample but not a new W173 owner upload. The 0.24.51 baseline parser already handled consecutive leading ID3 tags; this sample does not prove the W170-only interleaved Info/Xing or extended UTF-8 ID3v1 cases.

## Remaining owner acceptance

1. Install 0.24.54 over the existing CELIKOM installation; preserve login and settings.
2. Confirm Start shows only the standard connection message and does not ask for a second click during the verified Yandex 5.128.0 reconnect.
3. Continue real playback and upload checks.
4. To field-prove the W170-only parser additions, use a real MP3 with duplicate Info/Xing frames separated by ID3 or the bounded extended UTF-8 ID3v1 tail.

Keep W170 PR #65 in draft. Do not merge or publish without owner approval.

# CELIKOM Android · Test.75 HONOR replay, 2026-11-09 00:24–00:26+03:00

## Critical finding: proposed transport fix was not enabled
Owner test: `CELIKOM-combined-20261109-002624.txt`, `SVID_20261109_002458_1.mp4` (~79.4 s, Yandex RASKOL then «Дым», playback changes visible). Journal contains three runs; **only inspect latest `run_start` at 2026-11-09T00:24:45+03:00**, version `0.3.85-test.75`, ~1010 events, last elapsed ~99.2s. Previous retained runs include Test.73 and Test.74: do not mix.

**All 191 `yandex_witness_sample` entries in Test.75 have `enabled=false`, `available=false`, `yandexSessions=0`. Zero `yandex_witness_permission`, zero `yandex_witness_session_selected`; zero `source_framework_authority_verified`, zero `source_framework_seek_detected`, zero `source_framework_authority_lost`.** No system MediaSession observation was available, so `YandexFrameworkTransportPolicy.reconcile` could not authorize any platform override. Actual replacement engine continued to run the Test.73 external Media3 behavior. **Test.75 is NOT a phone-tested failed fix; it is a phone test in which the proposed feature never activated.** Root of permission/service inactivity not yet observed: likely user withdrew Notification Access after Test.74 per previous safety instruction, but **do not assert permission denied vs listener disconnected without checking Settings; the journal only proves `live == null`.**

Cross-check: prior Test.74 retained run had **213/213 witness samples `enabled=true`, `available=true`, `yandexSessions=1`**, and accurately saw missed pauses and 3.1–3.3 s seek lag. Difference between runs is channel availability, not proof of a new regression.

## Fresh Test.75 native symptoms
* RASKOL `42884423` alias as selected around t=38.5s; CELIKOM hot seeks only after slow Media3 updates: t=46.372s to ~75.153s, 50.496s to ~153.524s, 57.714s to ~158.057s. ACKs 49ms, 28ms, 42ms.
* «Дым» `39949113` ~t=66.1s; slow Media3 hot seeks at t=79.352s to 69.727s, 83.471s to 138.427s, 90.147s to 142.785s. ACKs 100ms, 47ms, 47ms. No correction sourced from new framework.
* Video sampled at 6s frames shows native same-track scrubs and pause UI; no visible settings/permission-grant step. Cannot infer exact permissions from video.
* Source package RASKOL and «Дым» are the same known failing songs. Audio file and library mappings are not implicated by this trial.

## Remediation without another speculative APK
1. **On the already installed Test.75**, in its UI tap `Проверить независимое управление Яндекса`, read disclosure, open Android system `Доступ к уведомлениям`, and explicitly enable `CELIKOM Test` *if the user chooses*. User must not disable Play Protect or any other protection for this. If setting shows enabled yet service remains `live==null`, inspect permission bind lifecycle and system's restricted settings without silent bypass. No new APK required for the first retry.
2. **Before any full song test**, start CELIKOM then export a 5–10s diagnostic TXT: demand `yandex_witness_sample {enabled:true,available:true,yandexSessions:1}` and `yandex_witness_session_selected`. If not, STOP; don't run bad-song playback. This is a missing preflight UI/contract in Test.75 and the developer's fault, not the owner's.
3. Only after positive preflight, repeat **one** failing track (RASKOL) on Test.75 with pause+seek. Inspect `source_framework_authority_verified`, `source_framework_seek_detected`, new engine logs, output behavior. If this channel is active and no fix, **then** debug policy/transport coupling and build a Test.76 as evidence demands.
4. For eventual product, the current opt-in notification-listener requirement may be unsuitable, and Play Protect install warning must be treated as a hard distribution blocker. Never ship this path as automatic or require protection disable.
5. Next build should surface explicit control-source state `Permission needed / Media session unavailable / Active` in user UI and gate instructions; don't silently claim repaired behavior while `enabled=false`.

**No server, files, stable app, original test source, audio library or live user data changed.** Test.75 signed remains experimental and not accepted.

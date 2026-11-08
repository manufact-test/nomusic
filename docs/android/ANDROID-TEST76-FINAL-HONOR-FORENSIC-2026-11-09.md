# Test.76 — final owner HONOR log / stop old Android track (2026-11-09)

**Source:** Owner-provided local `CELIKOM-combined-20261109-011905.txt`. Raw TXT contains three runs; **analysis only of LAST `run_start`** at file line 1636: `0.3.85-test.76`, local `2026-11-09T01:18:04+03:00`. Its last entry is t=61.294s. 471 JSON events, on HONOR NTH-NX9 / Android 13, Yandex Music `2026.10.3 #170gpr` code 24026531. **Do not commit raw owner logs, audio, or credentials.**

## Verified sequence

| Elapsed time | Observation | Meaning |
| --- | --- | --- |
| 0.086, 1.156, 3.224, 4.984, 9.110, 11.409s | Six successive `media3_connect_result` `connected=false`, `ExecutionException`, cause `SecurityException` | External Media3 client rejected; underlying cause not identified by log |
| 14.279s | Seventh direct Media3 attempt `connected=true` | **First connected ~14.3s after Test start** |
| 14.459–16.131s | «Папиросы» — Зануда, strict catalog ID `1944599`, backend `resolve found=true`, decoder prepared and `replacement_transition_complete` | Replacement works on one normal song |
| 20.837–21.488s | Native same-song seek on «Папиросы» observed and replacement subsequently rejoined | No general proof of fast seek on affected songs |
| 21.692–21.906s | Remote `SEEK_TO_OTHER_ITEM`, switched to RASKOL «Нас не понимают вообще», alias `548`, ID `42884423`, backend `resolve found=true` | RASKOL is identified and **its alternate exists** |
| 22.405s | `replacement_prepared`: RASKOL alternate duration 232333ms vs Yandex 232330ms | **Bad replacement file/duration is not demonstrated** |
| 21.815–61.294s | Media3 `STATE_BUFFERING=2`, position 0, `isPlaying=false`; retained connected controller; notifications switch to «Яндекс не обновляет трек» | Never heard alternate; source transport stuck; audio state of Yandex's *actual internal player* is not independently witnessed in this run |
| 24.931s, 54.927s | `source_controller_buffering_retained` for alias 548, no fresh player events | Old retention policy continues preserving a connected but stalled external controller |
| Entire last run | **91/91** `yandex_witness_sample`: `enabled=false, available=false, yandexSessions=0` | Opt-in framework channel NOT active. No `source_framework_track_divergence_verified`, `source_framework_fresh_probe`, `source_framework_fresh_controller_adopted` |

**Important distinction:** On prior **Test.75** run at 00:35, 101/101 platform witness samples were enabled and Yandex's framework session showed it continued playing «Дым» then RASKOL even when remote Media3 was stuck on older «Биг сити лайф». In this **Test.76** run, listener is absent, so **we cannot measure** whether the live Yandex framework player advanced or whether new Test.76 parallel recovery succeeds when enabled. Do not say the new probe was tested and failed; **it was not invoked**. Do not deduce that source app itself is broken. We do know normal user's objective still fails.

### Outcome
**Test.76 rejected as a practical fix / archived; not merged to stable.** No more blind minor Test.77 delay tweaks. Owner explicitly chose a **new single-player Android architecture investigation**, not further AudioEffect + second MediaPlayer synchronization.

Immutable protections remain: `backup/android-test50-exact-source-owner-accepted-20261108` (owner-accepted), stable Android original, server, PC/Windows and Chrome extension remain untouched. Owner's approval changes research scope to allow evaluation of a **compatible modified Yandex Android client with internal audio-source integration**, subject to safe install, privacy and Play Protect checks — this supersedes an older 2026-11-04 doc that forbade considering a patched Yandex client.

**Next:** [ANDROID-ONE-PLAYER-ARCHITECTURE-FEASIBILITY-2026-11-09.md](ANDROID-ONE-PLAYER-ARCHITECTURE-FEASIBILITY-2026-11-09.md). Do not ask the owner to retest Test.76 unless a specific new data point is required.

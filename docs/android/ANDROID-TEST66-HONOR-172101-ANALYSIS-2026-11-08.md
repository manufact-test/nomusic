# Test.66 HONOR 50 — owner combined 2026-11-08 17:21:01

## Evidence boundary
Private owner combined `CELIKOM-combined-20261108-172101.txt`: three distinct runs, **Test.64** (16:17:09+03, 1695 events), **Test.65** (16:46:54+03, 1244), and **Test.66** (17:19:19+03, 1114). Only the third is Test.66; do not merge timings. Source has no hardware audio PCM. The owner reports notification status finally works and original plays on absent tracks. APK Test.66 is still NOT accepted as stable.

## Test.66 facts
- 16 observed songs; 12 `replacement_transition_complete` (12/12 tracked successful replaced songs), 4 `NO_MATCH` in the full fresh APPROVED-only catalogue; no evidence about pending. Live catalogue refresh: HTTP 200, **138 approved rows** (not the 133 rows in prior runs).
- `notification_status_published` appeared 28 times. Four NO_MATCH songs: «Тебе не будет больно», «Капитал», «Линия жизни», «Были танцы» correctly published the long absence message and played original. This text is unnecessarily long for collapsed Android shade.
- Replacement connection measured strictly as `album_observation` to `replacement_transition_complete`: Test.66 median **691.5 ms** (12), Test.65 median **624 ms** (13), Test.64 median **699 ms** (18). The observed samples differ; do not claim general acceleration.
- Stratified by path: Test.66 prefetch reused 8, median **509 ms**; Test.65 prefetch reused 12, median **588 ms**. Test.66 cold-start 4, median **1708.5 ms**; Test.65 cold-start 2, median **1804.5 ms**. Different songs/network states: directional evidence, NOT a controlled speed test.
- Selected Test.66 timings: «Хлоп-Хлоп» 473 ms, «Ау» 474 ms, «Три слова» 497 ms, «только ты никогда не узнаешь» 521 ms; «Розовое вино» **3067 ms**, «Нас не понимают вообще» (Космонавты, RASKOL, ID 42884423) 1744 ms, «Легко ли быть молодым» 1673 ms.
- Root of «Розовое вино» outlier: promoted lookahead current waited about 400 ms and hit `current_handoff_timeout`; speculative download then logged failure; fallback private sparse was ready about 1.54 s after cold start, followed by alignment and crossfade. No evidence the UI catalogue change caused the delay. Avoid indiscriminately shortening the guarded wait or altering Test.50 audio.
- No confirmed crashes, reconnect outage, source-buffer event or failed replacement join in Test.66. The 12 `audio_command_anomaly` records were classified `expected_same_song_blend`, not abnormal failures. Not acoustic proof.
- RASKOL **track present**, but owner pause/seek failures were not actually exercised in this run. «Дым» 39949113 is **absent**; BUFFERING untested. Do not mark either repaired. All Yandex original album metadata restrictions remain subject to HTTP 451; approved-only NO_MATCH is not proof of pending state.

## Follow-up isolated change (NOT an APK)
Branch `feature/android-0385-test66-compact-notification-honor-20261108` based on Test.66. Only the notification text for fresh approved-catalogue NO_MATCH while playing is compacted to `Нет одобренной версии · оригинал` (32 chars). Full qualified wording stays in the Activity; pause, ambiguous/stale/451/no-ID handling, actions, sound and network untouched. `TestCatalogueNotification` extended to assert short, accurate shade text and the intact Activity caveat.

**Validation status:** source patch committed in isolated branch, no new version number, no new APK, no CI/real-device verification yet. Do not distribute or declare it fixed on HONOR. Before any next APK: full host tests, Android D8, same-signature signed side-by-side APK, verify SHA/certificate, upload APK/verification/receipt to ChatGPT Library `/CELIKOM/Android/Test`; preserve frozen stable Android 0.3.92 and Test.50 audio.

## Decision
Keep **tested Test.66 APK** as the immediate physical baseline, not a proven performance improvement and not a stable promotion. Continue investigating cold-start tail with additional matching samples; do NOT roll back just because one speculative prefetch failed.

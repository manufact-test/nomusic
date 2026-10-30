# HONOR 0.3.58 — second user audio regression, 30 Oct 2026 (21:48)

Source: user-provided `CELIKOM-combined-20261030-214846.txt`, kept outside public GitHub; includes 3 segments **0.3.54 (848 events), 0.3.58 (460 events), 0.3.58 (735 events)**. Always segment by `run_start` — previous comparisons conflated versions.

User: near-unlistenable gaps on manual seek and now track transitions; **normal and long intentional pause/resume tested OK**, preserve successful path.

Latest 0.3.58 segment has **8** `audio_command_anomaly` commanded-silence reports (43,45,57,48,45,45,49,461 ms), versus preceding 0.3.58 segment **7** (53,41,50,44,209,45,47 ms). Command inference only; no microphone observation. Thus failure persists even after Gate G; automated test green is not seamless playback.

Current engine investigation:
- `ReplacementEngine.bufferSource` explicitly distinguishes native source buffering from user pause but ultimately invokes `pauseSource(s,true)`, which zeros replacement gain, pauses decoder and revokes ramp transaction. Tiny 14–72ms seek-buffer events are frequent; test whether seek-in-flight buffering is duplicated ownership interruption.
- `seek` already calls `audioOwner.sourceGainDuringAlignment(effect)` to restore source during alignment. Earlier Gate D repaired original restoration and seek single-flight; avoid reverting it.
- `fade` is deliberate break-before-make to prevent double audio. Its source fade (100ms) happens while replacement is silent; then replacement gain ramps over 180–200ms. Log `replacement_source_fade_complete` states `replacementStillSilent:true` by design. This can be audible and must be assessed with deterministic transition simulations, not by shortening timers randomly.
- Existing `replacement_resume_aligned`, `replacement_resume_seamless` and Gate E pause retention are proven useful by user's long-pause report. Preserve them.
- User requests no endless loop of reimplementing old fixes: compare old Gates D/E/F/G and their tests before any change, cherry-pick only applicable mechanics. Preserve signed 0.3.58 and snapshot branch `backup/android-0358-honor-regression-before-fix-20261030`.
- UpdateCenter UI duplicated version and `Проверить обновления` summary: commit `2f4941c` removes repetition, caches verified latest result keyed to installed versionCode; no device claim.

Next: focused engine regression replay (seek + brief buffering; source boundary + release timing; seamless long pause). Do not publish a new APK or call it fixed until Java/D8, full Android CI, strict original-signer APK verification, then real HONOR listening. No desktop/backend work.

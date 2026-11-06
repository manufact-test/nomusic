# Test.50 — remember NEXT during current prepare (2026-11-06)

Baseline: Test.48 (not rejected Test.49). Input CELIKOM-combined-20261106-230322.txt, last run Test.49: 7 prefetch starts, 15 cold starts, 19 completed transitions; previous Test.48: 25 prefetch starts, 5 cold starts, 30 completed transitions. Distinct usage scenarios, not measured acoustic PCM.

Regression mechanism: on Test.49 after 60s, source_next_identity_resolution knows next track and source_next_readonly_boundary reports authorizedForPrefetch=true but prefetchStarted=false. prefetchLookahead discards a known next ID during current preparation; no replay arrives from source. New code queues candidate metadata (not audio) while foreground preparing and launches original prefetch only after exclusive current join; validates source key, next candidate, account, authentication; discards on boundary. No audio DSP, seek, timing, crossfade, source effect, permissions modified. Test.49 promoted lease guard is not carried forward.

New tests cover deferred next and stale next on source change. Keep stable 0.3.92, Test.48 and Test.33 unchanged; PC, Hostinger, backend untouched. CI APK still separate from stable OTA. Need signed CI and real HONOR listening for Next and shuffle before acceptance.

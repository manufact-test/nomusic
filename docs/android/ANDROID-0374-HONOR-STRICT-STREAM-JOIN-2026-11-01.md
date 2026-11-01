# Android 0.3.74 — bounded HONOR stream alignment experiment (2026-11-01)

## Rollback points

- Accepted 0.3.72 baseline: `backup/android-0372-ota-accepted-before-transport-diagnostics-20261031` at `5e18fd070dbf6115f643079b03637b0d180e9665`.
- Accepted OTA 0.3.73 + passive diagnostic: `backup/android-0373-honor-passive-transport-before-sync-guard-20261101` at `40bb482fdd60a35a4d65a0b700df3ec375aef3c5`.
- Do not move either backup branch. An OTA rollback after installing 0.3.74 needs old source rebuilt with a **higher** versionCode than 75, and the same signing certificate.

## Why this controlled experiment

In the owner's 0.3.73 HONOR journal `CELIKOM-combined-20261101-110706.txt`, the new instrumentation paired all 42 MediaPlayer seek requests/ACKs (40 ALIGNMENT, 2 WARM). Of 30 same-item position changes, 4 took over 500ms to exclusive replacement handover (max 959ms); 2 handovers retained 247-265ms source/decoder transport drift. Eight cold complementary entries showed 115-344ms drift, and each new-song boundary to join start took 493-955ms. These are **transport clocks, not PCM or hardware acoustic samples**.

The 0.3.73 stream handover accepts up to 350ms drift. This experiment tightens only the **final streaming decoder handover gate**, without changing the source restoration logic, seek ACK corrections, Media3 arbitration, gain law, UI or routes.

## Single-mode 0.3.74 change

- A streaming decoder must visibly advance and its projected source-position difference must be no greater than 100ms **before any audible replacement gain is granted**.
- At most 2 *silent* WARM decoder corrections may be requested, each with a bounded 70-250ms future-position lead based on the last observed seek callback latency. This compensates for the source continuing to run while Android seeks asynchronously; it does **not** claim sample-accurate synchronization.
- One handover has an overall 3000ms timeout. If the stream does not settle, retain the original Yandex output and skip replacement for this track. No same-track retry loop, no extra DSP detach/reattach, no added buttons/permissions.
- Preserve the 0.3.73 `replacement_seek_request`, `replacement_seek_ack` and cold join telemetry. New `replacement_join_guard_verified` / `replacement_join_guard_fallback` mark outcomes.
- Existing local-file behavior and ordinary pause/resume thresholds remain unchanged. This is one automatic audio mode, not a user-facing A/B choice.

## Mandatory verification

- New deterministic tests: predicted seek targets, successful bounded same-session correction, two-failure fallback and hanging warm callback deadline.
- Retain all 0.3.67 slow HTTP data-seek, single-flight callback, pause, Next/boundary, overlap ownership, updater, release signing and negative archive tests.
- Stage CI must build JDK17/Android API36/D8, produce offline kit, and show `publish-stable` SKIPPED.
- Promote to guarded production only on successful stage tests; sign with accepted certificate SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`, release 0.3.74 / versionCode 75.
- HONOR listening and a new owner journal decide whether this reduces audible repeats/dips. A successful host test or transport-drift log is **not proof** of acoustic improvement.

> **RELEASE POSTCRIPT (31.10.2026):** This staging report became the source of signed Android **0.3.70/code71** at production `06c2d9d01730007e453e15b5b20b067972bf1bf6`. SDK36/D8, signer/DEX/manifest checks and stable publish [41226869075](https://github.com/manufact-test/nomusic/actions/runs/41226869075) SUCCESS; actual HONOR sound/Recents still unaccepted. Full release receipt: [ANDROID-0370-SIGNED-HONOR-RELEASE-2026-10-31.md](ANDROID-0370-SIGNED-HONOR-RELEASE-2026-10-31.md). The staging status below records its earlier point in time.

---

# Android HONOR 0.3.69 → next candidate: detached resume, installer Recents, join clocks

**2026-10-31 · Android-only nonpublishing staging. No APK, no owner audio acceptance.**
Branch: `feature/android-0370-honor-join-pause-updater-staging` created from immutable production code `a30f949b10a72f62977e70cba30767b7c382a249`, not from the diverged old staging branch. Frozen backup `backup/android-0369-honor-listening-control-20261031` remains untouched. This file documents candidate code, not a signed release.

## Mechanisms isolated from the HONOR report

1. **Detached >30s pause, alias183:** 0.3.69 showed `pauseDurationMs=35704`, `replacement_resume_aligned.driftMs=132,seekSkipped=true`, followed by a new linear join. In `ReplacementEngine.update`, a retained position within `HANDOVER_DRIFT_MS=350` was accepted *before* strict pause correction; strict correction itself required `effect!=null`, but the 30s pause timer had released the effect. The detached branch could therefore bypass the existing `PAUSE_ALIGN_TOLERANCE_MS=85` despite significant transport error. Candidate rechecks only a genuinely detached long-pause resume before granting decoder output; keeps original audible during the bounded existing decoder seek. Short retained-effect pause, cached seek, Next and streaming priority retain their existing code.
2. **Installer stale Recents:** `UpdateInstallReceiver` previously ignored `STATUS_SUCCESS`. Candidate verifies its expected installed code equals PackageManager's actual installed code and then calls Android `AppTask.finishAndRemoveTask()` for this app's tasks. It does not close the task on a pending/canceled/failed install, and never tries to relaunch from the background. If OEM denies task removal it logs a warning and lets the owner launch manually. No stable.json, URLs, signing, backend, website or authentication changes.
3. **Cold join's intermittent dip/repeated syllable:** alias182/183/185 coarse join drift ~188–200ms, while user-confirmed perfect alias184 Next was ~134ms. None proves PCM phase. To preserve 0.3.69's best listening baseline, candidate **does not change** 160ms complementary linear gain law or join correction threshold. Adds passive `replacement_join_clock_summary`: initial/end/min/max *transport* drift sampled during the existing join, explicitly `sourcePcmMeasured=false`, `phaseVerified=false`. This can identify changing drift during the join, but cannot establish real source PCM correlation, output amplitude, cancellation or an acoustic fix.

## New regression fences

- `TestHonor066JoinLab.detachedLongPauseResyncBeforeJoin`: reproduces 35.7s detached 132ms drift, requires silent source-owned decoder seek before a new join, and preserves one-mode completion.
- `TestResumeClock`: 220ms detached offset now requires one silent correction; normal retained-effect short pauses still avoid gratuitous seeks, long pause at identical position still reattaches without a correction.
- `TestUpdateInstallPolicy`: confirmed success + exact installed code only. Receiver compiled by SDK36/D8 and uses public Android task API.
- Complete `tests/run_engine.py`, addon host tests, architecture gates, SDK36/D8 CI; staging branch is added to the validation workflow's push filter, whose publish job remains strictly production-only.

## Non-negotiable acceptance

A green CI is only code/DEX evidence, not a HONOR speaker/BT measurement. Before declaring sound improved, owner must listen on HONOR to (1) naturally joined songs with both successful and previously affected examples, (2) pause >35s and resume within a song, (3) manual Next + several finger seeks, (4) normal quick pause, Stop, Bluetooth/route loss, background Range. For updater, test system installer `Обновить` both success and cancel, then Recents and next manual launch. If no successful post-install receiver callback occurs on this OEM, task-card cleanup is **not** guaranteed and needs a device-specific alternative.

**Release gate:** only after full staging SDK36/D8 passes and review of actual changes; then one new original-certificate signed Android APK, verify version, DEX, signer and downloaded SHA, request physical HONOR owner review. `0.3.69/code70` remains the last signed production version until that gate. Desktop, backend, website, catalogue and account logic untouched.

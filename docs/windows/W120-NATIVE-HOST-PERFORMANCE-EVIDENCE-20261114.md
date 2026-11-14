# W120 — Native-host performance evidence without changing playback cadence — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W120 code backup: `backup/windows-main-pre-w120-native-host-performance-20261114` @ `e4da7bad1bc83b4eb2888de6c3f4d67a0732af78`.
- W120 implementation commit: `9a9193d7bd728a4ff1a2da2f8b5f11c42c4d8a7b`.
- Main CI [43596984190](https://github.com/manufact-test/nomusic/actions/runs/43596984190) and Windows integration CI [43596984195](https://github.com/manufact-test/nomusic/actions/runs/43596984195) — **SUCCESS**.

## Changes

1. Native host caches the last safe state sent to the Yandex renderer. Identical state is not executed into the renderer repeatedly; the cache is cleared on renderer reinjection.
2. A failed local state read invalidates the cached enabled/disabled observation, so the next successful read can report the transition truthfully.
3. Every 30 seconds the host samples only its own Electron main-process CPU usage. At 80% or higher it records the fixed event `NATIVE_ELECTRON_CPU_HIGH`. Raw CPU counters, PIDs, process names, account identifiers and audio metadata are never written.
4. `DiagnosticLog` recognizes the CPU event as an incident, includes `ElectronCpuHighObserved` in the text export and preserves the event in support snapshots and diagnostic history.

## Deliberately unchanged

- Existing 300ms native relay cadence remains unchanged.
- CDP playback observation and 403 recovery remain enabled.
- No audio-source, gain, VPN or original-file behavior was changed.
- This is instrumentation and removal of redundant renderer IPC, **not proof that #53 is fixed**.

W23 tests cover unchanged-state deduplication, fixed CPU-threshold recording and the unchanged 300ms cadence. W15 tests cover diagnostics allowlisting, export, imported incidents and durable archive. No installer was built. Owner Task Manager evidence is still required to identify whether the load comes from CELIKOM, Brave, Yandex renderer, GPU or another process.


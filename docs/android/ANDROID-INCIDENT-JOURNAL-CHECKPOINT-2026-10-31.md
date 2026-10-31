# CELIKOM Android — independent offline incident journal (prepared, not released) — 31.10.2026

## Why this exists

The owner observed that CELIKOM could temporarily fail to connect, while the ordinary diagnostics button was empty or unavailable. The existing full audio journal deliberately requires a short-lived **server-confirmed owner/admin diagnostic lease** (`NativeApi.fullDiagnostics()` and `DiagnosticAccess`). Losing server access can prevent that lease or export. Do **not** weaken the owner-only gate on full diagnostic traces.

The private combined report `CELIKOM-combined-20261031-025719.txt` (not in GitHub) includes three 0.3.61 runs. The run beginning 02:46:21 +03:00 had two `backend_result(resolve, timeout)` and one `replacement_stream_failure(IOException, 9604ms)` while Android reported Wi-Fi validated and VPN active. Later run 02:54:43 +03:00 connected again. This proves intermittent request failures but does **not** locate the failing hop or prove that Hostinger was unavailable.

## Implementation (Android-only, unreleased)

- `IncidentEvent.java`: strict event and field allowlist. It rejects arbitrary `player_state`, title/artist/track identity, URLs, emails, access tokens, exception messages, and unrelated payloads. No tracks/audio/credentials are logged.
- `IncidentLog.java`: append-only, private Android file with bounded **256 KiB current + 256 KiB previous** segments. It never resets on app startup, does not use the account/session/diagnostic grant, and supports an offline copy.
- `IncidentJournal.java`: initializes at app/service startup through `LogStore.init()`, records anonymous app start, and (Android API 30+) the OS-reported previous process exit reason once per exit. It captures stage, elapsed time, error class and active network/VPN capabilities when an API request fails. Exceptions in logging never affect playback.
- `LogStore.java`: forwards **only allowlisted** event categories to the incident journal whether or not the full privileged journal is recording.
- `NativeApi.java`: records non-sensitive failure information on request exceptions, including failures that occurred before an HTTP status was received.
- `RecorderActivity.java`: an independently available **«Сохранить журнал сбоев (офлайн)»** button, export via Android document picker, separate request code and snapshot from the admin-only full diagnostic export. No network, account or diagnostic grant required.
- `TestIncidentLog.java`: host regression for redaction, offline persistence across object/process recreation, bounded rotation, process-exit reason and restricted event schema; included in both native addon host suite and release build test list.

This addition does **not** change `ReplacementEngine`, audio ownership, preparation/seek/pause, desktop code, Yandex backend, hosting, permissions, signing, release-spec or auto-update routes. Existing Android 0.3.61/code62 remains the published stable APK. No version bump yet; it should be bundled with the next justified, tested Android release.

## Acceptance requirements

1. With the server unreachable or signed out, launch the app, attempt a CELIKOM network operation, then export the offline incident journal **without entering credentials**.
2. Close/kill/restart the app; earlier errors must still appear. On API30+, include the previous process exit reason when available. The inability of a terminated process to record a precise instant of death remains an OS limitation.
3. Unit test confirms the incident TXT cannot contain song/artist, user email, tokens, arbitrary server response, or raw exception messages.
4. Trigger repeated events: size remains bounded; exporter does not depend on network or full owner-only diagnostic grant.
5. Existing gated full diagnostics remain available only to verified administrators. Existing audio regressions and signed-APK CI must stay green. These are host-test guarantees, not an in-hand HONOR UI acceptance test.

## Audio issues left for the *next* release work (not implemented here)

The owner A/B-tested Yandex Music smooth transitions: playback tails behaved well while the AI/smooth-transition feature was OFF and short overlaps/transition problems returned when ON. The log has native early transition candidates with 1.4–6.8 seconds remaining but no Android-readable setting state. Do not claim raw `userSeek=true` proves manual touches or that log timestamps measure actual acoustic silence (`hardwareOutputMeasured=false`).

Agreed development order to confirm with owner: keep Yandex smooth transitions OFF while stabilizing first-track and next-track original→replacement cold handover, then protect baseline with a backup and separately research smooth-transition interoperability. Do not build a second independent prefetch/seek controller or alter live audio without a failing replay.

**Fallback question (not approved for implementation):** No documented public Yandex Music integration was found to programmatically change its smooth-transition preference. Ordinary Android apps cannot write arbitrary private settings of another app. A user-visible explanatory prompt/manual setting route is safer; UI automation through Accessibility requires explicit user opt-in, is fragile and out of scope. Research interoperability first.

**Separate deferred scope:** optional external server uptime probe every ~5 minutes. Do not build periodic telemetry polling from all phones by default. Android WorkManager periodic interval minimum is 15 minutes and execution can be deferred by battery policy; do not promise live five-minute phone monitoring.

## Existing safety checkpoint

- Working branch: `feature/android-unified-preparation-seek-gate`.
- Pre-incident implementation HEAD: `ffbe3b28d5c55fe8ece7ec8dc7d8bf300622c093`.
- Accepted-in-part audio baseline backup: `backup/android-0361-honor-positive-listening-20261031` -> `3860db5b8c5fafb3afe200d47e36d56b8ae9db15`.
- Previous measured playback QA: `docs/android/AUDIO-0361-HONOR-POSITIVE-QA-AND-TAIL-2026-10-31.md`.
- Owner has explicitly forbidden touching desktop CELIKOM.

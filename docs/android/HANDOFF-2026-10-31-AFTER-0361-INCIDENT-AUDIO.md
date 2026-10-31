# CELIKOM Android — FINAL HANDOFF, 31 October 2026
## Current authoritative status and exact scope

**ONLY ANDROID.** Repository: https://github.com/manufact-test/nomusic ; working branch: feature/android-unified-preparation-seek-gate. Never touch desktop extension, feature/api-range, Yandex ad protection, server, catalog, other services, payment, Hostinger application or website. This instruction outranks obsolete historical handoffs.

Published and partly accepted physical listening baseline: Android 0.3.61 / versionCode 62, package pro.celikom.nativeprobe. Existing live signed APK SHA256 2549495a5abe80462ade1fca975025dea4efdf122b93fbfe94744b7e1492383b. Original certificate SHA256 67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f. Stable release-spec remains 0.3.61/code62; **NO new APK has been published for the incident journal**. Published stable manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json . CI skips same-or-lower versionCode; do not bump it just for documentation.

Immutable baseline/rollback: backup/android-0361-honor-positive-listening-20261031 -> 3860db5b8c5fafb3afe200d47e36d56b8ae9db15. Do not force-push, rebase or overwrite this backup. Previous Android HEAD before journal work: ffbe3b28d5c55fe8ece7ec8dc7d8bf300622c093.

Unreleased Android incident implementation: bba3dc464bc823eba85eede3188e26d91a9f510f (CI https://github.com/manufact-test/nomusic/actions/runs/41149303399 both jobs SUCCESS; same-code publishing skipped). Follow-up admin-only UI and authorization fix: 5327c146ea0989207fac3bf3ca5d32de12bf5dda (CI https://github.com/manufact-test/nomusic/actions/runs/41150122610: native-android SUCCESS and publish-stable SUCCESS with same-version deployment SKIPPED). Current branch head can advance with this documentation commit: always fetch and verify before editing. Do not mistake any source-only commit for a deployed APK.

## 1. What actually happened on the HONOR phone, and what did NOT happen

- The user has been testing many Android APK versions. Repeated interventions to fix song boundaries introduced pause, manual seek and next-track regressions. Android 0.3.59 was explicitly REJECTED by a real HONOR test: known lags plus a newly broken pause/resume. The user is understandably frustrated by endless rebuilds and regression testing.
- Android 0.3.60 remained imperfect. Android **0.3.61 gave a markedly better real listening experience**: manual seeking and pause/resume generally behaved correctly; switching to the next song seemed smooth, with no obvious initial jump; one rare lag could be perception or real. Do NOT rewrite the audio engine casually or claim full acceptance.
- Remaining perceived problems: first moments of some tracks can briefly play Yandex's original, then switch to the approved CELIKOM replacement; the player timer might continue after replacement audio ends; song boundaries may feel slightly early/late; user heard a single possible overlap.
- Critical owner's real-world A/B: when **Yandex Music «Плавные переходы между треками» (AI/smooth-transition assistant) was OFF**, natural next-song boundaries largely sounded normal. Turning it ON reproduced early tails, overlap and some seeks/start hiccups. This strongly implicates Yandex crossfade but does NOT prove a fully isolated causal mechanism, and combined diagnostics do not record the Yandex preference value.
- AGREED ORDER: keep Yandex smooth transitions OFF during all near-term audio work. First stabilize cold original-to-CELIKOM handover and remaining issues with the setting OFF while preserving good pause/seek/Next. Only after physical user acceptance, create a new immutable backup, enable the feature and research robust interoperability. That compatibility is then the next major/top-priority issue. No automatic Yandex setting modifications now.
- Research: official https://www.yandex.ru/support/music/ru/listening-and-settings/app-settings says smooth transitions overlap end and beginning of consecutive songs by design. Android app sandbox prevents ordinary third-party apps from writing private Yandex settings. No documented public Yandex API for disabling the option was found. Last-resort user-facing explanation/manual guidance may be offered if needed. Accessibility click automation is fragile and must NOT be deployed without explicit separate consent; never silently switch other-app settings.

## 2. Why the previous diagnostics were misleading (LESSONS: do not repeat)

**A. Original full diagnostic architecture was genuinely unsuitable for incident forensics during outages.**
- LogStore logs the sensitive full combined trace only while NativeApi.fullDiagnostics() holds a 60-second server-confirmed owner/admin grant.
- NativeApi.refreshDiagnostics() must authenticate and request auth/me over the same network path that sometimes fails. Its failure means no grant, so the recorder may not start, export can be rejected and a report may be blank. The user's first exported diagnostic actually came back empty while CELIKOM could not connect.
- A blank report then is evidence of a diagnostic blind spot, NOT proof that no failure happened. The previous assistant had not accounted for the dependency cycle: network-dependent diagnosis cannot reliably diagnose a network outage.
- Full diagnostics must remain owner-only because they can contain detailed playback data. Do not bypass this protection to solve reliability.

**B. The earlier analysis also interpreted events too strongly.**
- A live HTTP 200 from the server AFTER the outage proves only that that endpoint responded at probe time, NOT that the entire request path was good earlier. The prior "server is fine, so no outage" conclusion was unjustified.
- The report CELIKOM-combined-20261031-025719.txt (PRIVATE, supplied by owner; do NOT commit raw logs) includes three separate 0.3.61 runs. One 02:46:21 (+03) run with VPN and validated Wi-Fi contains two backend_result(resolve timeout) and one replacement_stream_failure(IOException, after 9604ms). A later 02:54:43 run connected. This proves intermittent failures, NOT which hop broke (VPN, DNS, mobile transport, Hostinger, auth, intermediary).
- Distinguish network transport events from playback timing; do not conflate outages, version mismatches and the Yandex crossfade feature.
- Native Media3 source_discontinuity reasonCode=1 / userSeek=true is reported as SEEK; it does NOT prove the human dragged the seek bar. The native Yandex player may have triggered a programmatic seek, including around crossfade. Do not claim automatic natural source completion for such events.
- replacement_outgoing_candidate when source still reported 3.6–6.8s remaining did NOT remove the old decoder. In 0.3.61 it records retainedUntilConfirmedBoundary=true. Read the subsequent actual replacement_source_boundary event before claiming early cutoff.
- Telemetry explicitly marks hardwareOutputMeasured=false: 637–1073ms command-to-handover intervals and AudioOwnership commands do not measure acoustic silence, Bluetooth output, physical overlap or speaker waveform. They do not prove "no clicks" or "zero lag".
- Combined logs can contain multiple versions and runs; divide by run_start/version/time, separate incomplete runs and align chronology. One earlier report mixed 0.3.59, 0.3.60 and 0.3.61. Never mix statistics and attribute them to the wrong APK.
- Changes cannot be based on only userSeek flags, a speculative timer delta or success-only handover logs. Reproduce the exact ordering and **first add a failing regression**; then alter the smallest ownership/transition path and verify the old good cases.

## 3. The NEW independent offline incident journal, what it solves

New source under android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/:
- IncidentEvent.java: strict allowlist for event type/field/value, no raw track title, artist, token, email, URL, response or exception message.
- IncidentLog.java: app-private append-only bounded two segments (256KiB current + 256KiB previous). Retains events across app process restarts. Does not reset on app open.
- IncidentJournal.java: initialized with LogStore, records app launch and sanitized network failures with endpoint class, stage/elapsed time, OS network/VPN capabilities; on Android API30+ tries previous process exit reason when available.
- NativeApi.java and LogStore.java: independently forward allowlisted events even if server grant or privileged full LogStore.active is unavailable. Journal failures are fail-open for playback.
- RecorderActivity.java: "Сохранить журнал сбоев (офлайн)" saves an anonymous TXT through the system document picker; independent of network, refresh/login call and 60s full-diagnostic grant.
- TestIncidentLog.java: privacy, persistence, bounded rotation, previous-exit schema and allowlist host regression. Included in android/native-companion/tests/run_addon_host.py and android/native-companion/build_release.py.

**IMPORTANT OWNER CHANGE: ADMIN-ONLY BUTTON.** The final change 5327c146 restricts button visibility with View.GONE and export actions with NativeApi.diagnosticHint() based on signed-in account ID and locally cached prior online confirmation from auth/me. This is the SAME established administrator identity hint as the full diagnostic UI, not a new freely settable role. If the server later becomes unreachable, previously verified admin can still see/export the offline anonymous incident journal. If the admin signs out or switches account, the hint is cleared and export is denied. If a new admin device never received online verification, the button cannot appear while offline; first verify online when connectivity returns. Ordinary users do not get another button or export access. The ordinary full "Сохранить диагностику" remains separately gated by the short-lived online privilege lease; no relaxation. Also the hidden legacy button uses GONE instead of INVISIBLE so no blank gap remains for regular users.

The device-side journal can only save events while the app process runs. After a crash/kill, next startup may record OS previous-exit reason. It cannot guarantee capturing the exact final instruction at a fatal crash, failures before initialization, or isolated failures outside the Android app. No background collection from every customer's phone and no server upload was implemented. There is no promise of real-time five-minute monitoring: Android WorkManager has a periodic minimum of 15 minutes and battery deferral. Desktop has its own independent monitoring and is OUT OF SCOPE.

**Mandatory phone acceptance of this unreleased feature when combined with next APK:** after a legitimate admin has been verified online, disconnect Internet/server, cause a network attempt, confirm admin offline TXT export succeeds without new auth; restart app and confirm old events persist; logout/switch to ordinary user and confirm no button; test full owner-only detailed report unchanged; no sensitive fields leak. Host CI success is not a physical acceptance test. This anonymous incident journal is deliberately NOT equivalent to the full audio combined diagnostic.

## 4. Source locations, safe release mechanics and immutable constraints

- Main native source: android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/
- Playback engine: ReplacementEngine.java, AudioOwnership.java, ClockSupervisor.java, SourceEventArbiter.java, ProbeService.java; only study/alter after a failing focused regression. Existing unified preparation/seek gates must remain.
- UI/admin: RecorderActivity.java, NativeApi.java, DiagnosticAccess.java, LogStore.java.
- Diagnostics: docs/android/AUDIO-0361-HONOR-POSITIVE-QA-AND-TAIL-2026-10-31.md and docs/android/ANDROID-INCIDENT-JOURNAL-CHECKPOINT-2026-10-31.md.
- Native release/test: android/native-companion/release-spec.json, build_release.py, verify_release.py, tests/run_addon_host.py, addon/TestDiagnosticAccess.java, addon/TestIncidentLog.java, tests/TestHonor061EndTransitions.java.
- CI: GitHub Actions workflow Android 0.3.55 architecture and release contract verification. Current workflow name is historical; rely on actual runs and the exact commit SHA.
- Existing auto-update, notification and signed Hostinger APK publish are working from 0.3.61. Existing release is immutable. Next release requires strictly greater versionCode, unchanged package ID/certificate, full tests, original signing inputs, signed APK independent DEX/provenance verification, atomic APK+manifest deploy. DO NOT hand off an unsigned build or overwrite live signed 0.3.61 with source-only code.
- Backup and actual APK on the HONOR are independent. No HEAD changes in source should alter installed app until a new release is published and owner installs it.
- Private original signing material stays private; never print, copy to GitHub, telemetry or chat.
- Desktop: feature/api-range, extension/**, ad-protection/**, server/**, website/**, billing/** NEVER modify.

## 5. Exactly what the next chat should do — NOT yet implemented

1. Verify branch HEAD, current CI result for 5327c146 and this docs commit, read this full handoff, positive 0.3.61 QA, incident checkpoint and relevant earlier architecture/regression docs. Confirm published stable manifest is still 0.3.61/code62. Preserve 0.3.61 accepted-in-part rollback.
2. Do not publish the incident-only APK: user asked to **bundle it with actual remaining playback fixes** in one next release. Smooth transitions in Yandex OFF during development and first test.
3. Investigate initial original-to-CELIKOM replacement delay on some tracks and any remaining OFF-mode natural transition lag using exact run/time evidence. Separate backend resolve/transport (timeouts, VPN/cold network), allowed identity/provisioning and decoder prepare/seek/ownership. Query actual docs or source as needed; do not guess.
4. Build a deterministic **red regression** for the specific observed failure path, then fix minimally without a second controller. Preserve pause/resume, manual seeks, Next handover, source-end tails, network reconnect, account/track cancellation, Bluetooth route changes. If no failing evidence/replay, collect a focused new user diagnostic instead of speculative engine redesign.
5. Require full native host regressions, 15 virtual hours/300 transitions, source-to-DEX provenance, signed release checks, restore/fail-open behavior and actual HONOR acoustic test. Avoid promising zero physical discontinuities from command telemetry.
6. When implementation is complete and tested, bump Android versionCode/version once, sign/build/publish through existing automated pipeline, retain fixed permanent download URL, verify manifest/signer/APK and give owner one new APK to install and test. The new offline admin-only journal is bundled into that release. No repeated unverified micro-APKs.
7. AFTER owner accepts OFF-mode audio, create immutable backup, then separately research and fix interoperability with Yandex smooth transitions ON, restoring from baseline if regression. Prefer proper state coordination; only as explicit later fallback offer manual Yandex setting guidance. No secret toggling of third-party app settings.
8. Document exact differences, human test results vs inferred diagnostics, and update current handoff after real conclusions. **Do not overwrite old historical docs**; add clear latest pointer at the top of NEXT-CHAT.md so the next agent never treats 0.3.55/0.3.59 as current.

## 6. Handoff trust priorities and owner's preferences

- Owner requests professional self-contained work blocks, not unfinished previews, misleading "fixed" declarations, or constant APK churn. Never claim a phone symptom fixed by host unit tests only.
- The previous assistant wasted considerable time through repeated fixes/regressions and sometimes misread telemetry. This handoff is explicit about uncertainty and bad assumptions so the next chat does not repeat them.
- Owner asked that **documentation be finished first in this chat** and that the next chat make audio changes. We made ONLY the requested isolated admin visibility rule and already authorized offline incident logger; no audio changes in this handoff. The next agent should do the remaining audio debugging.
- Private logs the owner attached must remain private; use a summary not raw titles or personal data in GitHub.
- If anything here contradicts live verified repo/source state, inspect before acting, describe the discrepancy, and preserve the accepted stable release.

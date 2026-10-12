# Android 0.3.9: effective service state and terminal connection evidence

Owner0.3.8 report: MusicBrowserService is exported and manifest-enabled; Media3LibraryService is manifest-disabled; Media3SessionService is private. One browser attempt ended in not_connected and no media. This cannot prove intentional rejection because the original timeout overwrote prior failed callbacks. Original0.3.4 normal query returned no_public_service;0.3.8 queried MATCH_DISABLED_COMPONENTS. Manifest-enabled ServiceInfo alone does not account for component overrides.

0.3.9 queries both disabled-inclusive and normal resolution for each standard media action. Only currently normal-resolvable exported/unprotected candidates may be bound. Rows include manifest_enabled, normal_media_query_match and getComponentEnabledSetting when readable. It does not enable, modify or bind disabled/private Yandex components. A missing ordinary query result is reported as unavailable/disabled, not a proved permission denial. Current report cannot yet establish actual component overrides.

Connection evidence is bounded to12 events with class name, timestamp, event and exception class only. It preserves connect_exception, connection_failed_callback, connection_suspended_callback, connected and timeout_without_callback in browser_attempts independently of activity teardown. The seven-second timeout only marks still-connecting attempts, preserving terminal failures. Metadata and tokens are not included in error logs. No credentials, audio, permission request, identity substitution or transport command is added.

Emulator tests distinguish aggregate failed callbacks, timeouts, pending and admitted sessions and enforce runtime-disabled exclusion. Real service admission remains pending. Owner only needs to repeat the state-query button with CELIKOM visible and report after8seconds. Sound-path tests are already accepted and do not need repetition. A blocked public-browser path must not be represented as automatic synchronization support.


## Physical 0.3.9 result and 0.3.10 next probe

HONOR NTH-NX9 / Android 13 / Yandex 2026.09.5: MusicBrowserService is runtime disabled (setting 2), Media3LibraryService runtime enabled (setting 1), exported and unprotected. Legacy platform browser to the active Media3 endpoint returned connection_failed_callback in 74 ms. This establishes a failed legacy connection, not a definitive rejection of native Media3 clients. No current metadata was obtained.

0.3.10 uses androidx.media3:media3-session:1.8.0 MediaBrowser with a SessionToken for the normally resolvable exported service. Real CELIKOM identity, no connection hints, no transport commands, no library enumeration, no new requested permissions. Read-only current metadata/playback snapshots, bounded connection wait, disconnect/release on teardown; manual shared track remains unverified.

Install over 0.3.9, start music, open CELIKOM by its ordinary app icon, press player-state check, leave open 8 seconds, copy report. Equalizer and accepted tone test are unnecessary for this connection test. Physical admission and exact track ID remain unproven until that report.


## 0.3.10 physical success and transient failure

Reports (3) and (5) established a real Media3 connection on HONOR: playing «Я хочу быть с тобой» / Nautilus Pompilius (position 103887 ms, media_id 17), then paused «Урбан» / Баста (position 177722 ms, media_id 8). Names and pause are real current session data; small media IDs are not proven Yandex catalog IDs. Report (4) was a stale snapshot, not evidence of pause failure. Report (6) failed future completion with SecurityException after 27 ms, with media empty. Owner reports toggling VPN before this second report; causality remains unproven, because the recorded failure is local media-session connection admission.

## 0.3.11 lifecycle and recovery

Reuse an active connection when pressing check, preserve the same application-owned probe across Activity teardown, and keep observation bounded to a two-minute window renewed by explicit check. Disabling observation, clearing results, or window expiry releases the connection. No production background-service claim: system may still terminate the process; the report retains observed_at_ms to distinguish fresh from stale data.

Immediate asynchronous connection failures retry at most three attempts (1 s then 3 s delay), pending connection timeout remains 7 s. Tickets invalidate canceled/old callbacks so timeout is not overwritten by late cancellation. A dropped established session clears its old snapshot before bounded reacquisition. Diagnostics retain sanitized exception types, failure stage, semantic session_rejected marker and client class/method frames; no raw messages or bundle values. Metadata reports only bounded extra key names and existing numeric whitelist. Exact_track_id_verified remains false. Version uses BuildConfig.VERSION_NAME instead of an obsolete literal.

Debug-only local MediaLibraryService test refuses first connection, accepts retry, changes current item, and verifies repeated connect reuses the same admission. Fixture and ExoPlayer dependency excluded from distributionCandidate. Device test: ordinary icon, start one player check, switch between Yandex pause/play/next and CELIKOM within two minutes; check button may refresh without disconnecting. Send report after next track; no repeat sound test. Test VPN reconnect separately only after baseline passes.

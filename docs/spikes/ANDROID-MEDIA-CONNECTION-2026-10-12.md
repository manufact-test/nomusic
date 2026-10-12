# Android 0.3.9: effective service state and terminal connection evidence

Owner0.3.8 report: MusicBrowserService is exported and manifest-enabled; Media3LibraryService is manifest-disabled; Media3SessionService is private. One browser attempt ended in not_connected and no media. This cannot prove intentional rejection because the original timeout overwrote prior failed callbacks. Original0.3.4 normal query returned no_public_service;0.3.8 queried MATCH_DISABLED_COMPONENTS. Manifest-enabled ServiceInfo alone does not account for component overrides.

0.3.9 queries both disabled-inclusive and normal resolution for each standard media action. Only currently normal-resolvable exported/unprotected candidates may be bound. Rows include manifest_enabled, normal_media_query_match and getComponentEnabledSetting when readable. It does not enable, modify or bind disabled/private Yandex components. A missing ordinary query result is reported as unavailable/disabled, not a proved permission denial. Current report cannot yet establish actual component overrides.

Connection evidence is bounded to12 events with class name, timestamp, event and exception class only. It preserves connect_exception, connection_failed_callback, connection_suspended_callback, connected and timeout_without_callback in browser_attempts independently of activity teardown. The seven-second timeout only marks still-connecting attempts, preserving terminal failures. Metadata and tokens are not included in error logs. No credentials, audio, permission request, identity substitution or transport command is added.

Emulator tests distinguish aggregate failed callbacks, timeouts, pending and admitted sessions and enforce runtime-disabled exclusion. Real service admission remains pending. Owner only needs to repeat the state-query button with CELIKOM visible and report after8seconds. Sound-path tests are already accepted and do not need repetition. A blocked public-browser path must not be represented as automatic synchronization support.


## Physical 0.3.9 result and 0.3.10 next probe

HONOR NTH-NX9 / Android 13 / Yandex 2026.09.5: MusicBrowserService is runtime disabled (setting 2), Media3LibraryService runtime enabled (setting 1), exported and unprotected. Legacy platform browser to the active Media3 endpoint returned connection_failed_callback in 74 ms. This establishes a failed legacy connection, not a definitive rejection of native Media3 clients. No current metadata was obtained.

0.3.10 uses androidx.media3:media3-session:1.8.0 MediaBrowser with a SessionToken for the normally resolvable exported service. Real CELIKOM identity, no connection hints, no transport commands, no library enumeration, no new requested permissions. Read-only current metadata/playback snapshots, bounded connection wait, disconnect/release on teardown; manual shared track remains unverified.

Install over 0.3.9, start music, open CELIKOM by its ordinary app icon, press player-state check, leave open 8 seconds, copy report. Equalizer and accepted tone test are unnecessary for this connection test. Physical admission and exact track ID remain unproven until that report.

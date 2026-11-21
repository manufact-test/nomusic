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


## 0.3.11 physical reports (7)-(9), 0.3.12 identity evidence

Report (7): three immediate future_result/SecurityException/session_rejected failures, no media. After owner restarted Yandex, report (8) connected and obtained playing «Воздух» / Легенды Про, ID 11. Report (9) obtained playing «Здравствуй» / MACAN, Три дня дождя, ID 17, position 9259 ms. Owner explicitly states only returned and copied the report, did not press check again. However connection journal timestamps differ and journal is reset, so uninterrupted connection ownership and recreation mechanism are not proven by these reports. New track retrieval without reported manual check is observed; persistent stability still requires testing. ID 17 also previously identified a different title, reinforcing that it cannot be treated as a stable catalog track ID. No numeric candidate in reported item or metadata extras. VPN causality unproven.

0.3.12 inspects current MediaItem request metadata and publicly shared Yandex track URI fields. Non-Yandex stream/local paths, query, fragment and user info are never emitted. Candidate IDs remain exact_track_id_verified=false. If COMMAND_CODE_LIBRARY_GET_ITEM is granted, getItem requests ONLY the currently observed media ID, at most three requests per observation run with a five-second timeout each. No library traversal or transport commands. Generation/current-item key guards discard late results from an older track. The result may be unavailable or merely return a local queue ID; neither is silently upgraded to a catalog ID.

Debug service returns an item URI containing a test token; instrumentation verifies ID extraction and token stripping and verifies candidate remains unconfirmed. URI tests also reject user-info credentials and arbitrary private stream paths. Successful connection clears obsolete media3_error; prior failures remain in bounded connection journal.


## 0.3.12 physical exact-ID check and 0.3.13 remaining public channel

Owner report: connected current «Здравствуй» / Три дня дождя, MACAN / BRATLAND, duration 228000 ms, media_id 13; user share link confirms catalog ID 141103805 and album 37458189. Request/local URI absent, request extras empty, metadata candidate IDs absent, get_item_allowed=false. Therefore getItem was correctly NOT sent. Same title previously had local ID 17; neither 13 nor 17 is accepted as catalog identity. Existing stale shared_track 142820338 is unrelated. Owner was listening over car Bluetooth; this proves state reading on that route, not attenuation/replacement there.

Research: MediaController.getSessionExtras, SessionToken.getExtras and custom SessionCommand extras are separate public sources from MediaItem metadata. These channels were not inspected in earlier probes. 0.3.13 reads only keys and whitelisted positive track-ID candidates/public Yandex track links, with bounded declared command inventory; sends NO custom commands and no forbidden getItem. onExtrasChanged refreshes the evidence. Test includes namespaced track_id and a tokenized public URI and verifies secret values stripped and candidates remain unverified. No claim Yandex exposes ID through this channel before physical test.

Primary API references:
- https://developer.android.com/reference/androidx/media3/session/MediaController#getSessionExtras()
- https://developer.android.com/reference/androidx/media3/session/SessionToken#getExtras()
- https://developer.android.com/reference/androidx/media3/session/MediaController.Listener#onExtrasChanged(androidx.media3.session.MediaController,android.os.Bundle)

Fallback research: CELIKOM tracks table stores album/title/artist/duration and service_track_id. Metadata matching can produce candidates, but uniqueness inside CELIKOM's incomplete catalogue cannot prove the externally playing Yandex ID. Such matching is not silently promoted to exact identity or used for automatic replacement under the current requirement. No server/API change deployed. No supported direct Yandex current-track-ID integration found in searched official sources; this search result is not proof none exists.


## 0.3.13 physical result and 0.3.14 catalog diagnostic

Report (10): connected playing «Здравствуй», local media ID 13; session/token extras empty; declared commands only like/dislike plus rating, all command extras empty. No exact ID found in inspected public sources. No custom command was sent. Owner authorized a separate metadata-only catalog diagnostic, without automatic replacement.

0.3.14 includes a private owner snapshot of CELIKOM track metadata captured during CI via existing pinned SSH; SELECT only under a read-only transaction. No HTTP endpoint, DB write, audio bytes/storage paths/user/session records or credentials exported. Snapshot generated outside Git (ignored asset), private encrypted one-day artifact and closed owner APK. No server deployment. At most 5000 rows with complete flag. APK requires no new network/notification/audio recording permissions.

Matcher compares normalized title (remix/live qualifiers retained), order-independent artist set, album and original duration within 1500 ms. All four required for a strong candidate. Missing data, ambiguous candidates, incomplete/stale snapshot (seven days) prevent selecting a candidate. Even a unique full match is unique_metadata_candidate_unverified/exact_track_id_verified=false/replacement_started=false: catalogue membership is not proof of playing external ID. Report includes up to ten ranked candidates and field rejection reasons, active replacement availability, source age/size and missing metadata count.

Instrumented cases: artist reordering, duplicate metadata across IDs, remix title, absent album, mismatched duration, stale/incomplete snapshot, missing current metadata; no sound replacement code enabled. Physical test should use a song with an approved CELIKOM version; compare diagnostic candidate ID to explicit Yandex share link. Negative controls are other editions and a song absent from CELIKOM. Full feasibility remains unresolved if candidates cannot be distinguished reliably.


## 0.3.14 physical catalogue results and 0.3.15 freshness repair

Owner reports: «Вспышка» uniquely matches 38436680 across all four fields, «Животные» uniquely matches 48592132 across all four fields. «Здравствуй» produces zero candidates (global missing metadata on two unrelated rows explains catalog_metadata_incomplete). No exact external ID proven or replacement enabled. Alternate recording of «Вспышка» unavailable to owner; remix physical negative control remains untested.

The first transition report reconnected after manual Check, so cannot prove automatic observation. The next copy-only report retains the previous connection timestamp but still reports paused «Вспышка» with data age ~131 seconds despite owner switching to «Животные». This fails the automatic transition test. Cause (process recreation, scheduling/background suspension, or remote updates) is not established from the report.

0.3.15 marks snapshot ownership by process UUID and elapsed realtime; snapshots older than five seconds, future timestamps or from another process cannot claim fresh data or a selected current catalogue candidate. Historical evidence remains explicitly stale. On resume, expired two-minute windows are reconciled immediately and a new process clears persisted live connection claims without implicitly restarting observation. Bounded twenty-entry track transition history and resume/window/process evidence distinguish updates before returning from reconnect/manual refresh. No foreground-service or permanent-background guarantee added; physical background transition still requires retest. Tests cover age boundary, foreign process, future timestamp, bounded transitions and stale candidate rejection.

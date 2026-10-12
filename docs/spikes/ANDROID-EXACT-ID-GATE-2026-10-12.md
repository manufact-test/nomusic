# Exact Android track identity is the next feasibility gate

**Owner constraints, confirmed 2026-10-12:** exact source track ID only. Ynison/account-side integration is withdrawn; no OAuth developer dashboard, client registration or Music tokens should be requested. Artwork/title/artist/duration matching cannot satisfy current identity. The uncommitted 0.3.16 artwork experiment was fully reverted before any remote push or APK build. Android remains 0.3.15. Historical Ynison scripts below are unused engineering research and are not part of the APK.


Owner explicitly prioritizes exact current identity before additional sound replacement or UI development. Suspend proposed synchronized-tone work. Existing 0.3.15 proves short background transition, a transition after an owner-reported 30-second screen-off interval, fresh paused state, a finger-selected seek to 145179 ms (owner confirms roughly 2:25, not requested 1:30), and resumed playing state at 156437 ms. These are state observations, not complete replacement proof. Physical precision of seek not independently measured.

## Historical research — withdrawn: account playback synchronization (Ynison)

Yandex official help describes synchronized queues across devices. Public implementation source from MarshalX/yandex-music-api at tree 9ca132e5c18a72aab779c1fc68c169380a9357d0 describes authenticated websocket state with active_device_id_optional, player_state.player_queue.current_playable_index and playable_list[].playable_id/album_id_optional/playable_type. Unlike CELIKOM metadata matching, this can expose server identity for tracks absent from CELIKOM. That is a researched candidate channel, not physical proof it reports this owner's Android device correctly or permits CELIKOM access.

Investigated source: yandex_music/ynison/{_base.py,client.py,messages.py,utils.py,models/ynison_state.py}, examples/ynison_remote.py, tests/ynison_fake_server.py and test_ynison_messages.py. Library initial handshake registers an inactive remote client with can_be_player=false, is_currently_active=false, zero player-action timestamp and DO_NOT_INTERCEPT_BY_DEFAULT; registration is a server-side change even though no pause/seek/queue/volume command is sent. Default app_name=yandex-music must not be copied as CELIKOM identity; use a distinct CELIKOM name/device id if a legitimate authorized live experiment proceeds.

Authorization is unresolved. Library documentation says its default Device Flow client_id belongs to official Android Yandex Music and asserts an own Music OAuth application cannot be created. Generic Yandex ID OAuth documentation does not establish access to Music/Ynison. Do not disguise CELIKOM as the official client, silently reuse its credentials, print tokens, or ask for a password/token in chat. No Yandex credential exists in the current environment. A usable authorized access path must be settled before offering a live-test build. Existing installed Media3 access does not grant account authorization.

## Historical implementation — unused isolated offline decoder

tools/diagnostics/ynison_identity.py extracts only a numeric TRACK playable_id for an explicitly bound, present, online active device and a received frame no older than five seconds. Missing/other/duplicate devices, invalid index, injected content, local tracks/radio/videos and malformed IDs reject selection. No metadata inference, private fields, credentials or audio URLs emitted; exact_track_id_verified=false and replacement_started=false remain explicit until physical verification. No network or auth implementation added to Android, no APK rebuilt and no server deployed. Synthetic tests cover selection independent of catalogue membership, wrong devices, queue bounds, injected content/types, age limits and secret stripping. Tests do not prove live Ynison access.

## Historical proposed Ynison acceptance — superseded, do not request

Use account/device-owned authenticated session, bind the exact playing phone (not whichever account device happened to be active), and compare live server ID to explicit share link on at least two catalogue songs and one absent from CELIKOM. Change songs without manual sharing/check; pause/resume/seek and screen-off. Multiple devices, offline state and VPN reconnect must not silently select another device or stale ID. If server omits mobile state, rejects authorization, or is too delayed, keep this gate open rather than build the full app around inference.

## Share-link option

Android ACTION_SEND carries the actual track link when Yandex/user invokes sharing; registering a receiver does not initiate Yandex's share action or subscribe to future songs. Accessibility UI automation could interact with the share button after explicit service enablement, but depends on exposed on-screen UI; locked-screen/background automatic sharing is unproven and cannot be presented as a transparent all-song solution. No Accessibility or clipboard monitoring introduced. Manual share remains an explicit reference, never proof of the next playing track.

Sources:
- https://yandex.ru/support/music/ru/listening/playback-queue
- https://ym.marshal.dev/yandex_music.ynison.models/
- https://ym.marshal.dev/yandex_music.ynison.client/
- https://ym.marshal.dev/yandex_music._client.device_auth/
- https://ym.marshal.dev/token/
- https://yandex.ru/dev/id/doc/ru/concepts/ya-oauth-intro
- https://developer.android.com/develop/ui/compose/sharing/receive
- https://developer.android.com/reference/android/accessibilityservice/AccessibilityService

## Historical transport preparation — withdrawn, do not request authorization

tools/diagnostics/ynison_live_probe.py now implements redirect/state websocket handshake and the inactive registration frame using a distinct CELIKOM client name and randomly generated device ID. Owner-supplied already authorized Music token comes only from hidden terminal input or CELIKOM_YANDEX_MUSIC_TOKEN; no token/password is accepted in report, logged, saved, extracted from installed apps or obtained with borrowed OAuth client credentials. This is an engineering probe, not an Android deliverable and not live success. It registers a passive server device (not purely read-only on server) but has no sound/control commands.

Incoming frames bounded to 1 MiB, report to 120 frames and runtime 120 seconds. TLS is enabled with normal certificate checks; protocol redirect hosts must be under music.yandex.ru with no port/userinfo/path, and all HTTP redirects are refused so Authorization cannot be forwarded cross-origin. Error reports contain class only. Device-discovery report exports truncated title/type and hashed device identity, not tokens, tickets, raw queue, media URLs or raw device IDs. No current ID is selected until expected active phone hash is explicitly bound. An idle account may emit no fresh state frames; observation_finished never asserts current identity. Network loss ends the probe rather than retaining a current-ID claim.

Nine local tests passed for the decoder and fake transport: two IDs arrive on separate state frames without any playback command; own passive registration, mismatched device, stale/invalid state, injected content and wrong media types, secret stripping, host and HTTP redirect rejection. These are simulated frames, not evidence of authorized Music access. No new APK or server deploy. Generic Yandex OAuth docs explain registering API permissions, but do not advertise a usable Music/Ynison permission. Earlier dashboard/token proposals were withdrawn. There is no owner authorization action pending; do not revive these proposals.

Additional sources:
- https://yandex.ru/dev/id/doc/ru/register-api
- https://yandex.ru/dev/id/doc/ru/concepts/ya-oauth-intro
- https://github.com/thedvxch/yandex-music/blob/main/src/ynison/client.ts
- https://github.com/thedvxch/yandex-music/blob/main/src/ynison/messages.ts
- https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html


## Desktop comparison after owner correction

Inspected extension/src/player/core.ts and extension/src/adapters/yandex-music-adapter.ts. Browser bridge executes in the page main world, observes that page's fetch/XHR JSON responses and reads track objects with realId/id. The page also exposes track path links. Browser adapter ranks current candidates using current player evidence; artwork alone is not a supported exact-identity source. No change to accepted extension behavior.

Native Android companion is a different process/UID and has no equivalent access to Yandex's internal JS/network client/player objects. In observed public Media3 data, queue IDs were short and unstable; actual catalog ID was not exposed in tested fields. Yandex using catalog IDs internally does not demonstrate third-party companion access to them. Android feasibility gate remains exact local source identification without server-side account integration or inference from mutable metadata. Do not promise a source exists, and do not continue replacement or UI development until live ID acquisition is proved.

## Local source audit and owner-suggested share automation, 2026-10-13 Minsk

Inspected the actual 0.3.15 report generated at 1791836270225 from the owner's resumed playback check. `session_identity` advertises six custom like/dislike actions and standard command 40010 only. AndroidX Media3 **1.8.0** `SessionCommand.java` identifies 40010 as `COMMAND_CODE_SESSION_SET_RATING`; library root, children, item and search commands are 50000–50006 and are absent. Do not confuse rating with permission to read the catalogue, issue unavailable queries, or build another probe merely to repeat those queries. Current-item request/local URIs are absent and session/token extras are empty in this report. This is evidence about the tested version/connection, not a universal assertion about all Yandex releases or protocols.

Read AndroidX Media3 1.8.0 `MediaSessionLegacyStub.java` and `LegacyConversions.java` through the repository API. Standard conversion to legacy `MediaDescriptionCompat` sets media ID from `item.mediaId` and media URI from `item.requestMetadata.mediaUri`; metadata conversion likewise receives the player item's ID and URI. Thus the standard compatibility conversion is **not an independent catalogue-ID source**. This source inspection does not constitute a physical test of a separate Yandex legacy connection, and does not rule out app-specific extras on another connection. Existing legacy probe only connects eligible enabled public services; the owner's older MusicBrowserService is disabled. Do not enable private/disabled components or impersonate Android Auto.

Yandex's own share documentation explicitly describes three dots → Share → copy/send link. Owner's prior ACTION_SEND test already delivered the exact ID 142820338. That confirms a source ID for the **shared item**, not continuous current-playback identity. Android's ACTION_SEND receiver receives sharing initiated by the source app; it has no API that asks another app to share its internal current item.

Owner explicitly suggested automated three dots → Share as a fallback. Accessibility APIs can retrieve exposed active-window nodes and invoke ACTION_CLICK after the user enables the service. This makes a foreground UI experiment plausible; it does **not** prove unattended acquisition when Yandex is hidden or the screen is locked. It must not be described as a transparent background solution. No Accessibility service or additional permission was introduced in the accepted diagnostic APK during this audit. No screenshot/template matching, coordinate tapping, artwork matching, or automatic sharing to people implemented.

If the fallback is implemented, first inspect only the visible Yandex player/menu and establish an unambiguous menu/share target. Obtain the actual link through CELIKOM's share target rather than background clipboard monitoring (Android 10+ denies ordinary background clipboard reads). Bound one user-initiated attempt, refuse unrelated packages and ambiguous nodes, stop on lock/window change/timeout, and invalidate identity on player item changes. Compare the received ID against a separate manual share reference on two songs, including one absent from CELIKOM. Foreground success alone does not pass the required automatic playback identity gate.

**Outcome:** no new automatically accessible local exact-ID channel confirmed. Manual sharing is proven; UI automation remains an unbuilt, untested fallback with a foreground constraint. No new APK needed merely to retest unavailable library commands. No owner checks pending at the end of this source audit. Android remains 0.3.15, replacement/UI work remains gated.

Primary sources:
- https://github.com/androidx/media/blob/1.8.0/libraries/session/src/main/java/androidx/media3/session/SessionCommand.java
- https://github.com/androidx/media/blob/1.8.0/libraries/session/src/main/java/androidx/media3/session/MediaSessionLegacyStub.java
- https://github.com/androidx/media/blob/1.8.0/libraries/session/src/main/java/androidx/media3/session/LegacyConversions.java
- https://yandex.ru/support/music/ru/new-library/share-track-or-playlist
- https://developer.android.com/reference/android/accessibilityservice/AccessibilityService
- https://developer.android.com/reference/android/view/accessibility/AccessibilityNodeInfo
- https://developer.android.com/about/versions/10/privacy/changes#clipboard-data
- https://developer.android.com/develop/ui/compose/sharing/receive

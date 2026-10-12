# Exact Android track identity is the next feasibility gate

Owner explicitly prioritizes exact current identity before additional sound replacement or UI development. Suspend proposed synchronized-tone work. Existing 0.3.15 proves short background transition, a transition after an owner-reported 30-second screen-off interval, fresh paused state, a finger-selected seek to 145179 ms (owner confirms roughly 2:25, not requested 1:30), and resumed playing state at 156437 ms. These are state observations, not complete replacement proof. Physical precision of seek not independently measured.

## New channel found: account playback synchronization (Ynison)

Yandex official help describes synchronized queues across devices. Public implementation source from MarshalX/yandex-music-api at tree 9ca132e5c18a72aab779c1fc68c169380a9357d0 describes authenticated websocket state with active_device_id_optional, player_state.player_queue.current_playable_index and playable_list[].playable_id/album_id_optional/playable_type. Unlike CELIKOM metadata matching, this can expose server identity for tracks absent from CELIKOM. That is a researched candidate channel, not physical proof it reports this owner's Android device correctly or permits CELIKOM access.

Investigated source: yandex_music/ynison/{_base.py,client.py,messages.py,utils.py,models/ynison_state.py}, examples/ynison_remote.py, tests/ynison_fake_server.py and test_ynison_messages.py. Library initial handshake registers an inactive remote client with can_be_player=false, is_currently_active=false, zero player-action timestamp and DO_NOT_INTERCEPT_BY_DEFAULT; registration is a server-side change even though no pause/seek/queue/volume command is sent. Default app_name=yandex-music must not be copied as CELIKOM identity; use a distinct CELIKOM name/device id if a legitimate authorized live experiment proceeds.

Authorization is unresolved. Library documentation says its default Device Flow client_id belongs to official Android Yandex Music and asserts an own Music OAuth application cannot be created. Generic Yandex ID OAuth documentation does not establish access to Music/Ynison. Do not disguise CELIKOM as the official client, silently reuse its credentials, print tokens, or ask for a password/token in chat. No Yandex credential exists in the current environment. A usable authorized access path must be settled before offering a live-test build. Existing installed Media3 access does not grant account authorization.

## Implemented isolated offline decoder

tools/diagnostics/ynison_identity.py extracts only a numeric TRACK playable_id for an explicitly bound, present, online active device and a received frame no older than five seconds. Missing/other/duplicate devices, invalid index, injected content, local tracks/radio/videos and malformed IDs reject selection. No metadata inference, private fields, credentials or audio URLs emitted; exact_track_id_verified=false and replacement_started=false remain explicit until physical verification. No network or auth implementation added to Android, no APK rebuilt and no server deployed. Synthetic tests cover selection independent of catalogue membership, wrong devices, queue bounds, injected content/types, age limits and secret stripping. Tests do not prove live Ynison access.

## Physical acceptance before any replacement development

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

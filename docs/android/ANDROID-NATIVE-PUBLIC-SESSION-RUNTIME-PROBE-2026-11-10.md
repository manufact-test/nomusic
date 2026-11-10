# CELIKOM Android — genuine publisher Media3 session read-only capability probe (10 Nov 2026)

## Why this experiment

[Signed manifest CI 42782747091](https://github.com/manufact-test/nomusic/actions/runs/42782747091) verified the unmodified, publisher-signed exact #170gpr 5 splits: **three** media service declarations with relevant standard Android intent actions. Two declare MediaBrowserService, one Media3 LibraryService and one Media3 SessionService (actions may coexist on one service). Of the three services **one** is exported without a manifest permission guard and enabled; **one** unexported; **one** explicitly disabled. This establishes a *candidate public binder*, NOT an audio-source API or guaranteed session connection.

Android Media3 \`MediaController\` documents \`replaceMediaItem()\` gated on \`COMMAND_CHANGE_MEDIA_ITEMS\`. A provider-owned session *may* permit external playlist changes; the platform cannot grant source injection by itself. Even if this command appears, it says **nothing** about rights, URL acceptance, current track/edition, decoder source before prepare, user account or reliable native seek. No commands should be attempted without separate explicit permission.

## Independent, unchanged-publisher runtime capability-only attempt

New isolated, **CELIKOM-owned** \`public-session-probe\` module:
- On a disposable emulator only, downloads the same exact pinned publisher source archive and verifies version/split set/publisher signature, with no repackaging.
- Installs 5 unchanged original split APKs and the own small diagnostic Activity. No account login, playback, music selection, ADB dumpsys, capture, injection, or AudioTrack.
- Own Activity enumerates Android's publicly exported permissionless MediaBrowser/Media3 Session/Library services for exact pinned package only; no component names or private provider identifiers logged. Refuses multiple eligible candidates.
- Connects via documented \`SessionToken\` + \`MediaController.Builder.buildAsync()\` and reports **only booleans** for \`COMMAND_CHANGE_MEDIA_ITEMS\`, \`COMMAND_SET_MEDIA_ITEM\`, \`COMMAND_GET_CURRENT_MEDIA_ITEM\`, pause and seek, plus connection status. Does **not** call replace/add/set/prepare/play or read current MediaItem. Releases controller after read.
- CI helper prints only a strict allowlisted, categorical result. No third-party binary, probe APK, logs, media or secret artifacts are published. Original Yandex on owner's HONOR remains untouched.

This runtime attempt can legitimately be **inconclusive** if the unlogged original does not publish a session, if its service declines controllers, or emulator ABI does not initialize it. Never infer negative global capability from that. Conversely \`COMMAND_CHANGE_MEDIA_ITEMS=true\` merely grants playlist command permission, not the requested native replacement.

## Hard product gate

No real \`trackId + edition + generation -> FileInfo -> actual decoder descriptor -> exactly one source before prepare\` has been observed in unchanged Yandex. No authorized third-party file-URI source contract exists in evidence. No root, bypass, unofficial account API, second player or WebView is allowed. Until that evidence exists, **NO-GO for CELIKOM native source replacement**. Never distribute the probe as a CELIKOM solution.

Source: https://developer.android.com/reference/androidx/media3/session/MediaController

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


## Runtime first pass and controlled platform-browser fallback

CI 42783663050: mechanics SUCCESS, but exact signed original #170gpr on disposable Android11, unauthenticated, yielded one public binder candidate and Media3 state CONNECTION_NOT_ESTABLISHED; every flag false because the handshake failed, not because Yandex definitely rejected a command. Added one last strictly read-only platform MediaBrowser.connect() fallback to this exact exported service. Reads only categorical PlaybackState actions, never invokes play, media URI, queue, OAuth, FileInfo or decoder. A failure without login is still inconclusive for authenticated playback. CI follow-up recorded separately after run.


## FINAL CHECKPOINT 10.11.2026 — legitimate public MediaSession experiment, NO usable source host

**Code HEAD:** `dc61cd8d7f6c116d91e74ae30c174a50528cde83`. **Immutable backup before docs:** `backup/android-native-public-session-final-evidence-20261110`. This is a *first-party CELIKOM-owned, read-only diagnostic* against the **genuine pinned publisher-signed Yandex**, not a native audio replacement and not a patched host.

**Verified CI:**
- [42782747091](https://github.com/manufact-test/nomusic/actions/runs/42782747091) SUCCESS, static signed five-split manifest. Three media service declarations, two `MediaBrowserService` actions; one explicit exported, enabled and without manifest permission binder candidate. This does **not** imply externally replaceable audio.
- [42783663050](https://github.com/manufact-test/nomusic/actions/runs/42783663050) SUCCESS test mechanics; cold guest-free disposable Android 11 controller handshake **not established**. `COMMAND_CHANGE_MEDIA_ITEMS` false only because controller was not connected.
- [42784630427](https://github.com/manufact-test/nomusic/actions/runs/42784630427) SUCCESS test mechanics; fallback through the platform `MediaBrowser.connect()` to that exported candidate **rejected**: `PUBLIC_BIND_REJECTED`. No playback command ever sent.
- [42785272172](https://github.com/manufact-test/nomusic/actions/runs/42785272172) SUCCESS test mechanics **after a single bounded launch of the unmodified original guest UI on isolated emulator** and verifying MAIN process exists: still **`PUBLIC_BIND_REJECTED`**, Media3 not connected, platform browser not connected. No login or account involved.
- [42785272231](https://github.com/manufact-test/nomusic/actions/runs/42785272231) SUCCESS existing synthetic hooklab jobs, **not publisher audio**.

**Narrow interpretation:** public *manifest* service candidate does not permit third-party controller access in the tested **unauthenticated disposable environment**. Exact binder rejection condition is **not known**; no claim about a logged-in publisher app or anti-tamper. The test did not call `replaceMediaItem`, `setMediaItem`, play/pause, seek, URL, FileInfo or decoder; no user metadata was read. Android `MediaController` may permit queue changes only if session owner advertises the required commands; here there was no connected controller to inspect. This does **not** establish a native pre-prepare source replacement.

**Engineering admission:** NO-GO for the requested exact original-Yandex one-player alternative audio source. There is **no verified supported publisher source API/SDK, authorized instrumented host, or runtime `track+edition+generation -> real decoder source` witness**. Stop additional emulator/package or speculative DEX experiments unless an actually new lawful host capability appears. No new user APK or manual QA now. Explicit next dependency: publisher-approved integration/compatibility agreement identifying actual source-before-prepare API and rights/DRM limits. Test.50, official HONOR, Windows, extension, server, DB and production untouched.


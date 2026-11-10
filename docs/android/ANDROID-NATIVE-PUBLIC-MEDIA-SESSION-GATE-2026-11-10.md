# CELIKOM Android — unmodified publisher MediaSession manifest gate (10 Nov 2026)

## Purpose

A further *legitimate* possible path, distinct from patching, would be publisher-permitted Media3 `MediaController` playlist replacement **within the Yandex-owned single player**. Android explicitly exposes `replaceMediaItem`, but **only if the session owner grants `COMMAND_CHANGE_MEDIA_ITEMS`**. Even such permission is not evidence that Yandex accepts third-party audio URIs, maps the exact source to the current track+edition, or does so before prepare. This path cannot be advertised as functional.

## New bounded evidence approach

Enhanced `audit_unmodified_yandex_ipc.py` to inspect the **publisher-signed pinned #170gpr base manifest in isolated CI**, without patch/install/login/media access. Counts *three platform-documented media-service actions*:
- `android.media.browse.MediaBrowserService`;
- `androidx.media3.session.MediaSessionService`;
- `androidx.media3.session.MediaLibraryService`.

For each media service, classify explicit `exported`, service/application-level permission guards and explicit disabled status. Print aggregated counts only; **no component class names, authorities, URIs or credentials**. This is not an authorization claim. Not every media service with `exported=true` is bound by a third-party app; Android version, service logic and runtime policy also matter. No session is connected, no playback is controlled, and no `replaceMediaItem` is invoked.

## Exact decision gates

1. **Manifest gate:** zero permissionless public candidates implies no directly eligible service *from the declared intent-action set*; other session discovery approaches exist, so avoid universal impossibility claims. If candidates exist, it is only a hint to investigate.
2. **Runtime observation, only with authorized separate device/host and user consent:** connect through Android's **public controller API**, inspect only available command flags, never extract titles/account/cookies/tokens/streams. The session must offer `COMMAND_CHANGE_MEDIA_ITEMS`, not only PLAY/PAUSE or NEXT.
3. **Contract/legal gate:** show publisher grants externally supplied rights-cleared `MediaItem` with the *actual Yandex player's own* source-before-prepare and exact track+edition association. Even if replacing a queue entry is possible, it may reset the song, break radio or be disallowed. No mutation in diagnostics.
4. Until **all** of the above, native replacement remains **NO-GO**. Do not ask user to change main HONOR app, disable Play Protect, or install a clone. Current Test.50 remains untouched.

Primary Android documents:
- https://developer.android.com/reference/androidx/media3/session/MediaController
- https://developer.android.com/reference/androidx/media3/session/MediaSession.Callback
- https://developer.android.com/media/media3/session/control-playback
- https://source.android.com/docs/security/app-sandbox

Only if a genuine publisher-supported source boundary is demonstrated does the already-tested `NativePrePrepareAdmission` model become a candidate to integrate. Model tests and manifest discovery do NOT prove a native one-player swap.

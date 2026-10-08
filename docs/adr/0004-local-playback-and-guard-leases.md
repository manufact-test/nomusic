# ADR-0004: Local playback and guard leases

- Status: implemented for Stage 3 validation; live acceptance pending
- Date: 2026-10-08

## Decision

The original service remains the queue, UI and playback clock. A separate CELIKOM HTMLAudioElement plays only when the exact current Track ID matches the explicitly selected demo ID, the ID is non-ambiguous/confident, and metadata duration matches the selected native master within 1.5 seconds. A DOM media object is resolved only inside the MAIN-world adapter; stream URLs and credentials are never transferred or fetched by CELIKOM.

`ReplacementController` owns one operation, with session/generation cancellation. It loads a muted replacement before requesting a guard. MAIN revalidates the exact binding before muting. An old asynchronous load, error or lease release cannot modify a new operation. Fail-open disposes replacement synchronously, then requests a token-scoped release; a missing acknowledgement triggers an immediate token-scoped signal as a fallback to the independent watchdog.

`OriginalAudioGuard` intercepts only the selected element's native volume/mute accessors. Physical original mute remains forced while logical reads/writes preserve the site's latest user intent. It refuses properties that cannot be intercepted safely. Release restores original descriptors and latest intended values. MAIN stops shared-DOM replacement media and releases the guard on binding change, master error/end, pagehide, new session and heartbeat loss. Visibility timeout is 12 seconds visible / 120 seconds hidden; this is a recovery deadline, not a claim of instantaneous restoration after context termination.

`SyncEngine` follows native pause/seek/rate/volume/mute and checks drift at 500 ms intervals with a provisional 350 ms threshold and 800 ms correction cooldown. Projection is bounded; paused/seeking/unready clocks do not advance. A long legitimate pause does not trigger stale-clock recovery. Live testing must establish that corrections are unobtrusive.

The synthetic packaged demo uses the accepted PoC's fetch-to-blob path, with cancellation, load bounds and URL revocation. Only the demo loops/modulo-seeks. Future real files must stream through the Stage 4 Range endpoint and fail open on premature ending. Asset exposure is restricted to one MP3 and the existing Yandex Music origin; no remote code or new host permission is introduced. Resource access follows [Chrome's content-script guidance](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts).

Manual original restoration stores a per-track bypass. It survives same-track state updates and unrelated settings; an exact different track or explicit Start re-arms it. Global Stop persists in local storage. The popup has four primary controls; diagnostics and synthetic binding are collapsed developer-only details. Add Track explains that backend uploads are not yet available.

## Gate

0.3.0 failed the owner's first live launch with `normalizeTrackId` on a captured undefined core. This exact signature is reproducible by registering the engine before the core and then injecting the complete group. 0.3.1 resolves dependencies at construction and bundles each world into one ordered classic script; manifest and recovery injection cannot diverge in dependency order. Polling a failed startup does not re-inject it; a refreshed page creates new immutable globals.

The owner's 0.3.1 diagnostics confirm healthy startup and guarded replacement with −1 ms drift, but generation 49 and repeated same-track releases do not establish stability. 0.3.2 fixes two independently reproduced defects: sub-second data-audio utility elements gaining master priority during pause, and an already guarded exact binding being discarded when seek temporarily reduces readiness to HAVE_METADATA. A retained binding pauses replacement until ready; admission still requires current data, and an emptied, ambiguous, changed or duration-mismatched master fails open. Catalog duration is kept independent of native media duration. MAIN compares the guarded stream identity locally, releases on source change and blocks stale-track retry until an exact different ID or explicit Start; raw URLs never cross the bridge. Activation/restore counts and safe binding reasons make the remaining live gate observable.

Unit, generation/race and compiled MAIN/ISOLATED mock integration tests are necessary but do not validate real browser decoding, autoplay, isolated DOM wrappers, CSP, timer throttling or audible sync. Stage 3 closes only after the separate live checklist. No Hostinger deployment or arbitrary-format support is implied by this stage.

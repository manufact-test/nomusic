# Read-only probe 0.0.3: actual Playback state binding

Branch: `experiment/desktop-native-probe-state-20261108`. Accepted 0.4.73, product extension source/manifest, server and Android are unchanged. No production deployment.

## Evidence and mistake

Owner probe 0.0.2 at 2026-11-08T13:25:30.340Z found a controller through fiber-context, but found no queue, entity or media player. Its playback flag was true.

The probe incorrectly read queueState/currentMediaPlayer directly from Playback. Public pinned Yandex module 7123 exports VE (Playback); its real state getter returns playbackState. Correct paths are playback.state.queueState.currentEntity.value and playback.state.currentMediaPlayer.value. Module 41938 controller also reads getPlayback().state.

Earlier fixtures reproduced the incorrect direct-field assumption, allowing tests to pass. Those tests did not establish compatibility with the owner's actual playback instance. This was our implementation/testing mistake.

## Correction and verification

Engine reader version 3 and probe 0.0.3 use the state getter. Node lifecycle tests, generated-reader tests and browser React fixture now instantiate the actual exported VE prototype from pinned Yandex code; direct queue/player fields are explicitly undefined. Fixtures still supply controlled backing state: these checks do not prove a real signed-in session.

Functional commit f71d0508fa72c56b2a6c12b9e426019572a0fe05 passed [CI 42485258646](https://github.com/manufact-test/nomusic/actions/runs/42485258646), including Chrome/Brave checks and accepted desktop regressions.

Additional experimental reload guards are scoped to the operation's own first entity source read and returned source object. They must not block a new track's independent read/play or an independent same-track setSrc after pause. Local lifecycle/reader suite: 35 passed. These guards are excluded from the read-only archive and are not connected to product playback.

## Deliverable and remaining boundary

CELIKOM-Engine-Check-003.zip: 5154 bytes; SHA-256 3d423cf07aaf79250a50e6e0073167a8314c8d1f8a64db25a18a3fa640cd0897.
Library identity libfile_6fcfc601349881919dc743c12ac355e3, version 4.

Archive contains only manifest, popup HTML/CSS/JS and generated inspect-only reader. Permissions: activeTab, scripting, clipboardWrite. No background task, content scripts, broad host permission, network interception, playback mutation or audio download.

Owner step: replace files in the EXISTING check-extension folder, reload ONLY CELIKOM engine check in Brave's extensions page, then copy its result on the playing Yandex tab. No Yandex refresh required; version-2 reader is replaced. Expected header probeVersion 0.0.3 / readerVersion 3. Accepted CELIKOM 0.4.73 should not be updated.

## Owner confirmation, 2026-11-08T13:42:13.106Z

Owner returned probeVersion 0.0.3 / readerVersion 3. Controller and binding found; trackId and entityTrackId both 42498653; durationMs 220820; playbackState, queuePair, entity, player, sourceLoader, reload and mediaRef present. Discovery matched fiber-context, without limits or property errors. Media events, native hooks and source/play/setSrc method descriptor checks all passed. pending was false.

This confirms live read-only binding on the owner's Brave tab and resolves the previous probe's wrong state path. encryptedRestoreViaEngine:true reports the presence of a reload entry point only; it does NOT mean encrypted restoration was executed successfully. Likewise fence flags describe configurable method shapes, not installed or executed protections.

Next experiment must provide exclusive playback ownership, reuse the existing broker/downloader, and exercise actual source replacement plus original restoration. Do not run the accepted replacement player and native replacement concurrently. Begin with one explicit current-track switch, then pause/seek/Next/Stop/error restoration; do not enable automatically on startup.

Actual source switching and encrypted restoration remain unverified. No native playback backend has been enabled for the owner.

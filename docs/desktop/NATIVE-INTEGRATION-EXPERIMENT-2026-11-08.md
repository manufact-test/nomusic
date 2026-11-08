# Native experiment 001: integrated desktop extension

Branch: `experiment/desktop-native-integration-20261108`. Base is owner-accepted desktop 0.4.73 (`63d8cd891e1db82e0245122391fd4ab5cdd323be`). No production publication. Product extension sources/manifest, Android and server are unchanged; packaging overlays live under spikes/native-source only.

## What is integrated

The existing content controller, popup, account/entitlement broker, upload and support paths remain in use. Only the replacement-controller factory is substituted in the experimental dependency bundle. The existing ReplacementPlayer class supplies its complete validated Range downloader, but no ReplacementPlayer is instantiated and no replacement audio element is created. The native controller publishes legacy playback policy enabled:false, preventing legacy muting and intro guards from becoming a second playback owner.

Prepared files pass existing MP3 duration inspection and fresh broker admission. Only a bounded Blob, track ID, duration, expiry and session generation cross into MAIN. Bearer and signed audio URLs stay in the isolated/background flow. Staging bytes does not register a source; registration occurs on explicit activation for the exact live native queue ID.

NativeSession uses the real Playback.state binding and stock core.reload(entity), rather than assigning encrypted original bytes to audio.src. It waits for actual media metadata after paused reload, because that stock method can resolve before setSrc finishes loading. Stop cancels pending source work and unregisters replacement descriptors immediately. Original restoration precedes Blob revocation. If restoration fails, the URL is retained instead of invalidating a potentially playing source. Reload guards remain scoped to their own operation and source.

Next with new queue metadata and an old audio source waits for Yandex's own transition, rather than reloading the new song at the old audio's position. MAIN also watches expiry, heartbeat loss and wrong-ID source state. No automatic playback backend fallback or competing legacy owner is enabled.

The existing metadata adapter intentionally invalidates unchanged song metadata after an arbitrary src change. An experiment-only prototype wrapper uses the real native queue when its audio element matches the observed master, preserving the popup/upload track ID across an intentional same-song source switch. Product adapter source is unchanged.

## Verification and limits

Local lifecycle, reader and session/controller suites: 46 passing tests. Integrated VM test runs the real downloader and generated MP3 inspector through isolated/MAIN RPC and verifies disabled legacy policy, activation and manual restore, including the concurrent emergency-release signal. Native reload/Playback class bodies come from pinned public Yandex code, not invented direct-field playback objects.

Accepted desktop suite: 360 passing tests. Browser fixture exercises official Chrome and Brave with actual MV3 research scripts, actual Yandex resource/source/Playback/reload classes, actual React context discovery and actual HTML audio. Controlled resource responses deliberately use decodable fixture media: encrypted original decryption with a signed-in Yandex account is NOT tested. Browser results and exact commit/run identifiers are recorded separately after the final run.

The integrated extension still requires an owner listening check. End-to-end signed-in startup and encrypted restoration have not been proven by the read-only probe or controlled fixture. No measured real-world speed improvement is claimed. Cold complete-file downloads can be slower than 0.4.73's streaming path. Version 001 supports zero-gain MP3 only, maximum 30 MiB, and expires prepared native files after at most five minutes; expiry restores the original. M4A, gain application, next-queue prefetch and continuous authorization/expiry renewal are outside this minimum experiment.

## Build and manual check

Build accepted sources with CELIKOM_API_BASE_URL set to the existing configured service origin, then run `node spikes/native-source/build-integrated.mjs ABSOLUTE_OUTPUT_PATH`. GITHUB_SHA records exact committed experimental source provenance. Packaging emits version 0.4.74 / version_name 0.4.74-native-experiment-001, an internal provenance file, a deterministic ZIP and an external SHA-256 receipt. This does not change accepted package.json, manifest or core source.

Use a SEPARATE folder. Disable ordinary CELIKOM, load the experimental unpacked folder, sign in normally if the separate extension ID has no stored account, and reload Yandex once. Never run two CELIKOM playback extensions simultaneously. Check two known available MP3 tracks: beginning, pause, seek, Next, Return original and Stop. If unexpected behavior occurs, disable the experiment, re-enable accepted 0.4.73 and reload Yandex. Its existing folder and stored account remain intact.

# CELIKOM Android A1 — external playback research notes

**Date checked:** 16 November 2026  
**Purpose:** Check whether public Yandex / Android Media3 information already explains the current TrackWrapper → source → Player → decoder investigation.

## Findings

### 1. No public source found for the official Android app's obfuscated internal route

The public material reviewed does not disclose the official Yandex Music Android application's exact internal call graph for the pinned signed 2025 build. No public write-up found an equivalent to the current `LIEa → Lqj8 → Lxj8 → Lvj8 → LfT2` route or a ready-made fix for connecting the selected native Track to the active decoder.

Do not treat third-party clients or web-player hooks as evidence of the official Android app's runtime dispatch.

### 2. Media3 documentation gives an important alternative to the MediaItem-only search

Official Android documentation describes the pipeline:

- `MediaSource` defines the media timeline and creates `MediaPeriod` instances.
- `MediaPeriod` loads the period and provides data for renderers.
- `DataSource` is the component that requests bytes from a network or local file.
- An `Extractor` parses container data into track information and access units for a decoder.
- A `MediaSource` is commonly created from a `MediaItem` by `MediaSource.Factory`, **but ExoPlayer also exposes playlist APIs that accept `MediaSource` objects directly** (`setMediaSource`, `setMediaSources`, `addMediaSource`). That path can bypass the internal MediaItem-to-MediaSource factory conversion.

Sources:
- [Media sources — Android Developers](https://developer.android.com/media/media3/exoplayer/media-sources)
- [Media3 ExoPlayer API — Android Developers](https://developer.android.com/reference/androidx/media3/exoplayer/ExoPlayer)
- [MediaSource API — Android Developers](https://developer.android.com/reference/androidx/media3/exoplayer/source/MediaSource)
- [Media3 glossary — Android Developers](https://developer.android.com/media/media3/exoplayer/glossary)

**Impact on this investigation:** do not require every valid source handoff to pass through a `MediaItem` getter or mutator. The next bounded LfT2 inspection may follow an identity-proven edge into `MediaSource`, `MediaPeriod`, `DataSource`, or `Extractor`. This is a search boundary informed by Media3's public contract, not proof that the Yandex route uses any particular component.

### 3. Public third-party Yandex clients show how stream resolution can work, but are not the official app

The public [YaMuLite Android client](https://github.com/dpronyaev/yamulite-android) describes its own implementation using Media3 ExoPlayer. Its README documents a stream-resolution flow of download-info → CDN XML → signed URL, and local-first playback for downloaded files.

A separate community [yt-dlp Yandex Music plugin](https://github.com/fgsfds1/yt-dlp-yandex-music-plugin) and its [API research notes](https://github.com/fgsfds1/yt-dlp-yandex-music-plugin/blob/master/research/api-notes.md) describe reverse-engineered web API behavior, including `get-file-info` and different encrypted/raw transport modes.

Limitations:
- These are unofficial third-party projects and undocumented API observations, not Yandex's official Android implementation.
- They use their own clients/player or web/API flow; they do not prove the internal callsites in the signed Yandex APK.
- Do not copy their authentication, URL, key, or transport handling into CELIKOM. The current task is to identify the original native source boundary without changing architecture or adding a second player.

### 4. Yandex's official playback troubleshooting is about network/device stability, not the current static identity gap

[Yandex's support article](https://yandex.ru/support/music/ru/technical-issues/playback-stop) says playback interruptions can be affected by unstable connectivity, VPN/proxy, high audio quality requiring a stable connection, battery saver, and background-data restrictions.

This is useful when diagnosing real playback dropouts on the device. It does **not** explain why the static audit has not proven a same-object edge from TrackWrapper to the selected Player item or decoder.

### 5. Three distinct Yandex builds — separate evidence roles

**2025.10.4 #120.1gpr — current CI #229 specimen**
- Version code 24025542; publisher-signed XAPK 45,961,661 bytes; SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`; 16 splits / 6 DEX.
- Used in the 2025 LSPatch2 laboratory clone experiments and pinned for the current static LfT2 audit.
- This is not yet proven to be the final CELIKOM product runtime target.

**2026.10.3 #170gpr — verified original ARM13 control**
- Version code 24026531; publisher-signed XAPK 60,433,885 bytes; SHA-256 `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`; 5 splits.
- [CI #42990078186](https://github.com/manufact-test/nomusic/actions/runs/42990078186) verified the untouched original package installed and launched its MAIN on native ARM13. The control did not test clone, login, audio or Play Protect.
- `android/native-yandex-hooklab/clone_native_splits_ephemeral.py` also pins #170gpr for a separate structural clone research trial. This does not establish it as the final product target.

**2026.09.5 #167gpr / #167.1gpr — owner handset report**
- Previously reported as installed on the owner's phone. No exact original package + verified SHA is pinned in the current A1 evidence.

Do not conflate #170gpr with #170rur (different distribution channel). Public mirror version listings are inconsistent and are not publisher provenance.

**Target remains unresolved:** determine the exact Yandex build the CELIKOM A1 product packaging is intended to use. The manifest `<queries><package name="ru.yandex.music"/></queries>` establishes Android package visibility only; it proves neither that Yandex is embedded nor that it is absent. Inspect packaged DEX/resources and build inputs. If no source-of-truth answer exists, ask the owner once, presenting all three builds and their distinct roles. Do not choose by newest version number or transfer obfuscated findings across builds.

## Practical conclusion

The next step is first to establish the exact intended Yandex build and verify its original signed split package. Then perform the bounded `LfT2;` class inspection documented in [ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md](ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md) against that exact binary.

Use the public Media3 contract to avoid an overly narrow MediaItem-only assumption, but require exact signed-DEX identity evidence before following a route. No architecture changes, generic hooks, APK changes, account access, private values, or audio reads are justified by this web research.

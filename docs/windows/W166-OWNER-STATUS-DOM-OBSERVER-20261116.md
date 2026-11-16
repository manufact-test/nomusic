# CELIKOM Windows — W166 owner status, pause tone and passive DOM decoder witness

Date: 16 November 2026  
Product: CELIKOM Windows only  
Status: source committed; CI and one internal W20 owner-review package pending; owner acceptance pending.

## Source of truth and rollback

- Repository: `manufact-test/nomusic`
- Working branch: `main`
- W166 code checkpoint: `5bfd6c6e33c4a1008952ba1fc6c53918ce93792e`
- Exact pre-W166 backup: `backup/windows-main-pre-w166-owner-status-dom-observer-20261116` @ `7b956d18314ef1d0d1bf6871551b33dc5d2840ba`
- App version: **0.24.48.0**
- Native module: **0.24.31**
- W23 package: **0.24.11**
- Diagnostics schema: **W55**

## Owner feedback on W165

Owner screenshots after installing 0.24.47.0 showed:
- Active song still displayed gray `Версия CELIKOM доступна`.
- `Пауза` appeared green.
- The gap below active status was smaller but still too large.

W165 was not accepted. The source confirmed the pause color was explicitly enabled by `activelyReplacing || (paused && serviceConnected)`; the current status row remained 40 px tall with an 8 px bottom gap, so reducing only the gap did not remove most of the whitespace.

## Previously accepted VPN/audio behavior

The owner accepted 0.24.46.0 after repeated VPN changes while CELIKOM playback continued without interruption or extra recovery text. This remains frozen. W166 does not change audio, VPN, route recovery, entitlement, Yandex files or playback commands.

## W166 UI implementation

- Active status row height: **28 px** (was 40 px).
- Active status bottom gap: **4 px** (was 8 px).
- Idle/disabled placeholder gap remains **18 px**.
- `Пауза` is neutral; it is never an active CELIKOM indicator.
- Green requires a verified current replacement source and PLAYING state.
- Verified active wording: **«Играет версия CELIKOM»**.

The reduction from 40+8 to 28+4 removes 16 px from the active status-to-account transition without changing the idle/disabled state or other rows.

## Why the active text stayed old

W165 already contained the intended active copy, but it is shown only after the native host reports `NATIVE_SOURCE_VERIFIED`. W54 diagnostics showed Media properties but no CDP `kUrl`, so the strict current-source branch never ran. The old neutral availability text was therefore still correct under the old evidence path; changing the label/color alone would have hidden the missing source proof.

## W166 passive DOM decoder witness

When a Media player does not expose `kUrl`, W166 uses the same Media player's own DOM node as a read-only fallback:

1. `Media.playerCreated` supplies the player's `domNodeId`.
2. `DOM.getDocument` initializes the DOM agent; `DOM.pushNodesByBackendIdsToFrontend` resolves only that backend node.
3. `DOM.getAttributes` reads only the node's `src` attribute. `DOM.attributeModified` / `DOM.attributeRemoved` track only `src` changes on that mapped player node.
4. The URL is compared in memory against the exact approved, entitled, unexpired CELIKOM grant.
5. The same player must be in PLAYING state (`kPlay`/`kPause` events only as fallback when `kIsPlaying` is not exposed), and its CELIKOM track ID must equal the current Yandex queue track ID.

If CDP `kUrl` is present, it remains authoritative and DOM fallback is disabled for that player. If the element uses `blob:` / MediaSource, the DOM URL is not the signed CELIKOM resource and no green state is granted. A network prefetch, HTTP 206, grant, mapping, source-held marker, generic PLAYING state or another Media player is not enough.

The observer does not use `Runtime.evaluate`, `Network.getResponseBody`, extra fetches, play/pause/seek, or any audio/VPN/source-routing mutation. It never writes raw URLs, src values, tokens or query strings to logs.

An approved grant arriving after the player node was first seen triggers a bounded refresh of only active Media player nodes that lack `kUrl`, so the observer does not miss a direct source set before the grant became available.

## W55 diagnostics

Safe summary fields:
- `NativeDomMediaNodeObserved`
- `NativeDomSourceAttributeObserved`
- `NativeDomSourceBlobObserved`
- `NativeDomSourceOtherObserved`
- `NativeDomSourceAttributeMissingObserved`
- `NativeDomCelikomSourceMatched`

These distinguish missing DOM node, missing src, blob/MediaSource, another direct source, and exact CELIKOM match without exporting URLs or DOM text.

## Changed files

- `windows-companion/w23/host.cjs`
- `windows-companion/w23/native-host.test.mjs`
- `windows-companion/w23/package.json`
- `windows-companion/w15/Celikom.Companion/PlaybackSourceEvidence.cs`
- `windows-companion/w15/Celikom.Companion/CompactPlaybackPresentation.cs`
- `windows-companion/w15/Celikom.Companion/CompactPopup.cs`
- `windows-companion/w15/Celikom.Companion/DiagnosticLog.cs`
- `windows-companion/w15/Celikom.Companion.Tests/Program.cs`
- `windows-companion/w15/Celikom.Companion/Celikom.Companion.csproj`
- `windows-companion/w15/Celikom.UpdateSupervisor/Celikom.UpdateSupervisor.csproj`
- `windows-companion/w20/installer/CELIKOM.iss`
- `windows-companion/w20/owner-review-package-20261114.request`
- `docs/windows/NEXT-CHAT.md`
- This W166 handoff.

## Verification and package

- Main CI: pending at source handoff.
- Windows integration CI: pending.
- W20 safe installer staging: one internal package requested; artifact and SHA256 pending.
- No production signing, stable feed, Hostinger deployment or customer publication.

## Owner review

After installing **0.24.48.0 over 0.24.47.0**, check:
1. When a CELIKOM version is actually selected by the current player, the line reads **«Играет версия CELIKOM»** and is green.
2. When paused, **«Пауза»** is neutral.
3. The active status row-to-account gap is tighter; the idle/disabled placeholder retains its previous spacing.
4. No VPN/audio retest is required unless there is a genuine regression.

If the active line remains neutral, export W55 diagnostics. Use the DOM fields to determine whether the Yandex player exposes a direct signed src, uses blob/MediaSource, has no DOM node, or has no src attribute. Do not weaken the proof gate or force green.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, audio engine, VPN recovery, entitlement authority, source routing, updater architecture, production signing or deployment. No broad audits or intermediate installers.

# CELIKOM Windows — active handoff W166 (16 November 2026)

**Status: W166 source changes are committed. Main CI, Windows integration CI and one W20 internal owner-review package are pending. Owner acceptance is pending. VPN/audio behavior accepted in W164 remains frozen.**

## Source of truth

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `main`.
- W166 code checkpoint: `5bfd6c6e33c4a1008952ba1fc6c53918ce93792e`.
- Exact pre-W166 rollback: `backup/windows-main-pre-w166-owner-status-dom-observer-20261116` @ `7b956d18314ef1d0d1bf6871551b33dc5d2840ba`.
- App: **0.24.48.0**, native module **0.24.31**, W23 package **0.24.11**.
- Diagnostics schema: **W55**.
- Full handoff: `docs/windows/W166-OWNER-STATUS-DOM-OBSERVER-20261116.md`.

## Owner feedback on W165 / 0.24.47.0

W165 was not accepted:
- Active track still showed gray `Версия CELIKOM доступна`.
- `Пауза` appeared green.
- Spacing improved only slightly and was still too large.

The screenshots were inspected against source. The green pause was an explicit UI branch:
`activelyReplacing || (paused && serviceConnected)`.
The current-track status row was still 40 px high with an 8 px gap; changing only the gap had left most of the whitespace intact.

## Owner acceptance carried forward from W164

The owner installed 0.24.46.0 and repeatedly toggled VPN while CELIKOM music played:
- Music continued without interruption.
- No extra recovery/status text flashed.
- VPN/audio behavior is accepted.

**Do not modify VPN recovery, audio playback, source routing, entitlement checks, Yandex files or recovery/reload behavior. No VPN/audio retest is required.**

## W166 changes

### Compact UI
- Active status row height reduced from 40 px to **28 px**.
- Active status bottom gap reduced from 8 px to **4 px**.
- Idle/disabled placeholder spacing remains **18 px**.
- Green is now based only on a verified, currently-playing CELIKOM source. Paused state is neutral.
- Active text remains **«Играет версия CELIKOM»**.

### Focused decoder observer fallback
W54 showed Media properties but no CDP `kUrl`. The previous implementation therefore had no exact current source URL and correctly stayed neutral. W166 adds a passive fallback only when that player does not expose `kUrl`:

1. Receive `Media.playerCreated` for a specific player and its `domNodeId`.
2. Resolve that exact backend node through read-only CDP DOM methods.
3. Read only that Media player's `src` attribute.
4. Compare it in memory to an approved/entitled, unexpired CELIKOM signed grant.
5. Require the same player's `kPlay` state (only if `kIsPlaying` is unavailable) and exact current Yandex queue track identity.

If the element uses `blob:` / MediaSource, it does not prove the signed CELIKOM source and remains neutral. Mapping, prefetch GET, HTTP 206, generic PLAYING, or a different Media player do not count. If CDP `kUrl` exists, it remains authoritative and the DOM fallback is not used for that player.

The observer is read-only: no `Runtime.evaluate`, no response-body reads, no extra fetches, no play/pause/seek, no audio/VPN/source-routing changes. Raw URLs and DOM attribute values are never exported.

## Diagnostics

W55 adds safe booleans:
- `NativeDomMediaNodeObserved`
- `NativeDomSourceAttributeObserved`
- `NativeDomSourceBlobObserved`
- `NativeDomSourceOtherObserved`
- `NativeDomSourceAttributeMissingObserved`
- `NativeDomCelikomSourceMatched`

No signed URL, token, src value or arbitrary DOM text is logged.

## Verification / package

- Main CI: pending.
- Windows integration CI: pending.
- W20 safe installer staging: one package requested; run/artifact/SHA256 pending.
- Expected internal package:
  - `CELIKOM-W166-OWNER-STATUS-DOM-OBSERVER-02448-UNSIGNED.exe`
  - `CELIKOM-Windows-0.24.48.zip`
  - `SHA256SUMS.txt`

## Owner check after delivery

Install **0.24.48.0 over 0.24.47.0** and check only:
1. On a track whose CELIKOM version is actually playing, the status reads **«Играет версия CELIKOM»** in green.
2. Press Pause: **«Пауза»** is neutral, never green.
3. The gap below the active status is visibly tighter; idle/disabled spacing remains unchanged.
4. No VPN/audio retest unless a real regression appears.

If the active status remains neutral, export the new W55 diagnostic. Its DOM fields distinguish: no Media DOM node, no src attribute, blob/MediaSource, other direct source, or an exact CELIKOM match. Do not force green without proof.

## Hard boundaries

No Android, browser extension, backend, Yandex original files, audio engine, VPN recovery, entitlement authority, source routing, updater architecture, production signing or deployment. No broad audits or intermediate installers.

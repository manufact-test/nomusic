# W90 — Windows admin gain parity audit, 2026-11-13

Owner: all boosted CELIKOM tracks seem unboosted in Windows; Big City Life specifically drops mid-song while admin preview remains loud. Code-level result: this is a SYSTEMIC Windows gain gap; the separate sudden drop is NOT proven to have the same trigger.

## Proven pipeline
- Server PdoCatalogRepository selects track_replacements.gain_db. ResolveService returns bounded numeric gain_db. Admin audio-gain.js applies live Web Audio DSP **only to preview**. AudioController returns original audio_assets bytes under signed Range/ETag — no byte-level gain.
- Chrome extension replacement-player.ts applies numeric asset.gainDb using its Web Audio limiter; it needs the unmodified raw file.
- Windows before W90: GrantValidator.FromResolve ignored gain_db, SourceGrant lacked it. Native W22 file-info maps the approved raw audio_url but sets native Yandex **boolean** gain:false. This cannot implement arbitrary per-track numeric gain. Neither the stored setting nor the actual media stream was silently erased from server.
- Consequently all songs with nonzero gain_db CAN be quieter on Windows than in admin/Chrome. This is not proof of mid-song dip, and not evidence of changed storage bytes.

## Changes and limits
Branch experiment/windows-w90-boosted-tracks-gain-parity-20261113, original handoff ba46821aaee8f9750b725699d4b7db7656a2b0cc, rollback backup/windows-w90-pre-gain-parity-20261113.
W90 transports finite bounded one-decimal gain_db through typed Windows SourceGrant, defaults missing values to zero, rejects malformed grants. Native adapter emits only code+track ID GAIN_CONFIGURED_NATIVE_DSP_NOT_APPLIED on positive/negative gains in single/batch mapping; does NOT alter Yandex decoder, metadata gain bool, media URL, audio samples, volume, network rights, playback or entitlement. Tests cover positive/negative, zero, original, batch, malformed.
**This is a diagnostic/non-release contract correction, NOT an audible gain fix. Do not issue this as a stable installer.** Owner still has 0.24.32; 0.24.33 TEST has Windows CI green but no real-world listening/VPN validation.

## Next audio work
Achieve per-track dB gain WITHOUT a second independent player. Either validate existing Yandex decoded-output DSP on supported pinned build with real listening and no audio cut/duplicate connections, or build versioned, limited **Windows-only pre-rendered media variants** server-side (signed URLs/Range/ETag/clip/rollback/batch backfill). Preserve the Chrome original URL to prevent double gain. Never process all songs on-the-fly via Hostinger PHP or overwrite originals. Measure several +dB, -dB and 0dB songs and Big City Life before/after dip. Only then claim sound boost parity. Investigate separate VPN, false green «Ты», hiss and freezes independently (#52/#53/#54).


## Live DB audit (READ-ONLY, 2026-11-13)
Executed [Windows W90 SQL aggregate audit](https://github.com/manufact-test/nomusic/actions/runs/43434214069) with verified pinned SSH host/user and read-only transaction; job SUCCESS, no files, audio bytes, or rows mutated:
- active approved versions: **1493**
- with `gain_db > 0`: **1**
- with `gain_db < 0`: **0**
- with `gain_db = 0`: **1492**
- invalid gain values: **0**

The Windows code bug is universal for any nonzero admin gain, but the live active catalog currently contains **one** boosted song. This count does NOT establish the identity of that song, reset history, or settings for disabled/pending versions. Do not claim all 1493 songs were formerly boosted; identify the lone boosted row and audit prior edits only with read-only, privacy-limited access. Reproduction of Big City Life's mid-song volume dip remains separate/unverified. Issues #56 / #54.

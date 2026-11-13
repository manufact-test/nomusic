# W47 — Owner Windows 0.24.4 post-W45 CORS morning diagnostics

Date 2026-11-10. Evidence uploaded by owner: `4.txt` exported at 2026-11-10 07:19:12 UTC. **READ ONLY analysis; no runtime change, no installer, no new user action until audible playback verdict is known.**

## Confirmed from this morning's 07:17–07:19 UTC segment

- Installed GUI `0.24.4.0`, native module `0.24.4`, matching versions; `NativeIntegration=ACTIVE`, `BridgeStarted=true`, `Enabled=true`, `SignedIn=true`. The morning segment starts with `GUI_STARTED`, `BRIDGE_STARTED`, `START_ENABLED`; later `HOST_LOADED`, `RESOURCE_HOOK_ATTACHED`, `RENDERER_STATE_ON`. `YandexVersion=unknown` in TXT; do not infer exact deployed native Yandex version.
- Two unsupported/unapproved tracks `109388237`, `97416296` have `RESOLVE_MISS/GRANT_MISS`; the first has `SOURCE_ORIGINAL`. This is expected fallback, not a replacement failure.
- Three rights-approved tracks: `42498653`, `85025192`, `78608850`; all have `GRANT_FOUND/RESOLVE_APPROVED`, `SOURCE_MAPPED` or `SOURCE_BATCH_MAPPED` for genuine file-info.
- For all 3 approved tracks, **exactly one** independent audio probe reports `AUDIO_PROBE_HTTP_PARTIAL` (206), `AUDIO_PROBE_MIME_MPEG` and `AUDIO_PROBE_BYTES_MPTHREE`; this is substantive confirmation that the post-W45 live service delivers 32 initial bytes of a valid MP3-shaped signed source in the renderer's CORS/CSP context.
- The prior evening's `AUDIO_PROBE_FETCH_BLOCKED` events in the *historical section* are from 2026-11-09; there are **none for 2026-11-10**. That is consistent with W45 `music-application://desktop` fix, also verified independently in live HTTPS CI.
- Morning shows `MEDIA_REQUEST_SEEN` 9 times, **all** accompanied by `MEDIA_HTTP_UNVERIFIED`. Source `windows-companion/w23/renderer-entry.mjs` uses `PerformanceObserver(type:'resource')` for any CELIKOM audio URL and cannot distinguish fetches from the independent `audioProbe.run` versus real Yandex player request. **Do not claim real native player fetched 206.**
- No morning `MEDIA_PLAYING`, `MEDIA_PAUSE`, `MEDIA_ERROR` etc, but code only observes DOM `<audio>` and Yandex may use WebAudio; absence is **NOT_OBSERVED**, not proof of playback failure.
- Morning export stops at ~07:19:04 UTC for native renderer and ~07:19:10 UTC GUI: it shows no owner's subjective audible verdict and no decoded-data evidence.
- Old `SOURCE_SYNTHETIC_RESPONSE` records belong to earlier 2026-11-09 sessions, not the new morning segment. Source of current W22 adapter waits for original file-info; do not attribute prior synthetic responses to the morning trial.

## What is PROVEN / NOT PROVEN

**PASS** = signed tiny Range GET, correct audio MIME and MP3 magic, CORS reachable, mapping to original file-info response. **Still unproven** = distinct real Yandex media request 206/full Range, native source/decryptor/decoder acceptance, audible alternate audio, native Pause/Seek/Next and fallback after starting.

## Source-coded next issue if owner reports silence

- `windows-companion/w22/native-resource-adapter.mjs:toDownloadInfo` explicitly deletes `key/iv` and forces `codec`, `transport:'raw'`, `gain:false` in a patched genuine file-info envelope. Android cross-audit W46 notes genuine Android file-info is richer. It is only a plausible **second** problem, not proven root cause for Windows.
- In `windows-companion/w23/renderer-entry.mjs`, `MEDIA_REQUEST_SEEN` is emitted for `PerformanceObserver` on CELIKOM audio URLs; the **independent 32-byte probe itself** generates resource timing entries. Next diagnostic must separate probe requests from true player requests (without logging signed URLs), and classify actual native decoder acceptance safely, before modifying audio descriptor.
- If owner confirms no audio, compare privacy-safe original Windows file-info schema/decoder state and actual player fetch with 206; avoid blindly copying plaintext key/iv or fabricating metadata. Native original fallback should remain fail-safe. Distinct W45 CORS fix stays deployed.

**Current manual gate:** Ask the owner only: **Did a substituted track actually play after W45 or did Yandex still stop / play original?** No repeat installation requested; `4.txt` already gives transport proof.

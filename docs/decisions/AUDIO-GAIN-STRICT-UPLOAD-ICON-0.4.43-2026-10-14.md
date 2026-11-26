# Audio mixer and owner feedback — 0.4.43 (2026-10-14)

Owner authorized an admin loudness slider with preview/save/reset and chose to
adjust Papirosy himself. No new edit to real audio or manual gain choice performed.

## Scope

- Upload screenshot was 183720ms original, 180872ms file: 2848ms difference,
  below previous 5000ms hard block but above actual 1500ms playback tolerance.
  Latest owner intent: prevent unsuitable submissions. Hard client/server block
  now uses >1500ms in both directions; exactly1500ms allowed. >5000ms additionally
  gives stronger explanatory text. This boundary change disclosed before work.
  Original/file times use whole m:ss, difference uses whole seconds; validation
  remains millisecond-precise. Server uses stored duration, then row-lock recheck.
- Toolbar uses authoritative popup target rather than any other healthy tab.
  Unhealthy pulse turns gray before waiting for authorization; offline resets
  clear icon. Popup mark/status also reflect actual errors/suspension/startup
  state. Existing manual Stop/Return, heartbeat/access authority unchanged.
- Additive migration018: per-replacement gain_db DECIMAL(4,1), default0.
  Owner/moderator gain save validates -12..12dB, CSRF and optimistic prior gain,
  row lock, audit. Viewer has read-only adjusted preview. Shared AudioAsset,
  music bytes, timing, moderation and signed URL version untouched.
- Admin slider immediately previews chosen gain, reset sets0, Save persists it.
  API includes bounded gain; legacy absent field means0, malformed/out-of-range
  field rejected. Extension uses gain only on replacement audio. Default0 keeps
  former direct-media path. Nonzero gain uses Web Audio with dynamic peak
  limiter, makeup compensation and final0.98 ceiling; preview and player DSP
  canonical sources identical. Context/load failures fail open to original.
  Destroy closes/disconnects audio context. Explicit Start refreshes resolver
  so saved gain applies on next replacement without waiting for cache expiry;
  currently playing version is unaffected, signed ranges not invalidated.

## DSP reference

Web Audio fixed makeup gain definition:
https://webaudio.github.io/web-audio-api/#computing-the-makeup-gain
For threshold=-1dB/knee0/ratio20 the fixed boost is0.57dB; compensate it to
preserve intended quiet-signal gain. Initial native test detected this actual
amplitude discrepancy; corrected in both preview and player, assertions kept.
Browser harness also corrected transpiler-format comparison, real decoder wait,
and disposable profile shutdown; no production permission/guard weakened.

## Validation

228 extension tests PASS, including selected-tab error/recovery, gain bounds,
1500/1501ms boundaries, screenshot case, direct form submission/reselection.
Native Chrome38626227616 PASS: offline measured boost/attenuation/peak ceiling,
real decoded MP3 media playback with gain, volume/mute/cleanup and slider/reset.
Full MySQL/native CI38626234285 PASS: gain POST/CSRF/viewer denial/stale-save/
reset; signed version/AudioAsset unchanged. MariaDB38624943927 PASS.
Final CI38626650987 SUCCESS; configured private Chrome38626640919 attempt2
SUCCESS (first attempt timed out in unchanged support browser harness; retry
passed all support and gain tests). Guarded deploy38626641678 SUCCESS, release
0.4.43-ab704439fe3c108250a890172b93c32978ff27dc. Migration018 checksummed/rerun,
private environment and all22 audio objects preserved, isolated file/MySQL
restore PASS. Live read-only audit: gain controls and migration PASS, 2 ordinary
tickets and1 song report retained, actionable duration alerts0, Papirosy200829ms
andgain0dB unchanged, both earlier repaired songs preserved. Owner UI/audio
acceptance pending.

Owner package CELIKOM-0.4.43-full.zip SHA256
625e9ecb744d796d8253505076127a2cad839b2ee2eca92c9c7aceb0e430d809.
PR6 remains OPEN/unmerged, Issue7 OPEN. No real music gain preset, emails or
account/trial/session/promo mutations performed.

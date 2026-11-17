# CELIKOM Android A1 — NAV24 owner phone result and NAV25 bounded non-EOS sample gate (18 Nov 2026)

## Authoritative owner diagnostic — private TXT stays out of GitHub

Owner supplied `CELIKOM-A1-Diagnostics-1794954950264.txt`, read locally in the conversation. The current (not older rotated NAV23) marker is `NAV_V24_EXACT_AUDIO_TYPE1_STATE2_ENGINE_HOLDER_READONLY`. **Do not commit/upload raw owner TXT or any private contents.**

The original Yandex Music native 2025.10.4 plays normally (pause/seek/Next work); owner reports no playback problems. Only CELIKOM alternate audio is missing.

Actual NAV24 on-phone summary:
- Original `RENDERER_TYPE_STATE_ACCESS=REGISTERED`. All previously installed `QUEUE_SCOPE`, `STREAM_ATTACH`, `SAMPLE_READ`, `STREAM_DETACH`, `SECONDARY_CALLER`, `ENGINE_HOLDER_SCOPE` = `REGISTERED`.
- `ENGINE_HOLDER_SCOPE_ENTER=FEW`, `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW`, `DIFFERENT=NONE`, `UNAVAILABLE=NONE`.
- `ENGINE_HOLDER_READ_RETURN_MINUS4=MANY`, `MINUS5=FEW`, `MINUS3=FEW`, `OTHER=NONE`; `READ_RETURN_LINK_LOST=NONE`.
- `ENGINE_HOLDER_RENDERER_TYPE1=MANY`, `TYPE_OTHER=NONE`, `ENGINE_HOLDER_TYPE1_STATE2=MANY`, `ENGINE_HOLDER_TYPE1_STATE_NOT2=MANY`, `TYPE_STATE_UNAVAILABLE=NONE`.
- **Strict holder+attached-stream+type1+state2 return cohort**: `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4=MANY`, `MINUS5=NONE`, `MINUS3=NONE`, `OTHER=NONE`.
- The old independent `QUEUE_SCOPE_ENTER=NONE` and `QUEUED_HOLDER_ATTACHED=NONE` continue to describe a different helper; do not treat as a playback regression.
- `NATIVE_TRACK_FLOW_EMIT=FEW`, `FLOW_TRACK_SAME_OBJECT=FEW`, `TRACK_WRAPPER_LINK=MANY` (track metadata route). `EXO_READ_POSITIVE=MANY` (a separate source path). **Neither is proven same selected track/album/edition → active renderer.** `WRAPPER_MAIN_SOURCE=NONE`, `TRACK_SOURCE_READ_LINK=NONE`, `TRACK_SOURCE_ALBUM_READ_LINK=NONE`.
- `IDENTITY_STATUS=STRUCTURAL_ONLY`; `CELIKOM_REPLACEMENT=NOT_CONNECTED`. This is not an audio substitution acceptance.

**Interpretation:** NAV24 establishes active Media3 type-1/state-2 renderer with a same-reference holder/stream returning original `b.g=-4` often. **-4 is a buffer-read result but can represent EOS; aggregated returns do not prove non-EOS samples, audible PCM or the selected Yandex song.** No title, album, edition, stream bytes, account data or private identifiers needed in this next stage. AppMetrica exception constructor categories are not evidence of crashes.

## NAV25 targeted next stage

New code on the same exclusive working branch retains the exact NAV24 engine-holder/renderer/stream type-state guard. After a single untouched original `b.g(iA9,RF2,int)` and only in the bounded existing sample window, optionally resolve the original `RF2` inherited public `isEndOfStream()Z` accessor. It reads ONLY a boolean on the supplied original buffer after the call; never reads payload or alters arguments, return, data, sound, signed Yandex or engine lifecycle.

Runtime accessor can be absent/obfuscated: `BUFFER_EOS_ACCESS=NO_HOOK` and `ENGINE_AUDIO_TYPE1_STATE2_BUFFER_UNAVAILABLE` will then count, **not** falsely classify a sample. On strict type1/state2 `-4` with exactly matching holder/stream, classify `BUFFER_NON_EOS`, `BUFFER_EOS`, `BUFFER_UNAVAILABLE`. No classification for other return values, wrong renderer kind, not-started state, mismatched stream, stale detached stream, or unregistered reflection. Java JVM cases cover positive, EOS, missing, wrong state/stream/detach and privacy invariants.

This stage is **read-only**. Even a non-EOS sample is not by itself sound on the speaker or the currently selected title/edition, and MUST NOT unlock Stage B. Continue remaining selected-track/album/edition linkage and authorized CELIKOM replacement after owner NAV25 diagnostic. Do not confuse JNI/Exo factory read counters with the same renderer's media item identity.

Working repo: `manufact-test/nomusic`.
Only working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
Pre-NAV25 exact backup: `backup/android-a1-nav24-owner-realphone-before-nav25-buffer-eos-20261118` @ `710e6ffd90f058f1b65391df78919bc4cb74458a`.
Original publisher Yandex and existing NAV24 verified APK in personal ChatGPT Library remain intact.
NAV25 requires a successful new owner-signed Android13 ARM CI **and verified Library upload** before user is told to test. No success claims or substituted GitHub Actions download links.

**Do not alter** stock Yandex 2025.10.4, the existing A1 architecture, Test.50, Windows/browser/server, normal playback, nor any account state.

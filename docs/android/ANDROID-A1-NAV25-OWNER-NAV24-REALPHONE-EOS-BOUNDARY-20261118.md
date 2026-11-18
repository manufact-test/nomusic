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


## Signed NAV25 and verified personal Library release — FINAL

- Exact native ARM13 publisher-original-first, owner-signed one-time CI **#44193129891 SUCCESS**, source/workflow HEAD `8b31f68005ca84b40d1ce1104424132d9c38bd12`.
- NAV25 JVM model CI **#44192983731 SUCCESS**. Original NAV24 baseline signed APK and all previously accepted versions untouched.
- Owner signed APK: **71,475,180 bytes**, **SHA-256 `5757472158cf83899ceddf6f27c4281bd5d020085bdefcb581906bc19b76581d`**. Extracted from successful CI artifact `CELIKOM-A1-NAV25-Owner-Started-Audio-Buffer-EOS-20261118`.
- Owner certificate decoded from `META-INF/OWN-KEY.RSA`, SHA-256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` exactly matches NAV24 accepted signer. Embedded publisher `assets/lspatch/origin.apk` SHA-256 **`1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`**, unchanged from NAV24.
- Personal ChatGPT Library **uploaded, independently listed and downloaded back**. SHA and all bytes compared with original signed CI APK: **`LIBRARY_NAV25_BYTES_IDENTICAL=true`**.
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV25-Started-Audio-Buffer-EOS-ReadOnly-20261118.apk`
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV25-Инструкция.txt`
- Signed code reserve: `backup/android-a1-nav25-started-audio-eos-signed-code-ci-green-20261118` @ `8b31f68005ca84b40d1ce1104424132d9c38bd12`.
- Latest code and docs branch remains `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. No user phone NAV25 diagnosis received yet. **CELIKOM replacement NOT_CONNECTED** until a subsequent on-device proven selected-track identity and actual replacement integration.

**Owner's next check:** install NAV25 from verified personal Library **over NAV24** without data clear/uninstall; regular listening 2–5 tracks, export TXT, report whether original Yandex remains normal. Parse `BUFFER_EOS_ACCESS`, `ENGINE_AUDIO_TYPE1_STATE2_BUFFER_NON_EOS/EOS/UNAVAILABLE`, previous strict holder+type+state statuses, `READ_RETURN_LINK_LOST`, and `CELIKOM_REPLACEMENT`. If getter reports NO_HOOK, never infer non-EOS; research an exact signed 2025 flags method before further runtime changes.

## NAV25 owner phone diagnostic — 18 Nov 2026

The latest export identifies NAV25 as active; an older NAV24 marker remains in the retained log. All previous renderer checks are registered. Holder/stream matches are FEW, mismatches and lost links NONE; started audio renderer reads and the -4 return cohort are MANY. The new EOS accessor reports NO_HOOK, with NON_EOS=NONE, EOS=NONE and UNAVAILABLE=MANY. These bins represent missing observation, not a claim that audio buffers are empty or playback has failed. Selected-track linkage is unproven; replacement remains NOT_CONNECTED. No runtime changes or new APK were made. Existing signed checkpoints are preserved. Raw owner diagnostic stays private.

Separate account/Passport telemetry is present in the same diagnostic export, but it is not audio evidence and contains no exported token values. It is excluded from this audio investigation; do not inspect or instrument credential contents. This is not a reason to abandon the existing read-only audio research.

## Latest owner NAV25 phone TXT — current state and next target

Private file `CELIKOM-A1-Diagnostics-1794984522604.txt` received and analyzed; never commit raw TXT.

- `DIAGNOSTIC_BUILD=NAV_V25_EXACT_AUDIO_TYPE1_STATE2_BUFFER_EOS_READONLY;ACTIVE` is present (NAV24 appears only as historical rotated entries).
- All renderer hooks remain registered except `BUFFER_EOS_ACCESS=NO_HOOK`. Thus `ENGINE_AUDIO_TYPE1_STATE2_BUFFER_NON_EOS=NONE`, `...BUFFER_EOS=NONE`, `...BUFFER_UNAVAILABLE=MANY`. This only means the optional public accessor did not resolve; it does not indicate empty buffers or playback failure. Do not spend another APK cycle repeating the same public-name lookup.
- Runtime engine-holder/renderer link still present: `ENGINE_HOLDER_SCOPE_ENTER=FEW`, `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW`, `DIFFERENT=NONE`, `UNAVAILABLE=NONE`; `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4=MANY`; `READ_RETURN_LINK_LOST=NONE`. Original playback remains user-reported normal.
- Stage B source chain is still disconnected: `NATIVE_TRACK_FLOW_EMIT=FEW`, `NATIVE_TRACK_SOURCE_REQUEST=FEW`, `FLOW_TRACK_SAME_OBJECT=FEW`, `TRACK_WRAPPER_LINK=MANY`, but `WRAPPER_MAIN_SOURCE=NONE`, `WRAPPER_DESCRIPTOR_LINK=NONE`, `TRACK_DESCRIPTOR_FACTORY_LINK=NONE`, `TRACK_FACTORY_SOURCE_LINK=NONE`, `TRACK_SOURCE_OPEN_LINK=NONE`, `TRACK_SOURCE_READ_LINK=NONE`, `TRACK_SOURCE_ALBUM_READ_LINK=NONE`; `CELIKOM_REPLACEMENT=NOT_CONNECTED`. Separate Exo factory/open/read counters are MANY but are not same-track proof.
- No new runtime code or APK was created after NAV25. Do not ask owner for another install now.

**Next engineering target (not EOS and not another constructor census):** the static chain is already proven end-to-end: TrackWrapper `LtCa` → `LiLb` → native Player source setter → playlist holder `LuIb` → `Lo96` MediaPeriod → `Lup1/Lxh6` stream array → exact `LmQ8.try/new` renderer stream-reference comparator → native renderer attached stream/read. The exact next unresolved gate is the *runtime outcome* of the already-proven comparator, on the same renderer that is type1/state2 and continues into original `b.g` reads. Design one bounded, read-only NAV26 witness at `LmQ8.try(Lxh6,k)Z` and/or `LmQ8.new(Lxh6)k`: call the original exactly once, preserve its return, record only finite true/false or matched/unmatched counters, and retain weak in-memory object identity only long enough to correlate the exact `Lxh6` holder + renderer with existing attach/read evidence. Distinguish active started audio renderer from prefetch/other renderer and queue transitions; no raw objects, field values, metadata, IDs, URLs, DataSpec, credentials or audio bytes in output. Reuse the existing exact `Lxh6` stream-array and renderer `k.while()` proof; do not repeat the static chain or EOS accessor probe. Only after this runtime comparator outcome is correlated to current selection/queue generation should the next selected-track/album/edition gate be considered. No source swap or replacement APK until the witness is justified, tested and CI-green. Keep original Yandex behavior unchanged.

## NAV26 comparator observer implementation — JVM green, signed ARM pending

- NAV26 adds an exact hook for the already signed 2025 `LmQ8.try(Lxh6;Landroidx/media3/exoplayer/k;)Z` method. It calls the original once, preserves its boolean unchanged, then reads the already-proven renderer attached-stream getter and retains only weak in-memory identity references to holder/renderer/stream. It exports no object values or metadata.
- Both raw comparator return outcomes are recorded neutrally as TRUE/FALSE; **no assumption that TRUE means equality** is baked into the model. On a later exact type1/state2 renderer read, a result is correlated only if holder, renderer and stream references all match. Comparator evidence is invalidated on renderer reattach and detach to prevent stale reuse.
- JVM regression CI **#44259704837 SUCCESS** after the reattach invalidation fixture. Pre-NAV26 code backup: `backup/android-a1-nav25-owner-signed-library-verified-final-20261118`; NAV26 JVM-green code backup: `backup/android-a1-nav26-comparator-identity-guard-jvm-green-20261118` @ `19c73c433eee23359566c3df2a3a0e5e52756b9c`.
- One-shot signed Android13 ARM NAV26 CI **#44259704834 IN PROGRESS** at the time of this update. Do not ask owner to install until this exact run succeeds, APK signer/hash are verified, and file is independently present in personal ChatGPT Library. Older NAV26 attempts at earlier SHAs are not release candidates.

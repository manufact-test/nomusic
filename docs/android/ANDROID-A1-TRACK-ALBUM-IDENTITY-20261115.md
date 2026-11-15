# CELIKOM Android A1 — Track/Album identity bridge

**Дата:** 15 ноября 2026  
**Репозиторий:** manufact-test/nomusic  
**Рабочая ветка:** experiment/android-a1-metrica-init-state-observer-arm13-20261112

## Checkpoint

- Runtime code commit: a655712d210189f3bc611847235de3ed4d985c1a.
- Branch HEAD before documentation update: 90f8ea394e1ac4168aa63f976e17fd18eb24befb.
- Current clone-green / publisher-first-green backup: backup/android-a1-track-album-publisher-first-ci-green-20261115 @ 90f8ea394e1ac4168aa63f976e17fd18eb24befb.
- Pre-large-push rollback: backup/android-a1-track-album-reference-pre-large-push-20261115 @ e0740cf224b34d3260822fa2248a8b136feac1e5.

## Static signed DEX findings

[Audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959) **SUCCESS**. The output is deliberately bounded and does not disclose private method/field names.

1. The native Track model declares one field typed as Album.
2. Two Track constructors accept exactly one Album-typed argument. Static inspection did **not** prove a direct write of that same argument to the Track instance's Album field (constructors_storing_same_album_argument_on_track = 0). Do not claim the constructor alone proves the model field value.
3. One exact Track copy-method shape accepts a Track and an Album and returns a Track. It reads the source Track's Album field; static register tracing finds a path that passes the Album argument to a Track constructor and returns a new Track. This is an **argument-to-returned-Track candidate**, not a proof that every branch uses that argument.
4. The copy method and constructor signatures give a safe read-only observation point: capture only the Album-typed argument and resulting Track object after the original method returns. Never read Track fields or Album values directly.

## Runtime observer added

Files:
- exit-callsite-witness-module/.../StageBAudioEvidence.java
- exit-callsite-witness-module/.../ExitCallsiteWitness.java
- ci/test_a1_stage_b_audio_evidence.py
- ci/a1_metrica_witness_private_parser.py
- ci/test_a1_metrica_witness_private_parser.py

Hooks:
- AUDIO_NATIVE_TRACK_ALBUM_HOOK: registers the two constructors that contain exactly one Album parameter; synthetic constructors with no Album parameter are ignored.
- AUDIO_NATIVE_TRACK_ALBUM_COPY_HOOK: registers the exact Track copy method and captures its returned Track plus Album argument after the unmodified original method returns.
- Both hooks are protective: observer errors do not replace or suppress the vendor method result/exception.

Identity handling:
- Only weak references to Track and Album objects are retained; comparisons use Java ==.
- No Track field reflection, Album ID/title/name, URLs, DataSpec, account values, credentials, headers, tokens or audio buffers are read or retained.
- Track→Album association conflicts revoke the Album link. The map is bounded to 32 Track identities; source links remain bounded to 16.
- Album identity is propagated through:
  Track constructor/copy result → Track Flow → wrapper → descriptor → factory → DataSource instance → successful open → positive read.
- TRACK_SOURCE_ALBUM_READ_LINK is only marked after the exact linked source had a successful open() and a positive read(). Reopen/close and identity conflicts invalidate the evidence.
- The read hot-path scan remains bounded to 256 inspections per source/reopen window; TRACK_SOURCE_READ_SCAN_EXHAUSTED means sampling ended, not that a source is absent.

New summary counters:
- TRACK_ALBUM_CONSTRUCTOR_LINK
- FLOW_TRACK_ALBUM_LINK
- TRACK_WRAPPER_ALBUM_LINK
- TRACK_DESCRIPTOR_ALBUM_LINK
- TRACK_FACTORY_ALBUM_LINK
- TRACK_SOURCE_ALBUM_LINK
- TRACK_SOURCE_ALBUM_OPEN_LINK
- TRACK_SOURCE_ALBUM_READ_LINK
- TRACK_ALBUM_IDENTITY_CONFLICT

The summary is now 53 rows; AUDIO_STAGE_B_STATUS is the final row at index 52.

## CI validation

- [Signed Track/Album static audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959): **SUCCESS**.
- [Clone-only native ARM13 #43703211359](https://github.com/manufact-test/nomusic/actions/runs/43703211359): **SUCCESS**, 25/25 stable observations, both Album hooks and all existing Track/Exo source hooks REGISTERED.
- [Publisher-first native ARM13 #43703211345](https://github.com/manufact-test/nomusic/actions/runs/43703211345): **SUCCESS**, original publisher app 16/16 splits and clone co-installed, 25/25 stable observations, no suppression, both Album hooks and all Track/Exo source hooks REGISTERED.
- Final CI verdict: METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO.
- stage_a = NO_GO, stage_b_current_player_album_edition_attested = false, audio_or_account_tested = false.

## What this does NOT prove

- Track Flow may include queued, prefetched or download-only tracks; it is not proof of the current audible selection.
- The Album-typed constructor/copy argument association is not proof of edition/generation semantics. The Track model has other nested metadata types, but their meanings are not yet established.
- A positive Exo DataSource read proves source activity only. It does not prove that this is the current player item or that the bytes reached the active decoder.
- The separate signed 2025 audio inventory found two private MediaDataSource implementations and one MediaExtractor.setDataSource(MediaDataSource) sink candidate. It did not prove a same-object chain from that source through readSampleData to MediaCodec input/AudioTrack output. Do not assume MediaExtractor is the music decoder solely from registration.
- No audio/account playback was tested in CI.

## Next work

1. Identify the current selected Track state, distinguishing it from queue, prefetch and download work. Use identity-only observations; no field-value reads.
2. Identify the exact edition/generation object and its relation to the selected Track/Album. Use signed DEX structure and method flows; do not guess semantics from obfuscated names.
3. Trace the same source identity to the actual decoder input/renderer. Establish an object-level path, not merely class-level hook registration.
4. When the owner supplies a diagnostics file, read the nine Album counters alongside open/read/close counters. Distinguish NONE, conflict, scan exhausted and hooks not registered.
5. Keep Stage A **NO-GO** until current Track + Album + edition + decoder identity and actual audio are demonstrated.

Do not modify Test.50, frozen A1, Windows, browser extension, backend, original publisher app or account. Do not ask the owner to install/test a new APK unless a specific owner-side measurement is genuinely required.

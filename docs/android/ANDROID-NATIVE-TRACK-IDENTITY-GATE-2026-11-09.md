# CELIKOM Android — trackId/edition/generation correlation (09.11.2026)

Goal: A rights-approved source must be selected for the same **currently-playing**
track ID and exact edition in the **single** original Yandex player, before its
native decoder prepare. Wrong ID or delayed radio/Next result must NEVER
replace a different song.

Static publisher-signed #170gpr evidence from prior CI:
- `DownloadInfoApi.b` publishes `tracks/{trackId}/download-info`; caller
  `Ln39.a` calls `Ldjv.a():String` immediately before invoking
  `DownloadInfoApi.a`. `Lhee.a(Ldjv,Ls3p,Lc82,Li77)` is separately the
  known native `FileInfoApi.a` caller, establishing a **candidate common
  identity type**, not proof of playback identity. Source:
  CI 42609925869 (signed DEX invoke neighborhood).
- Native FileInfoApi source request has multiple String parameters of
  unknown semantics and the DTO itself has no independently proven track ID.
- Hence static traces DO NOT establish `trackId/edition → native MediaSource`.
  Never identify the song solely by display title, MediaSession ID or download
  route; no made-up token/ID joins.

New separate pure-Java `NativeTrackIdentityGate` is a **MODEL ONLY** of
binding (native playback generation, exact ID+edition) → (trusted FileInfo
request) → (descriptor at true pre-prepare boundary). Mismatch permanently
rejects that generation, late Next callbacks are ignored, no duplicate
commit, unknown ID or edition => ORIGINAL. It does not perform observation,
hook a decoder, access an account, or modify media.

Local independent Java 17 run: `javac --release 17` and
`NativeTrackIdentityGateTest` produced **10,015 assertions PASS**,
including 2,500 rapid Next cycles and RASKOL/«Дым» IDs.
This validates only the model, **not** a native Yandex audio result.

Native runtime blocker remains: macOS ARM emulator [42672246229](https://github.com/manufact-test/nomusic/actions/runs/42672246229)
failed `HV_UNSUPPORTED` before application install, even with
`-accel off`. New Actions 42673655477 and 42674235050 returned
workflow-level `failure` with no jobs/logs, so their new track-identity
static scan is still UNTESTED and its outputs must not be trusted yet.

Do NOT install any patched Yandex on the owner's HONOR, disable Play Protect,
collect login credentials, release vendor APKs, or modify accepted Test.50.
Only connect this gate to real playback after a lawful, separated native
read-only witness demonstrates identity and genuine decoder ownership.

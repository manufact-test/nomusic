# W127 — Reconcile current-decoder proof after queue identity race — 14 November 2026

- Repository: `manufact-test/nomusic`.
- Product: the one existing CELIKOM Windows application.
- Working branch: `main` only.
- Exact pre-W127 rollback snapshot: `backup/windows-main-pre-w127-current-decoder-witness-race-20261114` @ `4b7d2277d98986d8d4ab0ed9ba42a76fc25da810`.
- W127 implementation commit: `4fe42d745b6708524c65eb4f9855e026f314fefa`.
- W127 regression-test commit / code HEAD: `7e4c8268cba30f781a3fa091d9657718ec463b66`.
- Main CI [43603865004](https://github.com/manufact-test/nomusic/actions/runs/43603865004) — **SUCCESS**.
- Windows integration CI [43603864999](https://github.com/manufact-test/nomusic/actions/runs/43603864999) — **SUCCESS**.

## Problem found

The native CDP observer can receive the exact decoder `kUrl` and `kIsPlaying=true` before the Yandex renderer exposes the new current queue track ID to the 2.2-second status sampler.

Before W127, `capturePlayerProperties` only created the verified witness when the queue ID was already present and matched at the instant of the CDP event. If the queue identity arrived afterwards and Yandex emitted no further decoder-property event, the valid current CELIKOM decoder could remain neutral indefinitely. This was a false-negative ordering race, not evidence that the audible source was wrong.

## Change

1. The native host retains bounded per-view decoder-player state, including the validated source track identity, source-observation time, playing state and gain-variant metadata.
2. On the existing host status tick, after reading the current Yandex queue track, it reconciles that current identity against the retained CDP decoder state. The source must still be marked playing, match the exact current track, and originate from the already validated signed CELIKOM resource/grant.
3. The source observation must be recent (under ten minutes) and fall within the three-second queue-observation allowance for the existing 2.2-second status sampling cadence.
4. When the late queue identity makes the proof valid, the host emits the existing source-match diagnostic once, sends the verified-only heartbeat and calls the existing `__celikomBridgeNativeConfirmedCurrentSource` hook. That hook only cancels a still-pending redundant source-recovery reload; W127 does not issue a player reload or control playback.
5. Player destruction and CDP detach continue to invalidate the witness. Detach also clears the retained per-view decoder map.

## Regression coverage

The new W127 native-host test deliberately delivers signed `kUrl` + `kIsPlaying=true` before the current queue ID exists. It asserts:
- no source proof is emitted while current queue identity is unknown;
- after the exact current track ID arrives, the retained decoder state is reconciled and one source proof is emitted;
- the verified-only heartbeat is sent;
- the existing pending-recovery suppression hook is notified;
- signed media URLs remain absent from diagnostics.

The complete W22/W23/W60 original-source, VPN, 403 and audio regression step passed. W15 entitlement/login/native-state tests, GUI warning-as-error build, Supervisor build and the remaining Windows integration gates also passed. Main CI passed on the exact W127 test commit.

## What this does NOT close

- **#52 remains OPEN.** W127 fixes the CDP/queue event-order race. It does not prove that the owner hears the CELIKOM alternative on «Ты»; actual playback acceptance is still required. A decoder-source witness is not speaker-level acoustic proof.
- VPN A→B recovery code from W89/W94 is present and CI-tested, but actual reconnect time and uninterrupted playback on the owner's PC remain unverified.
- #53 still needs the owner's safe Task Manager snapshot and the exact elevated-rights prompt source; do not guess or request administrator access.
- #54 remains a separate Big City Life mid-track volume-drop diagnosis.
- #56 has server-side sidecar and signed Range identity verification, but Windows loudness/headroom/clipping, seek, Next and crossfade acceptance remain open.
- #57 and #58 remain separate audible recovery/original-source issues.
- All six owner issues (#52, #53, #54, #56, #57, #58) remain OPEN.

No installer was built. No production media, original audio, browser extension, Android code, entitlement policy, VPN behavior or updater trust configuration was changed. The production updater remains dormant until the real approved feed origin, P-256 public key and Authenticode signer fingerprint are provisioned.

Continue from the current live `main`; preserve the one-product/main/backup/no-intermediate-installer contract in W119 and the authoritative top of `NEXT-CHAT.md`. Do not close #52 from CI alone.

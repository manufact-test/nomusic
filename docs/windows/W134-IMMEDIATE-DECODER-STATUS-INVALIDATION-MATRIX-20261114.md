# W134 — Immediate downgrade coverage for every decoder-proof invalidation — 14 November 2026

- Repository: `manufact-test/nomusic`.
- Product: the one existing CELIKOM Windows application.
- Working branch: `main` only.
- Change type: regression tests only; W133 runtime behavior unchanged.
- Exact pre-W134 backup: `backup/windows-main-pre-w134-verified-status-invalidation-matrix-20261114` @ `63b3a155bde732d527cfa57e5280bae69b3acbb6`.
- W134 regression-test/current code-test HEAD: `d6c091fb109baeaa1690b15ca3f90d7c914a279a`.
- Main CI [43609116940](https://github.com/manufact-test/nomusic/actions/runs/43609116940) — **SUCCESS**.
- Windows integration CI [43609116972](https://github.com/manufact-test/nomusic/actions/runs/43609116972) — **SUCCESS**.

## Coverage added

W134 extends W133's immediate neutral-heartbeat downgrade coverage from source-left to every invalidation path:

1. Current exact signed decoder becomes `NATIVE_SOURCE_VERIFIED`.
2. The current decoder is then independently invalidated by one of:
   - `kIsPlaying=false` (pause);
   - `Media.playerDestroyed`;
   - `Media.playerErrorsRaised` for the exact current decoder;
   - CDP observer `detach`.
3. Each path must immediately send `NATIVE_MAPPING_ACCEPTED`, without waiting for the regular 2.2-second status sampler.
4. Heartbeat payloads and diagnostics must not contain the signed media URL.

All four subtests passed as part of the full W22/W23/W60 original-source, VPN, 403 and audio regression step. Main CI and the full Windows integration CI both passed.

## Acceptance boundary

W134 is test-only and does not change playback, player controls, source reloads, queue, URL handling or audio. It verifies the W133 status downgrade paths; it does not establish audible output.

**Issue #52 remains OPEN** pending owner-PC proof that «Ты» (13 карат) actually plays the alternate source. No installer was built. Continue from live `main`; preserve the one-product, exact-backup, no-intermediate-installer rules.

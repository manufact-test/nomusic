# W131 — Invalidate stale source mapping after verified decoder source-left — 14 November 2026

- Repository: `manufact-test/nomusic`.
- Product: the one existing CELIKOM Windows application.
- Working branch: `main` only.
- Exact pre-W131 rollback snapshot: `backup/windows-main-pre-w131-source-left-map-invalidation-20261114` @ `9eb710d1227f56419d6e9f35b34b44b7941ef8ae`.
- Runtime fix: `5fb5f32d0364d476889bf56d0f8e8fc0e38d71b2`.
- Regression test: `2f41091d1af072483ed5c79782958002b0ee2101`.
- Current code/test HEAD: `2f41091d1af072483ed5c79782958002b0ee2101`.
- Main CI [43606490844](https://github.com/manufact-test/nomusic/actions/runs/43606490844) — **SUCCESS**.
- Windows integration CI [43606490908](https://github.com/manufact-test/nomusic/actions/runs/43606490908) — **SUCCESS**.

## Change

The native host calls `__celikomBridgeNativeRecoverSourceLeft(trackId)` only after passive CDP previously confirmed that the current Yandex decoder was playing the exact CELIKOM signed source and then observed it leave that source.

The renderer now invalidates the old per-track mapped-source marker immediately after validating that callback's current track identity, before checking whether CELIKOM is still enabled. If a VPN/entitlement state transition races with source-left recovery, the transition no longer mistakes the stale historical mapping for an active CELIKOM decoder and does not issue a redundant `QUALITY_CHANGE` reload of a track that has already returned to Yandex original.

When CELIKOM remains enabled, the existing bounded source-recovery path still runs unchanged and can reapply a fresh authenticated grant. No entitlement bypass, source selection rewrite, new player, server change or audio processing change was introduced.

## Regression coverage

- New W131 renderer integration test maps the current track, simulates the verified CDP source-left callback, then immediately applies the state-off transition.
- It verifies no second `QUALITY_CHANGE` reload, no loss of playing state or position, and the expected no-reload transition.
- Existing W99 verified source-left recovery test still passes.
- Full W22/W23/W60 original-source, VPN, 403 and audio regression step passed; W15 entitlement/login/native-state tests and the complete Windows integration workflow passed.

## Acceptance boundary

This removes one CELIKOM-generated redundant reload when a verified current decoder has already left the CELIKOM source. It does **not** prove the owner's VPN A→B switch is now free of every audible pop: Yandex/network buffering may still contribute, and real playback on the owner's PC remains required. **Issue #58 stays OPEN** until that field acceptance is completed.

No installer was built. Continue from live `main`; keep the single-product, main-only, exact-backup and no-intermediate-installer rules.

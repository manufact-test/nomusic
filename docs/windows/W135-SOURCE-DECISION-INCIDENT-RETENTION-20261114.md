# W135 — Retain source-decision evidence in durable owner diagnostics — 14 November 2026

- Repository: `manufact-test/nomusic`.
- Product: the one existing CELIKOM Windows application.
- Working branch: `main` only.
- Change: diagnostics/archive policy and regression tests only; no player or audio behavior changed.
- Exact pre-W135 backup: `backup/windows-main-pre-w135-source-transition-incident-retention-20261114` @ `adc87e2d3358fb64fba0a760518374e7d88e56c5`.
- Implementation commits: `e8e482da6acbfc677823e754066baa14e6e7d48e`, `3045a9deaa7f87e031313741b64f4f9fbdd6e5c5`.
- Regression-test/final code-test HEAD: `5a40357d28f1a1cc4f467a16bfaaaf38aa530b3f`.
- Main CI [43610044707](https://github.com/manufact-test/nomusic/actions/runs/43610044707) — **SUCCESS**.
- Windows integration CI [43610044672](https://github.com/manufact-test/nomusic/actions/runs/43610044672) — **SUCCESS**.

## Change

W22/W23 already emits source-decision events with exact numeric track IDs, but those events were not all classified as durable incidents. A busy native event log could rotate them out before the owner or support exported diagnostics.

W135 adds the bounded, allowlisted source evidence to both the durable seven-day incident archive and the 15-minute automatic support snapshot:

- `SOURCE_ORIGINAL`, `SOURCE_UNKNOWN`, `SOURCE_ACTIVE_REPLACEMENT`;
- `NATIVE_ORIGINAL_SOURCE_*`, `NATIVE_UNKNOWN_SOURCE_*`, `NATIVE_REPLACEMENT_SOURCE_*`;
- current-source revalidation decisions;
- source-left decisions and bounded recovery scheduling;
- `PLAYER_DECODER_CELIKOM_SOURCE_MATCHED` for exact current signed-decoder evidence.

Only fixed event codes and validated numeric track IDs are stored. No URLs, signed query strings, tokens, audio data, or arbitrary error messages are added. Ordinary `NATIVE_CONNECTED` remains non-incident polling/status chatter.

## Regression coverage

W15 tests now verify:
- source classes and exact decoder proof qualify as durable incidents;
- ordinary connection status does not;
- ORIGINAL / UNKNOWN / ACTIVE_REPLACEMENT decisions survive more than 2,500 later native status polls in the support snapshot;
- the same events survive in the persistent incident archive and owner TXT export;
- secrets and signed URLs remain excluded.

Full W22/W23/W60 original-source, VPN, 403 and audio regression step passed. W15 entitlement/login/native-state contract tests passed. Both CI workflows are green.

## Acceptance boundary

W135 improves evidence retention; it does not change source selection, route recovery, player state, reloads, or audio. **#58 remains OPEN** pending real owner-PC VPN A→B playback acceptance. **#52 remains OPEN** pending owner-PC confirmation that «Ты» (13 карат) actually plays the alternate source. CI and decoder evidence are not speaker-level proof.

No installer was built. Continue from live `main`; keep the one-product, exact-backup, no-intermediate-installer rules.

# W118 — W98 exact post-stage identity and signed Range reconciliation

Date: 14 November 2026  
Repository: `manufact-test/nomusic`  
Product line: `main` only

## Exact code and verification

- Exact code/test HEAD: `228a9d66cd2f858a537ce37a773fe65820a4e964`.
- Exact pre-documentation backup: `backup/windows-main-pre-w118-docs-20261114` @ the same code SHA.
- Main CI [43592142890](https://github.com/manufact-test/nomusic/actions/runs/43592142890) — **SUCCESS**.
- Windows integration CI [43592142866](https://github.com/manufact-test/nomusic/actions/runs/43592142866) — **SUCCESS**.
- Stage 5 live integrity audit [43592142904](https://github.com/manufact-test/nomusic/actions/runs/43592142904) — **SUCCESS**.
- W90 live read-only gain inventory [43592142899](https://github.com/manufact-test/nomusic/actions/runs/43592142899) — **SUCCESS**.
- W98 private gain reconciliation [43592142876](https://github.com/manufact-test/nomusic/actions/runs/43592142876) — **SUCCESS**.

## What W118 closes

The previous W98 staging script fetched `inventory-after.json` but did not compare it with the initial inventory. A same-count replacement substitution or a source/version/gain change between the two reads could therefore escape the final manifest check.

Added `.github/scripts/hostinger-windows-gain-verify.mjs` and nine contract tests. The helper now requires exact identity continuity across:

- Initial and post-stage replacement ID set.
- Track ID, source version, admin gain, original source SHA-256, duration and source byte size.
- Persisted private sidecar SHA-256 and size versus the renderer metrics manifest.
- Live entitled resolver response: replacement/track/version/gain, source SHA-256, selected sidecar SHA-256, duration and source size.
- Signed HTTPS Range response: HTTP 206, verified ETag, audio/mpeg and a nonempty bounded byte range.

The remote live-verification response now returns the additional identity witnesses. The stage script passes both initial and post-stage inventory into the verifier before publishing the private manifest. Empty trailing TSV fields for an already-staged variant are preserved and parsed correctly.

## Exact live result

- W90 found 1,493 active approved replacements: **one active nonzero-gain row** and 1,492 zero-gain rows. No invalid gain values.
- Active nonzero row: replacement 37 / Yandex track 40371622 / admin gain +11.5 dB.
- Disabled «Папиросы» is not an active replacement and was not staged.
- W98 found the existing private sidecar and did not render or insert a new one:
  - `W98_EXISTING_VARIANT_VERIFIED replacement=37 track=40371622 gain=11.5dB`
  - `W98_GAIN_IDENTITY_RECONCILIATION_PASS count=1`
  - `W98_PRIVATE_GAIN_STAGE_PASS count=1 live_signed_range=206 manifest=private`
- The final successful run was retried after transient SSH connection timeouts from earlier runners. The failed attempts timed out before establishing SSH; no database or media operation ran in those attempts.
- Stage 5 rechecked the private snapshot, original media inventory and migration/schema invariants. Original audio objects remained unchanged; the live database was not restored or rewritten.
- Existing sidecar remained unchanged. No new `windows_gain_variants` row was required.

## What this does NOT close

- #56 is now **server-side sidecar and signed Range verified**, but real Windows acoustic QA remains open: loudness, clipping/headroom, seek, Next, crossfade and 403 recovery.
- #54 Big City Life mid-track volume drop remains a separate diagnosis.
- #52 «Ты», #53 Brave/Windows performance, #57 403→206 hiss, #58 original-track VPN switch and VPN reconnect still require separate owner-PC evidence.
- No Windows installer/ZIP was built or delivered in W118.
- The CELIKOM automatic updater remains dormant and **not production-ready**: production trust values are empty, no live signed feed is published, the main app has no trusted Supervisor launch callsite, and no real signed crash/rollback test has run.

## Next work order

1. Prepare exactly one coherent Windows QA EXE+ZIP from the current `main`, reusing the existing final-QA packaging path without replaying the old one-shot Hostinger deployment/migration request.
2. Verify installer metadata, ZIP structure/CRC, SHA-256 values and in-place upgrade/session/native integration preservation.
3. Deliver that one build for a consolidated owner-PC acceptance pass. Do not publish to the public stable feed or mass-roll out.
4. Keep #52/#53/#54/#56/#57/#58 and VPN reconnect separate in the owner QA checklist.
5. Return to the customer updater only after the owner accepts the coherent Windows build. Keep W117 trust/bootstrap dormant until genuine production pins and official feed are provisioned.

## Safety

- One CELIKOM Windows product, one active `main` branch.
- No new `experiment/*` branch, second product, intermediate customer installer or mass release.
- Do not replay the old Hostinger deployment request; current Stage 5 request is read-only `audit`.
- Do not ask the owner for another email, password, token or secret.
- Do not alter original `audio_assets`, browser-extension audio or Yandex originals.

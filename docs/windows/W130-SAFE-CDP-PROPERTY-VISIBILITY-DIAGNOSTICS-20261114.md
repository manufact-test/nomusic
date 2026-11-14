# W130 — Safe CDP property-visibility diagnostics — 14 November 2026

- Repository: `manufact-test/nomusic`.
- Product: the one existing CELIKOM Windows application.
- Working branch: `main` only.
- Exact pre-W130 rollback snapshot: `backup/windows-main-pre-w130-cdp-property-observability-20261114` @ `312d61a62fb4abcb779df539503adf4226818185`.
- W130 host diagnostic commit: `5acbcc2af1a6cee85ef96bc81ce45d56d2f90726`.
- W130 safe-export implementation: `06cc9dc495a44a290936971e1d2c966ded11b4f6`.
- W130 diagnostic fixture test: `f79322e6acf4b8d2e7d9ac61b05e75fb943151a4`.
- W130 native-host event-order/privacy test: `d834c1c007b7cd1a0f96c04e4e38012d899b9b62`.
- Final W130 clarification/test HEAD: `74b27a27c8f1560591ed9ae11c17f5fceb0d538e`.
- Main CI [43605388622](https://github.com/manufact-test/nomusic/actions/runs/43605388622) — **SUCCESS**.
- Windows integration CI [43605388482](https://github.com/manufact-test/nomusic/actions/runs/43605388482) — **SUCCESS**.

## Why

The earlier owner export could say `NativeMediaUrlExactMatchObserved=false`, but could not distinguish two different conditions:
- CDP Media attached but did not emit player-property events at all;
- player-property events arrived, but this Yandex build did not expose a `kUrl` property.

That distinction matters for #52: absence of an exact decoder URL must stay unverified, but the next diagnosis should reveal whether the field itself is exposed.

## Change

The passive native CDP observer now emits two one-time, URL-free events:
- `PLAYER_CDP_PROPERTIES_SEEN` — at least one Media player-properties event arrived;
- `PLAYER_CDP_URL_PROPERTY_SEEN` — a property named `kUrl` appeared.

Only property-name presence is recorded. The URL value, signed query, SID, token, request body and arbitrary player-property values are never logged.

The owner TXT export adds:
- `NativeDecoderPropertiesObserved`;
- `NativeDecoderUrlPropertyObserved`.

The automatic support snapshot includes the corresponding safe booleans and allowlisted event codes. Both events are retained in the bounded incident history. The export explicitly states that these flags indicate Media-domain field availability only — **not** current-track identity, decoder selection, audible playback or replacement proof.

## Regression coverage

- A native-host test sends `kIsPlaying` without `kUrl`: properties-seen becomes true while URL-property-seen remains false.
- It then sends a `kUrl` property and verifies URL-property-seen becomes true without exporting the URL, token or SID.
- Companion tests verify durable incident retention, TXT summary booleans, automatic support-snapshot booleans and the explicit non-proof disclaimer.
- The W22/W23/W60 original-source, VPN, 403 and audio regressions, W15 entitlement/login/native-state tests, GUI warning-as-error build, Supervisor build and all remaining integration gates passed.

## What this does NOT do

- It does not turn green status on, change source selection, issue playback commands, fetch media, inspect response bodies or modify Yandex playback.
- A `kUrl` field being present is not proof that the URL matches the current track. W127's exact signed URL + currently-playing + current-track check remains the only source-verification path.
- **#52 remains OPEN.** If the Yandex build does not expose `kUrl`, the UI must remain unverified. Actual alternative playback on the owner's PC still needs acceptance.
- VPN A→B, #53, #54, #56, #57 and #58 remain open under W119's owner task order. No installer was built.

Continue from live `main`; preserve the single-product, main-only, exact-backup and no-intermediate-installer rules.

# ADR-0001: Monorepository and runtime baseline

- Status: accepted
- Date: 2026-10-07

## Context

CELIKOM needs a browser extension first, then a PHP API, billing/admin capabilities and potentially Android. The playback PoC proved the risky browser mechanism but intentionally has no production boundaries.

## Decision

Use one repository with explicit top-level modules:

- Chromium Manifest V3 client in `extension/`, authored in TypeScript and packaged without remote code.
- PHP 8.3 application in `server/`, installed through Composer with PSR-4 autoloading.
- Accepted experiments retained in `spikes/` until migrated behind tested contracts.
- Product, analytics and architecture decisions versioned in `docs/`.
- Android isolated in `android/` and blocked on its own technical gate.

Node 24 is the deterministic build runtime for Stage 1. The extension transpilation path uses Node's built-in type stripping, which keeps the foundation dependency-free; a dedicated type-checker may be added when production domain code appears, without changing source boundaries.

## Consequences

One pull request can validate cross-module contracts, while each runtime retains its own package metadata and artifact. The repository stays easy to clone and build. The tradeoff is that CI must explicitly test both JavaScript and PHP environments.

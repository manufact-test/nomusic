# Repository layout

Status: Stage 2 accepted; Stage 3 implementation pending live playback acceptance on 2026-10-08.

## Boundaries

| Path | Responsibility | May depend on |
|---|---|---|
| `extension/` | Production browser client, adapter/bridge, manifest, packaging | Versioned client contracts; no server secrets |
| `server/` | API entrypoint and future domain modules | PHP runtime and explicit adapters |
| `spikes/` | Time-boxed technical proofs | Nothing production imports directly |
| `docs/` | ADR, architecture, product and analytics definitions | Project decisions |
| `android/` | Reserved future native-client boundary | Nothing until Stage 16 gate |

The accepted playback PoC remains executable but is not a production dependency. Stage 2 migrated observation through a stable `ServiceAdapter`; Stage 3 implements separate replacement/sync/guard/fail-open components. Every migration keeps exact Track ID selection, fail-closed ambiguity and one-master-player semantics under tests and a separate live gate.

## Build contract

The root command `npm run ci` is the local equivalent of the repository CI path:

1. Repository lint and secret-pattern guard.
2. PoC, production extension and server-foundation tests.
3. Manifest and structural validation.
4. Reproducible extension archive plus SHA-256.

PHP runtime checks execute locally when PHP is installed and always execute in GitHub Actions. No generated `dist/`, `vendor/` or `node_modules/` content is committed.

## Branch contract

- `main`: last accepted gate.
- `develop`: integrated work accepted for the next release line.
- `feature/*`: one bounded stage or change.
- `spike/*`: disposable technical investigation.

Every merge must keep `npm run ci` green. Client release additionally requires the Stage 18 private-infrastructure gate.

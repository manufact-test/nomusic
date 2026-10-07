# Repository layout

Status: accepted for Stage 1 on 2026-10-07.

## Boundaries

| Path | Responsibility | May depend on |
|---|---|---|
| `extension/` | Production browser client, manifest, packaging | Versioned client contracts; no server secrets |
| `server/` | API entrypoint and future domain modules | PHP runtime and explicit adapters |
| `spikes/` | Time-boxed technical proofs | Nothing production imports directly |
| `docs/` | ADR, architecture, product and analytics definitions | Project decisions |
| `android/` | Reserved future native-client boundary | Nothing until Stage 16 gate |

The accepted playback PoC remains executable but is not a production dependency. Code moves from `spikes/` only with tests that preserve exact Track ID selection, fail-open restoration and one-master-player semantics.

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

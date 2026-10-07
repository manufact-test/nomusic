# ADR-0002: Public development, private client release

- Status: accepted
- Date: 2026-10-07
- Final enforcement stage: Stage 18

## Context

The repository is temporarily public while the product is unknown and the team is small. Public visibility simplifies early collaboration but is not appropriate for production secrets, internal artifacts or the final client delivery chain.

## Decision

Public GitHub may be used only during closed development. Before any release to clients, CELIKOM must:

1. Freeze and verify a complete repository mirror, tags, release metadata and encrypted backup.
2. Move the active repository to a private owner-controlled Git service, or make the existing repository private when that meets the threat model.
3. Move CI/CD to scoped, revocable project credentials. Personal passwords are never shared with automation.
4. Rotate credentials, remove public build artifacts and confirm that no production endpoint or secret remains in public history.
5. Deploy to a privacy-first, independently controlled hosting provider with tested backup, restore and rollback paths.
6. Decommission any starter hosting only after production verification and a successful rollback drill.

“Anonymous hosting” is not treated as a promise of absolute anonymity. Provider, payment, legal and abuse-handling requirements remain binding; the goal is data minimisation, ownership separation and controlled disclosure.

## Release gate

No public client release is allowed while source, production artifacts, secrets or deployment credentials depend on the public repository. Android Beta may remain limited to a named closed cohort only when it contains no production secrets and the cohort is documented.

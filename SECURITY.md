# Security policy

CELIKOM is under closed development and does not yet accept public production traffic.

Do not open a public issue containing a vulnerability, credential, personal data, private audio, or production endpoint. Report such findings privately to the project owner. Until a dedicated security mailbox exists, coordinate through the private project channel.

The repository must contain only synthetic fixtures and public development configuration. Secrets are injected by the CI/deployment secret store, scoped to the smallest required permission, and rotated after migration or suspected exposure.

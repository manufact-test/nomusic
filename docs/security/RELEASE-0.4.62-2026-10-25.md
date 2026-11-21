# Distribution/support-export audit — 2026-10-25

Scope authorized by owner: desktop and Android support-export hardening. No server, database, entitlement, refresh/session policy, approved audio, deployment, website or PR #6 merge changes.

Desktop 0.4.62: full diagnostics are a distinct background command gated by a live authenticated auth/me response and exact match of either of the two owner-designated identities. Local saved email, account preview, role field or promo are insufficient. The dispatcher also verifies the extension-owned popup sender. Normal status replies omit the full raw player/network/scoring traces. Both original clipboard export buttons use the privileged command; the login-network fallback is hidden. Logout hides the main button; each export is authorized again. Export output redacts credentials and signed URL queries. Existing playback/auth rotation is unchanged; core version only is bumped to match manifest.

These are official-client support-export restrictions, not server admin grants. Client code and each user's own playback can inherently be inspected/modified on that user's own device. The two identity hashes are policy identifiers, not secret credentials. No administrative server endpoint is unlocked by this client policy.

Checks: 317 extension tests pass, including normal-account denial, forged local identity/promo denial, wrong sender denial, privileged export dispatch, ordinary status projection and redaction. Production ZIP built with the existing HTTPS API origin; manifest/version/core match, duplicate archive entries absent, source maps/development/signing files absent. Existing bounded permissions/CSP/security package gate passes. No new npm/composer runtime dependency.

Read-only live boundary checks: health200; auth/me, entitlement, support and resolve401 without a bearer; /.env and /.git/config403. Initial transport timeouts resolved on retry. No credentials, account mutation or live submission was used in these probes. This does not test authenticated cross-account/SQL/admin workflows, dependency CVEs, OS exploits or constitute a full penetration test.

IMPORTANT: GitHub API confirms manufact-test/nomusic is PUBLIC. It must be made private for code confidentiality; previously downloaded source/APKs cannot be recalled. Visibility cannot be changed through the available GitHub connector tools. Do not represent this audit as a guarantee that nobody can steal/reverse engineer/hack anything.

Android 0.3.34 lives independently on feature/android-isolated. It removes APK recovery sources, closes the legacy tools entry, leases full logging/export to the two authenticated identities, clears old ungated journals on upgrade and private reports on account change/logout, and denies unverified audio-session broadcast stop requests. See its release proof and README. Physical playback/session checks are still required for changed Android entry/receiver paths.

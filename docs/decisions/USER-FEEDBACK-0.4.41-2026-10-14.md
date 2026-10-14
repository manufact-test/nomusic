# User feedback and contribution UX — 0.4.41

Owner authorized implementation on 2026-10-14 after reviewing four proposals.
Existing status wording and diagnostic button need no extra redesign.

## Implemented

- Existing support form offers ordinary correspondence (email answer) or current
  song report (category, optional comment, automatic whitelist-only diagnostics).
  Song identity is pinned; a changed track is refused before sending. Duplicate
  clicks, failed sends and popup reopening retain idempotent request identity.
- Inside each existing account/email in admin support, two category links show
  counts and separate histories. Existing tickets default to ordinary and keep
  their messages and mail workflow. Song reports have a resolve action with
  role/CSRF checks; no mandatory reply or email dispatch. Server deduplicates the
  same open account/track/category/comment report, even across fresh request IDs.
- Diagnostics contain selected player/bridge state, error codes, bounded request
  statuses and extension version. Credentials, raw logs, URLs, account records
  and arbitrary keys are omitted by client and server whitelists. Comment is
  user-entered free text, not an automatically generated technical dump.
- MP3 duration is measured locally from MPEG Layer III frames using the server
  inspector's constraints (VBR, ID3, supported MPEG versions). A warning appears
  before submission for >1500 ms; >5000 ms in either direction additionally asks
  for a suitable version. Upload remains warning-only, no unsafe trimming or
  new server rejection policy; existing admin moderation warning is preserved.
- One requested-song card per exact Yandex Track ID, ordered by distinct account
  demand descending then recency. A group decision updates pending proposals
  atomically and records each original proposal's review/audit; history retained.
- Suggesting approved active or pending audio shows a green result. Opening and
  submitting both check presence; server independently returns 409 without a
  new proposal when version is already present. Existing historical proposals
  continue to derive uploaded/fulfilled progress.

## Persistence and compatibility

017_song_support.sql adds ticket kind, report JSON/hash, per-message mail flag
and query indexes; all prior tickets remain ordinary and email-enabled. No table
or record deletion. No changes to account/session/access/promo/media records.
No additional extension permissions. Existing playback and VPN/tab recovery
remain intact. PR #6 stays open and Issue #7 stays open.

## Validation

Local extension 224 tests, lint and client security gates pass. Added tests cover
report privacy, identity pinning, retry/duplicate behavior, frame durations and
both warning boundaries, already-present suggestion UI and catalog races.
Server MySQL/CSRF/RBAC/mail tests and configured native Chrome UI checks run in CI.
Deployment and preservation evidence will be appended after completion.

Owner checks: ordinary support still sends an email reply; song reports arrive
under the same account in the song section and can be resolved without email;
local file duration warning; approved/pending green suggestion result; popularity
sort when several different accounts request the same absent song.

Initial full CI found a PHP SQL quoting error before any live deployment; it was
fixed in a572177f059b59e9f3579014d8564bc342da3b46. Full CI 38599174983 passes,
including ordinary support mail/retry/RBAC/CSRF regressions and new report/group
cases. Private Chrome CI 38598656472 and MariaDB migration CI 38598656473 pass.
Configured full extension ZIP SHA-256:
`73cb928a9a067b72f5763ee190089581825e46119eb0172421b1337c9d1b66f5`.

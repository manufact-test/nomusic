# W142–W144 — current-player source truth, retired-host lease and stable-feed publication race

Date: 15 November 2026. Repository `manufact-test/nomusic`, **only working branch main**. No new installer, second product or public release was produced.

## Code and exact rollback backups

- W142 pre-change exact rollback: `backup/windows-main-pre-w142-gui-source-and-heartbeat-handoff-20261115` @ `09c7b0168c4d70f2d7afe6e974a90600391bd65c`. Code commit `c919d1ed15842bd9d704f2d6cdb7540c78de3b77`.
- W143 pre-change exact rollback: `backup/windows-main-pre-w143-stable-feed-coherence-20261115` @ `c919d1ed15842bd9d704f2d6cdb7540c78de3b77`. Code commit `e772ca977b70ad9c1a9b972175e93907db04235c`.
- W144 pre-change exact rollback: `backup/windows-main-pre-w144-active-audibility-reconciliation-20261115` @ `e772ca977b70ad9c1a9b972175e93907db04235c`. Code commit `18aa813f0cbb83832b3f6f0e8150ada0a5439757`.

## Implemented

1. Main WinForms UI no longer equates legacy native mapping or `NATIVE_SOURCE_VERIFIED` text with proof of **currently playing** CELIKOM audio. Track, connection and overall state labels consistently require fresh PLAYING evidence and exact current source, falling back to neutral UNKNOWN, PAUSED or STOPPED. Existing compact popup uses matching source truth.
2. W15 bridge accepts sequenced current-owner heartbeats but remembers retired previous native instance IDs and rejects their late packets even with a larger sequence. A newly restarted instance can still assume the lease; Stop resets it. Real localhost test covers restart and late old-green transition.
3. Signed stable HTTPS `latest.json` and `latest.json.sig` cannot be swapped together atomically on a generic static host. W143 retries only `STABLE_MANIFEST_SIGNATURE_INVALID` at most three times, re-reading both documents under no-cache, with final hard failure. Wrong origin, redirects, invalid JSON/policy and downgrade remain unaccepted. Added transient and persistent mismatch tests.
4. W144 uses the same genuine Electron native audibility function both for selecting the authoritative Yandex renderer and for proving PLAYING in its current heartbeat. No event is required if `isCurrentlyAudible()` already says true. This **never** establishes ORIGINAL or ACTIVE_REPLACEMENT by itself.

## Verification and remaining blockers

- W141 Main + Windows integration at `09c7b016`: SUCCESS; W142 both at `c919d1ed`: SUCCESS.
- At note creation, W143 Main 43696396674 + Windows integration 43696396709; W144 Main 43696528740 + Windows integration 43696528671 were ongoing. Check final results before acceptance.
- Production auto-updater **not operational**: no approved official origin, protected release private key, pinned P-256 public key, signed trusted Authenticode installer/cert pin, production publisher or trusted bootstrap on owner PC. W140 downloads and stages only after genuine pinned production setup. Never invent trust or expose unsigned 0.24.37 as a signed stable release.
- No audio heard/tested on owner PC for W142–W144. No claim about reducing VPN pop, gain clipping, 403 recovery, autostart or full playlist accuracy. Issues #52, #53, #54, #56, #57, #58 remain OPEN.
- Follow W119, W139, and the latest top of NEXT-CHAT. One product, one `main`, exact backups, no interim installer. Continue substantial code blocks without asking owner for microtests.

## W145/W146 continuation (15 November 2026)

- W145 exact code backup `backup/windows-main-pre-w145-pending-safe-point-scheduler-20261115` @ `8642b98ba05c27f445d1bb110b78bae1ea09dc4e`, commit `6094432757c80d0305a1d49b32868a591b960ea0`: a previously verified signed pending package triggers 30-second safe-point scheduler checks, never repeated network checks while unsafe. Existing production trust, Supervisor, signed installer validation and stringent idle-Yandex gate unchanged. CI newer than W144 was in progress as this note was written.
- W146 exact code backup `backup/windows-main-pre-w146-compact-paused-source-status-20261115` @ `6094432757c80d0305a1d49b32868a591b960ea0`, commit `d4a94f63411e328b47aa5fe16b8acfbaf9dcb2a6`: compact source status only calls mapping pending when fresh current player is PLAYING; PAUSED/STOPPED override stale mapping. Regression added. Check W146 CI.
- W142–W144 and W142–W144 documentation CI success, all code snapshots backed up. None is owner-PC acoustic or production updater acceptance. P0 release-origin/private-signing-key/Authenticode/publisher/one-time bootstrap blockers continue unchanged.

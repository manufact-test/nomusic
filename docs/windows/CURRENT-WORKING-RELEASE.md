# CELIKOM Windows — current owner-accepted working build

**Status:** WORKING / OWNER ACCEPTED / LIMITED PRIVATE BETA, **not a signed public release**.
**Accepted:** 17 November 2026 after several hours of owner's playback and VPN-switch testing.
**Product:** CELIKOM Windows, not Android and not Chrome extension.

## Frozen binary and source

| Item | Exact value |
| --- | --- |
| Windows application | **0.24.51.0** |
| Native Yandex module | **0.24.32** |
| Build source (byte-for-byte W20 package) | `c717428a7d9f01fc8e33b482fcf66a9ed1a02947` |
| Frozen owner-accepted branch | `stable/windows-02451-private-beta-20261117` |
| Frozen backup branch | `backup/windows-02451-owner-accepted-exact-20261117` |
| Working/development branch | `experiment/windows-w167-owner-ui-regressions-20261116` |
| Original W169 pre-change backup | `backup/windows-w169-pre-track-handoff-crash-investigation-20261117` @ `92e0d9e63f5fd7dc7f243d7c2a2202cf5ad8b2de` |
| W20 staging CI | `44071025539` **SUCCESS**, private artifact `14320904994` |
| User Library | `/CELIKOM/W169/` |
| Production | **not deployed**; `main` unchanged |

**Exact output, no new rebuild:**
- EXE: `CELIKOM-W169-TRACK-HANDOFF-02451-UNSIGNED.exe` — 85,142,394 bytes — SHA256 `ecd62fbf722749307402d40537610ae84154d50ae27a64eddd823ab182a57b77`.
- ZIP: `CELIKOM-Windows-0.24.51.zip` — 84,662,575 bytes — SHA256 `94dab24ab74e61bc6e4341471c5757b9c0ddb7f0b610dac7f10161fb2cd9cfe2`. Contains the exact same EXE.
- `SHA256SUMS.txt` stored beside them in the personal ChatGPT Library. The three items were uploaded and list-verified.

## Acceptance evidence (distinguish reports from telemetry)

- The owner installed 0.24.51 and listened for several hours, including switching tracks and toggling VPN. Owner reports **no Yandex restarts, no interrupted playback and normal UI**. Owner explicitly accepted this as the current working version pending further observation.
- Latest owner diagnostics exported `2026-11-17T13:27:46Z`: AppVersion=0.24.51.0, NativeModuleVersion=0.24.32, NativeModuleMatchesApp=true, NativeIntegration=ACTIVE, BridgeStarted=true, Enabled=true. In the *last 15 minutes* sampled, no decoder error, event-loop stall, CPU/memory high, or crash evidence. Native heartbeat continues across tested route recoveries.
- There are route changes, temporary suspend/resume and some `ACTIVE_ENTITLEMENT_NETWORK_ERROR` and timeout events in *7-day persistent incident history*, but with recovery and no owner-observed audio issue. History also contains older `YANDEX_PROCESS_UNAVAILABLE` incidents, some from pre-W169 versions. They do not establish a current W169 crash. Do not incorrectly claim the *entire* 7-day history is empty.
- Diagnostics are bounded to a last-15-minute current window plus a 7-day incident history. They do **not** conclusively prove that every audio byte used the CELIKOM source or that the previously intermittent Yandex restart can never happen.

## Change freeze

Do **not** modify the owner-accepted EXE/native assets, release identity, VPN recovery, source routing, color statuses, Next UI, Yandex files or entitlement just to reduce background diagnostic noise. Future changes require a new branch/version, backup, tests and explicit owner validation. Do not call 0.24.51 a publicly signed GA release.

## Testing scope and public release boundary

- Current: owner and explicitly invited private testers only. Single unsigned, independently verified private-beta installer; Windows x64, Windows 10+; requires independently installed supported official Yandex Music.
- The user wants to reinstall the same binary on his own PC and share that binary with one friend. No new build is required.
- Personal ChatGPT Library is **not** a public CDN. Friend cannot be expected to open owner's private Library entry. Owner must obtain the EXE locally and share it privately, without account/session data. One license/account per person according to service terms; do not hand off owner credentials.
- Website download is **not yet authorized for public release**. `windows-companion/w20/release-gate.ps1 -Mode Release` intentionally blocks with `W24_RELEASE_BLOCKED_NO_VERIFIED_AUDIO_OR_SIGNING`. Before public publication: code-signing/security reputation, unsupported-version handling, clean-machine smoke with official Yandex, user consent/license, installer/update hosting, independent checksum verification, rollback, documentation/privacy/legal review, release-gate owner approval. Stage mode passing does not imply a public release.
- See `docs/windows/PRIVATE-BETA-INSTALL-AND-PUBLICATION-20261117.md` for exact reinstall and tester steps.
- See `docs/windows/W169-TRACK-HANDOFF-AND-YANDEX-RESTART-GUARD-20261117.md` for incident boundaries, W20 proof and implementation.

**If Yandex restarts again:** do not force a workaround or tweak VPN. Collect exact local time, new diagnostics, Windows Event Viewer Application Error/WER entries, process-exit evidence and check `NATIVE_RELAY_TICK_EXCEPTION` / `NATIVE_CDP_EVENT_EXCEPTION`. Owner's multi-hour acceptance is encouraging, not a guarantee.

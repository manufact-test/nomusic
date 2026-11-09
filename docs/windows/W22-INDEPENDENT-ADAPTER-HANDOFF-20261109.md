# W22 — independent adapter checkpoint, distribution blocker and next gate (2026-11-09)

**Purpose:** reduce dependency on a proprietary PulseSync Client and GPL-licensed PulseSync SDK by writing our own CELIKOM source-selection kernel. Preserve official Yandex Music desktop UI, decoder, Play/Pause/Seek/Next, playlist and native Yandex authorization. **Do not start a new player.**

## Evidence now available

- W15.2: native Companion account/bridge UI launch on owner's Win10, not heard in Yandex.
- W17: real PulseSync mod changed official signed EXE (AuthentiCode HashMismatch), original restored byte-identically.
- W18: CELIKOM SDK addon was imported, modified Yandex process started, no playback tested.
- W20: developer-only installer installs and removes CELIKOM EXE only (CI SUCCESS 42596579243).
- W21: independently written safe two-file backup/recovery engine, 20 contract checks passed (CI SUCCESS 42598726742). Not wired to customer installer.
- W22: independently written \`native-resource-adapter.mjs\`, 13 native source-only hook checks passed plus 10 W15 Node and 44 native bridge/MIME checks (CI SUCCESS 42599679157). It hooks an **already found** \`getFileInfo\` /\`getFileInfoBatch\` resource prototype and passes validated CELIKOM audio source as \`transport:raw\`, \`codec:mp3\` or \`aac-mp4\`. It never changes Yandex's clock/queue/control API. Next/Stop cancellation, no-change fallback, bounded stalls and disposal are tested **only in fixtures**.

## Independent third-party reference

[FkCensor by S4YN3X](https://github.com/S4YN3X/FkCensor) uses MIT-licensed source to alter Yandex ASAR and embedded EXE ASAR hash. Its \`assets/inject.js\` demonstrates a Yandex renderer file-info resource hook with \`downloadInfo\`, \`downloadInfos\`, \`fileInfo\` and \`fileInfos\` fields. W22 uses the resource shape as a compatibility research reference, not FkCensor's external track catalog. Any existing rights/attribution requirements remain with their author.

However, **its installer still changes the official signed EXE**, therefore it does not eliminate Authenticode or Yandex licensing concerns. An independently developed source adapter avoids the proprietary PulseSync dependency but not third-party product rights.

## Distribution and release guard

[Official Yandex Music Windows EULA](https://yandex.ru/legal/music_mobile_agreement/ru/) (version published April 3, 2026) includes Windows and restricts software modification (4.1), commercial redistribution (4.2), and distribution of modified versions (4.3), unless consent or legal exceptions apply. The copyright and any publishing/security issues need professional legal/product validation. PulseSync Client's separate EULA remains restrictive as documented in W20. No hidden patch, disabling Windows security or Yandex credential extraction is authorized.

## Next concrete engineering gate (not customer task)

1. In developer-controlled disposable Windows, discover Yandex 5.126.1 renderer file-info resource, implement and exercise the W22 adapter under exact version/signature checks and W21 protected recovery.
2. Use a legitimate standalone authorized Yandex music test account and CELIKOM approved track grant to prove audible real substitution and Play/Pause/Seek/Next (no imaginary test verdict).
3. Obtain distribution rights and an honest code-signing/Windows trust plan before packaging a one-click signed CELIKOM installer that touches any third-party files.

W22 CI does not deploy or alter real Yandex, and never uploads third-party binaries, user accounts or signed stream URLs. Production, Android, browser extension and server untouched.

# W188 — investigation after owner test of 0.24.61

Owner reports login succeeds but audio replacement does not. W54 at 2026-11-27T07:11:19Z shows AppVersion 0.24.61.0, NativeModuleVersion 0.24.31, NativeModuleMatchesApp=true, NativeIntegration=ACTIVE, BridgeStarted/Enabled/SignedIn=true. Current 15-minute window contains no SOURCE_* events, no resolve/mapping/file-info request, no PLAYER_NET request, no exact media URL, and no audible proof. This means the failure occurs before we can establish selection of a replacement source; do not infer an audio decode or CDN failure.

The exact W174 accepted audio source files remain unchanged: renderer-entry.mjs SHA 203b098914d549bc8d21b682b62df6486025cefa; native-resource-adapter.mjs SHA e3bfdc3ed579709c342c3ae87e2e83510e35826e; current-source-refresh.mjs SHA a5814bee52a8698ab79f9f4861f1b1451d85ee09.

W174/W173 verified Yandex 5.128.0.r22145392 only. The official compatibility catalog on main currently contains 5.128.0 as its newest reviewed pin and no 5.129.0 entry. Owner screenshot shows Yandex update prompt for 5.129.0. Exact official 5.129.0 installer/inner EXE/app.asar must be independently downloaded from Yandex S3, Authenticode-verified, hashed, image-built and tested in disposable install/restore sandbox before catalog addition. A workflow was added to run this on a Windows runner without changing the owner installation.

Do not change W174 audio hook files. Do not copy W182/W183/W185 player-hook experiments into this branch. First establish exact 5.129.0 compatibility and inspect the new ASAR call path against W174 endpoint discovery. No customer stable or mass OTA.


---

## W188 implementation and verification update — 27 November 2026

The active recovery work is now documented in `W188-W174-51290-RESTORE-HANDOFF-20261127.md`. The W174 audio baseline source hashes listed above remain unchanged.

On branch `recovery/windows-w174-02454-known-good-20261126`, product/test code commit `d0de9824c5e03422a9d6f928f17715de07bb76ba` (documentation checkpoint HEAD `8900099c6c0e9546b8d6988067d7f8a8ccd6fab4`), W188 adds a live Yandex 5.129 provider discovery/argument bridge and late-attach path around the existing W174 adapter. It does not replace the W174 audio implementation.

Official Yandex `5.129.0.r22295238` passed the isolated signature/hash, native image, byte-exact restore, ASAR hook/callgraph and compatibility contracts in workflow [45965695251](https://github.com/manufact-test/nomusic/actions/runs/45965695251). Exact hashes and test counts are in the active handoff document. Validation artifact ID: `15182926152`; this artifact is a candidate report/ASAR/audit bundle, not an installer.

Separate FlokiNET/private handoff workflow [45965695138](https://github.com/manufact-test/nomusic/actions/runs/45965695138), job `140394244238`, was still in progress at the time of this documentation update. Check its live status before any duplicate build. No owner installer or owner runtime playback acceptance is claimed. Do not call the issue fixed until the owner confirms the replacement audio is actually audible.

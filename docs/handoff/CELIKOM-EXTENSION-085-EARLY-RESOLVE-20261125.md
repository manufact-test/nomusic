# Extension 0.4.85 — early selected-track resolve on the recovered 0.4.78 baseline

Date: 25 November 2026. Owner-only candidate, NOT accepted/public stable.

## Baseline and rollback

Owner explicitly corrected the final pre-migration client to 0.4.78. Source is feature/upload-auto-cleanup-20261121 at 3329f97a7f7de1d74ca8fa8e5f3fd005c88e125c. Its original CI package was independently recovered and matched SHA256 67873c1085b0926a5f40531d17b06d444cbe0b5124442f2cdfa49245794bb56c. The Floki control differs only in api/config.json and manifest.json; runtime JS is byte-identical.

Before this change, main is preserved at 4b6d858a9763918d08f28fcab45a5baafa83b40d (held 84 runtime). The actual rollback for owner playback is the 78 control, NOT 73 and NOT held 84:
Library libfile_ba66ad969d048191a10900dceae714ae; ZIP SHA256 ba5c9b611cebaa4f9f3b615272bd0c0e289dd37d1a2c52c5eca73c671ab88e55.

This commit restores accepted 78 extension source/features to main, including 76 support attachments, 77 My Wave bounded metadata grace and 78 lossless upload cleanup. It keeps current Floki build default/retired-origin rejection, actionable Start errors, and the independent bounded authorization lease during route hints. The latter has explicit revocation/expiry/Stop tests and never extends authority without a verified server decision. It also retains bounded restore diagnostics. Infrastructure README stays current. No server, Android, Windows, release promoter or approval manifest changes.

The 79–84 extended intro wait, strict metadata/resource fences, broad whole-file joins, unbuffered-yield admission and range-network-retry experiments are NOT used in this candidate. Baseline 78 original stream player, MAIN guard, sync engine and adapter are retained. Intro tests are adjusted back to the actual 400ms baseline. The superseded vpn-audio-range.test.mjs (asserting the excluded network retry mechanism) is removed from the current suite, retained permanently in parent history; original baseline stream HTTP-error tests remain. This is a deliberate baseline correction, not disappearance of those historical changes.

## Two owner diagnostics on the 78 Floki control

Input filenames: Вставленный текст(20261125-202538).txt (without VPN) and Вставленный текст(20261125-202851).txt (interpreted as the VPN run from context). Both report 0.4.78.

Without VPN: eight successful activation milestones; new-track preparation about 581–1019ms, initial mid-song join 1546ms. The retained last three transitions explicitly hit intro-start-timeout; original playback starts while replacement readyState is 0, then replacement connects. Seven restores correspond to track changes, not proof of seven network outages.

Second diagnostic includes previous history, so its 12 timing rows must NOT all be counted as new VPN joins. New successful joins include preparation 462–1174ms, excluding earlier rows. Track 106618973 has 817ms load stage and joins around native 860ms. Retained last three transitions again time out before readiness. Track 114377621 starts an initial decoder seek while the original clock runs; readyState temporarily drops to 1 and the replacement later remains about 334ms behind, under the unchanged 350ms drift correction threshold. These are concrete startup/settling symptoms, not evidence that VPN alone caused them.

Track 48592121 preparation is canceled by state-changed before activation while the selection advances. The short retained trace cannot determine whether that was a user skip or another interruption; do not label it a proven stream failure.

All recorded config/resolve/auth/entitlement HTTP responses in these two files succeed. The final replacement is fully buffered and running in the second file. Network rows do NOT provide timings of all audio byte transfers, so they cannot exonerate the external server route or prove Floki caused every lag. The prior same-VPS signed-range audit remains a separate bounded observation.

## Narrow change

Previously the controller could identify the next track while its native source still loads but deferred its authorized descriptor request until native readiness/duration admission. 85 starts this same existing authorized resolve for ONE currently selected confidently identified track during native loading/handoff; subsequent preparation consumes the SAME in-flight answer.

Warm-up never constructs an audio element, pauses/seeks/guards native audio, or bypasses authorization, original admission, duration, expiry, confidence, ambiguity, negative TTL or manual-original rules. No future queue speculation or persistent grant cache is added. Warm descriptor lifetime is bounded to 5s and its signed expiry is checked before use. Stop, explicit retry, access suspension, identity change and destruction invalidate the local warm reference. Obsolete errors are handled without blocking another song. Actual activation still checks current operation and the existing validated master.

No new guard deadlines and no longer native pause are introduced. The goal is to overlap network work with Yandex source loading, rather than waiting longer. This can reduce late joins and their initial catch-up seeks; it does NOT prove all seek-settling/network problems are fixed. In particular, the sync threshold and algorithm are unchanged. Owner listening is still required.

Diagnostics add warmLeadMs to the bounded existing startup history; it records overlap without signed URLs or credentials. Restore history is bounded to 12 records.

## Verification and delivery

392/392 local extension tests PASS, including early loading overlap, sharing pending resolve, stale success/error, disabled/ambiguous/low confidence/unhealthy cases, Stop/manual bypass/access suspension, signed expiry/age and negative caching. A packaged MAIN+ISOLATED integration test proves that the real packaged adapter emits a loading snapshot early enough, starts exactly one resolve with zero replacement audio/native mute, then consumes that same pending resolve when native metadata becomes ready.

Existing pause/seek/retry/manual-original, late approval complete-file path, My Wave metadata grace, support attachment, upload cleanup and access tests pass. Manifest validation PASS. Current security gate PASS (67 packaged client files). No local real Chrome/Brave binary is available; VM integration and tests are NOT a live listening test.

Candidate ZIP: celikom-extension-0.4.85.zip, 2,493,307bytes.
SHA256: 0e3af87b830b980ef6427ebf5492adbf0e378debcaa52c10b594e47d7bd9b63c.
Private owner file: Library libfile_defefd80d12c8191bda63f2ec078842f.
Main CI must independently test/build and produce its private spool receipt; no public promotion/approval is implied. Keep .github/release/extension-owner-promotions.json approved empty and public_stable null until explicit owner acceptance.

Owner check: replace files in the SAME existing unpacked folder, Reload the extension AND Yandex, verify 0.4.85. Compare the same starts/skips with and without VPN; test pause and seek. Send one fresh diagnostic after any audible delay/silence. Do not require reinstalling multiple candidates or disable the legacy hosting rollback.

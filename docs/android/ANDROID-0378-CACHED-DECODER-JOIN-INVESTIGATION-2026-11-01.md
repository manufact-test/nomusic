# CELIKOM Android 0.3.78 — frozen baseline and cached-decoder join investigation

Date: 2026-11-01
Status: investigation checkpoint; no audio-code change made in this checkpoint.

## 1. Frozen rollback point

A dedicated immutable backup branch was created:

- Branch: `backup/android-0378-original-before-cached-join-20261101`
- Exact commit: `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`
- This is the 0.3.78 release-source commit recorded by release PR #27.
- Android version: **0.3.78**, versionCode **79**.
- Package: `pro.celikom.nativeprobe`.
- Signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.

Do not move, force-update, delete, or develop on this backup branch. It is the exact source rollback point. If a future experiment fails, restore the working branch from this exact commit (or cherry-pick/revert deliberately after comparing), not from a guessed earlier version.

The signed 0.3.78 APK already published to the stable Hostinger channel is immutable:
- URL: `https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/79-325d6eb5c538405b989907bd492a644b287143a1f590b76754778c62f66f89a9.apk`
- SHA-256: `325d6eb5c538405b989907bd492a644b287143a1f590b76754778c62f66f89a9`
- Size: 8,755,273 bytes.
- Stable manifest was fetched after upload and matched the intended 0.3.78/code79 release.
- Release PR: [#27](https://github.com/manufact-test/nomusic/pull/27), intentionally still open pending owner listening acceptance.
- Successful publication workflow: [41314737218](https://github.com/manufact-test/nomusic/actions/runs/41314737218).

Important distinction: backup branch is a source-code rollback point; the immutable signed APK URL/hash is the binary rollback/reference artifact. Keep both.

## 2. Current user-visible problem

The owner supplied a screen recording and a matching CELIKOM diagnostic export for the same 0.3.78 listening session. The prior chat correlated six replacement joins and highlighted two joins around the track “Биг сити лайф” as suspicious: the replacement decoder's position appeared to advance very little during the handover while the Yandex source timeline continued.

The prior analysis quoted approximately 224 ms and 239 ms as end-of-join transport/output-clock differences for those two joins. Treat these as **transport-clock observations only**, not measured PCM phase, Bluetooth presentation delay, or proof of an audible gap. The recording did not establish complete silence at those exact moments. Do not convert these figures into acoustic claims.

The owner is fatigued by repeated broad audio tuning. Keep the next experiment narrow, evidence-led, and reversible.

## 3. Working hypothesis — not yet proven

Investigate whether a replacement decoder that is reused from the in-memory/recent-audio cache follows exactly the same muted startup, decoder-advancement verification, warm alignment and handover gate as a newly prepared/streamed decoder.

A prior review noticed a potential asymmetry in `ReplacementEngine.prepare(...)` / `acceptAudio(...)` / `update(...)`: cached audio can enter `acceptAudio` directly, while a newly streamed source follows a different acquisition path. This is only a **candidate path difference**. It is not yet proven that cache reuse skips the join gate or caused the two suspicious joins. Inspect actual runtime events and current source before changing code.

Relevant source at the frozen baseline:
- `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/ReplacementEngine.java`
- Methods: `prepare`, `acceptAudio`, `update`, `fade`, `completeSeek`, `rememberAudio`, `audioKey`.
- Existing join gate in `fade(boolean coherentEntry)`: for coherent entry, waits for decoder advancement, checks transport drift against `STRICT_STREAM_JOIN_DRIFT_MS` (100 ms), can perform bounded WARM correction(s), and calls `skipUnstableJoin` to retain original audio when it cannot verify stable transport alignment.
- Existing transport evidence explicitly records `sourcePcmMeasured=false`, `phaseVerified=false`, `hardwareOutputMeasured=false`. Preserve that honesty.

## 4. Next implementation plan — do not broaden scope

1. Read this document, `docs/android/NEXT-CHAT.md`, `docs/project-status.md`, and the 0.3.78 release receipt.
2. Verify actual branch HEAD and diff against frozen commit `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`. Do not assume this document's branch is current.
3. Re-open the paired recording/diagnostic evidence from the conversation/owner-provided files. Correlate each suspicious join by timestamps and event sequence. Separate cached-file reuse from streaming preparation using explicit log evidence; if logs do not record cache origin at join, add passive diagnostic fields first.
4. Trace every path into `fade(...)`. Confirm that cache reuse, full-download fallback, partial streaming, prepared-before-arm, pause/resume, seek recovery and new-track preparation all receive the correct join mode and safety gate.
5. Add a deterministic actual-engine regression that starts from a **cache hit**, delays or stalls decoder advancement, and proves:
   - original remains audible until the replacement decoder is demonstrably advancing and within the existing transport threshold;
   - no replacement audio is granted early;
   - bounded corrections are not exceeded;
   - on timeout/unstable drift, replacement stays silent and original remains in control;
   - normal successful cache-hit join eventually completes;
   - existing stream-hit behavior remains unchanged.
6. Add a paired streaming-path regression so cache and stream paths are held to equivalent ownership/gate invariants. Do not assume their timing must be identical.
7. Run the complete Android native regression suite, API 36 compilation and D8 CI. Keep the candidate on a **non-publishing staging branch**. Do not upload to Hostinger stable or modify `stable.json`.
8. Only after CI passes, build a clearly identified test candidate through the existing signed pipeline in test-only mode (if supported by the current workflow); verify the receipt says `stable_published: false`. Never hand over an unsigned APK or a guessed artifact URL.
9. Owner installs/tests only the exact verified candidate. Ask for a focused listening comparison of the same affected join(s), plus a quick check of seek, pause/resume, Next and track boundary to detect regressions.
10. If no improvement, revert the experiment to the frozen 0.3.78 baseline and reassess evidence. Do not stack speculative fade-duration, gain-law, clock-lead or extra-mode changes.

## 5. Strict invariants

- Preserve the single approved audio mode. No A/B selector, linear/nonlinear toggle, extra user-facing controls or extra diagnostic buttons.
- Do not alter seek timing, WARM lead, fade duration, gain law, pause/resume, Next, buffering, Bluetooth routing, audio ownership, decoder lifecycle or Media3 event arbitration unless the new regression directly proves that exact path is responsible and the change is narrowly scoped.
- Never mute both source and replacement during an uncertain handover.
- Never grant replacement output solely because a cache file exists or metadata matches.
- Retain all current identity, live server resolve, entitlement, audio-session, measured-duration and fail-open safety checks.
- No desktop extension, backend, website, CMS, catalogue, authentication, updater or stable release changes.
- A passing host test or transport clock does not establish speaker/PCM phase or acoustic acceptance.

## 6. What the owner should be asked to do

Nothing until the next developer has completed source inspection, regression tests, SDK36/D8 CI and produced a verified signed test candidate. Do not ask the owner to repeat the same recording now.

## 7. First action for the next chat

Start by verifying the backup branch and current working HEAD, then inspect the cache-hit route through `ReplacementEngine`. Treat the cache-vs-stream gate difference as a hypothesis to test, not as a confirmed root cause. No code edits until the call graph and existing tests have been checked.

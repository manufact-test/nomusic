# CELIKOM Test.37: persistent verified-session effect

Status 2026-11-05: isolated experimental candidate; physical HONOR acoustic verdict **pending**. This is not the accepted rollback.

## Why this differs from Test.34–36

Test.36 diagnostics (fresh run `CELIKOM-combined-20261105-130734.txt`, begins at JSONL 3006) showed 18 new `DynamicsProcessing` preparations against the same verified Yandex audio session `225`. The experimental transfer was promoted once but that join still took 1.91s; other cold joins took 2.46s and 2.69s. 12 shared track IDs against accepted Test.33 were mixed (7 faster, 5 slower); uncontrolled mean 74ms slower in Test.36. User still heard nearly identical click/handoff. Loading-speed and acoustic handover were different problems.

Hypothesis, **not established cause**: re-creating, enabling and then disposing an Android `DynamicsProcessing` session effect at every song boundary may be audible on HONOR even with an unchanged audio-session ID. Another unresolved cause is 160ms overlapping playback of two differently mastered/phased sources; no source PCM is available to prove phase alignment.

## Precisely what Test.37 does

- Branch `feature/android-0385-test37-persistent-effect-20261105` from accepted Test.33 source `53d94d66a32b332b62848e0895285d81dda226e9` (not Test.36).
- `AudioOwnership.parkSourceEffect` silences the outgoing decoder first, resets Yandex gain to **0dB**, verifies effect control, then clears the previous track output lease while leaving the session effect enabled.
- On a confirmed new-track boundary with a **fresh verified identical session**, same signed-in account and active auto mode, `ReplacementEngine` retains the idle effect. The next fresh resolve and measured-duration-approved decoder uses `prepareSourceEffect(effect,true)` without a second `setEnabled(true)` or gain-init write.
- Existing effect listener also handles control loss while parked. After route loss, session mismatch, account change, source disappearance, service stop and manual stop the parked effect is reset, disabled and released via the single `AudioOwnership` command gateway. If the unity reset fails, the engine falls back to full release.
- Emit `audio_effect_session_parked`, `audio_effect_session_reused`, and `audio_effect_session_discarded` to separate actual reuse from old `replacement_original_muted` per-song markers.
- **Untouched:** same-song linear complementary `UNIFIED_JOIN_MS=160`, verified local-file and streaming transport, seek/ACK golden implementation, lookahead policy, identity, audio permissions, public stable app, Hostinger and OTA.

## Validation

- All host engine and recorded HONOR transaction suites passed locally, including new `Test37PersistentSourceEffect` (15 assertions) and existing Test.33 seek baseline and route/manual Next regressions.
- New test asserts only one effect **construction and enable** across three confirmed songs, source returned to unity between songs, effect release on stop/route/account/session/control loss, and untouched same-song seek.
- Native Android SDK36 compile, original signing/verification, uploaded signed APK and real-device acoustic output must pass separately in CI/on phone. Local host tests **cannot measure DSP crackle**.

## Rollback and delivery safeguards

- Only owner-accepted baseline is Test.33: immutable `backup/android-0385-test33-owner-accepted-20261105`, source `53d94d66a32b332b62848e0895285d81dda226e9`, signed APK SHA256 `7c51a7a394e53462b171ed3250953fbb7ab840a54587b4c89548aa957489a5e3`, Library ID `libfile_0924722c86908191bef31db36cfcf0ed`.
- Test.37 must keep distinct `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, version `0.3.85-test.37` / code `86122`, original signer; **no new dangerous permissions** and no root, LSPosed or patched Yandex.
- Do not overwrite Test.33 archive or mark Test.37 approved on CI success. Compare audible clicks **only** after owner installs the signed Test.37 APK; video/combined logs can show DSP reuse but cannot prove output quality by themselves.

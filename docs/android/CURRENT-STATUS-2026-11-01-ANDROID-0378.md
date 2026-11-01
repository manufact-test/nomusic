# CELIKOM Android — current status, 2026-11-01

**Current stable Android:** 0.3.78 / versionCode 79. Stable Hostinger publication is verified; owner acoustic acceptance remains pending.

**Frozen rollback source:** `backup/android-0378-original-before-cached-join-20261101` → `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`. Verified on GitHub after branch creation. Do not move or modify it.

**Signed stable APK:** SHA-256 `325d6eb5c538405b989907bd492a644b287143a1f590b76754778c62f66f89a9`; [download](https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/79-325d6eb5c538405b989907bd492a644b287143a1f590b76754778c62f66f89a9.apk). Stable manifest was verified against the published release.

**Current investigation:** owner-provided screen recording and matching 0.3.78 diagnostic. Two suspicious joins were highlighted around “Биг сити лайф”. Reported ~224/~239 ms values are transport/output-clock differences only; they do not prove PCM phase or audible silence.

**Hypothesis to test:** cache-hit decoder reuse may follow a different preparation/handover path from streaming preparation. Not yet proven. No audio code has been changed for this investigation.

**Next action:** inspect every `ReplacementEngine` path into `fade(...)`; add cache-hit and paired stream-hit actual-engine tests; verify original stays audible until the replacement decoder advances and meets the existing gate; fail open on timeout. Then full native tests + Android API36/D8 CI on non-publishing staging. Only afterward prepare a signed test-only candidate for owner listening.

**Do not:** change fade/seek/WARM/gain/pause/Next/AudioOwnership/Media3 logic speculatively; add modes or buttons; publish stable; touch desktop/backend/site/CMS/catalogue/auth/updater.

Read first:
- [Next-chat handoff](START-NEXT-CHAT-2026-11-01-AFTER-0378-CACHED-JOIN.md)
- [Full investigation and rollback checkpoint](ANDROID-0378-CACHED-DECODER-JOIN-INVESTIGATION-2026-11-01.md)
- [0.3.78 release receipt](ANDROID-0378-APPROVED-REPLACEMENT-AUTOSTART-2026-11-01.md)

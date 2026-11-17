# CELIKOM Android A1 — FINAL NAV21 handoff: await owner's phone diagnostic (17 November 2026)

**AUTHORITATIVE state for next chat. DO NOT RESTART RESEARCH OR BUILD ANOTHER APK BEFORE READING OWNER NAV21 TXT.** The owner has received NAV21, is testing it, and will attach the NAV21 on-device diagnostic TXT **to the next chat**. That NAV21 TXT has **NOT** been received or evaluated in this chat. Do not mistake earlier NAV20 TXT for NAV21.

## Working repository, immutability, protected backups

- Repo: `manufact-test/nomusic`.
- **Single permitted working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Exact NAV21 compiled and signed code commit: `def5f4ff420ec3b285ee1853009882a8f991ec1f`. Subsequent changes through handoff are **documentation-only**.
- Pre-NAV21 code snapshot: `backup/android-a1-nav20-owner-strong-read-before-nav21-20261117`.
- Prior final accepted NAV21 docs+code backup: `backup/android-a1-nav21-owner-scoped-readresult-library-verified-final-20261117` @ `886089b89e87fb8bfc5bf290eb421fcfbca13069`.
- **Final next-chat checkpoint (docs-only)**: `backup/android-a1-nav21-final-await-owner-txt-handoff-20261117`; must be created from final HEAD after updating docs. Do not change branch, signer, original Yandex APK, architecture, Test.50, Windows, browser extension or backend.

## Already delivered owner NAV21 APK, not a sound-replacement build

- The owner signed APK is in **personal ChatGPT Library** under `/CELIKOM/Android/Native/CELIKOM-A1-NAV21-Queue-Scoped-ReadResult-ReadOnly-20261117.apk`, next to `CELIKOM-A1-NAV21-Инструкция.txt`. This chat re-listed both files before final handoff; APK 71,466,988 bytes.
- SHA-256 exact APK: `581077a18ea8310d12b0e8049e10fe6d25089ed3043cb8340e0e304b2d0d10ce`. The previous development turn verified byte identity by re-downloading from Library.
- Signing certificate digest (APK v2/v3): `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`, same as accepted NAV17–NAV20; original publisher 2025.10.4 #120.1gpr embedded base SHA `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. The official original `ru.yandex.music` is not modified.
- Signed private native Android13 export CI **#44140575566 SUCCESS** (confirmed completed/success in this handoff), JVM regressions **#44140534551 SUCCESS**. No NAV22 required yet.
- NAV21 build marker: `NAV_V21_QUEUE_SCOPED_READ_RETURN_READONLY`.
- **Stage A:** native original Yandex sound/login/UI passed by owner on NAV17. **Stage B:** CELIKOM audio substitution `NOT_CONNECTED` / **NO-GO**. NAV21 only observes return code cohorts; it does NOT implement alternative audio.

## Last actual phone data: NAV20, NOT NAV21

Owner supplied NAV20 private `CELIKOM-A1-Diagnostics-1794937292351.txt`, summarized in [NAV20 owner real-phone results](ANDROID-A1-NAV20-REALPHONE-QUEUE-SCOPED-READ-RESULT-AND-NAV21-20261117.md). Do **not** upload raw private diagnostics to repo.

- Four exact signed-2025 native hooks `REGISTERED`.
- `QUEUE_SCOPE_ENTER=MANY`, `QUEUED_HOLDER_ATTACHED=ONE`, `ATTACHED_STREAM_READ_MATCH=FEW`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH=MANY`; no stream-reference mismatches or lost return links.
- Original `b.g()` post-call return `-4=MANY`, `-5=FEW`, `-3=FEW`, but those **aggregated** NAV20 counters mix queue-scoped and unscoped renderer streams. `-4` can denote EOS; neither a `-4` nor reference alias alone confirms active audible decoder/PCM, selected track, album/edition, entitlement, or CELIKOM substitution.
- NAV20 `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/FEW` for new process; many stale `METRICA_EXCEPTION` entries survive older rotated local logs, and are **not** evidence of hundreds of current crashes. No confirmed new `JAVA_CRASH` in supplied NAV20 report. Owner did not provide a reliable detailed new audio/Next/seek/My Wave assessment with this TXT.

## Exact NAV21 addition and immediate next step

NAV21 preserved **all** old aggregate counters and added separate, privacy-bounded post-`chain.proceed()` counters:
- `QUEUE_SCOPED_READ_RETURN_MINUS4/MINUS5/MINUS3/OTHER` — only when **renderer + stream + nonnull queue holder** still match at the exact return of the original native `b.g()`.
- `UNSCOPED_READ_RETURN_MINUS4/MINUS5/MINUS3/OTHER` — same renderer/stream but **no queue-holder** proof. Old strong references are invalidated on unscoped reattachment or detach; neither must be promoted to strict proof.
- Other markers include `QUEUE_SCOPE_ENTER`, `QUEUED_HOLDER_ATTACHED`, `ATTACHED_STREAM_READ_MATCH`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH`, `IDENTITY_STATUS`, `READ_RETURN_LINK_LOST`, `AUDIO_STAGE_B_STATUS`. Only categorical counters, not raw private data or audio buffers.

**Next chat:**
1. Receive and read the **NEW owner NAV21 TXT**, plus whatever the owner says about native audio, Next, pause/seek, My Wave, restarts or silence. Check the exported build marker before interpreting results.
2. Compare **strict scoped vs unscoped -4/-5/-3** and attachment/queue status. Assess whether a strict queue-holder attached stream actually returned -4; still don't conflate this with an audible track or audio substitution.
3. Only if the new TXT identifies a concrete missing link or a reproducible regression, make a bounded, noninvasive follow-up with exact pre-change backup, JVM tests, ARM13/signature verification, and new owner test APK **uploaded and verified in personal ChatGPT Library**. Never give GitHub Actions artifact URLs or sandbox download links.
4. Preserve all working historical APKs, same package/account state, do not ask owner to uninstall, clear data, bypass Play Protect, or restart prior static research; never reuse 2026.10.3 HookSpec obfuscated identifiers with signed-original 2025.10.4.

More supporting technical detail: [NAV21 signed release](ANDROID-A1-NAV21-OWNER-SCOPED-READ-RESULT-RELEASE-20261117.md) and [NAV20 real phone analysis](ANDROID-A1-NAV20-REALPHONE-QUEUE-SCOPED-READ-RESULT-AND-NAV21-20261117.md). `docs/android/NEXT-CHAT.md` remains the canonical pointer.

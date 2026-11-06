# CELIKOM Android Test.46 — signed delivery and handoff (2026-11-06)

## Build and delivery

- Separate side-by-side test package `pro.celikom.nativeprobe.test`, version `0.3.85-test.46`, code `86131`.
- Exact functional source: `e0ec5f7e80938ce18c2747e14f3425bcd360c34b`, branch `feature/android-0385-test46-current-first-20261106`.
- GitHub Actions [#42127928197](https://github.com/manufact-test/nomusic/actions/runs/42127928197) **SUCCESS**, signed artifact `13462152277`.
- Original signed APK preserved in [CELIKOM Library — Test.46](https://chatgpt.com/library?file_id=libfile_04a25097779881919d211499337c800f&account_id=personal), filename `CELIKOM-Android-0.3.85-TEST-46-CURRENT-FIRST-SIGNED.apk`.
- Verified APK SHA-256: `14a91c03c153f7ce3af32b6be286641f52b51d96af7ba36033a2febaa4f5541d`; 8,824,985 bytes. GitHub receipt and verification state original signing certificate match, v3 signature verified, native host suite/API36/D8/build isolation passed.
- No stable Android release, OTA/Hostinger deployment, desktop extension, catalog/backend, user permissions, or golden backup ref changed by this Test APK. Physical HONOR audio acceptance **not done**.

## Exactly what Test.46 changed versus Test.45

Diff `50851ec5fdbbb66bf6f4536be78b7f7e4a84c0af..e0ec5f7e80938ce18c2747e14f3425bcd360c34b` changes `AlbumProbe`, `RequestBudget`, `ProbeService`, request pacing tests and build metadata:

1. Current/audible album lookup runs before speculative next-album sampling in the source sample cycle (`ProbeService`).
2. Album requests now distinguish `audible_current` and `speculative_next`; a speculative lookup cannot occupy both request slots while the current song is waiting (`AlbumProbe`).
3. After speculative metadata request, a *different current song* may acquire the Yandex album request budget after **250 ms** rather than waiting the normal **1500 ms**. The 1500 ms ordinary pacing and 30 s per-album cooldown remain; speculation cannot immediately interrupt an audible lookup (`RequestBudget`).
4. Tests explicitly cover rapid Next after speculative lookup and cooldown preservation.

**Scope limitation:** Test.46 does **not** change the fade/envelope, PCM phase, sound ownership, exact Track ID matching, missing catalog entries, server upload logic, or mid-session drift/rejoin. It does not establish that the reported 10% bad transitions, degraded long listening, manual-Next seams, or Yandex smooth-transition ON/OFF difference were fixed. Test.45 separately shortened a still-downloading long successor's promoted-file wait from 1200 to 400 ms; the Test.46 diff contains no new such audio timing change.

## Owner findings still pending, no premature new APK

- Owner says about 90% of joins acceptable, about 10% poor; which songs are poor changes across runs. Manual Next is worse than natural next or simply skipping to the end. Listening/navigation for longer degrades quality. Yandex crossfade ON vs OFF appears behaviorally different. No precise audio fix verified yet.
- Four exact mobile IDs in the fresh Test.44 combined trace had `resolve(found:false)`: `34483761`, `53886987`, `108864304` (PHARAOH — Соната Ей), `61007010` (PHARAOH, ЛСП — Порнозвезда). A previous **read-only live** audit found these titles/IDs absent from active backend catalog, not simply Android lost sync. Do not invent a mobile-only Track ID equivalence or force title-only fallback. The owner will ask the separate music/upload chat about missing versions.
- Upload moderation queue has no count cap; the desktop historical client code in this source checkout has 10/hour upload-attempt cap, but the **owner explicitly corrected that the operative rate limit was raised to 500** in a later change. The 10/hour value must not be reported as the live limit without checking current deployment/commits. Do not modify backend in this Android handoff.
- Test.46 APK is an isolated experiment, not an accepted audio baseline. Owner-requested next step: new combined Android diagnostics in the **next chat**; correlate with current source song, manual/natural Next, session age, Yandex smooth-transition setting as separately noted by owner; fix real issues as one meaningful batch, avoid tiny serial APK experiments.
- Frozen owner-accepted Test.33 source `53d94d66a32b332b62848e0895285d81dda226e9`, backup `backup/android-0385-test33-owner-accepted-20261105`; Test.23/Test.28 rollbacks, stable 0.3.85/code86, stable.json, OTA, Hostinger, desktop and account permissions must remain untouched until explicitly requested. Do not conflate Test.46's host-test PASS with HONOR acoustic acceptance.

## Initial message for next chat

Continue CELIKOM Android only, taking `docs/android/NEXT-CHAT.md` and this document first. The last **delivered signed APK** is Test.46/code86131, source `e0ec5f7`, Library file `libfile_04a25097779881919d211499337c800f`, CI #42127928197 SUCCESS. It changed only foreground/current album metadata lookup priority over speculative Next, not fade or missing songs; not accepted by the owner. Wait for the owner's combined diagnostics in this next chat and analyze all three issues together: (1) long-session degeneration/more poor joins with each navigation, (2) manual Next poorer than natural next/last-second skip, (3) Yandex smooth transition ON/OFF and variable 10% bad acoustic joins. Four tracks `34483761,53886987,108864304,61007010` gave backend `found:false`; separate music chat investigates catalog/upload, don't hack Android title-only replacement. Respect already accepted Test.33 and stable/OTA/backups; no unrelated work, don't issue micro-builds, one complete meaningful test APK only after concrete diagnosis. Owner says upload-rate cap was recently increased to 500; historical 10 in this checkout is not reliable live state.

# CELIKOM Test.6: owner intro-delay evidence, silent early decoder prime, signed test handoff (2026-11-02)

## Why Test.5 alone was insufficient

Owner's new ZIP: two overlapping CELIKOM combined exports at 23:11:19 and 23:11:57 plus a 23:09:20 screen capture. The later export is the continuation of the **same** Test.4 run, not an independent second run. It also embeds Test and Test.2 logs; do not double-count. Raw journals and customer content must not be committed.

Test.4 version 0.3.85-test.4/code86089 on HONOR NTH-NX9 reported 16 source boundaries, 15 next-track prefetch starts, 13 ready, 12 cache consumed. Among 12 cold joins after source boundaries, 10 began within **321–610 ms**, two were late at 2060/5172 ms; four boundaries had no cold join (rapid skips/stuck current). For the 10 fast joins:

| Event relative to source boundary | Median |
| --- | ---: |
| Fresh current resolve | 111.5 ms |
| replacement_prepared | 172 ms |
| local decoder prewarm start | 214.5 ms |
| local decoder motion | 394.5 ms |
| cold-join start | 440.5 ms |
| transition complete | 521.5 ms |

Thus merely fetching the complete file in advance removed much network wait but left a reproducible cold-decoder/startup gate of roughly 200ms. These are transport/command timestamps, not acoustic PCM measurements. The screen-recorded AAC cannot establish which system produced every gap. The 2.06/5.17s outliers involved late or missed download readiness after rapid Next; silent decoder priming cannot speed up missing files.

The last Test.4 track (GUF "Было давно") stayed PREPARING on the original when its promoted current download was stolen by a further next prefetch. Test.5/source 9f2ff014... corrected only that race, and was valid but **did not** fix the ordinary cold join. User explicitly required treating song beginnings as primary and combining both changes.

## Test.6 functional change

The separate test APK reuses the complete Test.5 race/fallback/watchdog fix and adds one next-track decoder stage, only after the full replacement file has finished prefetched:

1. Create one bounded MediaPlayer for the **next** item's predownloaded local file; configure music audio attributes and mandatory zero gain.
2. Its native preparation and initial muted decoder motion take place while the **previous source track** is playing. When movement of at least 40ms is observed, pause the speculative decoder and seek it back to zero; seek ACK marks it ready.
3. This speculative player never touches Yandex source effect, never receives positive gain, never becomes the active replacement, and never changes AudioOwnership state. Low-level start/pause/seek commands are routed through new *silent speculative* methods in the sole AudioOwnership authority.
4. At a real source boundary, the existing **fresh current-track server resolve**, unique identity, album/duration policy, account generation, exact audio-key match and **measured file duration** remain required. Only then may the prepared, paused decoder be adopted.
5. Mismatch, changed timeline/account, missing decode readiness, native errors, source-session collision or 1800ms timeout discard the speculative player. The old fresh full-file normal decoder preparation remains the fallback.
6. Existing accepted HONOR seek-submission/ACK methods, normal full-file selection, Pause/Resume, replacement gain/clock gate and public stable package are unchanged.

New diagnostics: replacement_lookahead_decoder_prime_start, replacement_lookahead_decoder_prime_ready, replacement_lookahead_decoder_prime_adopted, replacement_lookahead_decoder_prime_discarded. At the next real listening test calculate (a) percentage of prefetched tracks with ready-before-boundary and adoption, (b) source boundary to join, (c) where lateness is download-bound vs decoder-bound, (d) whether old promoted-current hang recurs. Do not infer audible correctness from these events alone.

## Signed delivery and regression evidence

- Repository: manufact-test/nomusic; experimental branch feature/android-0385-intro-join-investigation-20261102.
- Functional SHA: **3c22a03f364a019ac545efb4e132ad3f5fc12c21**.
- Package: pro.celikom.nativeprobe.test, label CELIKOM Test, versionName 0.3.85-test.6, versionCode **86091**.
- GitHub Actions [#41523894044](https://github.com/manufact-test/nomusic/actions/runs/41523894044) SUCCESS. Full Android host suite including new lookahead test cases; unified AudioOwnership architecture guard; unchanged check_0385_seek_baseline.py; Android API36/D8; isolated APK signer/package/OTA checks. Build artifact ID **13177859581**.
- APK size 8,775,833 bytes; SHA256 **74d9b0369d31f84657fc951b7bb6a5c9396c62c30815e5faae222cd1b2de5e21**, locally cross-checked against both verification and receipt.
- Original certificate SHA256 **67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f**, v3 verified. Stable OTA/publisher/Hostinger writes false.
- Library: [APK](https://chatgpt.com/library?file_id=libfile_085b58b278f48191a17c48818dba3bde&account_id=personal), [verification](https://chatgpt.com/library?file_id=libfile_937665882e708191a5dc483f46f36dcc&account_id=personal), [receipt](https://chatgpt.com/library?file_id=libfile_bba341cab64081918847ecd9f7190c96&account_id=personal) under /CELIKOM/Android/Test/.
- Workflow artifact label and its embedded original filename are **stale Test.5 / CURRENT-HANDOFF-RECOVERY naming**. They do not reflect code version: signer-verified APK metadata, receipt and source SHA prove code86091/Test.6. The Library file names were corrected without altering APK bytes. The reusable workflow's fixed filename/name should be advanced with the **next functional release**, not as a cosmetic APK.
- Previous Test.5 and Test.4 Library APKs preserved for fallback. Stable original 0.3.85/code86 source 053b7d59beb53db5f30b942feba35e51a1ab256a and accepted-seek backup branches untouched; PR #37 unmerged.

## Only needed owner action

Install the linked CELIKOM Test.6 over the existing Test (not the stable original). Stop stable CELIKOM while listening to Test, leave Yandex Music "Плавный переход" OFF. Listen normally for **song starts** and **mid-song replacement staying connected**. No separate finger-seek or Pause/Resume retest. Save combined diagnostic only if the new version still has defects.

**Not yet acoustically accepted:** the prewarmed next-player reduces a known technical stage when ready, but actual sound and rare transitions need HONOR listening. If background decoder conflicts with the device, revert to Test.5 and diagnose; do not release stable.


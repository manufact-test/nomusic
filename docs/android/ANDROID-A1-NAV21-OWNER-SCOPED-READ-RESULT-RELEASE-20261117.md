# CELIKOM Android A1 — NAV21 signed owner-scoped renderer return diagnostic release (17 November 2026)

## Current owner-phone evidence, no substitution

Owner NAV20 actual handset diagnostics arrived: `CELIKOM-A1-Diagnostics-1794937292351.txt`; interpretation and bounded NAV21 code changes are documented in [NAV20 actual phone evidence and NAV21 diagnostic](ANDROID-A1-NAV20-REALPHONE-QUEUE-SCOPED-READ-RESULT-AND-NAV21-20261117.md). **Do not upload the private TXT to GitHub.**

NAV20 establishes the **same actual queue-holder-scoped native renderer stream** at read entry: `QUEUE_SCOPE_ENTER=MANY`, `QUEUED_HOLDER_ATTACHED=ONE`, `ATTACHED_STREAM_READ_MATCH=FEW` and no mismatches. It also proves original `b.g()` returned `-4=MANY`, `-5=FEW`, `-3=FEW` across *combined queue-scoped and unscoped links*. It does NOT prove that -4 came from a scoped holder; may be end-of-stream, and no currently audible track/album/edition is tied to a downstream audio output. **Stage A original Yandex live playback accepted on NAV17; Stage B CELIKOM substitution NO-GO and NOT_CONNECTED.**

NAV21 **read-only** model splits exact same original result codes into `QUEUE_SCOPED_READ_RETURN_MINUS4/MINUS5/MINUS3/OTHER` vs `UNSCOPED_READ_RETURN_MINUS4/MINUS5/MINUS3/OTHER`. A renderer that reattaches outside queue scope loses strong proof; detached or replaced stream returns cannot count toward matched links. Existing aggregate NAV20 categories retained for comparison. No audio bytes, private account data, track IDs, titles, URLs or tokens are read/exported. No effects on sound, exception semantics, output player, VPN, login, server or protection.

## Acceptance and exact APK

- **JVM model and exact source checks:** CI #44140534551 SUCCESS (as well as #44140400242 model test SUCCESS).
- **Full one-shot native Android13 ARM13 signed, publisher-first+clone, no-suppression 75s owner export:** CI **#44140575566 SUCCESS**.
- The exact signed NAV21 APK was built from code commit **`def5f4ff420ec3b285ee1853009882a8f991ec1f`**; later code commits are documentation only.
- APK size **71,466,988 bytes**, SHA-256 **`581077a18ea8310d12b0e8049e10fe6d25089ed3043cb8340e0e304b2d0d10ce`**.
- Verified Android v2 **and** v3 certificate SHA-256 **`048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`**, matches owner accepted NAV17–NAV20 for **in-place update** only.
- Embedded exact original publisher-signed **2025.10.4 #120.1gpr** origin.apk SHA-256 **`1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`**, unchanged. Xposed scope strictly own clone `pro.celikom.yandex.nativeclonelab`; official `ru.yandex.music` untouched.
- Verified module dex contains exact build marker **`NAV_V21_QUEUE_SCOPED_READ_RETURN_READONLY`**, both scoped and unscoped return counters, hook status, privacy-safe bounded exported summary.
- **Uploaded and then verified in user's personal ChatGPT Library**:
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV21-Queue-Scoped-ReadResult-ReadOnly-20261117.apk`
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV21-Инструкция.txt`
- Downloaded exact APK **back from Library**, checked its SHA-256 and byte-to-byte `cmp` against signed build. **LIBRARY_NAV21_BYTES_IDENTICAL**.

## Protected continuation

- Sole development branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Exact before-NAV21 backup: `backup/android-a1-nav20-owner-strong-read-before-nav21-20261117`.
- NAV17 through NAV20 APKs remain in Library unchanged; never uninstall, clear data/login, or bypass Play Protect. All other products, original Yandex, Test.50 untouched.
- **Next owner test:** Install signed NAV21 *over* NAV20 (same certificate, preserve login), listen to ordinary songs and Next/pause/seek/My Wave, export new TXT and report actual sound/restarts. Focus on `QUEUE_SCOPED_READ_RETURN_MINUS4` vs `UNSCOPED_READ_RETURN_MINUS4`, strong `QUEUED_HOLDER_ATTACHED` vs weak. Even a strong -4 does not attest audible PCM or rights/edition; do not activate CELIKOM alternative audio without further current-track/decoder and grant-safe fallback proof.
- Before further changes, interpret owner NAV21 TXT first. Do not start from old NAV18/NAV19 wait instructions or the 2026.10.3 HookSpec.

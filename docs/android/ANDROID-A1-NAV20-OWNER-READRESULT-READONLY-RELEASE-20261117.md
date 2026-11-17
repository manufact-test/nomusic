# CELIKOM A1 NAV20 — signed owner read-result diagnostic release (17 November 2026)

## Authoritative current state

- **Native original playback Stage A:** owner-accepted NAV17 PASS; retained signed NAV17, NAV18, NAV19 in personal ChatGPT Library.
- **CELIKOM audio substitution Stage B:** NO-GO / NOT_CONNECTED. NAV20 is **read-only**. Nothing in this release substitutes audio or establishes current audible song identity.
- **Owner NAV19 actual TXT** was supplied and analyzed: [real-phone NAV19 proof and bounded NAV20 changes](ANDROID-A1-NAV19-OWNER-REALPHONE-RESULT-AND-NAV20-READ-RESULT-PROBE-20261117.md). Four hook installs registered; queue scope **never entered** while same attached renderer stream reached observed b.g entry many times. This did not demonstrate b.g returned successful audio data.
- **New read-result observation:** after one unmodified original `b.g()` call, `onReadReturn` records coarse `STREAM_ALIASED_READ_RETURN_MINUS4`, `MINUS5`, `MINUS3`, `OTHER`, plus `READ_RETURN_LINK_LOST`. Even a -4 result can represent EOS; this does not prove rendered/decoded audible PCM. Unscoped match remains separate from holder / queued proof.
- **Diagnostic quality:** always append `DIAGNOSTIC_BUILD;origin=NAV_V20_RENDERER_READ_RESULT_READONLY` at owner export; cap repeated `METRICA_EXCEPTION/MUSIC_APP` logs to 8 and export only coarse `METRICA_EXCEPTION_SUMMARY`. Neither suppresses nor changes AppMetrica or Yandex exceptions.

## Verified CI and exact owner file

- JVM exact renderer contract **#44136882616 SUCCESS**.
- ARM13 existing clone differential **#44136827154 SUCCESS**; ARM13 readonly lifecycle **#44136827190 SUCCESS**.
- One-shot NAV20 full native Android 13 owner-signed export **#44137030390 SUCCESS** including publisher-first 75s test, original signed input, owner signer/in-place safeguards, read-only module.
- New owner APK SHA-256: `b60cad28cd815e0df29c5ffb83b2ec8d316426a5b2ff9661c7816bdbda1aeb60`, size **71,466,988 bytes**.
- APK v2 **and** v3 signing-certificate SHA-256: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`, matches NAV17–NAV19 owner signature.
- Embedded unchanged publisher original 2025.10.4 SHA-256: `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Scope restricted to `pro.celikom.yandex.nativeclonelab`; independent original `ru.yandex.music` untouched.
- Both file entries uploaded to and verified in **ChatGPT Library**, location:
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV20-Renderer-ReadResult-ReadOnly-20261117.apk`
  - `/CELIKOM/Android/Native/CELIKOM-A1-NAV20-Инструкция.txt`
- APK re-materialized **from Library** and its SHA-256 checked byte-for-byte against the exact verified local signed APK. **LIBRARY_BYTES_IDENTICAL** confirmed.

## Protected checkpoints and next gate

- Sole development branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Pre-NAV20 owner-result backup `backup/android-a1-nav19-owner-realrenderer-reads-before-nav20-20261117`; NAV19 remains intact in Library.
- The signed NAV20 runtime APK was produced by CI at code SHA `6ebce1bd4358aea68158eee42dfed097f5739ec1`; subsequent commits are documentation-only.
- **Next owner step:** in-place NAV20 update over NAV19; no data/account deletion, publisher uninstall or Play Protect changes. Play ordinary track, Next several times, pause/seek, My Wave, then export TXT and describe any restart, gaps, silent audio, or seek regression.
- Next gate requires runtime read return codes while attached stream still matches. If `MINUS4` observed, interpret as native read result **not** proof audible output. Do not enable replacement without strict exact track+album+edition, grant, listener/playback continuity and safe fallback gates. Do not rerun old global static research or use 2026.10.3 HookSpec symbols.

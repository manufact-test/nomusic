# Original signed Yandex runtime gate — 2026-10-13

This is a laboratory launch check, not a successful automatic-ID or replacement test.

## Reproducible input and environment

- Publisher base APK SHA-256: `a3e4d3aedd24ea0370ead4f25c4f0085a1f43b94e458ee949da86797df27fc61`.
- Original publisher signature verified for all five packages; no patching or re-signing.
- Android 11/API 30 Google APIs x86_64 image reports ARM64 support and `libndk_translation.so`.
- [Successful run 38467027409](https://github.com/manufact-test/nomusic/actions/runs/38467027409), source commit `326febe1094c69785496975c14bf7224ada8c080`.
- Driver uses ADB as a laboratory harness; those privileges are not available to an ordinary installed CELIKOM APK.
- The source APK is transferred as encrypted temporary test input. No publisher APK or decompiled source is committed or included in artifacts.
- The existing project identity key decrypts the input inside the runner only; no SSH connection or server change is performed.

## Observations

The original publisher packages installed successfully. The application launched.
Both input track links (142820338 and 141103805) reached an authorization screen:
`ru.yandex.music:id/authorize` was present, login controls were detected, and no share control was present.
No account login was performed. No playback or track switch was observed in this run.

The supplied link IDs must not count as current-track ID discovery. No ordinary-client ID path was demonstrated.
This does not establish that guest playback is impossible in every navigation path; it establishes the authorization gate in the two tested links.

## Limits and next gate

A logged-in laboratory session is necessary to trace actual playback and outgoing sharing for these paths.
A test account must be authorized by its owner through a secure login handoff; credentials or cookies must not be requested in chat or copied from another device.
Even obtaining an ID using laboratory instrumentation would not prove that an ordinary customer APK can obtain it.
Any candidate channel must subsequently work from CELIKOM's real ordinary identity, automatically over multiple tracks, without supplied track links, account-server coupling, root, USB, additional installers, or catalogue matching.

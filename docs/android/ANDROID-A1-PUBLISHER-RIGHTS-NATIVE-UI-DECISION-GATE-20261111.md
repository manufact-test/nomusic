# CELIKOM Android A1 — publisher-native UI decision gate (11.11.2026)

**Decision status: BLOCKED / NO USER APK / NO STAGE B.** This is a feasibility and authorization checkpoint, **not** an owner-approved product change, legal opinion or proof that Yandex's internal startup check has been identified.

## Independent facts cross-checked against source and exact CI

- Working branch `experiment/android-native-a1-lspatch-clone-loader0-20261111` was equal to handoff HEAD `e4644eaca8e3458499aceefdf4676afdb2e2ed27` at the start of this audit. Existing exact handoff backup `backup/android-a1-final-handoff-stagea-evidence-and-redroid-retry-20261111` matched that HEAD.
- Actual native ARM Android13 source `7c894ebe02e9b4ff1bc42f7a039e7f259e2e979d`: original #170gpr five publisher-signed APKs are alive/resumed ([original CI 42991987794](https://github.com/manufact-test/nomusic/actions/runs/42991987794)); own LSPatch0 module executes within an **owned** process ([CI 42987483624](https://github.com/manufact-test/nomusic/actions/runs/42987483624)).
- Three independent lab-signed clone layouts (five splits without loader, merged one APK without loader, merged one APK with LSPatch0/zero modules) all briefly start then show exact Android MAIN `ApplicationExitInfo = EXIT_SELF`, status `ZERO`. [CI 42991987803](https://github.com/manufact-test/nomusic/actions/runs/42991987803) was run attempt **2**, workflow **failure by product gate**, not an aborted test. Scoped fatal category `NOT_OBSERVED`; there is no recorded Java/native crash explaining these self-exits. No evidence identifies a specific integrity routine, signature check or Passport condition.
- [Stage A evidence CI 42994205737](https://github.com/manufact-test/nomusic/actions/runs/42994205737) is a **document consistency PASS**, with `STAGE_A_RELEASE_NO_GO`. Its JSON cannot replace written permission, a playable native UI or real user/audio testing.
- Redroid is headless, without Google Play/Play Protect, authentication or audible playback. It cannot validate the owner's HONOR. No user-facing APK has been approved.

## Public official integration / legal cross-check

1. [Yandex Music mobile software license](https://yandex.ru/legal/music_mobile_agreement/ru/) (published 03.04.2026, sections 1.4 and 4.1–4.4) sets limits on modification, derivative works, nonstandard distribution and commercial distribution without written rightsholder consent, subject to applicable law and any separate agreement. **Licensed CELIKOM recordings do not grant native Yandex app redistribution rights.**
2. [Archived Yandex Android vacancy](https://yandex.ru/jobs/vacancies/androidrazrabotchik-v-yandeks-muziku-_moya-volna_-11544) mentions an SDK embedding Music into **other Yandex applications**, not a publicly documented external SDK/partner license. Availability or lack of private commercial SDK is **unknown**.
3. [Official Yandex Music support](https://yandex.ru/support/music/ru/write-to-support) has an “other question” contact route. It is only a path to seek a suitable product/partnership contact, not authorization to proceed.
4. Android's public [MediaSession control](https://developer.android.com/media/media3/session/control-playback) allows external controllers to send playback commands; it does **not** expose an arbitrary third-party app's internal decoder/source selection callback. [Starting external Activity via Intent](https://developer.android.com/guide/components/activities/activity-lifecycle) opens an **external app**, not Yandex native UI embedded inside one CELIKOM APK. Neither route meets the approved contract.

No reviewed official public API supports **all at once**: one separately signed CELIKOM APK, publisher-owned full native UI/login/MyWave, its one original decoder, and rights-cleared source selection. This is **absence of verified evidence**, not proof of universal impossibility.

## Feasibility matrix (approved product contract unchanged)

| Candidate | Full native UI inside one CELIKOM APK | Original Yandex decoder + permitted source selection | Status |
| --- | --- | --- | --- |
| Official/licensed partner SDK or publisher-delivered component expressly providing both | **Potentially**, only if confirmed in writing | **Potentially**, only with documented callback, rights and support | **Only viable conditional route to investigate** |
| Android Intent to official installed Yandex | No: separate publisher app | No supported external source callback | Does not fit |
| Android MediaSession/MediaController | No: control/metadata only | No documented decoder substitution API | Does not fit |
| Music catalog/metadata API, track distributor, WebView, separate Media3 player | No equivalent full native UI | No single original decoder with source selection | Explicitly excluded |
| More independently re-signed APK/LSPatch/ABI/ZIP layouts | No demonstrated surviving native UI | No audio validation and software rights unresolved | STOP; already tested, no bypass |

## Minimum written answers required BEFORE renewed clone/embedding work

Publisher/authorized technical partner should explicitly confirm:
1. Whether an independent **third-party** Android app with its own package name/signing key may lawfully include or instantiate the **complete** native Music UI, login, MyWave and library.
2. Whether there is a supported, maintained component/SDK, delivery format, Android 13 compatibility and exact permitted distribution/update/signing terms, including **coexistence** with untouched official Music.
3. Whether original in-process decoder provides an approved, supported **source-selection integration** for authorized alternate recordings, retaining same-session pause, seek, Next, queue, preload and background playback.
4. Boundaries for rights to **the app** versus rights to **alternative masters/recordings**, user account/Passport handling, subscriptions, trademarks, geography, data protection and Play Protect.

A generic “we have an SDK” or “MediaSession supported” is insufficient; every product requirement must be explicitly matched. Do not store contracts, keys, personal contact information or other private correspondence in this public repository. Record only status and non-sensitive verification references.

## Decision and controlled next actions

**Current engineering decision:** A1 is **externally blocked pending rightsholder feasibility/permission**. This does **not** establish why the separately signed clone exits, and is not permission to change architecture. Stop binary repackaging and don't collect user credentials or disable protection.

**Owner decision needed to move the external dependency:** authorize *sending* the already prepared non-sensitive inquiry in `ANDROID-A1-PUBLISHER-SUPPORTED-INTEGRATION-OPTIONS-20261111.md`. Do not contact Yandex without that authorization. If approved, ask for SDK/rights/decoder answers above, obtain a written contract or explicit no-support answer before implementation. A written refusal or no qualifying interface is an architectural blocker requiring a **new owner product decision**, not an automatic switch to WebView, two apps or a different player.

**If a supported licensed route is confirmed:** separately verify native MAIN and MyWave/login (test identity, never scrape real user secrets), same original decoder with authorized recording, pause/seek/Next/background, independently signed side-by-side installation, Play Protect **ON**, real audible owner acceptance, exact signed binary SHA256 and immutable rollback backup. Only then mark Stage A accepted, release owner APK and explicitly remind owner about Stage B (independent injector replacing LSPatch).

Do not touch owner's single HONOR 50, accepted Android Test.50, Windows W61, extension, backend, production or publisher's original APK. Gate JSON `docs/android/CELIKOM-ANDROID-A1-STAGE-A-EVIDENCE-20261111.json` must remain NO-GO until real independent proof exists.

**Tracking:** [Issue #41](https://github.com/manufact-test/nomusic/issues/41); [approved master TZ](CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md); [authoritative handoff](ANDROID-A1-NEXT-CHAT-FINAL-HANDOFF-20261111.md).

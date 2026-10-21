# CELIKOM Android native companion — 0.3.26 candidate

This directory owns the current native application addon. The exact 0.3.22 Java source was recovered from its embedded source ZIP. Recompiling it produced a byte-identical `classes2.dex`: SHA-256 `650e8af017f98a9a016fb9b71386bb4774498eb6ca4a49606f16c8000ca57280`. `RECOVERED-0.3.22.json` preserves all recovered source hashes and the APK hash. The older `android/companion-probe` project is not the current installed application source.

0.3.23 playback was accepted by the owner on 2026-10-21. This candidate retains its synchronization/route handling and implements the agreed simple native UI based on the desktop popup: Start/Stop, Restore original, Upload version, Suggest song, access/song/version labels, collapsed Account/Support, and local diagnostic export. Connection instructions appear in the status area only when needed; no permanent setup section, promotional card or bottom tabs. Start now starts the service and arms replacement in one action; fallback identity confirmation remains explicit. Yandex notification access is not required.

0.3.25's interface was accepted by the owner; ordinary car/headphone/upload checks remain in progress. 0.3.26 adds the agreed notification shortcut. While the service runs, its quiet notification shows the actual current song/audio state, distinguishes missing replacement, pause, lost Yandex transport and lost audio session, and exposes Open CELIKOM and Stop. Suggest song is shown only for a fresh exact current target with no known existing replacement/preparation/error. It opens the existing presence check and explicit confirmation, never a direct background submission. The immutable action is pinned to service-run UUID, song key/ID and account epoch; unique URI identity prevents an old PendingIntent from being silently retargeted. State is sampled once per second and the notification is rebuilt only on meaningful changes, with no position ticker or repeated alerts. The activity and notification share a read-only playback snapshot. If app notifications are disabled, a conditional button opens Android's permission/settings flow without enabling playback. No new permissions, components, server endpoints or playback-engine changes are included.

Normal use: open Yandex Music and play a song; open its equalizer and choose CELIKOM; sign in once if needed and press Start; return to Yandex Music. Use the expanded CELIKOM notification to inspect state, propose the named song, open the application for file upload, or Stop. The equalizer is needed again only when the app reports that the trusted audio session must be reconnected. User notification permission is needed for the shade shortcut; Yandex notification-listener access is not requested. Android force-stopping/killing the process cannot be reported by the dead process itself; an old notification action never restarts or submits anything automatically.

0.3.25 corrects the owner-reported UI confusion: the Account summary explicitly says connected/not connected, with only login/logout inside it. Removed the separate access-check and activation buttons. The existing activation/entitlement operation now runs only after explicit Start, as in the desktop extension; simply opening the app or logging in does not start a trial. Account entitlement and expiry appear inside Account. Connection readiness is based on a current connected Yandex source and verified audio session, not merely an armed mode. While setup is required, the UI shows only the actionable instruction, with no prior song title. Once connected, it shows readiness, the actual identified song and the actual audio state separately. Late access/permission callbacks are fenced against Stop, logout, another Start and activity destruction. Audio synchronization and long-run behavior remain unchanged.

0.3.24 removes the former twelve-minute playback/service timers. The foreground service retains playback after the app task is swiped away, keeps a renewable 90-second wake-lock lease, and releases resources on explicit Stop or service destruction. This is not an auto-start/auto-resurrection feature: Android can still stop the process. The persistent notification provides Stop.

Long-session safeguards: two rotating local diagnostic segments of at most 8 MiB each, export of an immutable snapshot without stopping playback, 60 recent identity observations, 32 in-memory albums, the existing three-file/60 MiB audio cache, and a renewing budget of at most 24 public album requests per twelve-minute window (not a lifetime quota). Transient logging failures no longer terminate playback. Unknown/ambiguous identities keep the original.

Native contribution actions use existing server contracts only, after the user selects the exact current song, chooses a local MP3/M4A, confirms rights and explicitly submits. Upload/suggest use the desktop presence check first; track/account changes invalidate an unsubmitted target. Upload transfers run separately from serialized token refresh/playback downloads, have byte/time bounds and preserve a request UUID on retry. Support submits only typed text and, for song reports, the pinned identity/category/version; it does not attach raw diagnostics or send anything automatically. No real contribution or support message is sent by the offline checks. Desktop registration/recovery/promo/referral flows are not part of this native candidate.

The APK uses the same package and signing key, versionCode 27 / versionName 0.3.26, to update the accepted installation. Only app label, native activity theme and foreground-service description change in the manifest; permissions/components and original catalogue assets remain identical. Calls remain a deferred owner test. Hardware playback, Android background scheduling and real server submissions need physical/owner verification; host tests do not certify them.

## Isolated work

Work only in `feature/android-isolated`, under `android/**` and `docs/android/**`. Its pinned workflow rejects changes to desktop, backend, website, root configuration and workflow definitions. Do not merge this workspace branch wholesale into the desktop branch. Desktop 0.4.61 is commit `3a037e5fd5c1d09cd811dbf12dc80c7a12ed5e2e`; Android work does not change that ref.

The owner's accepted scope requires no staging setup for these client-only fixes. Builds/tests do not contact production. The installed APK uses the existing API and independent Android installation/session as before; no API/auth/session/catalogue deployment is included in this work.

## Build and verify

Use JDK17, Android SDK API36, compatible Android build-tools, Apktool2.11.1, the exact original 0.3.22 APK and external signing backup. Dependency hashes and official coordinates are pinned in `build-inputs.json`. Put the pinned JARs in `deps/` (ignored). Keep signing files outside the source directory. No network fetch or server snapshot is part of the build.

```sh
python3 build_release.py \
  --sdk /absolute/android-sdk \
  --build-tools /absolute/android-sdk/build-tools/version \
  --apktool /absolute/apktool.jar \
  --base-apk /absolute/CELIKOM-0.3.22-install.apk \
  --signing-dir /absolute/private-signing-directory \
  --output /absolute/CELIKOM-0.3.26-install.apk
```

The script compiles actual Android source, executes deterministic engine/phone replay/parser/API tests, creates addon DEX, packages an exact source snapshot, signs with the existing key, and verifies package/signature/version/permissions/assets/embedded source. Host audio adapters are test code only and are never sent to D8. Build output includes a verification JSON with `physical_phone_playback_verified: false`; it cannot certify headphone hardware behavior.

A physical check needs one update installation and an ordinary listening session beyond twelve minutes with screen off, headphone/vehicle Bluetooth route changes, seeking and track changes. Check interaction with the installed UI while parked. Calls remain optional/deferred. Keep other observations in one report rather than creating a new build for each minor issue. Do not uninstall the installed app first: the matching signer/package/versionCode are intended to preserve account and settings during an update.

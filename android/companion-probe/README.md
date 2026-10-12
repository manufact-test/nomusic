# CELIKOM native companion diagnostic 0.3.16-probe

## Current exact-ID investigation, 2026-10-13

Distributed panelOnly build adds no notification listener, Accessibility, internet, microphone or storage permission. The owner-approved audio checks remain available, but replacement/UI work is gated by a real source track ID. No artwork or metadata matcher is accepted as proof of identity; Ynison/account integration is withdrawn.

Two new investigation tools:

- The existing **Проверить состояние плеера Яндекса** action also attempts one independent framework MediaBrowser connection to the same enabled, exported and unprotected Media3 service, with CELIKOM's real identity and null hints. It records whitelisted framework metadata, the active queue item's URI/extras and session/browser/playback extras under `legacy_identity`, separately from the accepted Media3 observation. No playback, rating, search or unavailable library command is sent. Stop/reconcile and the existing two-minute observation lease release both connections. Old process evidence is marked stale. Framework conversion is not assumed to expose a catalogue ID; physical evidence is still required.
- **Подготовить код Яндекса для проверки ID** reads the installed application's base/split APK program archives via PackageManager. It exports only root `AndroidManifest.xml`, `resources.arsc` and `classes*.dex`, plus a version/file-list report. It never opens the application's data directory, preferences, accounts, downloaded songs or history; assets and arbitrary ZIP paths are excluded. Output is bounded to 200 MiB uncompressed and 128 entries, partial output is deleted on failure. A private FileProvider grants read access only when the owner uses Android's share sheet. No program file is modified and no new permission is required. Files may be large; this is an engineering export, not a user onboarding requirement.

Owner steps: install over the prior diagnostic; open CELIKOM normally (not via the equalizer), press the code-export button, prepare and save/send the resulting `yandex-code-*.zip` to the engineering chat. Separately, while a song is already playing, press the existing player-check button once and copy the report. Do not repeat the accepted audio/route checks.

Tests cover genuine framework connection and source-ID/URI evidence with no control commands, stale-process rejection, archive allowlisting across base/splits, omission of unrelated entries, cleanup on missing code, and the existing regression suite. Fixtures ship only in debug/test builds. Emulator tests cannot establish actual Yandex identity availability or whether HONOR permits reading the installed program archive.

## Historical diagnostic notes

Read-only owner diagnostic for installed `ru.yandex.music`, prepared after the owner rejected the WebView product route. This is not Beta and does not implement replacement. It is an isolated diagnostic, not a separate final product client; future integration must use the common account/EntitlementService and catalog.

No INTERNET, microphone, audio capture, effect application, accounts, grants or payment. Standard AudioEffect panel and OPEN/CLOSE receiver record events only. Broadcast package/session extras are untrusted claims; only actual panel callingPackage is recorded as verified origin. A missing callingPackage stays unverified. Session zero and stale IDs must never be used to attach effects. No session enumeration, interception, credential entry or APK modification.

Optional NotificationListener permission enables filtering MediaController by Yandex package before metadata access. Other notification contents are not read. Only title/artist/MEDIA_ID/MEDIA_URI without userinfo/query/fragment, duration and state are exported, capped. Raw Bundles, artwork, notification text and credentials are never exported. MEDIA_ID is a candidate, not an exact Yandex ID until independently cross-checked. Report remains on device, manual clipboard/share only. Recent audio-effect events are capped at30. Last state includes timestamp; it can become stale after disconnect/process death. Stop observation, clear, and revoke notification access are available.

Owner Honor50; exact Android/Yandex versions unknown and reported automatically. Steps: install, allow notification access for CELIKOM, open normal Yandex Music, inspect its equalizer settings and select CELIKOM if offered, play/next/pause/resume/screen-off30s, return and copy report. Missing equalizer/panel or IDs is an informative result, not a request to reinstall/login elsewhere. For exact ID verification, compare the observed candidate with a track link copied through Yandex's own Share function, without dumping other metadata.

Tests: spoofed broadcasts never imply verified caller/effect, bounded events, disabled observation, metadata sanitization, no audio/network permissions, native UI screenshot at font scale1.3. Emulator has no Yandex, so these tests are not service proof. API35 build/lint/native test; previous owned cross-app audio attenuation API29/35 is separate evidence. Physical background/routes and failure restoration are not accepted yet.

CI uploads only encrypted CMS envelopes (public recipient cert, private key stays outside git); no plaintext APK/screenshot artifact. This diagnostic uses ephemeral CI debug signing, not production distribution signing. Does not replace the installed old `pro.celikom.spike` WebView APK: owner can remove that obsolete diagnostic separately. Do not uninstall/reset any extension/account/backend state. PR6 stays unmerged, Stage16 partial,17 not started,15 excluded.

0.3.1 inspects only the current queue item and allowlisted numeric extras, records bounded state history, deduplicates broadcasts and keeps callbacks stable per session token. No real-Yandex effect or exact-ID acceptance is implied.

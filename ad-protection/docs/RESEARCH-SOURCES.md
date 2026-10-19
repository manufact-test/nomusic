# Existing projects & reuse/licensing review (Stage 0 notes)

These are research pointers only; **none of their source code has been copied** into ad-protection/.

| Project | Reference | Observed approach | License observation | Decision |
|---|---|---|---|---|
| fixYMusic | https://github.com/IyepI/fix-yandex_music | MutationObserver, selected DOM banner/modal removal; no verified audio ad suppression | Repository showed no declared license when checked | Study ideas; NO direct code copy without permission |
| YaBlocker | https://github.com/right-git/yablocker | DOM advertising selector scanning; documentation differs from requested manifest permissions | No declared license when checked | Research only |
| AdGuard Browser Extension | https://github.com/AdguardTeam/AdguardBrowserExtension | Mature browser filtering architecture | GPL-3.0 | Study design; don't copy into proprietary source without compliance/legal review |
| YaMusic Desktop Client | https://github.com/cptn73m0/ya-music-desktop | Webview injection: fetch/XHR/window.open URL checks and DOM hiding | MIT when checked | Candidate for carefully adapted ideas/code with preserved notices; do NOT indiscriminately monkey-patch global fetch/XHR |
| YandexMusicBetaMod | https://github.com/Stephanzion/YandexMusicBetaMod | Modifies desktop Yandex Music app; claims ad suppression | No declared license when checked | Different product surface; research only |

Notes:
- Some community add-ons install unpacked; that does NOT mean they passed Chrome Web Store review.
- Repositories and README claims do not demonstrate full audio ad blocking.
- Licensing may change: recheck the exact version before reuse.
- Verify rules using primary Chrome Web Store and Chrome extension docs at Stage 1/6; store acceptance cannot be promised.
- Do not infer permission to bypass paid access or region protections from the existence of a public repo.

Official documentation starting points:
- https://developer.chrome.com/docs/extensions/develop/concepts/declarativeNetRequest
- https://developer.chrome.com/docs/webstore/program-policies/

# CELIKOM Windows Companion — isolated planning home

**Status:** PLAN / DESIGN ONLY; 2026-11-08. No Windows client, integration, installer or working prototype has been created. Do not market this as an available product.

## Product in one sentence

A small CELIKOM Windows companion runs **next to the official Yandex Music desktop app**. The user listens and controls playback in Yandex Music. CELIKOM, when authorized and technically supported, resolves an exact track ID through the existing CELIKOM backend and **substitutes the audio source inside the original player**, without running an independent competing player.

This is a **hypothesis to validate on real Windows 10/11**; not a proven implementation. No replacement when compatibility, rights, identity, access or audio validity are uncertain.

## Branch boundaries

- Owner-accepted **browser extension 0.4.73** remains frozen at `archive/desktop-0.4.73-accepted-20261104`; the archive and its existing code must NEVER be modified.
- This planning branch: `planning/windows-companion-v1-20261108`, created from frozen accepted archive SHA `63d8cd891e1db82e0245122391fd4ab5cdd323be`.
- Planned isolated PoC branch: `experiment/windows-companion-integration-20261108`, **do not merge into stable or run deployments**; may only advance after independent approval.
- An existing, **different** `experiment/desktop-native-source-20261108` belongs to the browser-extension investigations, NOT this Windows-native app. Do not overwrite, reuse, merge or rebase it.
- Android work, song catalog work and the browser-extension fixes are owned by separate chats. Our scope is ONLY `docs/windows/**` while designing. Future code is allowed ONLY under `windows-companion/**` on the isolated PoC branch.
- No edits to `main`, `develop`, `extension/**`, `android/**`, `server/**`, `website/**`, workflows, production, subscriptions or approved audio.

## Documents

1. [ARCHITECTURE.md](ARCHITECTURE.md) — architecture, candidate integration routes, backend/contracts, safe fallback and threats.
2. [PRODUCT-DESIGN.md](PRODUCT-DESIGN.md) — Windows app screens, controls, copy, states, styling, interaction and accessibility.
3. [ROADMAP.md](ROADMAP.md) — feasibility gates, implementation stages, regression and handoff.
4. [mockup.html](mockup.html) — **offline interactive visual concept**, no real Yandex/audio/server integration, no production credentials, no telemetry.

## Frozen sources

- Accepted extension reference: `docs/desktop/README.md` and `docs/desktop/LIVE-APPROVAL-073-COMPLETE-FILE-2026-11-04.md` at the frozen archive.
- Current architecture: `docs/adr/0003-player-state-sources-and-bridge.md`, `docs/adr/0005-private-api-range-and-catalog.md`.
- CELIKOM brand: `docs/website/BRAND-GUIDE-v1.0.md` (Manrope, #0B1013, **#66E0BF** mint, #F7F8F4 paper).
- Current accepted brand/website sources are visual reference, not authorization to change the site.
- Competitor research: https://github.com/Hazzz895/FckCensor, https://github.com/S4YN3X/FkCensor, https://github.com/PulseSync-LLC/PulseSync-mod. Third-party code must not be copied without separate license review.
- Official Yandex Music Windows app: https://music.yandex.ru/download/; requires Windows 10+ and Yandex subscription.

## NEXT CHAT: implementation handoff

1. Read all four planning files and the frozen accepted docs; check the **latest** GitHub heads for the browser/Android teams read-only.
2. Ask for/observe a **real unmodified official Windows app** version, location, process tree and playback behavior; NEVER request passwords, cookies, private keys or audio files.
3. Complete Gate W0 / W1 in ROADMAP.md before changing any application files. Start with no-patch compatibility/discovery research.
4. Select only one isolated PoC route after a documented decision. Show an exact, reversible failure/rollback path.
5. Use `experiment/windows-companion-integration-20261108` for experiments; keep the planning branch as reviewable specifications. Never publish, deploy, change shared API or disturb browser/mobile work.
6. Deliver measured outcomes + a reversible test only when approved. If source interception is technically or contractually untenable, report the blocker rather than force a secondary-player workaround.

**Acceptance rule:** the owner must explicitly accept the integration route and visual mockup before implementation. Passing a unit test does NOT establish compatibility with the installed Yandex client.

## Current checkpoint: W2 read-only diagnostic (2026-11-08)

Owner's real Windows 10 / Yandex Music 5.126.1.0 W1 ASAR report is received. W2 source is implemented, native Windows CI passed (run 42506616157), test ZIP is saved to ChatGPT Library at `CELIKOM/Windows/Test/CELIKOM-Windows-Probe-W2.zip`. The user has **not yet** run W2; no source substitution has been attempted.

**For the next chat, read [NEXT-CHAT.md](NEXT-CHAT.md) first**, then [W2-TOPOLOGY-READONLY-20261108.md](W2-TOPOLOGY-READONLY-20261108.md). The original W0/W1 + W2 traces and tests are distinguished there. Do not repeat owner W1 questions. Continue only under `experiment/windows-companion-integration-20261108`, never modify the frozen browser extension or other teams.

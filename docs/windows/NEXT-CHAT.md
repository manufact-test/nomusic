# CELIKOM Windows — FIRST HANDOFF / 14 November 2026

Repository: `manufact-test/nomusic`.
**ONE active product line:** `main` @ `7a4768ecc7366abeb0358337f83e514e85cd8d53`.
Exact post-W57 green rollback: `backup/windows-main-post-w57-ci-green-20261114` at the same SHA.
Previous W54 rollback: `backup/windows-main-post-w54-gain-witness-20261114` @ `b045c640783e2708f5a887c5aa7eafbcf2febc50`.
No new `experiment/*` branches. Before each substantial change create exact `backup/*`, and avoid touching Android, extension, private original media or unrelated server logic.

**Read first:**
1. `docs/windows/W102-SINGLE-PRODUCTION-LINE-YANDEX-15MIN-AND-WORK-ORDER-20261113.md`
2. `docs/windows/W101-CELIKOM-WINDOWS-AUTO-UPDATE-AND-ROLLBACK-POLICY-20261113.md`
3. `docs/windows/NEXT-CHAT.md` (this file)
4. GitHub issues #52, #53, #54, #56, #57, #58; read actual code before changing.

**Exact CI proof at takeover:**
- Main CI [43523524721](https://github.com/manufact-test/nomusic/actions/runs/43523524721) — SUCCESS.
- Windows integration CI [43523524722](https://github.com/manufact-test/nomusic/actions/runs/43523524722) — SUCCESS, including W22/W23/W60 audio/VPN/source/403, W21 recovery, W24 ASAR/catalog, W15 tests and warning-as-error GUI compile.
- Earlier W103 `d903ffae` failed four integration tests because expected reload occurred before new 150 ms confirmation window; fixed in `7a4768e` with tests preserving actual delayed behavior. Do **not** revert to the failed intermediate.
- Stage 5 Hostinger restore proof [43514995243](https://github.com/manufact-test/nomusic/actions/runs/43514995243) SUCCESS: 1498 original audio SHA256 checks and isolated DB restore with Big City Life gain sidecar. Live DB untouched in that test.
- Dedicated gain-stage job [132132259655](https://github.com/manufact-test/nomusic/actions/runs/43495186951) SUCCESS: Big City Life track 40371622, configured +11.5 dB, measured +6.70 dB RMS and verified signed Range 206. Its parent workflow failed later in updater ZIP verification, **not** sidecar staging.

**Open defects (do not call them done):**
1. VPN reconnection 40–50 seconds — recovery code/CI exists, owner field test pending.
2. #52 «Ты» (тринадцать карат) false green — current decoder proof guard exists; audible alternative still needs confirmation.
3. #53 Brave/Windows load or freeze — durable Electron memory/event-loop + source diagnostics now exported; root bottleneck unproven. Need owner diagnostic and Task Manager CPU/RAM/GPU capture. Origin of elevated-rights prompt still unproven.
4. #54 Big City Life sudden mid-track volume dip — W54 records signed gain-variant URL selected/missing, native volume drop and source-left. This is **diagnostic evidence, not an acoustic fix**.
5. #56 admin gain — Windows private offline sidecar server stage/restore passed; owner seek/Next/crossfade/volume/headroom proof pending, no changes to extension originals.
6. #57 signed 403→206 hiss/pop — W103 now gives 150 ms post-prime CDP confirmation chance before reload; approved decoder already playing cancels pending reload only. No proof means bounded reload proceeds. CI green, owner acoustic test pending. Do not force a production 403.
7. #58 «Моя волна» and other original tracks pop under VPN change — original/unknown no-reload guards CI green, acoustic test pending.

**Other open work:** first/second/third start race, disappeared diagnostics, initial popup, false outdated-module message, tray autorun default, upgrade/repair user acceptance. Yandex releases are discovered every 15 min on `main`; app startup and EXE/ASAR change watcher are integrated, but *immediate recheck after bridge/start failure* remains open. W101 signed automatic in-app stable update and safe rollback are **not implemented**; current updater is manual/staff only.

**Next work order:** finish exact native bridge/start-failure Yandex compatibility recheck; complete signed in-app update + rollback per W101; verify existing startup guards and acceptance flow; run CI after changes; make **one** coherent final Windows EXE + ZIP and link it only when successfully built and independently verified. Do not send partial TEST installers or ask for new secrets/accounts/emails. The user expects big completed chunks and a short status, not endless theory. Mass release only after owner QA. No final package has been delivered and nothing was installed on user's PC from this handoff.

**Owner-side proof required:** VPN A→B reconnect, «Ты» audible replacement, Big City Life full-song loudness, natural 403→206 without hiss, «Моя волна» originals on VPN switch, Brave/Windows resource usage, and startup/reboot behavior. Never claim a real playback bug fixed by CI alone.

# CELIKOM Android Update Center — deferred UI follow-up (2026-10-30)

User tested newly signed CELIKOM 0.3.58 on HONOR and reports layout generally fine. One deferred UX issue:

- On initial app open, status presently reads like a call to action ("CELIKOM 0.3.58 · Проверить обновления") rather than showing the latest known result. Do not force manual tap before communicating known update status.
- Persist last verified server result with timestamp and installed versionCode. If cached successful result establishes installed version as current, immediately render "У вас последняя версия CELIKOM" in mint green on re-entry; in parallel refresh when interval allows, without flicker.
- Until any successful check, do not falsely claim latest; use neutral "Статус обновлений ещё не проверен" with auto-check. If cached result expired, surface timestamp/neutral status while checking. On update found, display release and actions. On failure, distinguish stale cached confirmation from fresh error.
- On manual check, keep stable region height and a brief minimum checking indicator, then return to appropriate current/update/error state.
- This is a deferred change to combine with next Android fixes, not an urgent standalone APK.
- Audio Gate G remains physically unverified on user's HONOR. User now testing real music on signed 0.3.58; collect subjective and diagnostic reports (track changes, seeks, pause, buffering, Bluetooth and network changes). Do not change audio based only on updater UX issue.

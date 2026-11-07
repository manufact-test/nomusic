# CELIKOM Android — актуальная передача / заморозка 2026-11-07

**Все Android-разработки поставлены на паузу по решению владельца на время миграции с Hostinger. Никаких новых APK, программных правок, серверных публикаций или самостоятельной миграции.**

**Обязательный полный документ:** [ANDROID-2026-11-07-FREEZE-TEST50-ROOT-CAUSE-AND-HOST-MIGRATION.md](ANDROID-2026-11-07-FREEZE-TEST50-ROOT-CAUSE-AND-HOST-MIGRATION.md)

**Возвращаемся к оригинальному эталону Test.50**: commit `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`, immutable backup `backup/android-test50-exact-source-owner-accepted-20261106`. Test.51–53 отвергнуты после диагностики на реальном HONOR 50. Последний combined: `CELIKOM-combined-20261107-152610.txt`; видео: `SVID_20261107_152425_1.mp4`.

После миграции и отдельного разрешения владельца искать **истинную причину** разницы управляемости треков/альбомов (RASKOL, «Дым» и другие): UI Pause/Seek vs Media3 состояние, застревание `BUFFERING` при `playWhenReady=true`, stale source между песнями. Test.53 ввела ложное `source_audio_quarantine_started` на нормальном треке, поэтому не переносить эту эвристику. HTTP `451 REGION_RESTRICTION` и `no_unique_candidate` — отдельная проблема определения альбомов/редакций, не путать с управлением аудио.

Не трогать эталонные DSP/переходы Test.50, стабильный Android, расширение ПК, backend/Hostinger до отдельной команды. Ветка `feature/android-0385-test50-rollback-package-20261107` содержит только Test.50 со следующим установочным номером `test.54/code86140`; работоспособность установки на телефон ещё не подтверждена.

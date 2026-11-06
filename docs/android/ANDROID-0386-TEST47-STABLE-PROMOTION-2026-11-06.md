# CELIKOM Android 0.3.86/code87 — сохранение Test.47 в основном OTA (06.11.2026)

## Решение владельца и граница релиза

Владелец прослушал Test.47 на HONOR 50 и не заметил существенного улучшения по сравнению с Test.46: переходы по-прежнему отличаются при повторах, слышен периодический «бжык». Он прямо разрешил сделать Test.47 **текущей основной** Android через обычную кнопку «Проверить обновление» перед переездом Hostinger. Это **контрольная рабочая версия, а не принятая по акустике**. Следующие эксперименты — исключительно отдельная Test APK; менять stable/OTA без нового согласования нельзя.

## Подтверждённая публикация

| Поле | Проверенное значение |
| --- | --- |
| Stable package | `pro.celikom.nativeprobe` |
| Версия / код | `0.3.86` / `87` (ранее `0.3.85` / `86`) |
| Исходник релиза | `3b51aa94706da2a94b81fab47e25222f16831133` |
| Изолированный функциональный Test.47 source | `9c90a73fc87a0b9b12d6c4da66c98028b14073cc` |
| Ветка релиза | `release/android-0.3.86-test47-promotion-20261106` |
| Ветка автоматической публикации | `feature/android-unified-preparation-seek-gate` |
| Предрелизный CI | [#42210033200 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42210033200) |
| Релизный CI, подпись и Hostinger | [#42210287109 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42210287109) |
| Live OTA manifest | [stable.json](https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json) |
| Signed APK в отдельном хранилище | [CELIKOM Android 0.3.86 в ChatGPT Library](https://chatgpt.com/library?file_id=libfile_b9f95444c49881918f437aa9add77ffc&account_id=personal) |
| APK SHA-256 | `a8b87263f177932eae1e11770a9e0dcd8fc5743aa10f2095bb00691fe8bede8e` |
| APK размер | `8 841 289` байт |
| Сертификат SHA-256 | `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` |

Сервер уже вернул `versionCode=87`, `channel=stable` и точную ссылку на immutable `87-<sha256>.apk`. Файл успешно скачан с этого адреса: локальная SHA-256 **совпала** с manifest. Пакет и оригинальный подписант прежние, так что установленное основное приложение code86 должно обнаружить code87 через штатный UpdateCenter. **Физическая установка на HONOR владельцем пока не подтверждена.**

## Что изменено относительно Test.47

- Аудио-сердцевина перенесена без дополнительных изменений: текущий source > speculative transfer, early Next skips impossible full-file wait, 16 cached files/96MiB, прежние accepted seek/ACK и no-blind play safety.
- Только релизная идентичность `release-spec.json` + `AppVersion.java` обновлена на `0.3.86/code87`; тест негативных контрактов обновлён для запрета предыдущих версий.
- `build_test_release.py` перестал привязывать подготовку отдельной Test APK к точной версии stable `0.3.85`; по-прежнему требует один валидный stable AppVersion и вставляет отдельную Test версию. Это не меняет исходник прежней подписанной Test.47.
- CI разрешает независимую проверку ветки подготовки до перепривязки основной публикации; publisher, OTA endpoints, cert и backend logic не переписаны.
- Full native regression + SDK36/D8 + signing/signature/archive/manifest verify и fetch live manifest прошли; каталог/расширение ПК/сайт/админка не изменены.

## Сохранённые ориентиры

- **До промоушена stable 0.3.85:** `backup/android-0385-pre-0386-stable-20261106` → `7b4558611f9e90fbcd9ca3eee61048a90382db87`; исторический `0.3.85/code86` manifest и SHA `e23c962d969129c5b839ed3676e36d6a337342e2761bde852e2048bbf1bda88a`.
- **Точная Test.47 перед промоушеном:** `backup/android-0385-test47-owner-selected-20261106` → `9c90a73fc87a0b9b12d6c4da66c98028b14073cc`; [подписанная изолированная Test.47 APK](https://chatgpt.com/library?file_id=libfile_8dc571f14c5481919d79fca6929cfed6&account_id=personal), SHA `8a02d9f66ada3d02d6793b57dfcd66872ced15836a6a5e67166bc908fb7fbd15`.
- **Test.46 перед Test.47:** `backup/android-0385-test46-pre-test47-20261106` → `77f393785371dd9a01f8c27f655e5682584730d4`.
- **Принятый старый эталон Test.33:** `backup/android-0385-test33-owner-accepted-20261105` → `53d94d66a32b332b62848e0895285d81dda226e9`.
- Существующие более старые владельческие backups остаются неизменёнными. Ничего не переписывалось принудительно.

## Новая диагностика: Test.47 не устраняет слышимый шов

Файл владельца `CELIKOM-combined-20261106-141814.txt` (5 592 строки): Test.45 JSONL-строки 4–3075 (263,5с), Test.46 строки 3076–4244 (109,8с), Test.47 с 4245 до конца (~104,6с; segment без `run_end` в экспорте).

| Сессия | Transport join summaries | Median start→summary | Range | Commanded silence | Ready lookahead |
| --- | ---: | ---: | ---: | --- | ---: |
| Test.45 | 37 | 391мс | 320–1503мс | 2 (96, 65мс) | 30 |
| Test.46 | 14 | 527мс | 309–654мс | 2 (167, 155мс) | 8 |
| **Test.47** | **17** | **394мс** | **321–717мс** | **4 (214, 219, 75, 169мс)** | **17** |

Сопоставление длительностей разных сессий не является controlled A/B: треки/темп навигации/настройка Yandex crossfade могли отличаться. Все четыре неожиданно зарегистрированных `commanded_silence` Test.47 возникли вскоре после **SAME_ITEM_SEEK с hot cached decoder** (около 8,165; 15,100; 16,643; 31,407с), а **не** при 17 новых joined-track границах. Это диагностика *командного состояния*, не измерение фактической акустической тишины. В 17 `replacement_join_transport_summary` указано `sourcePcmMeasured=false`, `phaseVerified=false` и разброс фазовой оценки (в ряде переходов более 80мс): значит, ускорение prefetch/очереди нельзя выдавать за исчезновение слышимой склейки. Отзыв владельца о почти неизменном звуке с этим **совместим**.

## Следующий безопасный шаг

Основная code87 остаётся замороженной точкой восстановления. Продолжать только в изолированном Test.48 или следующей тестовой ветке после проектирования **одного полноценного акустического пакета**. Не повторять круг «уменьшили таймер → прибавили таймер» без отдельного доказанного выигрыша. Не менять принятый seek/ACK или требовать микрофон/Accessibility/захват системного аудио; прежде оценить ограничения двух независимых PCM/аудиосессий и влияние Yandex crossfade. Четыре `found:false` — ответственность каталога другого чата, не Android title-only обход.

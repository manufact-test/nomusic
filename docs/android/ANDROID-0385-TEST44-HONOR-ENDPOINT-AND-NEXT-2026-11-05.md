# CELIKOM Android Test.44 — настоящий сбой владения звуком и медленный Next

05.11.2026. Отдельная экспериментальная ветка `feature/android-0385-test44-owner-endpoint-20261105`; функциональный исходник `e7eda030adfac2ab719603c35348ab33742a48dd`. Владелец не признал Test.43 акустическим эталоном: субъективно много песен по-прежнему переключаются с заметными срывами/задержками. Test.44 ещё не принят физическим прослушиванием.

## 1. Только два свежих Test.43, без дублей из combined

Архив владельца: `CELIKOM-combined-20261105-225544.txt`, `CELIKOM-combined-20261105-225740.txt`, два видео `SVID_20261105_225335_1.mp4`, `SVID_20261105_225637_1.mp4`. Приватные исходники диагностики и видео **не коммитить**.

- Первый combined: архивные Test.42 `21:57:15`, `22:00:16` и свежий Test.43 `2026-11-05T22:53:23+03:00`.
- Второй combined: повтор старого Test.42 `22:00:16`, повтор того же Test.43 `22:53:23` и ещё один Test.43 **`22:55:50+03:00`**. Учитывать два уникальных Test.43.
- В видео видны частые ручные Next/выбор других треков; второй ролик начинается в настройках Яндекса. Владелец утверждает, что во втором прогоне был включён плавный переход Яндекс.Музыки; само значение настройки **не записывается** в CELIKOM JSON.

| Только Test.43 | 22:53 | 22:55 |
| --- | ---: | ---: |
| Участков между границами/стартом | 20 | 10 |
| Успешных первых обычных same-song joins | 20 | 10 |
| Медиана граница → join | **0,545 с** | **1,105 с** |
| Максимум граница → join | 3,206 с | **5,281 с** |
| Ошибок `replacement_join_exception` | **2** | 0 |
| `current_handoff_timeout` | 1 | **3** |
| `replacement_stream_runway_wait` | 2 | 5 |

Цифры **не доказывают** зависимость скорости от настройки Яндекса: разные плейлисты, сеть, прогрев и ручные переходы. Мягче воспринимаемый звук второй записи не означает более ранний CELIKOM join.

## 2. Точная причина двух срывов во время fade

- В 22:53-прогоне на `46.571 с` («Каменные цветы») и `119.007 с` («Монпасье») зарегистрированы **`IllegalStateException: secondary gain without exclusive owner`**, `stage=final_decoder_gain`, `requestedDurationMs=220`.
- Их `lastCommandedMix=0.9997536` и `0.9990203`. `AudioOwnership.blendSameSong()` ещё правильно держал состояние `SAME_SONG_BLEND`: исключительное `REPLACEMENT` возможно **лишь после точного `mix=1f`**. Ошибка в `ReplacementEngine.fade`: прежнее `if(mix<0.999f)` пропускало почти-единицу и сразу вызывало `applyVolume(1f)`. Защита отклоняла команду, Test.43 возвращал оригинал и повторял попытку через 1,2с.
- От границы до успешного join: «Каменные цветы» **2,781 с**, «Монпасье» **3,206 с**. В Test.44 завершение разрешено **только после точного 1f**, при `0.999xxx` выполняется следующий ограниченный 20-мс шаг. `AudioOwnership` и экстренный retry сохраняются без ослабления.

## 3. Долгий Next — отдельно от fade

- 22:55-прогон: «Нету интереса» (10AGE) `51.243→56.524 с`, **5,281 с**. Уже **после** смены песни `source_next_identity_resolution` в `51.362 с` распознал её *текущий* alias, но `replacement_lookahead_prefetch_start` в `51.363` запустил для неё speculative **full-file** download. CELIKOM потратил 1,2с на `current_handoff_timeout`, отменил работу, только затем начал правильный progressive sparse current. Свою долю задержки дали последующее ожидание safe runway и muted warm alignment.
- Test.44: если `progressiveColdAllowed` и alias speculative observation **уже равен текущему**, пропускать speculative full-download. Текущая песня и так проходит fresh live resolve + progressive preparation. Настоящий *следующий* alias и frozen full-file prefetch/handoff не изменены.
- «Оля Лукина» (`78.208→81.924`, **3,716 с**) и «Танцуй сама» (`83.485→87.169`, **3,684 с**) — другой случай: legitimate full-file next prefetch начался **до** границы, но не завершился за 1,2с ожидания current handoff, затем sparse fallback ждал runway. Эти два случая Test.44 **не гарантирует устранить**.
- В 22:53-прогоне два promoted inflight prefetch успели завершиться за 0,61–0,79с после ожидания. Поэтому запрещать все предзагрузки или убирать 512-KiB safe runway нельзя: хорошим песням можно навредить.

## 4. Изменения и ограничения

- Только Test source: `ReplacementEngine.java`, `JoinTransitionPolicy.java`, новый `Test44OwnerEndpoint.java`; version `0.3.85-test.44`, `versionCode=86129`, `pro.celikom.nativeprobe.test` / CELIKOM Test.
- Не меняли формулу fade 140–220мс, положительный `gain_db`, Media3, matching, подписку, дополнительные Android permission, стабильную `0.3.85`, Hostinger/OTA, Chrome и эталонные сохранения.
- Все host regression, прежний HONOR golden seek, Test.43 recovery, настоящая next prefetch, Test.44 endpoint/cold-current checks и тестовый packaging contract **PASS локально**. Android API36/D8 и подпись проверяются обязательной отдельной GitHub CI; рабочий эффект на телефоне неизвестен.
- Даже без ошибок `final_decoder_gain` отдельные оригинальная и альтернативная записи **не имеют измеренной общей PCM-фазы**. Поэтому все «пшики» нельзя честно объявлять исправленными по транспортным логам. Следующая приёмка — реальное прослушивание, с/без Яндекс crossfade при желании владельца.

Референсы сохранены: Test.42 `d4ae7fc2ca6f65bc1db8c483d4e2f27e46f7edb0`, Test.43 `3695dffb1b2eb5e006c0d6ea571490c1be790568`, owner-accepted Test.33 `backup/android-0385-test33-owner-accepted-20261105` → `53d94d66a32b332b62848e0895285d81dda226e9`. Новая Test.44 **не эталон** до решения владельца.

## 5. Сборка и скачивание

- **Функциональный source SHA подписанной Test.44:** `e7eda030adfac2ab719603c35348ab33742a48dd`.
- [GitHub Actions #42101050469 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42101050469): native-android/API36/D8 PASS, host/replay PASS, build-test-app/signing PASS. Stable/publish jobs SKIPPED.
- **[Подписанная Test.44 APK напрямую в ChatGPT Library / CELIKOM](https://chatgpt.com/library?file_id=libfile_30dcedc847a08191bd852552ab474ecf&account_id=personal)**; APK файл без ZIP, `8 824 985` байт.
- `0.3.85-test.44`, `versionCode 86129`, пакет `pro.celikom.nativeprobe.test`, имя `CELIKOM Test`; SHA256 APK `ba4ec40f756382506691d03d5698dd408dbe31000b7fd9e5f207d4ffe441a38a`.
- Проверка CI receipt против неизменённых байтов APK **PASS**; сертификат совпадает с исходным `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`; **APK Signature Scheme v3 VERIFIED** (v2 отсутствует). Оригинальные assets и границы пакета проверены; OTA updater отсутствует, Hostinger write = false.
- APK ещё **НЕ прошла физическую/акустическую приёмку**. Этот отчет и NEXT-CHAT — отдельное изменение документации после функционального SHA и не являются исходником подписанной Test.44.

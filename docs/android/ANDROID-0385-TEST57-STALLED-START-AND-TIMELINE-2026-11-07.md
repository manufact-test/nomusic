# CELIKOM Android Test.57 — зафиксированный новый кандидат, 2026-11-07

**Статус:** сборка **PASS**, на телефоне **НЕ подтверждена**. Владелец попросил новую версию с правками *из принятой Test.50*, а не перепаковку/откат. Вечером следующего дня планируется завершение миграции Hostinger и переход на новый workflow через MCP. НЕ деплоить backend и НЕ менять стабильно работающее приложение при подготовке APK.

## Единственная исходная база
- Repo: `manufact-test/nomusic`.
- **Accepted Test.50 immutable source SHA:** `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`.
- Frozen backup: `backup/android-test50-exact-source-owner-accepted-20261106`.
- **Test.57 source compiled commit:** `d35d33ee4ec6d65c224b9023766df2f14772851a`.
- Isolated branch: `feature/android-0385-test57-stalled-start-and-boundary-20261107`.
- **НЕ использовать Test.51–55 как основу**: повторные контроллеры Yandex отвергались `SecurityException`, ложное блокирование звука Test.53, Test.55 fallback не сработал на телефоне.

## Анализ свежего пользовательского журнала до Test.57
Source: `CELIKOM-combined-20261107-231340.txt`, последний сегмент именно **Test.55** (не старые Test.52/53), и видео `SVID_20261107_231152_1.mp4`.
- RASKOL «Нас не понимают вообще»: Media3 на проблемном seek не отправляет явное same-item seek event; CELIKOM узнаёт о новой позиции только позднее по курсору, после чего cached decoder отвечает за 40–55 мс. Android callback число плееров 2→1→2 длится ~75–80 мс, так что Test.55 900мс-пауза не могла сработать. Без доверенного UI события стандартной Media3-сессии нельзя доказать нажатие Pause/Seek. Относится к широкой группе проблемных альбомов, не к двум жёстким исключениям.
- RASKOL→«Дым»: в Test.55 `onTimelineChanged` уже фиксирует текущий item `129` на **74.082с**, но `onPositionDiscontinuity` через 3мс ещё описывает **старый RASKOL alias 67 / same-item seek**. Корректный `onMediaItemTransition` приходит только **74.189с** — около 107мс позже. Старую замену можно безопасно заглушить раньше, как только **фактический current mediaItem Яндекса** изменился (не угадывать по счётчику плееров).
- «Дым» правильно сопоставлен с album `5281614` / track `39949113`, backend resolve 200 и replacement prepared. Но native `playWhenReady=true`, `isPlaying=false`, `STATE_BUFFERING`, позиция 0 на протяжении более 4 секунд, затем в 82с позиция ~2.6с без READY. Отсоединение/переподключение Media3 от этой буферизации ухудшало ситуацию и часто запрещалось Yandex.
- При возврате к тому же «Дыму» после здоровой песни Yandex сразу перешёл в READY. Поэтому цель новых правок — корректное завершение старого трека и **одна** попытка разблокировать реально зависший старт через *существующий* контроллер, а не переписывание декодера или детектирование по названиям.

## Что изменено в Test.57
1. `SourceTimelineBoundaryPolicy.java` (новая чистая политика) и `ProbeService.onTimelineChanged`: если подключённый контроллер сообщает другой **текущий** mediaItem с заполненным title и он отличается от `current.alias`, немедленно вызвать штатный `sourceBoundary`, заглушив старую подмену до позднего `onMediaItemTransition`. Не срабатывает для обычного seek в том же треке, speculative timeline и неподтверждённого идентификатора.
2. `StalledStartRecoveryPolicy.java` (новая политика): наблюдает **тот же** alias с Media3 `STATE_BUFFERING`, `playWhenReady=true`, без suppression, `isPlaying=false`, позиция 0–500мс, подтверждённая замена и отсутствие свежего события. **Только после непрерывных 4.2с**, с возрастом последнего события ≥3.5с, разрешает ровно **одну** попытку на текущий item. При другом item или новом generation сбрасывается.
3. `ProbeService.sample`: в разрешённом случае, *если* текущий контроллер всё ещё подключён и разрешён `COMMAND_SEEK_IN_CURRENT_MEDIA_ITEM`, отправляет **единственную** команду `seekTo(0)` по текущей сессии Yandex, чтобы попытаться повторно подготовить застрявшую песню. Это настоящее взаимодействие с транспортом Yandex (лог `source_stalled_start_seek0`, поле `transportCommandSent`), а не чистая диагностика. **Никаких повторных команд, перезапусков сервисов или вторых Media3 контроллеров**. Если Yandex не разрешил команду, остаётся исходное состояние без обрыва.
4. Удалён только разрушительный watchdog Test.50, который делал `controller.release();connect()` при обычной 3сек буферизации. Теперь `source_controller_buffering_retained`; истинная потеря подключения обрабатывается старой логикой.
5. **Не изменены:** `ReplacementEngine`, `PlaybackSource`, DSP, fade, resampling, private stream, seek decoder, entitlement, каталог/album match, permissions, signed-app package. **Pause и seek RASKOL пока НЕ исправлены** — без callback штатной Media3-сессии не доказано событие управления.

## Изменённые файлы (для переноса на новый MCP)
Java:
- `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/ProbeService.java`
- `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/StalledStartRecoveryPolicy.java` (NEW)
- `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/SourceTimelineBoundaryPolicy.java` (NEW)
- `android/native-companion/addon/Test57SourceRecovery.java` (NEW)

Regression/packaging:
- `android/native-companion/tests/run_engine.py`
- `android/native-companion/tests/run_addon_host.py`
- `android/native-companion/tests/check_test_app_build_contract.py`
- `android/native-companion/build_test_release.py`
- `android/native-companion/test-app-spec.json`
- `.github/workflows/android-0348-validation.yml`
- `.github/workflows/android-0385-test-app-build.yml`

No other files changed vs accepted Test.50 (source diff independently verified). Do not copy CI workflows to the new MCP platform without revising the secrets/toolchain.

## Verified build
- GitHub Actions: https://github.com/manufact-test/nomusic/actions/runs/42412051667 — native-android **PASS**, signed Test APK job **PASS**.
- Package `pro.celikom.nativeprobe.test`; version `0.3.85-test.57`; versionCode `86143` (upgrade over Test.56); original test signing certificate matches; APK signature v3 valid.
- APK `CELIKOM-Android-0.3.85-TEST-57-START-RECOVERY-SIGNED.apk`, size 8,833,177 bytes, SHA-256 `4ee8c43a8283fc4c750e0568442137e32e54b55737492091daaf374912f6b65e`.
- **ChatGPT Library backup**: https://chatgpt.com/library?file_id=libfile_25b7fd5962f48191a56ae22454f9dca6&account_id=personal
- Verification receipt and JSON in `/CELIKOM/Android/Backups/` Library with IDs `libfile_efd713e814ec8191bdb6e0a40a2d60b1`, `libfile_8f2e24962cec8191a71e70fc69363a43`.
- Stable package, stable OTA, Hostinger writes, production backend unaffected. **No actual phone acceptance yet**.

## Следующий шаг
Одна проверка на реальном HONOR 50: RASKOL → «Дым» (начнёт ли Yandex играть после one-shot seek0), далее нормальный трек, обратно. В новой диагностике искать `source_timeline_boundary_confirmed` и `source_stalled_start_seek0` (true/false). Если seek0 не поддерживается или Yandex остаётся в BUFFERING, задача не решена; не повторять команды вслепую. Отдельно исследовать корректное получение UI Pause/Seek без invasive permissions; владелец много раз отверг Accessibility, Notification Listener, root и требование самому ловить события на устройстве. После завершения миграции проверить новый API origin, auth, Range, private storage, SQL/catalogue и CI APK signing materials по новой платформе.

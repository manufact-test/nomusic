# CELIKOM Test.7 — общий список проблем, диагностика и проверенная тестовая сборка (2026-11-03)

## Что хочет владелец

**Всё исправлять совместно, одной Test APK, приоритет — звук в начале песен и на переключениях.** Вторично, но важно: исключить двойной звук после Yandex audio-session recreation, продолжить устранение редких mid-song dropouts и разобраться с очень редким seek UI после пробуждения экрана. Не выпускать отдельные косметические/диагностические APK. Не изменять принятые seek/Pause/Resume без доказанной необходимости.

### Consolidated owner issue list

1. **Интро/переходы (P0).** После Test.6 средняя/типичная задержка существенно лучше, но «тяжёлые»/быстрые Next ещё дают секунды исходника до замены. В новом owner combined `CELIKOM-combined-20261103-111640.txt` начался новый Test.6 run **2026-11-03T11:05:57+03**, 1547 events, 11 boundaries. Boundary→cold join (gen2..12): **389, 189, 139, 377, 2196, 103, 289, 239, 262, 201, 127 мс**. Самый поздний gen6/trackID48591644: boundary **31.803с**, prefetch started **31.625с** (лишь 178мс lead), ready **33.678с** (1875мс после boundary), cold join **+2196мс**. Источник: rapid playlist shift — в 31.009с index перестроился с22 на0, candidate alias20 впервые обнаружен/однозначно разрешён ~31.606–31.625, следующий ручной переход уже 31.710–31.803. Файл невозможно скачать 2с за 178мс. Более ранний read-only timeline sampling может выиграть часть времени на перестроениях playlist, но **не гарантирует устранения таких экстремальных ручных Next**. Нельзя выдавать эту оптимизацию за акустически доказанную.
2. **Двойной звук после ночной смены Yandex audio session (P0).** Предыдущий incident `CELIKOM-combined-20261103-110350.txt`: broadcast ID Yandex **74313→75561**, `trustedSession=74313` в CELIKOM, `DynamicsProcessing(0,74313)` продолжает приглушать старый источник, replacement становится слышен одновременно с новым оригиналом. HONOR Android13/API33: `verifiedSessionSender` ранее работал только API34+, так что смена была замечена, но не останавливала подмену. Владелец нажал «Отмена»→«Старт» и звук стал обычным. Test.7 включает **fail-closed** остановку replacement на новой session OPEN/старой session CLOSE при совпадающем заявленном пакете Yandex; не используется untrusted broadcast для автоматического доверия новому session ID. Это предотвращает наложение двух аудио, но **после реальной смены сессии понадобится проверенное повторное подключение**, бесшовного auto re-auth пока нет. Автоматическая подмена **между обычными песнями** сохраняется.
3. **Редкий seek после unlock (P1, НЕ воспроизведён).** Владелец дважды примерно за неделю видел, как в Яндекс UI ползунок перемотки двигается, но сама песня продолжает с прежнего места; Next возвращает нормальную работу. В новой записи 32 `replacement_seek_request` и 32 ACK; плохого события нет. Поэтому frozen HONOR accepted seek logic **не менялась**. Test.7 добавляет к пассивным `source_discontinuity` и heartbeat поле `deviceInteractive` для следующего инцидента. Если gesture вообще не дошёл до Media3 как discontinuity, CELIKOM не может угадывать seek по одному движению UI.
4. **Иногда замена не подключается (P1).** В прошлом captured audio-session incident alias8 не имел unique ID, пока network album request спустя ~23с не вернул identity; это **отдельная** причина ожидания помимо stale audio session. Не разрешать воспроизведение по неоднозначным метаданным.
5. **Mid-song dropout после background (P1).** Test.5 исправил доказанный cancelled promoted-current wait/hang; Test.6 сохранил recovery. Короткие тесты новых выпадений не подтверждали, длинное прослушивание ещё нужно; не объявлять универсально исправленным.

## Test.7 — одно общее экспериментальное изменение

Branch `feature/android-0385-intro-join-investigation-20261102`. **Functional SHA `a365dc1da36a9ee960100c40409d677778070e3f`**. Тестовый пакет `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, versionName `0.3.85-test.7`, code **86092**. Не путать с документными commits после этого SHA.

Фактически:
- `ProbeService` и pure `YandexSessionSafety`: для same-package session change включается stop/release replacement, оригинал остаётся, новый session не выбирается на доверии из неаутентифицированного broadcast; новые диагностические `replacement_yandex_session_stale_fail_closed`.
- Read-only next-track Media3 poll **2000→500мс** с немедленной проверкой при `onTimelineChanged`; две стабильные metadata samples/identity/album match, `MIN_LEAD_MS=3000`, current promoted download и fresh server authorization остаются.
- Passive `deviceInteractive` в seek discontinuity + heartbeat, без изменения фактических seek commands, ACK, Pause/Resume.
- Новый deterministic `TestYandexSessionSafety` host test; test contract и APK metadata/version обновлены в том же функциональном релизе. Название artifact исправлено (старое Test.5 label удалено).
- **Нет** обещания, что каждый rapid Next будет без 2с исходника: это физический download bottleneck, требует дальнейшей архитектурной оценки (cache/partial-start/network), особенно если файлов нет заранее.

## Доказательства CI/подписи и доставка

GitHub Actions [#41603059001](https://github.com/manufact-test/nomusic/actions/runs/41603059001) **SUCCESS**:
- полный host regression включая TestYandexSessionSafety, единые AudioOwnership/Media3 authority;
- неизменённый golden `check_0385_seek_baseline.py` PASS;
- Android API36, D8, отдельный package, OTA disabled, original signer;
- stable publisher, build-test-candidate, publish-requested-* **SKIPPED**;
- signed Test job completed SUCCESS.
- Artifact ID **13215970098**, name `CELIKOM-Test-0.3.85-test.7-code-86092`, ZIP SHA256 `50afbe026bfc7980ef5d6df76b92b64f51199c5fa4a536e3ad2166552748544a`. Download: [GitHub Actions artifact](https://github.com/manufact-test/nomusic/actions/runs/41603059001).
- Signed APK SHA256 from immutable runner receipt **`de9d14050be56de8d7f837973a070c704b75cb23bd381886ac0cbee20e80b5be`**. Signing certificate SHA256 **`67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`**, `signer_matches_original=true`.
- Verification+receipt included in ZIP; **ChatGPT Library upload pending**: temporary execution environment currently rejects writing artifact ZIP to filesystem. Download artifact file reference exists through GitHub plugin, but no verified local APK path to upload to Library. Do not invent a Library link or imply Library delivery succeeded. The owner may use GitHub artifact in the meantime.

**CI SUCCESS ≠ acoustic owner acceptance.** New Test.7 has not yet been run on HONOR. Install over Test package only, stable original remains a different app. Verify normal listening including repeated Next, background/session change, intros; no separate finger-seek/Pause/Resume retest unless a regression appears.

## Unchanged/prohibited

Stable original `0.3.85` / code86, package `pro.celikom.nativeprobe`, source SHA `053b7d59beb53db5f30b942feba35e51a1ab256a`. Both `backup/android-0385-honor-seek-accepted-20261102` and `backup/android-0385-honor-seek-accepted-recovery-20261102` untouched; `stable.json`, Hostinger, stable publisher, accepted seek and PR #37 must not be modified/merged. Yandex setting Smooth Transition OFF; never run two CELIKOM instances against one Yandex session.

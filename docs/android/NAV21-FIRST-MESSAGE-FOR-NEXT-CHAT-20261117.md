# First message for next CELIKOM Android A1 chat (17 November 2026)

Привет! Принимай **CELIKOM Android A1** как ведущий разработчик. Продолжай строго с сохранённой точки — **не начинай заново и не меняй архитектуру**.

**GitHub:** `manufact-test/nomusic`.

**Единственная рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

**Точный резерв финальной передачи:** `backup/android-a1-nav21-final-await-owner-txt-handoff-20261117`. Отдельный прежний резерв NAV21: `backup/android-a1-nav21-owner-scoped-readresult-library-verified-final-20261117` @ `886089b89e87fb8bfc5bf290eb421fcfbca13069`. Подписанный исходник APK: `def5f4ff420ec3b285ee1853009882a8f991ec1f`.

**Сначала прочитай:**
1. `docs/android/NEXT-CHAT.md`.
2. `docs/android/ANDROID-A1-NAV21-FINAL-HANDOFF-AWAIT-OWNER-TXT-20261117.md`.
3. `docs/android/ANDROID-A1-NAV21-OWNER-SCOPED-READ-RESULT-RELEASE-20261117.md`.
4. `docs/android/ANDROID-A1-NAV20-REALPHONE-QUEUE-SCOPED-READ-RESULT-AND-NAV21-20261117.md`.

**Что уже есть:** NAV21 — подписанная read-only APK, CI **#44140575566 SUCCESS**, доступна в личной ChatGPT Library: `/CELIKOM/Android/Native/CELIKOM-A1-NAV21-Queue-Scoped-ReadResult-ReadOnly-20261117.apk`. NAV17 — принятая основа воспроизведения оригинального Яндекса; **подмена CELIKOM пока NOT_CONNECTED / NO-GO**.

На настоящем телефоне NAV20 уже подтвердили `QUEUE_SCOPE_ENTER=MANY`, `QUEUED_HOLDER_ATTACHED=ONE`, `ATTACHED_STREAM_READ_MATCH=FEW`, оригинальный `b.g()` вернул `-4=MANY`, но NAV20 смешивала результаты строгой очереди и неподтверждённых подключений. **NAV21 раздельно считает `QUEUE_SCOPED_READ_RETURN_*` и `UNSCOPED_READ_RETURN_*`.** Совпадение потока и возврат `-4` ещё **не доказывают слышимое PCM, конкретную песню или её подмену**.

**В следующем сообщении я приложу новую диагностику NAV21 с телефона.** Сначала внимательно изучи именно её и сопоставь новые счётчики с NAV20. Пока не получишь диагностику, **ничего не пересобирай и не переписывай**. После анализа делай только конкретные обоснованные правки, крупными блоками, с резервом и CI. Не трогай оригинальный Яндекс, Test.50, Windows, расширение и сервер. Не проси удалить приложение или очистить данные. Готовые APK отдавай только через проверенную личную Библиотеку, не через GitHub Actions и не sandbox.

Отчётов поменьше — работай по делу.

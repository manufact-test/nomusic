Привет! Ты принимаешь **CELIKOM Android A1** как ведущий разработчик. Продолжай существующую работу, ничего не начинай с нуля и не меняй согласованную архитектуру.

**GitHub:** manufact-test/nomusic

**Единственная активная ветка:** experiment/android-a1-metrica-init-state-observer-arm13-20261112

**Последний кодовый checkpoint:** 90f8ea394e1ac4168aa63f976e17fd18eb24befb  
**Последнее изменение runtime hooks:** a655712d210189f3bc611847235de3ed4d985c1a

**Резерв кода с CI-green:** backup/android-a1-track-album-publisher-first-ci-green-20261115 @ 90f8ea394e1ac4168aa63f976e17fd18eb24befb  
**Резерв до большого захода:** backup/android-a1-track-album-reference-pre-large-push-20261115 @ e0740cf224b34d3260822fa2248a8b136feac1e5

Сначала прочитай полностью:
1. docs/android/NEXT-CHAT.md
2. docs/android/NEXT-CHAT-ANDROID-A1-TRACK-EXO-CONTINUITY-20261115.md
3. docs/android/ANDROID-A1-TRACK-ALBUM-IDENTITY-20261115.md
4. docs/android/ANDROID-A1-SOURCE-OPEN-READ-CLOSE-IDENTITY-20261115.md

### Где остановились

Добавлены read-only hooks для двух Track-конструкторов с Album-аргументом и точного Track copy-метода. Вызовы оригинальных методов не меняются и выполняются ровно один раз. Track/Album связываются только по Java object identity (==) и weak references.

**CI:**
- Static audit #43703523959 — SUCCESS. Найден один Track+Album→Track copy candidate, но прямая запись Album в новый Track не доказана.
- Clone-only ARM13 #43703211359 — SUCCESS, 25/25, hooks зарегистрированы.
- Publisher-first ARM13 #43703211345 — SUCCESS, original 16/16 splits + clone coexist, 25/25, без Metrica fatal suppression.

Это не product pass. **Stage A = NO-GO.** Не доказаны current selected Track, edition/generation, тот же объект на decoder input и реальное аудио. В CI не было playback/account test; телефон владельца не трогали; APK не публиковали.

### Продолжай с этой задачи

1. Найди identity именно текущего выбранного Track, отделив его от очереди, prefetch и download.
2. Структурно установи edition/generation и связь с Track/Album.
3. Проследи тот же объект до реального decoder input/audio renderer.
4. Не считай Track Flow или положительный Exo DataSource read доказательством текущего звучащего трека.
5. Продолжай read-only, bounded, fail-closed. Не читай значения полей, названия/ID альбомов, URL, DataSpec, аккаунтные данные или audio bytes.

Не меняй Test.50, frozen A1/LSPatch baseline, Windows, extension, backend или оригинальный Яндекс. Не создавай release APK из лабораторного клона. Не проси владельца делать ручные шаги или устанавливать APK, пока конкретное измерение действительно не понадобится. Работай крупными блоками, без промежуточных отчётов на каждом шаге. Если диагностика от владельца придёт — разбери её сам и сообщи только, что реально нужно проверить.

Продолжай самостоятельно.

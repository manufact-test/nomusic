Привет! Ты принимаешь **CELIKOM Android A1** как ведущий разработчик. Продолжай строго с текущей точки. Ничего не начинай с нуля и архитектуру не меняй.

**GitHub:** `manufact-test/nomusic`  
**Рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Последний code checkpoint:** `27ccbe8348d598fead0386e70ef68573b04270c4`  
**Code backup:** `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116`  
**CI #229:** [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139) — signed Yandex 2025.10.4 #120.1gpr, 16 splits / 6 DEX.  
**CI #230:** [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101) — compact logs, full report deleted after summary.  
**Последний runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`; после него hooks не менялись.

### Прочитай только два документа

1. `docs/android/NEXT-CHAT.md`
2. `docs/android/ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md`

Исследование Media3/Yandex и правила документации лежат в отдельных файлах, но загружай их только при необходимости. Не читай архивы и старые накопительные handoff-файлы.

### Первая задача — определить точную целевую версию Яндекса

Не начинай сразу трассировку LfT2.

CI исследует Yandex 2025.10.4 #120.1gpr; телефон владельца ранее был на 2026.09.5 #167gpr. Сначала проверь конфигурацию Android-сборки CELIKOM, package pinning, workflows, metadata и SHA, чтобы установить, какая версия реально является целевым runtime внутри CELIKOM A1. Не считай CI specimen и установленное на телефоне приложение автоматически одной версией.

Если репозиторий не даёт однозначного ответа — задай владельцу один короткий вопрос: исследуем закреплённый 2025.10.4 или целевой 2026 build с телефона?

Для выбранной версии используй только точный оригинальный пакет. Проверь подпись издателя, version, полный split set и SHA-256. Не доверяй зеркалам как источнику подлинности и не переноси обфусцированные дескрипторы между версиями.

### Затем — одна техническая задача

После подтверждения target build продолжи только с `LfT2;`:
- реальные class flags, superclass, interfaces и method descriptors;
- найти исполняемую continuation entry, если она есть;
- проследить только чтение сохранённого TrackWrapper и передачу того же объекта в MediaSource / MediaPeriod / DataSource / Extractor / Player.

Учитывай важный вывод Media3: Player может принимать MediaSource напрямую, поэтому не зацикливайся только на MediaItem. Но требуй доказательства идентичности объекта в подписанном DEX. Не повторяй уже закрытые LiLb и LXk6.

### Ограничения

- Только Android CELIKOM A1. Архитектуру, runtime hooks, APK и оригинальный Яндекс не менять.
- Не добавлять второй Player/decoder/AudioTrack.
- Не читать IDs, названия, URL, DataSpec, токены, account data, приватные значения полей или audio bytes.
- Не трогать NAV17, Test.50, frozen A1/LSPatch, Windows, extension, backend/API/DB и production.
- Stage B остаётся NO-GO, пока не доказана связь выбранного Track с активным декодером.
- Работай крупным законченным блоком, без промежуточных отчётов. Не загружай полные CI-логи или большие исходники целиком.

**Главное:** сначала правильно выбери бинарник, затем продолжай с LfT2. Не исследуй повторно то, что уже доказано.

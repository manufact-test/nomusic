Привет! Ты принимаешь **CELIKOM Android A1** как ведущий разработчик. Продолжай строго с сохранённой точки. Ничего не начинай с нуля и архитектуру не меняй.

**Продукт:** Android mobile app. Не Windows и не браузерное расширение.  
**GitHub:** `manufact-test/nomusic`  
**Единственная рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Последний code checkpoint:** `27ccbe8348d598fead0386e70ef68573b04270c4`  
**Точный резерв:** `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116`  
**CI #229:** [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139), 16 signed splits / 6 DEX, read-only.  
**CI #230:** [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101); CI output is now compact and the full JSON is deleted after summarizing.  
**Последний runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`; после него hooks не менялись.

### Прочитай только два документа

1. `docs/android/NEXT-CHAT.md`
2. `docs/android/ANDROID-A1-LFT2-TRACKWRAPPER-CONTINUATION-20261116.md`

Дополнительно, только если нужен внешний контекст: `docs/android/ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md`.

Не загружай старые накопительные handoff-файлы и все документы папки целиком. История сохранена в архиве и Git history.

### Текущая точка

CI #229 доказал цепочку идентичности одного TrackWrapper:

`LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>`

`LfT2.<init>` сохраняет тот же TrackWrapper. Но тело точного `LfT2.invokeSuspend(Object):Object` не найдено. Дальнейшая передача в MediaSource/MediaPeriod/DataSource/Extractor/Player не доказана. Stage B остаётся NO-GO.

**Сначала сверить target build:** CI сейчас анализирует Yandex 2025.10.4 #120.1gpr, а телефон ранее был на 2026.09.5 #167gpr. Не переносить выводы между версиями. Если целевая версия — 2026, сначала получить и проверить точный оригинальный подписанный split-пакет.

### Единственная задача

Исследуй только точный класс `LfT2;` в шести подписанных DEX:
- его superclass, interfaces, flags и реальные методы;
- где находится исполняемая continuation entry, если она есть;
- читает ли какой-либо метод сохранённый TrackWrapper и передаёт ли тот же объект в конкретную source/player boundary.

Если такой путь не доказан — закрой кандидат. Не запускай глобальный поиск и не повторяй уже закрытые LiLb/LXk6 маршруты.

### Ограничения

- Не менять архитектуру, runtime hooks, APK, оригинальный Яндекс и vendor behavior.
- Не добавлять второй Player/decoder/AudioTrack.
- Не читать IDs, названия, URL, DataSpec, токены, account data, приватные значения полей или audio bytes.
- Не трогать NAV17, Test.50, frozen A1/LSPatch, Windows, extension, backend/API/DB и production.
- Не просить ручную проверку без конкретной необходимости.
- Работай крупным законченным блоком, без промежуточных отчётов.

**Важно:** полный CI JSON не вставляй в чат и не загружай целиком. Вытаскивай только нужные поля из компактного результата.

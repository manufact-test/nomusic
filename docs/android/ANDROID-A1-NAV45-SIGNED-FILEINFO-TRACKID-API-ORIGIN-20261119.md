# CELIKOM A1 — исходный signed FileInfo(trackId) и связь с текущим source

**19.11.2026.** Узкая самостоятельная проверка после NAV45 на единственной ветке `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Оригинал Yandex Music **2025.10.4 #120.1gpr**, точный XAPK SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 16 издательски подписанных split APK и 6 DEX. Все файлы оригинала использовались только временно внутри GitHub Actions и удалены после проверки.

## Проверенная новая точка

[Exact signed original CI #44569443742 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44569443742), [one field writer #44568540492 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44568540492), [terminal 21-caller provenance #44568989076 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44568989076). Все шаги issuer verification, статического анализа и очистки завершились успешно.

- В **подписанном оригинале 2025**, а не в отдельной версии 2026, найдены две API surfaces с аннотацией параметра `trackId`: `FileInfoApi` и `DownloadInfoApi`, по одному прямому вызывающему месту на API.
- Для одного FileInfo/DownloadInfo аргумента есть **одна точная промежуточная Object-field связь**. Единственная запись в это поле принимает **входящий параметр String**. Выше неё — **21 точное прямое место вызова**. Среди них имеются вызовы, использующие String-поле объекта оригинального Track, но ни один не доказал, что это поле читается из **точно того же неизменённого формального Track**, переданного вызывающему методу: `same_formal_track_id_field_path_count=0`.
- Другая ветка передачи `trackId` обрывается из-за ветвления/неполной трассы. `Track.super():String` читает два String-поля (26 инструкций, String/StringsKt): его нельзя считать ID-аксессором. `Album.if():String` возвращает одно строковое поле (две инструкции), но это **не доказанный albumId**.
- Следовательно, **семантическая надпись `trackId` у API доказана**, но её связь с точным Track, пойманным через действующий `PeriodID → SLOT_B → TrackWrapper → original LiLb source → late Flow`, не доказана. Не установлен также `albumId`, `editionId`, replay/Next/MyWave generation. Отдельная структурная связь телефона NAV45 `SAME_CALLBACK=MANY, NO_LINK=MANY` остаётся частичной.

## Решение

Продолжать читать пустые MediaItem или угадывать, что `Track.new(...,long,...)` — это `trackId`, нельзя. Обнаруженное API-поле не является разрешением на замену звука. Нельзя принимать только совпадение имени `trackId` за same-source и selected-edition proof.

**`IDENTITY_STATUS=STRUCTURAL_ONLY`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`.** NAV46 с новыми счётчиками без установленной корректной точки не собран; установленный NAV45 и оригинальное воспроизведение не тронуты. Никаких изменений Java runtime/hooks, продакшена или звуковых буферов. Неприкосновенная NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391`, signed NAV45 `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8`, Test.50 и Windows неизменны.

Единственный оправданный следующий кодовый шаг: проверять исходное `trackId` API на том **же** точном original Track/source + album/edition и новом поколении воспроизведения, без второй точки звука и без предположений по имени поля. Если привязка не доказана — сохранить оригинал; повторные многократные DEX-соседние сканы и бессмысленные owner APK не запускать.

Добавлено только два ограниченных, read-only CI-инструмента `a1_private_track_model_identity_annotation.py`, `a1_private_track_id_api_provenance.py` и соответствующий workflow. Выходные логи содержат только классификации, без ID значений, URL, аккаунтов, приватных имён полей, APK и PCM.

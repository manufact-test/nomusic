# CELIKOM Blur — 34 source files missing from the validated candidate manifest (08.11.2026)

Pinned source tree contains 1526 track files. Original batch800 candidates manifest lists 1442 entries, with 50 historic rejects excluded. The other **34** track files have now been independently enumerated and recorded in [BLUR-SOURCE-GAPS.csv](BLUR-SOURCE-GAPS.csv).

- **28** track IDs have ordinary file sizes but no matching artist/title row in the source README and cannot safely be mapped to the right Yandex track, so they are **unmapped**, not considered tested or imported.
- **2** empty files (0 bytes), **2** files under 1024 bytes and **2** above the 25 MB MP3 importer limit; these 6 cannot pass the existing source-size guard.
- This list is separate from the **93 cumulative technical rejects** among previously examined manifest candidates (includes batch1000 preflight failures).
- Do not fabricate metadata, treat missing labels as valid, or change the importer and existing source policy solely to hit a round number.

## Вторая проверка: ID3 из оставшихся 28 (08.11.2026)

- [Read-only GitHub Actions — 28/28 файлов проверены](https://github.com/manufact-test/nomusic/actions/runs/42517724989); исходные байты подтверждены Git SHA-1.
- **27 настоящих MP3**, 1 `text/html` (Track ID `107972749`); из MP3 **26 имеют встроенные title+artist**, 1 без тегов (Track ID `50400505`).
- Извлечённые ID3 не равны независимому подтверждению правильности `Yandex Track ID → artist/title`. Уже обнаружено несовпадение RAW/Флора у другой пары. Официальный API Яндекс.Музыки из CI без входа возвращает HTTP 451; публичная HTML-страница не возвращает доступных метатегов ([read-only probe](https://github.com/manufact-test/nomusic/actions/runs/42518018499)).
- 26 треков с ID3 и 1 без тегов **не добавлены** до независимой проверки соответствия Yandex Track ID; никто не создавал фиктивных метаданных или права. Полный список в `BLUR-SOURCE-GAPS-FOUND-TAGS.csv`.

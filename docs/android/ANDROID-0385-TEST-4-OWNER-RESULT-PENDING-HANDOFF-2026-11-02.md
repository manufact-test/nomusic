# CELIKOM Android — итоговая передача после Test.4, ожидание проверки владельца (2026-11-02)

> **Статус:** Test.4 собрана, проверена автоматикой и выдана владельцу. Новая диагностика и оценка звучания ещё **не получены и не разобраны**. Следующему чату нужно сначала принять и полностью разобрать новые файлы, сопоставить с исходниками этой сборки, затем решать, нужен ли очередной аудиофикс. Никаких новых изменений кода после функционального Test.4 в рамках этой передачи нет.

## Контрольные точки

| Назначение | Package / версия | Source SHA / состояние |
| --- | --- | --- |
| **Оригинал — неприкосновенный** | `pro.celikom.nativeprobe`, 0.3.85 / code 86 | `053b7d59beb53db5f30b942feba35e51a1ab256a`; принята перемотка HONOR, в том числе после Next |
| **Текущая звуковая Test.4** | `pro.celikom.nativeprobe.test`, 0.3.85-test.4 / code **86089** | `d0b418d0173207b4900f27af365e87595301c4b1`; полноценный фикс подготовки, но акустически не принят |
| **Предыдущая Test.3** | тот же отдельный пакет, 0.3.85-test.3 / code 86088 | `7166fb6c036bc86fb263ba96a407a25dcfea97e6`; диагностический сервисный слой |
| **Предыдущая Test.2** | тот же отдельный пакет, 0.3.85-test.2 / code 86087 | `f3bc62b553275b3e3d38084a65d2eafedb5af889`; первый timeline prefetch |

GitHub: https://github.com/manufact-test/nomusic  
Рабочая ветка: `feature/android-0385-intro-join-investigation-20261102`  
Последний исходный **функциональный** SHA: `d0b418d0173207b4900f27af365e87595301c4b1`.  
Подтверждённый **документационный** HEAD перед этой передачей: `6df7daaf1819075939094cec02657202fbf91af1`. Последующие docs-only коммиты **не изменяют** собранную APK.  
PR #37: https://github.com/manufact-test/nomusic/pull/37 — **OPEN, NOT MERGED**.

Стабильные резервные ветки не менять:
- `backup/android-0385-honor-seek-accepted-20261102` → `053b7d59beb53db5f30b942feba35e51a1ab256a`
- `backup/android-0385-honor-seek-accepted-recovery-20261102` → тот же SHA.
Контрольная Test 86085 также сохранена в `backup/android-0385-test-first-owner-check-20261102` → `32a4afa7c381758502bf47d7b3facd200e74842a`.

## Выданная APK, неизменяемые артефакты

- **CELIKOM Test.4, 86089**: https://chatgpt.com/library?file_id=libfile_2ba812e846048191bfd23b83808c04ac&account_id=personal
- Verification JSON: https://chatgpt.com/library?file_id=libfile_6756d0187440819192827f2bd1b017b6&account_id=personal
- Receipt JSON: https://chatgpt.com/library?file_id=libfile_c5183b6c56508191be994729e231d3d2&account_id=personal
- Library каталог: `/CELIKOM/Android/Test/`.
- Успешный полный GitHub Actions: https://github.com/manufact-test/nomusic/actions/runs/41514473466
- Actions artifact ID: `13174867024` / `CELIKOM-Test-0.3.85-test.4-code-86089`.
- APK SHA256: `c62e93a73e48e949e112ceea4c4af38b83e7c889c3eecab3faa57df0c9d59702`; размер 8 767 641 байт.
- Сертификат SHA256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`; проверена V3-подпись, оригинальный подписант.
- Full Android regression, 22 handoff checks, неизменённый `check_0385_seek_baseline.py`, API 36, D8, package/label/signature/hash/OTA-isolation — **PASS**.
- `stable.json` и Hostinger не изменялись; stable publisher пропущен; обновление оригинального приложения не запускалось.

## Что сделано в Test.4

Ранее на реальных переходах замена подключалась через ~1.98–4.78 с, full-file скачивание занимало ~1.18–3.99 с. Предыдущий timeline lookahead видел следующий Media3 item за ~7–14 с, но из-за неполных metadata не разрешал предварительное скачивание. В Test.4:

1. Два согласованных снимка title/artist/duration позволяют осторожно идентифицировать следующий item даже без album ID/при timeline placeholder.
2. `AlbumProbe` ищет **однозначное** совпадение в собственном свежем каталоге/ранее изученных альбомных строках. Неоднозначность ⇒ no prefetch.
3. Предварительно запускается full-file download разрешённой замены без decoder/gain/AudioOwnership/seek.
4. При границе current-track fresh server resolve строго подтверждает audio key; совместимый уже готовый либо выполняющийся download подхватывается, избегая второго скачивания.
5. Несовпадающая/устаревшая заготовка инвалидируется. Поздний ответ учитывается лишь если идентичность всё ещё совпадает с текущим source.
6. Принятые seek/Pause/Resume, clock gate и механика перехода права на звук не изменены. Read-only фоновая диагностика Test.3 сохранена.

**Звук на HONOR ещё не проверен владельцем:** технический CI не доказывает отсутствие слышимых дефектов.

## План следующего чата — начать с новой диагностики

1. Принять полный combined TXT и, если есть, запись экрана/аудио. Убедиться по manifest/логам, что тест относится к **Test.4/code86089**, а не 86087/86088. Внятно сказать владельцу, что именно обнаружено; не делать ещё одну APK без анализа.
2. Построить временную шкалу для каждого перехода: source boundary → next track identity/album resolution → prefetch start/ready/failure → current resolve → file reuse/new download → replacement prepared → transition complete.
3. Проверить события `source_next_readonly_observation`, `source_next_readonly_boundary`, `source_next_track_identity_candidate`, `source_next_album_resolution`, `replacement_lookahead_prefetch_start`, `replacement_lookahead_prefetch_ready`, `replacement_lookahead_prefetch_failure`, `replacement_prepared`, `replacement_transition_complete`. Учитывать `promoted`, `cancelled`, fallback, reuse/mismatch и задержки service/background.
4. Для каждой песни сопоставить доступность title/artist/duration/album ID, placeholder, стабильность 2 снимков, unique match, фактический cache hit и миллисекунды между boundary и replacement ownership.
5. Видео/AAC сопоставить с логами. Отдельно отметить провалы **до включения CELIKOM**, когда звук оригинального Яндекса или запись могли дать тишину: предыдущий анализ зафиксировал как минимум один такой случай. Не приписывать все провалы CELIKOM без доказательств.
6. Если найден конкретный дефект Test.4 — локальный минимальный аудиофикс в отдельной ветке/очередной Test с code **>86089**, полный host regression, **неизменённый** seek baseline, API36/D8 и автоматический подписанный artifact; сохранить APK+receipt+verification в Library. Не выпускать тестовую APK ради косметики.
7. Если на прослушивании стало хорошо, зафиксировать именно акустическое решение владельца, не объявляя его заранее.

## Ограничения

- При тесте не запускать одновременно стабильный CELIKOM и CELIKOM Test против одной сессии Яндекс Музыки.
- Настройка Яндекса «Плавный переход» остаётся **OFF**.
- Не менять оригинал 0.3.85/code86, две резервные ветки, `stable.json`, stable release contract, publisher, Hostinger, PR #37.
- Не менять и не просить заново проверять уже принятую перемотку/Pause/Resume без объективного нового regression.
- Приоритет исключительно звук в начале и на стыке; никаких отдельных APK из-за цвета текста.
- Сырые пользовательские диагностики/видео не коммитить в публичные исходники.

## Документация для чтения по порядку

1. [NEXT-CHAT.md](NEXT-CHAT.md) — накопленный журнал и исходные исследования.
2. [Текущая Test.4](ANDROID-0385-TEST-4-INTRO-PREFETCH-HANDOFF-2026-11-02.md).
3. [Test.3 background recovery](ANDROID-0385-TEST-3-BACKGROUND-RECOVERY-DIAGNOSTICS-HANDOFF-2026-11-02.md).
4. [Test.2 lookahead](ANDROID-0385-TEST-2-NEXT-TRACK-PREFETCH-HANDOFF-2026-11-02.md).
5. [Lookahead design](ANDROID-0385-NEXT-TRACK-LOOKAHEAD-PREFETCH-2026-11-02.md).
6. [Intro join investigation](ANDROID-0385-INTRO-JOIN-INVESTIGATION-HANDOFF-2026-11-02.md).
7. [Accepted seek freeze](ANDROID-0385-HONOR-SEEK-ACCEPTED-FREEZE-2026-11-02.md).
8. [Side-by-side test app](ANDROID-0385-SIDEBY-SIDE-TEST-APP-BUILD-HANDOFF-2026-11-02.md).

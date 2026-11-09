# CELIKOM v5.13 — РЕАЛЬНЫЙ АУДИОПЛЕЕР «АУ» УСТАНОВЛЕН НА ЗАКРЫТОМ HOSTINGER

**Дата:** 18.10.2026. **Ветка:** `feature/api-range`. **Статус:** закрытый сайт и админка доступны по прежним URL, HTML v10 и FAQ v5.10 сохранены. **Аудиоблок v5.13 развёрнут и проверен в настоящем Chromium на Hostinger.** Пользовательская визуально-слуховая приёмка пока не подтверждена. **Публичного релиза нет.**

## Поставленные реальные исходники

- **«Без CELIKOM»**: новый MP3 `10AGE, Ramil' - Ау.mp3`, присланный владельцем 18.10.2026 после нахождения им работающего загрузчика; source size `4386226` bytes, duration `180.924083` s, source SHA-256 `f32c2d5ed99353b625d94a32720c814fe3ce17847ada325aa969b292bb5d3512`. **Это отдельная запись**, SHA-256 отличается от действующего CELIKOM replacement.
- **«С CELIKOM»**: существующий утверждённый файл track ID `144530503`, replacement ID 1; source SHA-256 `5dfdfaa97ee6f1168964a1a49a101bebb20bd5dca7147c41c1d2df366a2a00d8`, source duration `180.872` s, size `4345176`. Побайтно совпадает с первой загрузкой владельца.
- Отдельные клипы нарезаны с позиции 43 s, длительность `11.049796` s; оба MP3 192 кбит/с, 44,1 кГц, stereo. Вторая, текущая версия сохраняет исходное качество 192 кбит/с без дополнительной потери при передаче; нарезка выполнялась FFmpeg libmp3lame.
- **Private site files:** `celikom-private/demo-audio/clips/service.mp3` (SHA-256 `3f826bb0ef3fa6b8faf07857616b5202ce00aa3a7d1e47dc47d6dc611a4c22e0`) и `.../restored.mp3` (SHA-256 `d14e926aa506ec8ad3112cd73c516e935be1dca612e83dc46bca8c0f5a8342b5`); each permission 0600, private storage outside `public_html`.
- `service.mp3` was transported without byte modification through owner file → isolated local 11s crop → unreferenced blob in **private** `manufact-test/nomusic` GitHub blob storage (Git SHA `5b9cbce17fcf01d9af3663775e4c577d46c9d598`) → GitHub Actions authenticated file transfer → protected Hostinger. File SHA rechecked before installation. Temporary transfer text file was removed from user's Library after transfer.
- Original extension audio, database, mappings, version and media store remain untouched. No changes to `extension/`, `server/` or `android/`. No public release; PR #6 not merged.

## Реальный сайт и проверка

**Закрытый сайт:** https://lemonchiffon-narwhal-791953.hostingersite.com/#sound

- `CmsV10OwnerMotion.php`: existing sound card after CMS render, two real audio elements, play/pause, seek, timer; site reports `data-demo-ready=true` only when both sources are present and distinct, and approved replacement hash matches.
- `owner-sound-player.js`: live playback, pause, scrub, real-time swap at the same position, keyboard-friendly controls, gentle volume fade, visible unavailable/error states. Existing owner-approved v10 grid, typography, images, header, FAQ and desktop/mobile design not rebuilt.
- `website/public/index.php`: protected staging-only HTTP byte-range streaming from fixed private paths; no directory traversal, no public direct MP3 URL.
- [Private original clip installation: PASS](https://github.com/manufact-test/nomusic/actions/runs/39152386583).
- [REAL SITE audio deployment + Chromium acceptance: PASS](https://github.com/manufact-test/nomusic/actions/runs/39152443250) (Git SHA `1ed63b6cf038ff2d1abfed093ec0fac4bbed136e`). Verified authenticated HTML, clip endpoints HTTP 206 with Range bytes 0–1023 and `audio/mpeg`, Play→position >0.6s, switching source at same second, Pause, switching while paused does not auto-play, 5s scrub, playback resumes past position 5. All checks **PASS 1440px desktop / 390px mobile**. Unauthenticated endpoint HTTP 401. Existing deploy backup + rollback installed and no rollback activated.
- Browser tool acceptance file: `website/tests/OwnerV10LiveSoundBrowserTest.py`; workflow: `.github/workflows/celikom-v512-audio-deploy.yml` (visible display name v5.13). Only isolated website changes; production release gate `&& false` retained.

## Что дальше

**Владелец должен только посмотреть и послушать** [готовый аудиоблок](https://lemonchiffon-narwhal-791953.hostingersite.com/#sound), убедиться, что обе версии звучат как ожидается. Не нужно ничего скачивать или вручную нарезать. Если появятся визуальные/звуковые замечания, исправить только сайт и повторить защищённый staging gate. Затем пользовательская проверка остальной мобильной/планшетной версии, админки, и только после согласования следующий этап. **Не запускать сайт публично без отдельного разрешения.**

**Исторический v5.12** о недостающей второй записи устарел: владелец прислал настоящий файл, и полноценный A/B плеер уже установлен.

# START NEXT CHAT — CELIKOM Android 0.3.78 / cached-decoder join investigation
Date: 2026-11-01

Привет. Продолжаем CELIKOM. Сначала прочитай этот файл и затем подробный checkpoint:
[`ANDROID-0378-CACHED-DECODER-JOIN-INVESTIGATION-2026-11-01.md`](ANDROID-0378-CACHED-DECODER-JOIN-INVESTIGATION-2026-11-01.md).

## Зафиксированная точка отката — НЕ ТРОГАТЬ
- Repository: `manufact-test/nomusic`
- Frozen backup branch: `backup/android-0378-original-before-cached-join-20261101`
- Frozen commit: `bf011dcf1a70c504883a8e5e742e0b038f41d9b0`
- Release: Android **0.3.78 / versionCode 79**
- Signed stable APK SHA-256: `325d6eb5c538405b989907bd492a644b287143a1f590b76754778c62f66f89a9`
- Stable APK: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/79-325d6eb5c538405b989907bd492a644b287143a1f590b76754778c62f66f89a9.apk
- Signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`
- Release PR #27 remains open pending owner listening acceptance. Stable manifest publication was verified.

## Где остановились
Пользователь передал screen recording + matching 0.3.78 diagnostic export. Предыдущий чат отметил два подозрительных handover на «Биг сити лайф», где replacement transport/output-clock position seemed to advance less than Yandex source. Приведённые ранее ~224/~239 ms — только транспортные/MediaPlayer clock observations. Это НЕ PCM phase, не hardware/Bluetooth presentation measurement и не доказательство audible silence.

## Что исследовать
Гипотеза: cached decoder reuse path может обходить или отличаться от muted startup / decoder-advancement / warm-alignment gate, в отличие от streaming path. Это пока НЕ root cause. Проверь call graph в:
`android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/ReplacementEngine.java`
Особенно `prepare`, `acceptAudio`, `update`, `fade`, `completeSeek`, `rememberAudio`.

## Что сделать первым
1. Проверь текущий working HEAD, diff и backup ref. Не предполагай, что SHA ветки не изменился после документационных коммитов.
2. Восстанови корреляцию видео и диагностики; найди фактические cache-hit/stream-hit события для двух подозрительных joins. Если происхождение decoder на join не логируется — сначала добавь только пассивные diagnostic fields.
3. Проследи все пути к `fade(...)`; установи, проходят ли cache hit, stream hit, full-download fallback, pre-arm preparation, pause/resume и seek recovery одинаковые safety gates.
4. Напиши actual-engine RED regression: cache-hit decoder startup задержан/не двигается; оригинал остаётся audible; replacement не получает output до подтверждённого движения и drift в пределах существующего порога; при timeout оригинал сохраняется; успешный cache join проходит.
5. Добавь парный stream-hit regression. Сохрани single audio mode и все ownership/fail-open/duration/session/entitlement checks.
6. Полный Android test suite + API36 + D8 CI. Только non-publishing staging. Stable channel / stable.json не трогать.
7. Лишь после PASS собрать проверенный signed test candidate, убедиться что receipt явно говорит `stable_published:false`. Не выдавать unsigned APK и не придумывать ссылки.
8. Пользователь тестирует только точный проверенный candidate. Никаких дополнительных записей до готовности кандидата.

## Жёсткие запреты
- Не менять seek timing, WARM lead, crossfade/fade duration, gain law, pause/resume, Next, buffering, Bluetooth, AudioOwnership или Media3 arbitration без прямого доказательства и регрессионного теста.
- Не добавлять A/B, linear/nonlinear modes, переключатели или дополнительные кнопки.
- Не трогать desktop, backend, website, CMS, catalogue, auth, updater.
- Не публиковать новый stable APK без физической проверки пользователя.
- Не считать transport clocks доказательством speaker PCM phase.

Пользователь просит краткие рабочие сообщения: если от него ничего не требуется — прямо так и сказать. Не заставлять его повторять уже переданные материалы.

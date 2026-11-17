# CELIKOM Android A1 — восстановленные находки по Яндексу и Media3

**16.11.2026. Только документирование ранее сделанного исследования, без новых хуков, сборок или APK.**
Актуальный продуктовый статус — исключительно в [NEXT-CHAT.md](NEXT-CHAT.md).

## Что реально нашлось и чем полезно

**1. Media3 допускает прямую передачу MediaSource.** Официальный AndroidX Media3/ExoPlayer API предоставляет `setMediaSource(MediaSource)`, `setMediaSources(...)`, `addMediaSource(MediaSource)`; объект `MediaSource` отвечает за `Timeline` и создание `MediaPeriod`. Значит, исследование фактического native source→Player не должно требовать обязательного промежуточного `MediaItem`. **Это контракт Android Media3, а не доказанный способ вызова внутри официальной Яндекс Музыки.** Верификация: [ExoPlayer API](https://developer.android.com/reference/androidx/media3/exoplayer/ExoPlayer), [MediaSource API](https://developer.android.com/reference/androidx/media3/exoplayer/source/MediaSource), прежняя заметка [external playback research](ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md).

**2. В подписанной Яндекс Музыке 2025.10.4 есть настоящее coroutine resume `RAa`.** [Сохранённое исследование](ANDROID-A1-RAA-SOURCE-RESUME-IDENTITY-20261115.md) и [статический CI #43696198020](https://github.com/manufact-test/nomusic/actions/runs/43696198020) (SUCCESS) показывают:
- `com.yandex.music.shared.player.download2.o.for(...)` создаёт `RAa(o,Oe2)`; `RAa.invokeSuspend(Object)` снова вызывает `o.for(...)` с **тем же экземпляром continuation**.
- При этом `TrackWrapper`-аргумент после resume может быть **явным null**, поэтому простая привязка ThreadLocal только к аргументу wrapper теряет идентичность.
- В ранее созданном экспериментальном **read-only** observer восстановление допускается только по точному Java instance `RAa == RAa` из слабой ссылки; конфликт/GC/чужая ссылка → отказ от связывания. Регистрация observer в лабораторном CI **не** доказывает звук или выбранный трек.
- Аналогичная граница существовала у `Fp0`: Flow Track→request допускает null после coroutine resume. Не повторять без конкретного нового факта.

**3. Не перепутать с полностью закрытым `LfT2`.** [Точная проверка класса CI #12](ANDROID-A1-LFT2-EXACT-CLASS-CLOSURE-20261116.md): `LfT2` — `final Object`-наследник с `equals/hashCode/toString`, **без `invokeSuspend`**. Его чтения `LtCa;` не выходят в playback. `RAa` и `LfT2` — разные сущности; возврат к `LfT2` запрещён без новых оснований.

**4. Native Exo source наблюдали, но current selected item ещё не доказан.** [NAV17 source audit](ANDROID-A1-NAV17-STAGE-B-PINNED-2025-FILEINFO-SOURCE-AUDIT-20261114.md) описывает статическую цепочку `download2.o.while(...)` → нативный descriptor → `download2.exo.c.for(...)` → `RetryingBalancingDataSource` factory → `open/read/close`. Отдельные read-only наблюдатели используют weak-reference identity и fail-closed lifecycle. Положительный `read` у источника не означает, что он относится к **играющему** треку: это может быть prefetch, offline/download или другой элемент очереди. В NAV17 нет измеренного равенства current selected Track → source/decoder, нет применённой CELIKOM-версии аудио.

## Что НЕ следует брать за доказательство

- Официальная [справка Яндекс Музыки об остановках воспроизведения](https://yandex.ru/support/music/ru/technical-issues/playback-stop) описывает VPN/прокси/сеть/энергосбережение, а **не** внутренние классы приложения. Для Stage B она не решает проблему идентичности.
- [YaMuLite](https://github.com/dpronyaev/yamulite-android) и [yt-dlp Yandex Music plugin](https://github.com/fgsfds1/yt-dlp-yandex-music-plugin) — сторонние реализации; их CDN/API схемы, токены и плееры нельзя переносить на официальный нативный Яндекс.
- Сохранённые публичные материалы **не раскрывают** точный obfuscated call graph издательской версии Яндекс Музыки.
- Old RAa documents include historical “Stage A NO-GO”; it is superseded by **NAV17 Stage A PASS** (owner confirmed original music on 14 Nov). Stage B remains **NO-GO**.

## Уточнение 17.11 — прямой MediaSource API проверен на signed NAV17

Точечный независимый read-only CI [#2 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44049682525), 3/3 unit tests, 16 publisher-signed splits и 6 DEX на **точно том же оригинале NAV17 2025.10.4 #120.1gpr**. Сценарий: android/native-yandex-hooklab/ci/direct_media_source_player_contract.py. Проверены только 11 уже известных Player owners и точный параметр AndroidX MediaSource.

Результат: **0** методов Player с таким точным типом параметра, **0** прямых callsite, exact_media_source_class_defined=false. Это **ограниченный отрицательный результат** для необфусцированного имени/точного контракта, **не** доказательство того, что нативный Яндекс не использует MediaSource: типы и вызовы могут быть обфусцированы/косвенными. Публичный API Media3 выше остаётся верным для SDK, но напрямую на signed 2025 app без точных DEX-методов не переносится. Не начинать массовое исследование обфусцированных MediaSource/List/Object.

Кодовый checkpoint 433191c0b6e5f2a2eabef8589aa01c02f326e3b1, backup backup/android-a1-direct-mediasource-contract-ci-green-20261117; до изменений backup backup/android-a1-pre-direct-mediasource-contract-audit-20261117 @ a142f5fe48f92d68727f4c9873a4a6cfda56b156. Никаких runtime hooks, APK или audio изменений. **Stage B NO-GO**, same-object selected native Track → active decoder не обнаружен.

## Точное ограничение для следующего разработчика

Использовать доказанный **NAV17 original = Yandex Music 2025.10.4 #120.1gpr** (`assets/lspatch/origin.apk` SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`) только для уже установленной линии исследования. Это **не** выбор будущего production target. Отличать #170gpr контроль и #167gpr старое приложение телефона.

Новая работа возможна только при конкретной узкой гипотезе с **same-object** selected Track (track+album+edition+duration+generation) → активный source/player/decoder, исключая prefetch и stale queue, без раскрытия значений и без повторного LiLb/LXk6/LfT2, глобальных census, новых player/AudioTrack. При отсутствии такого доказательства не менять исходный native player и не объявлять Stage B готовым.

## Контрольные точки

- Проверенный read-only `LfT2` код: `e6bf9b6933d17d503b4f3b1d4f7d460df4b52f6a`; [CI #12 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43909098407).
- Предыдущий документационный HEAD до этой передачи: `a324963b84876a88513bc1d208a42519489c397f`.
- Pre-doc backup: `backup/android-a1-before-yandex-media3-research-handoff-20261116`.
- Runtime hooks и APK **не изменены**; последний hook-change `a655712d210189f3bc611847235de3ed4d985c1a`.

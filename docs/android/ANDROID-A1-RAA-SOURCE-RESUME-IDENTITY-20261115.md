# CELIKOM Android A1 — RAa main-source coroutine continuity, 15.11.2026

**Только исследовательская scoped-ветка, Stage A NO-GO.** Не продукт, не подмена аудио, не распространять лабораторный APK и не просить владельца устанавливать его.

## Точная статическая находка

Issuer-signed original Yandex 2025.10.4 #120.1gpr (6 DEX, hash-pinned, read-only) [CI #43696198020](https://github.com/manufact-test/nomusic/actions/runs/43696198020) — SUCCESS, вердикт `SIGNED_NATIVE_SELECTED_ITEM_STATIC_HANDOFF_CANDIDATES_ONLY`.

1. В `com.yandex.music.shared.player.download2.o.for(o,qX8$d,tCa,f6a,n26,Oe2)` непосредственно создан `RAa(o,Oe2)` перед coroutine suspension-capable логикой; `o.while(QBa,f6a,n26)` строит Exo descriptor дальше по этому же методу. Статическая последовательность ещё **не доказывает** фактическое исполнение при audible playback.
2. `RAa.invokeSuspend(Object)` вызывает точно тот же `o.for` с `Oe2`, являющимся **собственным объектом RAa** (Dex receiver reg6 → move-object reg5 → arg5), `raa_resume_exact_same_continuation_static_proven=true`.
3. Регистру wrapper arg2 непосредственно перед повторным вызовом присваивается литерал null (`const/4 0`, без переписывания или branch после этого присваивания); `raa_resume_explicit_null_wrapper_argument_static_proven=true`. Поэтому старый ThreadLocal scope, который опирался только на wrapper arg2, может завершиться на suspension, а после resume получить null.
4. Исходная Flow Track → Fp0 → Gp0.new с null Track уже была доказана [#43695462019](https://github.com/manufact-test/nomusic/actions/runs/43695462019). Вместе это **две статически проверенные coroutine replay-границы**, но пока не runtime selected source.

## Что сделано

- **Код** `2267c64f1df04b31a47f1a6e9d67b367ceea56db`, **точный резерв до RAa** `backup/android-a1-raa-source-resume-pre-identity-20261115` @ `df872b6d326d253f9fef6999a232e372ac27d46a`.
- Hook `RAa.<init>(download2.o,Oe2)` после оригинального вызова отмечает точный continuation по слабой Java-ссылке `==` и известному track-linked wrapper. На resume `o.for` с null wrapper получает scope только при exact-повторном объекте RAa; конфликт, null, GC, повторное использование для другой wrapper fail closed.
- Новый registration event `AUDIO_NATIVE_MAIN_CONTINUATION_HOOK / MAIN_CONTINUATION`; PID-scoped парсер должен видеть его наравне с остальными пяти registered hooks. Регистрация ≠ фактическое исполнение.
- НОВЫЕ bounded counters `NATIVE_MAIN_CONTINUATION_CONSTRUCTED`, `MAIN_CONTINUATION_RECOVERED`, `MAIN_CONTINUATION_CONFLICT`. Два разных доказательства не смешиваются: `WRAPPER_MAIN_SOURCE` считается только для **прямого** одинакового wrapper-аргумента; восстановление через RAa идёт исключительно в `MAIN_CONTINUATION_RECOVERED`. Так же `FLOW_TRACK_SAME_OBJECT` не засчитывается для recovery через Fp0 (фикс `facf275dcf6fa585843e9f84effa93a1aac83f49`).
- JVM regression на возврат через RAa, неизвестную ссылку, чужую wrapper, конфликт identity и последующую цепочку descriptor→factory→source→open→read. Summary теперь 40 строк, статус CELIKOM_REPLACEMENT/NOT_CONNECTED остаётся последним.
- Модуль ничего не меняет в нативном плеере; оригинальные vendor methods исполняются ровно один раз. Нет Track fields, URL, account, cookies, audio, etc. Нет override prepare.

## CI и незакрытые критерии

- Издательский signed static RAa replay [#43696198020](https://github.com/manufact-test/nomusic/actions/runs/43696198020): **SUCCESS**, обе точные статические проверки true.
- Предыдущий кодовый Fp0 checkpoint: [clone-only #43695595723](https://github.com/manufact-test/nomusic/actions/runs/43695595723) **SUCCESS**, 25/25 и **пятый Track continuation hook REGISTERED**; [publisher-first #43695595735](https://github.com/manufact-test/nomusic/actions/runs/43695595735) SUCCESS, но без аудио.
- Новая RAa-версия `2267c64f`: [clone-only ARM13 #43696449267](https://github.com/manufact-test/nomusic/actions/runs/43696449267) **SUCCESS**, 25/25 stable, все **шесть** Track/RAa hooks REGISTERED; [publisher-first ARM13 #43696449282](https://github.com/manufact-test/nomusic/actions/runs/43696449282) **SUCCESS**, original 16/16 publisher splits + clone simultaneous install, verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. `stage_b_current_player_album_edition_attested=false`, `audio_or_account_tested=false`. Это лабораторная устойчивость и регистрация, **не** реальная подмена/decoder proof.
- **Stage A остаётся NO-GO** до фактического разрешённого same-current-selected Track + album/edition/generation → decoder preprepare → DataSource.read и реального audio QA. `CELIKOM_REPLACEMENT / NOT_CONNECTED`.

## Что проверять дальше

В owner-диагностике (если владелец сам пришлёт, не просить новых установок) сначала `AUDIO_NATIVE_TRACK_CONTINUATION_HOOK` и `AUDIO_NATIVE_MAIN_CONTINUATION_HOOK` со статусами регистрации, затем `NATIVE_TRACK_FLOW_EMIT → NATIVE_TRACK_SOURCE_REQUEST → TRACK_CONTINUATION_RECOVERED → TRACK_WRAPPER_LINK → NATIVE_MAIN_SOURCE_ENTER → MAIN_CONTINUATION_RECOVERED → WRAPPER_DESCRIPTOR_LINK → TRACK_DESCRIPTOR_FACTORY_LINK → TRACK_FACTORY_SOURCE_LINK → TRACK_SOURCE_OPEN_LINK → TRACK_SOURCE_READ_LINK`. При NONE — только локализовать недоказанный переход, не трактовать как отсутствие звука. Дополнительно проверить album/edition/generation и current-source связь до prepare, без приватных значений и без подмены.

Никогда не трогать owner-accepted Test.50, замороженный A1, Windows, расширение, backend, основную Яндекс.Музыку на телефоне и Play Protect.


## Финальный контрольный резерв 15.11.2026

Проверенный код `2267c64f1df04b31a47f1a6e9d67b367ceea56db` сохранён отдельным точным immutable резервом `backup/android-a1-fp0-raa-dual-resume-ci-green-20261115`. Исследовательская ветка получила лишь документационные изменения после этого code checkpoint. Следующие изменения начинать от неё с резервом; не переносить лабораторный статус на audio/replacement acceptance.

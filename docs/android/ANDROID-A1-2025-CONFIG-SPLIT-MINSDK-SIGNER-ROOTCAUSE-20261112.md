# CELIKOM Android A1 — устранён блокер подписи 2025 (12.11.2026)

## Проверенный результат

**Только самостоятельная подпись 2025 lab clone:** PASS **16/16**, но Stage A всё ещё **NO-GO** до независимого подтверждения Android ARM13, нативного UI, Yandex login и звука. Stage B LOCKED. Исходный оригинальный XAPK владельца НЕ модифицирован и НЕ опубликован.

- Реальный [CI 43105227726](https://github.com/manufact-test/nomusic/actions/runs/43105227726): **SUCCESS** — оригинал 16/16 issuer-signed PASS; own-key rebuilt 16/16 apksigner PASS. [CI 43105590847](https://github.com/manufact-test/nomusic/actions/runs/43105590847) — повторный контроль after runtime-only change SUCCESS.
- 15/15 synthetic signer diagnostics tests + 7/7 ZIP cleanroom tests PASS. Официальный Android SDK **Build Tools 35.0.0**, НЕ Debian symlink: собственные synthetic APK с minSdk 21 и 28 подписаны и проверены; две умышленно испорченные тестовые подписи отвергнуты.
- Проверено все 16 отдельных lab-splits, отдельный временный CELIKOM signer, сертификат отличается от подписи издателя, идентичность исходных DEX и нативных .so байт-в-байт, переписаны 7 provider authorities; все 16 неповреждённых original publisher-signed APK прошли verifier перед обработкой.
- Удалено 45 старых v1/JAR-сигнатурных элементов **только из пересобранных одноразовых lab APK**. Предыдущая CI доказала, что сама очистка v1 **не решала** проблему. Она НЕ является самостоятельной причиной исправления.

## Конкретная техническая причина прежнего отказа

1. [CI 43100028330](https://github.com/manufact-test/nomusic/actions/runs/43100028330) и прежние подписные CI падали на split index 0. Старая диагностика неверно относила информационные `--print-certs` строки к root-cause «certificate/v1».
2. На официальном SDK35 уточнили **одно реальное ERROR-сообщение**: JAR/v1 digest-signature algorithm не поддерживается для более старых проверяемых API уровней. Фактически [CI 43105002785](https://github.com/manufact-test/nomusic/actions/runs/43105002785) подтвердил, что **split index 0 — конфигурационный**, его оригинальный и пересобранный манифест **не объявляют minSdkVersion**.
3. Прежний скрипт принудительно подписывал каждую часть с `--min-sdk-version 21`, но вызывал `apksigner verify` **без** диапазона для отдельно лежащего config-split. Проверка такого APK по умолчанию могла включать API 1–20, для которых данная подпись не обещала совместимость.
4. Из проверенного оригинального base.apk читается **minSdkVersion=24**. Все конфигурационные splits устанавливаются только вместе с base и используют тот же реальный минимальный SDK пакета. Исправлено: подписывать все 16 при minSdk=24, для *именованных config splits* явно проверять `--min-sdk-version 24`; для base.apk оставить **обычную независимую проверку SDK по манифесту**. Цифровая подпись по-прежнему строго обязательна на каждом split, отключения верификации или подделки ключей нет.

**Следствие:** 16/16 подписных PASS теперь доказаны не синтетикой, а исходным pinned 2025 XAPK в одноразовом CI. Это не доказывает поддержку изменения package identity или внутреннее доверие к собственному сертификату при запуске Яндекса.

## Изоляция и доказательства

- Исследовательская ветка: `experiment/android-a1-2025-sdk-signer-triage-20261112`.
- Точный зафиксированный резерв **полного доказанного signing-pass**: `backup/android-a1-2025-owner-sdk35-all16-signed-verified-20261112` @ `fcf6cb1107c53611294b74ef787d40b7234cf342`.
- Новый вспомогательный код: `android/native-yandex-hooklab/ci/official_sdk_signer_control.py`; исправлены `lab_signer_signal_gate.py`, `test_lab_signer_signal_gate.py`, `owner_2025_gpr_lab_clone_no_bypass_arm13.py`.
- Новый исходно проверенный workflow: `.github/workflows/android-a1-2025-official-sdk-signer-triage.yml`.
- Реальный ARM13 workflow: `.github/workflows/android-a1-2025-own-clone-native-arm13-75s.yml` и [CI 43105679694](https://github.com/manufact-test/nomusic/actions/runs/43105679694). **Перед передачей/следующей работой обязательно проверить реальный conclusion и логи**; не трактовать подписание как запуск.
- Pinned оригинал 2025: XAPK 45 961 661 bytes, SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 16 original apk publisher-signed, в черновике Release `a1-yandex-2025-gpr-private-test` (ID 442137464, asset 736739728). **Ни в коем случае НЕ публиковать draft и НЕ вкладывать binary/ключи в коммиты или Actions artifacts.**
- Замороженная A1 `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743` — **нетронута**. Android Test.50, Windows, extension, production API/backend, HONOR владельца, штатный Яндекс нетронуты.

## Следующий барьер, который нельзя перепрыгивать

1. Реальный ARM13 install 16 отдельно подписанных splits, MAIN >=75 s на чистом disposable устройстве. Это не эквивалент работы на HONOR и не проверка login/audio.
2. Если install/MAIN FAIL — точная безопасная классификация install или MAIN EXIT_SELF/JAVA exception; отличать от уже исправленного signer-blocker. **Не повторять старый signing-fail без новой причины.**
3. Только после реального стабильного native UI — возможность законной штатной авторизации, библиотека, MyWave, родной плеер, интеграция уже принятого audio contract issue #42/PR #43, реальная подмена аудио и согласование звучания владельцем. Никаких WebView/двух движков/эмуляции плеера.
4. Если требуются подпись издателя, отключение app self-check, Passport/DRM или обход защиты, **не внедрять**; документировать NO-GO и варианты с правообладателем. Ни одну копию Яндекса нельзя считать свободно разрешённой к коммерческой модификации/публикации без подтверждения прав.
5. Только после звукового принятия Stage A — отдельно напомнить владельцу о Stage B: замене LSPatch собственным адаптером.


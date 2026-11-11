# CELIKOM Android A1 — 2025 GPR v1-signature cleanroom A/B (11.11.2026)

## Итог из реального GitHub CI

[CI 43099023249](https://github.com/manufact-test/nomusic/actions/runs/43099023249) — FAIL без очистки; [CI 43100028330](https://github.com/manufact-test/nomusic/actions/runs/43100028330) — FAIL с очисткой старых META-INF/v1 signing artifacts из отдельного disposable unsigned lab APK. Обе проверки сначала успешно криптографически подтверждают 16/16 исходных подписанных Яндексом APK. Наш independently/lab-signed clone неизменно не проходит обязательный apksigner verify на первом split index 0 ДО установки на Android. Категории обеих ошибок: missing_verified_signature, v1_jar_problem, certificate_or_signer. Причина ещё не доказана. **Гипотеза «достаточно удалить старые v1 META-INF файлы» не подтвердилась.**

Тест 43099023249: оригинал 16/16 PASS; десять синтетических ZIP unit tests PASS; до подписания unsigned 452 ZIP members и 2 v1 signer markers, после подписания 451 members и 2 v1 markers; структура/CRC ZIP корректны; apksigner verify FAIL. Проверено, что archive intact, no duplicate/unsafe entries, no encryption. Не выдавать presence v1 markers после пересоздания новой подписи за доказательство старой подписи.

Тест 43100028330: оригинал 16/16 PASS; **17/17 synthetic unit tests PASS**; lab builder удаляет obsolete META-INF signing chain из отдельной временной пересобранной копии до zipalign/own-key signing, сохраняя все остальные ZIP member contents byte-for-byte. Тем не менее после подписи verifier FAIL на том же первом split 0, с теми же категориями. Итого native CELIKOM install/MAIN/UI/login/audio **не происходили** и нет рабочей APK-сборки.

Отдельно, **17/17 synthetic unit tests также прошли локально** в Python unittest и py_compile. Реальный CI вердикт 43100028330 — FAILURE, а не зелёная сборка продукта.

## Код, ветка, резерв

Рабочая исследовательская ветка: experiment/android-a1-owner2025-v1-sanitized-signer-lab-20261111.
Точный backup ДО захода: backup/android-a1-owner2025-v1-clean-before-builder-20261111 @ ff42f3f41f8c458eb5aed182a321f3a922027e70.

- android/native-yandex-hooklab/ci/lab_signer_signal_gate.py — read-only bounded ZIP CRC/duplicate/metadata/signature problem classification, сырой вывод и бинарные данные не публикует.
- android/native-yandex-hooklab/ci/test_lab_signer_signal_gate.py — 10 synthetic tests.
- android/native-yandex-hooklab/ci/lab_unsigned_archive_cleanroom.py — удаляет устаревшие v1/ JAR signature metadata ТОЛЬКО из самостоятельно пересобранного disposable unsigned output, НЕ из Yandex original.
- android/native-yandex-hooklab/ci/test_lab_unsigned_archive_cleanroom.py — 7 synthetic tests, no-overwrite, byte-preservation, unsafe-archive rejection.
- android/native-yandex-hooklab/ci/owner_2025_gpr_lab_clone_no_bypass_arm13.py — строго требует issuer-original gate, ZIP-integrity и apksigner PASS для lab-split перед любым install.
- .github/workflows/android-a1-owner2025-v1-clean-signing-lab.yml — source-only CI 17 tests + actual unsigned scratch lab signer verification, files and keys erased, no APK artifact.

## Положительные контроли и ограничения

- Подлинный publisher-signed original Яндекс.Музыка 2025.10.4 #120.1gpr: 16/16 signature PASS [CI 43090872523](https://github.com/manufact-test/nomusic/actions/runs/43090872523); native ARM13 75s same PID/resumed 25/25 [CI 43091414430](https://github.com/manufact-test/nomusic/actions/runs/43091414430). **Это только оригинал, не CELIKOM**.
- Наш separately signed 2026 clone ранее устанавливался и MAIN завершался EXIT_SELF(0). Это другая стадия, причина неизвестна; не смешивать 2025 packaging и 2026 runtime.
- ChromaSync-Clone-3.0.1.apk wrapper жив в ARM13 75s, nested re-signed origin без обвязки падает; чужой sigBypassLevel=2, код, бинарь, авторизация, DRM не переносятся. Нельзя подделывать издательские сертификаты и выдавать разрешение распространять Яндекс без лицензии.
- Issue #42 helper audio contract уже закрыт и ПР #43 уже интегрирован в frozen A1; 32/32 tests PASS. Это source-only, не нативная подмена звука.
- Main A1 experiment/android-native-a1-lspatch-clone-loader0-20261111 @ cc4cb0f93489168db21502f3ef195855ae9fb743, Android Test.50, Windows, extension, site, API, backend и владелец HONOR не тронуты.
- Отдельные старые runs [43097031056](https://github.com/manufact-test/nomusic/actions/runs/43097031056) и [43096955087](https://github.com/manufact-test/nomusic/actions/runs/43096955087) на момент последней проверки всё ещё QUEUED zero jobs. Не создавать их дубликаты.

## Что делать следующему чату

**Не повторять** очистку META-INF signing artifacts, Apktool resource rebuild или ту же APKEditor переподпись: 2025 clone всё ещё не проходит SDK. Следующий эксперимент нужен только после более точного, но безопасно категоризированного объяснения отказа apksigner по первому split 0 и независимого теста подписного toolchain на собственном синтетическом APK. Возможные классы проблем — SDK/version/signing-mode и APKEditor output; это ГИПОТЕЗЫ, пока нет данных. Никогда не ослаблять обязательную цифровую проверку, не подменять сертификат издателя, не внедрять security/DRM/Passport/Play Protect bypass.

После реального 16/16 собственных подписей — native Android13 ARM install + MAIN lifecycle; затем native Yandex UI/login/playlist/one decoder/audio и обязательный акустический приём владельца. Вопрос права на модификацию/распространение приложения самостоятельный и должен быть решён до выпуска. Ни собственного Android APK CELIKOM, ни Stage A PASS нет. **Stage A NO-GO, Stage B locked.**

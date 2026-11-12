# CELIKOM Android A1 — парный нативный A/B, происхождение APK и собственный SourceStamp (12.11.2026)

**Вывод по проверенным на данный момент запускам:** Stage A **NO-GO**, Stage B LOCKED. Установка уже работает. Не работает MAIN независимо подписанного Яндекс-хоста. Владелец запретил возвращаться к теме обращения к Яндексу; вместо этого ведём фактическое техническое исследование.

## Как проверялось, без предположений

Исходник: подлинный издательский **Yandex Music 2025.10.4 #120.1gpr**, 16 из 16 splits, исходный SHA256 XAPK `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053` (45 961 661 байт), только ранее существовавший **unpublished draft**, ни один файл не публиковался.

### A/B на одном настоящем ARM13 Android в одной чистой VM

[Реальный GitHub Actions CI 43171090649](https://github.com/manufact-test/nomusic/actions/runs/43171090649) получил оба запуска в **одном** ARM64+ARMv7 Android 13 Redroid guest, одинаковая среда/пакет `ru.yandex.music`, без смены namespace, APKEditor, LSPatch либо патчей манифеста, ресурсов или DEX:

- 16/16 оригинальных APK проверены криптографически, установлены и **MAIN остаётся жив и resumed все 25 наблюдений за 75 секунд**.
- Штатно удалено исходное приложение из чистой VM. 16/16 отдельно подписанных собственным временным сертификатом APK прошли Android-verify/install. **MAIN сразу падает**, `ApplicationExitInfo.JAVA_CRASH`, `IllegalStateException` в `YANDEX_APP` на UI thread. В сообщении исключения приватный классификатор обнаружил только фиксированный маркер `SIGNATURE`. Имеющиеся в XAPK DEX, .so, манифест, ресурсы не преобразовывались.
- `PAIRED_ORIGINAL_STABLE_OWN_KEY_MAIN_SIGNATURE_JAVA_CRASH` — **реальная подтверждённая причинная развилка**. CI FAILURE закономерен, потому что наш native MAIN не выдерживает 75 сек.

### Проверка всех APK-полезных данных, а не только DEX и .so

Новый `android/native-yandex-hooklab/ci/own_key_full_payload_identity_gate.py` хеширует содержимое **всех** APK ZIP entries кроме v1/JAR-signature артефактов и пустых ZIP-directory markers. Проверки на синтетике: 7/7 PASS (тесты подмены manifest/resources, отсутствия entries, дубликатов, unsafe input). В [CI 43172112962](https://github.com/manufact-test/nomusic/actions/runs/43172112962) вскрылась единственная **дополнительная entry** на оригинальной стороне: `stamp-cert-sha256` (документированный Android SourceStamp). В independently re-signed APK она исчезла. Других различий состава entries этот конкретный пробег не показал. Это конкретный недостающий метаданный объект, но его отсутствие само по себе **не было доказано причиной** Java-краша.

### Проверка отдельного собственного, а не чужого SourceStamp

Новый эксперимент использовал **официальный Google Android SDK 35** `apksigner.jar` из SHA256-проверенного архива. Временная независимая подписная пара: отдельный **собственный app signer** и другой независимый **собственный source-stamp signer**, никогда не имитируется подпись издателя, никаких защит не отключено.

[Реальный CI 43173312016](https://github.com/manufact-test/nomusic/actions/runs/43173312016) зафиксировал:

- `source_stamp_crypto_verified_16_of_16=true`; **каждый из 16 separately own-signed APK** имеет новый валидный SourceStamp, отличный от издательского. И собственная app signature проверяется штатно.
- **8 661** ordinary/non-stamp APK ZIP entries проверены по распакованному SHA256 и оказались **точно идентичны** оригиналу. Соответствующие Android manifest/resources/DEX/native payload не преобразованы.
- На той же VM исходный издательский MAIN **75 сек PASS**, собственный APK с полноценным валидным **нашим** SourceStamp 16/16 install PASS, но **MAIN 75 сек FAIL**: `JAVA_CRASH / ILLEGAL_STATE` + первый error message marker **`SIGNATURE`**.
- `verdict=OWN_SOURCE_STAMP_STILL_MAIN_NO_GO`. Значит, **простое отсутствие SourceStamp НЕ является достаточным объяснением**. Независимый законно сформированный SourceStamp не решает старт. Это НЕ утверждение, что принцип source stamps в целом бесполезен, и НЕ доказательство конкретного vendor self-check: исходная issuer signed identity и собственный app signer всё ещё различаются.

Тесты выполняются только в одноразовом ARM13 GitHub runner, оба временных приватных ключа и derived lab signed APK удаляются. Не было вмешательства в DRM/Passport/Play Protect/проверки Яндекса, никаких сертификатов издателя не выдавалось за свои, ни одного APK пользователю или в Actions artifact не опубликовано.

## Текущее узкое место

**Подписать/установить ≠ запустить собственную копию.** В последнем A/B исключены: разница эмуляторов, смена package name, APKEditor rebuild, перемена APK обычных файлов, отсутствие собственных криптографически валидных SourceStamp metadata, ARM архитектура или грубая ошибка штатного APK verifier. **Не исключены:** издательский signer identity, signature-based разрешения Android, проверяемое доверие к пакету и связанные подписные инварианты, особенности ZIP/scheme metadata. Это последняя критическая техническая часть перед native UI, но не «мелкий баг», пока нет подтверждённого штатного способа независимого запуска.

Следующий строго доказуемый диагностический ход — **сравнить фактически предоставленные Android PackageManager permission grants** оригинальной и independently signed копии с тем же именем в одном госте. Для этого уже добавлены read-only `owner_2025_signature_permission_comparison.py`, синтетические фикстуры и опрос только штатного `dumpsys package`, без смены permission/сертификатов/UID, с фиксацией только счётчиков и публичного `com.yandex.permission.READ_CREDENTIALS`. Даже обнаруженное расхождение предоставленных прав **не означает**, что оно единственное вызывает `IllegalStateException`.

Главная A1 остаётся заморожена: `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`. Не изменены Android Test.50, Windows/extension/backend/production, HONOR, штатный Яндекс и оригинальный черновик Release. #41 OPEN.

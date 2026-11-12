# CELIKOM Android A1 — реальные штатные мосты Android 13, 12.11.2026

**Подтверждённый итог:** Stage A **NO-GO**, Stage B **LOCKED**. Никакой аудиоподмены, CELIKOM native UI или работающей потребительской APK этот блок НЕ дал. Издательский 2025 MAIN работает; независимый own-signed clone по-прежнему падает с Java IllegalStateException/SIGNATURE, подтверждено ранее, здесь НЕ переподписывали его снова.

## Новая гипотеза, которая действительно была проверена

**Возможно ли без модификации и обхода подписей использовать штатные публичные Android 13 поверхности оригинального Яндекса:** cross-UID activity embedding (показать нативный интерфейс в нашем host) и стандартный MediaBrowserService (получить разрешённую сессию действующего проигрывателя). Это не LSPatch, не WebView, не собственной плеер и не замена архитектуры продукта. Речь об исследовании доступности API; даже успешный IPC не доказал бы source-before-decoder swap.

### Эксперимент 1 — подлинный издательский 2025 манифест, CI 43177629249 PASS

- Источник: только уже сохранённый unpublished draft 2025.10.4 #120.1gpr XAPK, размер 45 961 661, SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`.
- Криптографический `apksigner` на каждом из **16/16 оригинальных APK**, точные package/version/issuer PASS.
- В настоящем `AndroidManifest.xml`: 138 activity/activity-alias, из них 11 manifest-exported+enabled, но **0 разрешённых сторонних Activity** через `allowUntrustedActivityEmbedding` и **0 exported Activity** с объявленной `knownActivityEmbeddingCerts` allowlist. Поэтому **нельзя полагаться на поддерживаемый cross-UID native embedding** данного релиза на Android 13. При этом манифест не раскрывает все runtime-решения.
- Найден **один exported MediaBrowserService**, публично объявленный стандартным Android action. Это ещё не разрешённая browser-сессия и точно не source hook.
- CI: https://github.com/manufact-test/nomusic/actions/runs/43177629249. Перепаковки APK, эксплуатации или печати приватных атрибутов нет.

### Эксперимент 2 — НАСТОЯЩИЙ ARM Android 13, CI 43178136217 PASS

- Отдельно **собрали наш диагностический APK** (без опасных разрешений, без чужого кода); запустили на native ARM64+ARMv7 Android 13.
- Все **16 неизменённых оригинальных publisher-signed APK** проверены и установлены; нативный MAIN исходного Яндекса запущен и жив. **Собственное независимо подписанное приложение** тоже установлено/запущено параллельно.
- Android PackageManager нашего приложения находит **ровно один** стандартный `MediaBrowserService` без manifest-level permission guard.
- **Реальный результат `MediaBrowser.connect()`: `CONNECTION_REJECTED`**. `getRoot()` и `getSessionToken()` НЕ доступны; отправлено **0** playback, seek, custom или source change команд. В Android 13 CI без аккаунта и воспроизведения **реальный публичный доступ к сессии не установлен**.
- **Ограничение вывода:** этот отказ в чистой среде НЕ доказывает отказ при любых авторизованных пользовательских состояниях. Даже успешный MediaBrowser сам по себе **не является** callback для замены аудио в декодере и не даёт отдельно подписанному APK доступа к чужим private source objects.
- CI: https://github.com/manufact-test/nomusic/actions/runs/43178136217. Два задания SUCCESS относятся к корректности проверки, а не Stage A. Private Android guest и оригинальный APK удалены после проверки; опубликован был только краткоживущий **наш собственный** отладочный APK как внутренний CI artifact с retention 1 day, НЕ сборка для владельца.

## Наш код / безопасность / следующая граница

- `android/native-yandex-hooklab/ci/owner_2025_native_bridge_manifest_witness.py` — реальный verified issuer APK / read-only manifest API gate.
- `android/native-yandex-hooklab/owned-public-browser-probe/` — minimal OWN Android native public browser connection client; не управляет медиа и не запрашивает пользовательские данные.
- `android/native-yandex-hooklab/ci/owner_2025_real_public_browser_ipc_arm13.py` — реальный ephemeral same-device signed publisher + OWN APK runtime gate.
- `.github/workflows/android-a1-2025-native-bridge-manifest-witness.yml`, `android-a1-2025-real-public-browser-native-arm13.yml` — отдельные CI.
- Исходный XAPK не опубликован, оригинал на HONOR, Test.50, Windows, extension, backend, frozen A1, производство не изменены.
- Нового **native in-process source-before-prepare host** нет, contract B42 (34/34) остаётся подготовленным, но к декодеру не подключён. Не повторять signer/ZIP/SourceStamp/grants, и не пытаться обходить signature/Passport/DRM/Play Protect ради открытия браузера.
- До появления доказанной штатной поверхности source selection и отдельного нативного UI **пользовательскую APK НЕ выдавать**. Владелец не должен проходить ручной тест без фактически работающей сборки. GitHub issue #41 остаётся OPEN.

**Вывод:** две принципиально новые поверхности исследованы на оригинале: встраивание Activity статически недоступно, browser IPC в чистом ARM13 реально отвергнут. Это новые закрытые/ограниченные условия, НЕ исправление главного блокера.

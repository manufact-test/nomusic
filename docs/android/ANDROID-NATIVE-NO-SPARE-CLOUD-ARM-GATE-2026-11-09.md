# CELIKOM Android — нет запасного телефона: удалённый ARM-стенд (09.11.2026)

**Статус:** никакие облачные устройства ещё не запущены, APK никому не передавались, модуль в нативном Яндексе не запущен. Текущий HONOR, эталон Test.50, сервер и официальная Яндекс.Музыка не затронуты.

## Кандидаты без покупки телефона

1. **Google Developer Device Platform** (Preview): Device Streaming — настоящие удалённые Android-устройства с доступом ADB. В каталоге есть **Samsung Galaxy A52 5G, Android 14, physical/Streaming, ID `a52xq-34`**. Каталог: https://docs.cloud.google.com/developer-device-platform/device-catalog ; ADB: https://docs.cloud.google.com/developer-device-platform/device-streaming . Доступ к аккаунту/проекту Google Cloud пока отсутствует.
2. **Samsung Remote Test Lab**: доступ к реальным Galaxy после бесплатной регистрации, возможен Remote Debug Bridge (ADB). https://developer.samsung.com/remote-test-lab ; https://developer.samsung.com/sdp/blog/en/2021/06/04/using-remote-test-lab-with-android-studio . Сверить актуальные модели, Android версии, ограничения и правила https://developer.samsung.com/terms?location=us до установки.
3. Firebase Test Lab: физических Android много, но **Arm-виртуальные устройства не имеют Google Play Store**, поэтому Play Protect там не доказать. Google указывает на миграцию к Developer Device Platform. https://firebase.google.com/docs/test-lab/android/avds ; https://docs.cloud.google.com/sdk/gcloud/reference/firebase/test/android

## Обязательный preflight до любых установок

- Выбрать разрешённый удалённый физический Android 13+ с **`armeabi-v7a`**. Присутствия `arm64-v8a` недостаточно: точная #170gpr использует 32-битный ARMv7 split.
- До загрузки APK — запустить только read-only `python3 android/native-yandex-hooklab/probe_arm_device.py` через отдельную ADB-сессию. Скрипт не устанавливает и не удаляет пакеты, блокирует известную модель HONOR 50, установленный Яндекс, неподдерживаемый ABI/API, эмулятор.
- Визуально проверить, что Play Protect включён. `com.android.vending` сам по себе не доказывает его состояние. Облачный verdict не заменяет тест на стандартном сертифицированном пользовательском аппарате.
- **Не передавать никакие проприетарные перепакованные APK Яндекс.Музыки в облако без отдельного разрешения владельца, проверки правил провайдера и лицензий.** GitHub artifacts с ними также не создавать. Не выдавать получение облачной сессии за автоматическое право устанавливать чужое приложение.
- Если провайдер допускает, сначала на облачном ARM проверять только **наш собственный минимальный демонстрационный Android host без Яндекса/учётной записи** для отделения LSPatch loader от кода Яндекса. Успех такого host не доказывает CELIKOM runtime.
- Следом, при отдельном согласии владельца, исследовать штатный нативный Яндекс без root, sigbypass/impersonation, отключения защиты, удаления установленного официального клиента или доступа к паролям и токенам.

## Без облачного доступа

Можно развивать статический безопасный DEX-аудит FileInfoDto → eed → источник до prepare и собственные unit-тесты. Это не runtime доказательство. Повторять проваленные x86/x86_64 LSPatch-тесты нельзя. Gate запуска на настоящем ARM остаётся **NO-GO**, пока физический ARM-стенд не пройден.

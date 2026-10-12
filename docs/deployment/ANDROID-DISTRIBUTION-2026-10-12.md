# Android: блокировка установки и подготовка распространения

## Проверенные факты

Honor50/Android13: владелец получил Google Play Protect «Приложение заблокировано для защиты устройства», без подтверждения установки, в версиях0.3.1/0.3.2 после удаления0.3.0. Вчера0.3.0 устанавливалась с подтверждением. Нельзя объявлять причину сменой версии Android или повреждением APK.

Проверены APK0.3.0/0.3.1/0.3.2: v2 RSA/SHA256 подпись и полный content digest корректны во всех. BIND_NOTIFICATION_LISTENER_SERVICE присутствует во всех; INTERNET/RECORD_AUDIO/READ_SMS/RECEIVE_SMS/BIND_ACCESSIBILITY_SERVICE отсутствуют. Получены разные certificate SHA256:

-0.3.0:9936ffe1066fa18f1f7c67346f0e6964ebaa75001e6d3b93e298ee4850ac6048
-0.3.1:c3cc3ba794449c4319fd351771e155c88cf357d45a03738f5f82db83bce8cf55
-0.3.2:f5fb8d33fc2b8b00c24f241932403e5437615fc4049e214a865574926fc9f74f

Временные CI debug ключи объясняют несовместимость обновления поверх, но НЕ доказывают root cause Play Protect после удаления. Повторная пересборка блокировку не сняла. Согласно Google, internet-sideloading+notification listener может блокироваться автоматически. Имя/обфускацию/package/разрешения ради обхода не меняем; отключение защиты и USB владелец не выбрал.

## Подготовленные изменения

Перед переходом к системным настройкам — явный диалог о широком доступе Android, фильтрации Яндекс Музыки, локальном хранении и ручной передаче. Кнопка отмены доступна; новых разрешений нет. В коде MusicListener фильтрация package перед обработкой MediaController; содержимое уведомлений не выгружается. Нельзя утверждать, что само пояснение снимает блокировку установки.

Release signing поддерживает закрытые переменные CELIKOM_ANDROID_KEYSTORE, CELIKOM_ANDROID_STORE_PASSWORD, CELIKOM_ANDROID_KEY_ALIAS, CELIKOM_ANDROID_KEY_PASSWORD. Выпуск требует существующего постоянного ключа и не заменяет его debug подписью. Ключ/пароли не публиковать в GitHub или чат. Постоянный ключ ещё не создан/не настроен; Play Console аккаунт не подтверждён. Поэтому распространяемого release пока НЕТ, подпись/дистрибуция не объявляются решёнными.

## Следующий внешний шаг

1. Владелец выбирает официальное обращение о Play Protect либо тестовое распространение через свой Play Console. Подготовленный draft ниже не отправлялся.
2. Для обращения: приложить конкретный APK, package pro.celikom.nativeprobe, его SHA256, описание ограниченной функции, подтверждение согласия пользователя и снимок блока. Идентификация владельца/контакт отправителя нужны в форме Google, не выдумываются.
3. Для Google Play: зарегистрированный аккаунт разработчика, постоянный upload key/Play App Signing, публичная privacy policy и сведения об использовании данных; проверка доступности требований в Console. Internal test не обещает одобрение финального клиента.
4. После официального решения или тестового канала проверить установку с включённой Play Protect, обновление поверх и отзыв доступа на Honor50; затем проверить другие прошивки. Только потом возвращаться к диагностике exact Track ID/native replacement.

https://developers.google.com/android/play-protect/warning-dev-guidance
https://support.google.com/googleplay/android-developer/answer/9845334

## Draft: Play Protect classification review (not submitted)

Our own diagnostic app, CELIKOM (package pro.celikom.nativeprobe), is blocked with “App blocked to protect your device”. It requests user-enabled notification listener access solely to inspect the MediaSession of the installed Yandex Music app. It does not read or store notification message bodies from other apps. It has no INTERNET, SMS, accessibility, microphone or audio-capture permissions. Reports stay on-device and are shared only by an explicit user action. The app does not modify audio or request account credentials. We verified APK v2 signatures and complete content integrity. Please review the classification and advise whether this intended permission use requires another distribution route. We understand that APK integrity alone does not establish policy compliance and that review does not guarantee approval.

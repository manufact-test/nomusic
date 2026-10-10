# CELIKOM — этап 9.1: обязательная почта и восстановление

**Решение владельца от 10.10.2026.** Дополнение к Master ТЗ MVP v1.5 §14 / Приложение H, Плану работ MVP v1.6 «Этап 9 — Аккаунты + устройства» и Issue #8. Это ОБЯЗАТЕЛЬНАЯ часть этапа 9 до коммерческого trial/billing. Не начинать Stage 10.

## Контракт подтверждения
- Публичная регистрация создаёт пользователя **без access/refresh-токенов**. Код из 6 цифр отправляется на введённый email. Срок 10 минут, максимум 5 неверных вводов, повтор отправки ограничен. Секретные значения — только server side.
- `POST /api/v1/auth/verify-email`: email + code + installation_id. Только валидный код включает аккаунт и создаёт сессию. При смене аккаунта/версии нельзя автоматически подтверждать адрес.
- `POST /api/v1/auth/resend-verification`: email + исходный пароль + installation_id (не доступно без подтверждения личности). Лимит запросов. Повторный вход в неподтверждённый аккаунт возвращает pending-state и письмо, но никогда токены.
- **Уже созданные аккаунты** имеют NULL/no email-security row; ни один старый токен не работает до подтверждения email. Учетное имя остаётся тем же, удалять данные пользователя нельзя.
- `POST /api/v1/auth/request-reset` отвечает **одинаково** для зарегистрированных/незарегистрированных email, без перечисления адресов. Код reset действует 10 минут. Верная комбинация email+code даёт замену пароля, аннулирует все старые сессии и подтверждает владение адресом, даже если прежний пользователь успел зарезервировать неподтверждённую почту.
- `POST /api/v1/auth/reset-password`: новый пароль 12–128 символов, допустимы буквы без цифр; Argon2id/bcrypt, отсутствие пароля или кода в логах и JSON ответа.
- Авторизация другого устройства — обычный вход с паролем, без OTP для каждого устройства. Backend продолжает учитывать установки и отзывать сессии. Кнопка «Мои устройства» удаляется из компактного popup; будущие настройки безопасности могут её вернуть.
- Форма CELIKOM: собственные ошибки email/password/code вместо нативных tooltip, глазик для пароля, корректные границы ввода/автозаполнения, хороший focus-border, заметная серверная ошибка, нормальные отступы, без дублирования «Готово».

## SMTP и безопасность запуска

Ни одного почтового секрета нет в исходниках и extension. Сервер принимает секреты только из приватного окружения:
`CELIKOM_MAIL_TRANSPORT=smtp`, `CELIKOM_SMTP_HOST`, `CELIKOM_SMTP_PORT` (465 TLS или 587 STARTTLS),
`CELIKOM_SMTP_USER`, `CELIKOM_SMTP_PASSWORD`, `CELIKOM_MAIL_FROM`,
`CELIKOM_MAIL_CODE_PEPPER` (случайный секрет минимум 32 символа).
Только проверенный отправитель с соответствующим доменом SPF/DKIM/DMARC и TLS. Подтвердить работу живой доставки **на настоящий тестовый ящик**, получение кода, повтор и восстановление, не выводя ни одного кода в CI logs. Требуются отдельный DNS/email provisioning и защищённое внесение конфигурации; временный `hostingersite.com` не означает наличие почтового адреса на нём. Пока SMTP не подготовлен, регистрация на новом backend должна возвращать безопасный `email_unavailable` и не создавать аккаунт.

## Безопасное развёртывание

1. Подготовить SMTP mailbox/from и проверить доставку, DNS и лимиты исходящей почты. Секреты задаёт владелец в защищённом Hostinger/GitHub secrets интерфейсе, не в чате.
2. Подтвердить CI на disposable MySQL 8/PHP 8.3 и Chrome fixtures: register pending, wrong/expired/5 failed codes, verified-only access/refresh, resend cooldown, legacy user, password reset across devices, replay and test without SMTP.
3. Проверить backup и **обновить Stage5 snapshot список до 22 таблиц** (новая `user_email_security`), применить аддитивную миграцию `005_email_security.sql` без изменения существующих 004/музыкальных таблиц.
4. Защищённый Hostinger rollout только после письма и полного CI, с private env backup, schema/checksum audit, rollback. Существующую рабочую Chrome 0.4.4 не трогать; собирать новый owner-only пакет с SHA-256.
5. Ручная приёмка UI и живых писем в двух Chrome-профилях, с настоящим email; особое внимание Brave/Chrome autocomplete, copy/paste, double focus, password eye, error readability. Потом закрывать Issue #8 и этап 9.

## Фактическое развёртывание — 10.10.2026

**HOSTINGER TEST BACKEND РАЗВЁРНУТ И ПРОВЕРЕН.** Пользователь подтвердил получение настоящего тестового письма CELIKOM в Proton. Секреты Gmail SMTP хранятся только в приватном Hostinger env; токены и пароли не публиковались.

- [Pre-deploy snapshot](https://github.com/manufact-test/nomusic/actions/runs/38054641908): 21 таблица, 5 аудио, private env — PASS.
- [Isolated pre-deploy restore](https://github.com/manufact-test/nomusic/actions/runs/38054748599): PASS.
- [Owner-approved protected deploy](https://github.com/manufact-test/nomusic/actions/runs/38054935718): релиз `0.4.5-bffd2c93df1ac0d3a45de385197a4c51b7c5df94`, миграция 005, PHP 8.3, HTTPS — PASS.
- [Read-only Hostinger DB/audio/env audit](https://github.com/manufact-test/nomusic/actions/runs/38055294402): approved #1, pending #2/#3, original media hash and checksum 005 preserved — PASS. GitHub edge 403 accepted only after on-host audit without отключения защиты Hostinger.
- [Post-deploy snapshot](https://github.com/manufact-test/nomusic/actions/runs/38055393728): **22 таблицы, 5 аудиофайлов** и private env — PASS.
- [Isolated post-deploy restore](https://github.com/manufact-test/nomusic/actions/runs/38055485798): восстановление SQL и аудиофайлов — PASS.
- [Private browser package](https://github.com/manufact-test/nomusic/actions/runs/38055111493): Chrome 0.4.5 с email verification/recovery; SHA256 `a3812e53678b27d2fa07a1f6f145dabb1bad7717ba5d37024cff7257b6d0835c`.

**Незакрытая приёмка:** в настоящем Chrome проверить имеющийся аккаунт → письмо с кодом, регистрацию нового пользователя, сохранение ввода кода при закрытии popup, reset-by-email и ретест плеера. Серверная отправка из новых auth endpoint пользовательским сценарием **ещё не подтверждена**, подтверждена только доставка отдельного SMTP-теста. Stage 9 и Issue #8 остаются открытыми. Не трогать рабочую 0.4.4, PR #6 и Issue #7, не начинать Stage 10.

## Состояние
**Новая email-верификация включена на тестовом Hostinger**, публичный платный запуск ещё не разрешён: требуется ручная приёмка. PR #6 OPEN/unmerged, Issue #7 OPEN. Approved #1, pending #2/#3, private owner uploads и Stage8 admin сохранять.

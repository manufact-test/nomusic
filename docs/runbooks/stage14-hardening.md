# Stage 14 operations and recovery

Do not manufacture a global incident to test UI. Use disposable integration tests.
Do not reset/backfill account trials, sessions, catalog, reward policy or ledgers.

1. Run CI with PHP 8.3/MySQL, native Chromium and isolated MariaDB before release.
2. Build the single client pinned to the existing HTTPS API and verify ZIP checksum
   and security gate. Keep reserve 0.4.4; update existing unpacked installation.
3. Use restricted Stage5 snapshot and isolated restore workflows before server deploy.
   Check current HEAD lease before each request; no live database replacement.
4. Deploy immutable verified package via existing guarded Hostinger workflow, retaining
   existing environment/flags/credentials and applied migrations. Snapshot counts are
   point-in-time evidence, never a permanent expected user/catalog count.
5. Read-only audit compares environment/media hashes and canonical table state to the
   pre-deploy snapshot. Confirm approved 144530503/#1, roles, contribution rate scope,
   API anonymous refusal and existing flags. Real user/manual moderation is untouched.
6. Roll back release pointer to retained previous immutable package if health fails.
   This package has no migration; do not restore old SQL over new user data.

Contribution limits are fixed-hour attempt budgets: account 10 uploads/20 requests;
device 20/40; IP 60/120. Account limit was already present. Each accepted scope uses
an atomic SQL increment, so parallel workers cannot authorize more than its ceiling.
Scopes intentionally count malformed/retry attempts; idempotent result handling does
not grant unlimited free abuse requests. Shared-NAT budgets are higher than account
budgets. Audio Range/HEAD is outside these write quotas. Only server REMOTE_ADDR is
used; if adding a proxy, explicitly configure its trusted chain before using headers.
Bucket keys are keyed hashes; no raw address/device metadata is stored there.

Before customer distribution: configure independent encrypted backup destination,
retention and owner key custody; test provider-loss recovery; verify provider access
logs omit signed query tokens and rotate logs; add disk/free-space alerts using
read-only operational probes. Do not claim these source-independent operations were
executed merely because a runbook exists. Android APK signing key must stay outside
Git and public build logs/artifacts; Stage18 privacy gate remains mandatory.

## 20.10.2026 — клиент 0.4.58: VPN-switch reconnect (ручная приёмка открыта)

Сценарий: установленная 0.4.57 после смены VPN осталась `access_reconnecting`/`suspended=true` при живом bridge; последовательные `auth/me` timeout и network error, оригинальный звук восстановлен. Нет доказательства браузерного `online` при возврате VPN. См. [разбор и исправление](../decisions/VPN-NO-ONLINE-RECOVERY-0.4.58-2026-10-20.md).

В 0.4.58 после сетевого сбоя следующая плановая проверка (существующая пауза 5 с) сбрасывает застрявший GET transport. Выход из suspension допускается только после успешного серверного подтверждения доступа; отдельные сетевые подсказки не дают разрешения. Не повторять POST/trial, не включать приложение после пользовательского Stop/Original, не подменять оригинал при неподтверждённом доступе.

Gate для владельца: обновить установленное расширение на месте, reload расширения и вкладки Яндекс.Музыки; переключить VPN во время воспроизведения и дать автоматическому циклу восстановить соединение без ручного Start. Зафиксировать исход `suspended/replacementError/bridge/network/lastRecoveryHint` после возврата сети, а также сохранение оригинального звука во время обрыва. При повторном отказе запросить безопасный diagnostic dump. **Полный CI и package PASS, но ручная VPN-приёмка ещё не проведена/не сообщена.** Backend/БД не менять.

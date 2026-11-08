# CELIKOM Companion Windows — product and UX/UI design v1

**Status:** design proposal awaiting owner approval; mockup is illustrative only. User interface is **CELIKOM Companion**, not a skin/fork of the official Yandex Music UI. No fake features or working audio claims.

## Product rules

The user installs the official Yandex Music app, then CELIKOM, signs into a **CELIKOM account** and enables substitution. The entire music library, albums, recommendations, playlists, player, keyboard media keys and play/pause/seek stay in Yandex Music. CELIKOM has a **compact window + tray icon** for service status, the current song, track reporting, uploads and subscription.

**One app, one account, one backend:** share user's CELIKOM account/entitlement/rewards and the approved catalog with browser + Android. Separate native per-device auth session; platform status must NOT log out other clients. No additional subscription/Windows-only tariff is invented. If an account is not authorized, leave Yandex unchanged.

Do not present CELIKOM as a licensed/official Yandex product. Installation must make this distinction clear. No heavy separate music player, duplicate media controls, forced account wizard or autonomous audio downloads.

## Information hierarchy

1. **Home / Главная** (default, target window 460 × 640 logical px; min content width ~380 px): top brand + connected account chip, connection to official Yandex, replacement enable/disable, current song identity, replacement state, 3–4 relevant actions, calm footer status.
2. **Добавить версию** (flow/sheet): song from exact current Yandex ID, title/artist summary, select owned audio file, rights confirmation, duration validation/size format and preview, progress and **server-confirmed** pending moderation. Never show success for a merely local file; no public URL assumption.
3. **Предложить песню** (sheet): exact ID selected from current playback or pasted Yandex link; disabled if approved version exists; report only with user confirmation; server receipt and request status.
4. **Аккаунт** (sheet): email or account identity, trial/active/expired, bonus for contributions, current device login, renew/manage subscription via existing server-backed flows, logout (only this device), support.
5. **Настройки и диагностика** (sheet): Start with Windows optional OFF by default; start minimized optional OFF; check updates; compatibility/Yandex version; limited diagnostics export after user action. Advanced version/hash fields behind a fold, not shown at launch.

**No internal page for selecting/playing albums.** Return to Yandex for playback. Browser extension and Android maintain their own UIs.

## Home window wireframe (text contract)

```text
┌────────────────────────────────────────┐
│  ◖C CELIKOM              [АККАУНТ]   × │
│  Для Яндекс.Музыки                     │
│                                        │
│  ● Яндекс.Музыка подключена             │
│    Официальное приложение • Windows    │
│                                        │
│  Подмена версий                [ ON ]  │
│  Только для проверенных песен          │
│                                        │
│  СЕЙЧАС В ЯНДЕКС.МУЗЫКЕ                │
│  [ cover placeholder ] Название       │
│                        Исполнитель     │
│  ● Версия CELIKOM доступна             │
│                                        │
│  [ Вернуть оригинал ]                  │
│  [ Загрузить версию ]                   │
│  [ Предложить песню ]                   │
│                                        │
│  Управление музыкой — в Яндексе        │
├────────────────────────────────────────┤
│  Главная   Аккаунт   Настройки  [?]    │
└────────────────────────────────────────┘
```

Default on/off is a user choice, not a claim of installed functioning integration. If no exact current track: no phantom title/artist/image, upload disabled until exact Yandex link or a real ID is provided.

## Distinctive states and copy

| State | First line | Primary CTA | Secondary policy |
|---|---|---|---|
| First launch, no official app | «Яндекс.Музыка не найдена» | «Открыть страницу Яндекса» | Official https://music.yandex.ru/download/; never bundle Yandex installer. |
| Official app installed but closed | «Яндекс.Музыка не запущена» | «Открыть Яндекс.Музыку» | Only start after explicit click, if supported. |
| Installed, unsupported version | «Версия Яндекса пока не поддерживается» | «Подробнее» | CELIKOM disabled; no patch/auto-fix. |
| CELIKOM logged out | «Войдите в CELIKOM» | «Войти» | Yandex unchanged; no Yandex password requested. |
| Trial/entitlement expired | «Доступ CELIKOM закончился» | «Управлять подпиской» | Use authoritative backend billing status; no silent renewal. |
| Ready, replacement disabled | «Подмена выключена» | «Старт» | Original plays in Yandex. |
| Enabled + no song/ID confidence | «Ожидаем песню в Яндексе» | None | No guessing track by title. |
| Enabled + not in approved catalog | «Проверенной версии пока нет» | «Предложить песню» | Yandex plays original. |
| Enabled + preparing source | «Подготавливаем версию…» | «Вернуть оригинал» | Yandex remains audible until validated. |
| Enabled + active replacement | «Играет версия CELIKOM» | «Вернуть оригинал» | Native Yandex play/pause/seek; no duplicate player buttons. |
| Source unavailable/expired | «Не удалось подменить — играет оригинал» | «Повторить» | Error is not a false connected/success claim. |
| Account/server offline | «Нет связи с CELIKOM» | «Повторить» | Original playback unaffected. |
| Corrupted local integration | «Не удалось восстановить клиент» | «Инструкция восстановления» | Do not lie that rollback succeeded. |

**Stop vs Original**: `Стоп` disables future substitutions globally. `Вернуть оригинал` affects only the current track and persists for it during retries, until next track/explicit user action. Do not use both when only one is relevant. On active substitution and exact ID, show Original primary; on paused/off show Start. Avoid flashing/changing CTA repeatedly.

## Design tokens (existing CELIKOM brand; no reinvention)

- Font **Manrope** 400/500/600/700/800 (self-host only when license checked; fallback `Segoe UI, sans-serif`).
- Main ink `#0B1013`; mint `#66E0BF`; paper `#F7F8F4`; subdued text `#556368`; borders `#DCE8E3`; link `#14594D`.
- Base window uses calm **light** paper with dark header/feature band or top bar; native window titlebar can be customized only if keyboard and window management remain accessible.
- No neon #66E0FF (not the approved v10 brand mint), no acid gradients/glassmorphism, no Spotify/Yandex styling copies.
- Rounded corners: window 22–28px, cards 18–22px, CTA 14px; section rhythm 12/18/24px. Label 11–12px; body 14–15px, title 20–24px.
- Component set: Topbar, ConnectionStatus, AccessChip, EnableSwitch, NowPlayingCard, TrackStatus, MainAction, SecondaryActions, ShellNavigation, AccountSheet, UploadSheet, Preferences, Diagnostics.
- Status is signaled by **text + icon + color** (never color alone): mint = connected/ready, neutral = off/idle, red = recoverable error. No animation/flashing between «версия доступна» and «подключено».
- Comfortable min touch/click target 40×40px; keyboard tab order/focus visible; a11y names and reduced-motion; scalable Windows DPI 100/125/150/200%; RU first with future EN ready.
- No music cover display if no authorized image URL; use neutral placeholder. Never collect raw cover/audio URLs in support logs.

## Window/tray behavior

- Tray icon gray when disabled or disconnected, green when actively attached **and** CELIKOM access valid; red indicator only for actionable failures.
- Tray context: `Открыть CELIKOM`, `Старт / Стоп` (when permitted), `Вернуть оригинал` (if active), `Настройки`, `Выход`. A dismissed window may continue as a tray process only after clear user choice; `Выход` unhooks integration and releases its resources.
- Windows startup OFF by default, explicit permission/setting; no forced overlay or auto-launch popups.
- When Yandex quits or updates, revert to neutral detecting, safely dispose old hooks, do not spam notifications.
- Notification only for first successful setup, loss requiring action, or version mismatch, rate limited.
- Self-update and Yandex compatibility are two separate statuses; software updates cannot be disguised as forced music app changes.

## Upload/suggestions/rights

- Reuse browser/mobile server contract only after current endpoint audit; do not invent new permissions.
- Contribute/song reward policy 2% per approved song up to 20% monthly **subject to latest backend authoritative rules**; don't hardcode unverified numbers in UI.
- Verify MIME/format/duration/size and that user affirms rights before upload. No premature success claim.
- If version already exists, disable redundant request; provide explanation and optional «Вернуть оригинал» if active. Duplicate detection is server-authoritative.

## Review gates

W-UX1: static offline visual prototype must show all statuses with no overflow at ~390/460/768 px and at 125/150% scaling. W-UX2: owner approves design, terminology and Windows behavior. W-UX3: after technical PoC, replace any assumptions with real confirmed behavior; no fabricated control state or progress.

See [mockup.html](mockup.html). It is a **design demo**, not a Windows build, and includes no live service connection.

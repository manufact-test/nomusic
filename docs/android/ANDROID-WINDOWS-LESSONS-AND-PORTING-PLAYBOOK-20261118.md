# CELIKOM Android A1 — Windows incident pool and code-reuse playbook
**Дата:** 18.11.2026  
**Назначение:** передать Android-разработчику проверенные Windows-инциденты, точные места исправлений и ограничения переноса. Это технический справочник, а не разрешение менять Android runtime вслепую.

## 0. Сначала — текущая граница платформ

### Windows: принятая рабочая база
- Приложение: **CELIKOM Windows 0.24.51.0**.
- Native Yandex module: **0.24.32**.
- Владелец несколько часов слушал музыку и переключал VPN; сообщил, что Яндекс не перезапускался, музыка не прерывалась, UI работал нормально. Это текущая owner-accepted рабочая версия / private beta.
- Точный W20 source package: **\`c717428a7d9f01fc8e33b482fcf66a9ed1a02947\`**.
- W169 UI handoff: \`1ac135ba5312473cc6c7feca8d1f5f57726f5342\`.
- W169 native Electron exception guards: \`b2f9131132e26020fd861dcb71d3c33b8ff9a0c1\`.
- Владелец подтвердил VPN-переключения без слышимого разрыва на этой версии. Причина прежних редких перезапусков Yandex не была доказана окончательно; W169 закрыл опасные необработанные ошибки, а не доказал, что именно они вызвали конкретный старый вылет.
- Полная история и release boundary: \`docs/windows/CURRENT-WORKING-RELEASE.md\`, \`docs/windows/W169-TRACK-HANDOFF-AND-YANDEX-RESTART-GUARD-20261117.md\`.

### Android A1: не считать Windows-успех Android-успехом
- Текущая Android-ветка: \`experiment/android-a1-metrica-init-state-observer-arm13-20261112\`.
- Android handoff на момент создания файла: NAV31, ветка HEAD \`258171c8f7121a22c1139c218b12f9b9c54348d2\`.
- Текущий Stage B CELIKOM replacement: **NOT_CONNECTED**. NAV31 — read-only native lifecycle/holder diagnostic APK, а не подмена аудио.
- Оригинальный Yandex 2025.10.4, один штатный Player/decoder и существующая подпись должны оставаться нетронутыми. Следующий Android шаг определяется \`docs/android/NEXT-CHAT.md\`, а не этим Windows playbook.
- Android уже доказал отдельные structural/renderer/queue-holder связи, но это пока не равно выбранному текущему Track+edition+generation, активному MediaPeriod/decoder input или PCM. Не объявлять звук подменённым по одному положительному счётчику.

## 1. Короткая модель Windows-архитектуры

Windows не создаёт второй музыкальный плеер. Она подменяет разрешённый source на границе нативного Yandex resource/file-info до того, как штатный Yandex player использует источник.

Основные слои:
- **W15 .NET companion** — авторизация/entitlement, Start/Stop, локальный bridge, process lifecycle, UI, обновление.
- **W22 native resource adapter** — exact track mapping и изменение file-info только для проверенного CELIKOM grant.
- **W23 Electron host + renderer** — доверенная граница между desktop main process и renderer, Yandex player state, passive CDP decoder witness, source recovery.
- **W20 installer / W24 native image checks** — безопасная установка, обновление/восстановление нативного модуля и проверка целостности.

Ключевой принцип для Android: **сохранить штатный player и clock; доказать точную границу source selection до prepare; не строить второй player и не синхронизировать два независимых audio clock.** Но Windows-файлы, Electron/CDP hooks и desktop Yandex API не являются Android implementation.

---

## 2. Каталог Windows-проблем: симптом → причина → исправление → переносимость

### W56 — настоящие HTTP 403 на CELIKOM media после преобразования signed URL

**Симптом.** На ранней Windows-сборке Yandex запрашивал CELIKOM media, но сервер отвечал 403. Владелец слышал оригинальные песни, когда ожидал replacement.

**Доказанная причина.** Desktop Yandex \`DownloadInfoSource.src\` добавлял \`?vsid=...\&source_index=...\` к уже подписанному CELIKOM URL, в котором query уже содержал \`token\`, \`expires\`, \`sid\`. В итоге значение SID повреждалось вторым знаком вопроса, и строгая серверная проверка HMAC/session/expiry правильно возвращала 403.

**Windows-код.**
- \`windows-companion/w22/native-resource-adapter.mjs\` — \`nativePlaybackUrl()\`, \`toDownloadInfo()\`.
- Для уже валидированного replacement media URL добавляется инертный хвост \`&celikom_native_query_guard=0\`. Yandex metadata query поглощается значением этого незначимого поля; \`token/expires/sid\` остаются неизменными, \`#t=\` seek fragment продолжает работать.
- Guard применяется только к approved+validated CELIKOM media URL. Обычные Yandex URLs, grant resolve, HMAC, SID и server policy не меняются.
- Исходный W56 code commit: \`e6313ce5ed1099616a353fb59927847bb1db2beb\`.

**Проверки/доказательство.** Синтетические и PHP проверки: guarded URL Range 206, corrupted SID/expired/forged HMAC по-прежнему 403; disposable Yandex integration/restore. Затем владелец подтвердил реальное воспроизведение на Windows 0.24.7: настоящие native Media GET 206 и ноль 403.

**Android: НЕ переносить guard.** В Android не доказано аналогичное \`?vsid\`-добавление. Android \`NativeGrantContract.java\` намеренно принимает только canonical signed URL и запрещает неизвестные query-параметры. Сначала получить приватную диагностику именно финального Android media request URL после всех native преобразований; только доказанная Android query corruption может оправдать отдельную совместимую правку. Никакого ослабления HMAC/session/expiry.

### W76/W89 — устаревший или не загруженный source, bounded recovery без бесконечных reload

**Симптом.** После transient bridge/source failure current mapped track мог остаться на оригинальном source; повторные запросы и reload могли вызвать лишний переход/поп или работать уже на следующей песне.

**Windows-код.**
- \`windows-companion/w23/transient-source-recovery.mjs\` — \`createTransientSourceRecovery()\`.
- Recovery хранит job по точному track ID + epoch; перед каждым prime/reload проверяет, что job всё ещё текущий, CELIKOM active и Yandex currentTrackId совпадает.
- Повторы ограничены задержками \`650 ms\` и \`2400 ms\`; подтверждение после grant ждёт короткое окно, чтобы Yandex сам показал свежий decoder source.
- Если passive decoder witness уже подтвердил текущий CELIKOM source, \`confirmedCurrentSource()\` отменяет ожидающий retry/confirmation и не делает лишний reload.
- \`cancel()\` увеличивает epoch и очищает таймеры/jobs. Next/Stop/disable должны инвалидировать старую работу.
- В W89 для current mapped track с grant, но без наблюдаемого media GET, был добавлен максимум один refresh на трек за 120 секунд; renderer повторно проверяет exact current track, enabled state и player availability. Это не бесконечный retry.
- Существующий Yandex \`reloadEntity("QUALITY_CHANGE")\` в Windows сохранял pause/position/queue; это desktop-only контракт.

**Android переносит только правила:** bounded retry; exact current item; generation/epoch fence; stale async completion discarded; retry только при доказанной причине; current source proof может отменить будущий reload. Android не должен вызывать Windows \`reloadEntity\` или менять source, пока точная Android native pre-prepare точка не доказана.

### W152/W157/W158/W164 — VPN A→B: сеть потерялась, но текущая музыка ещё играет

**Симптом.** VPN переключался, CELIKOM терял entitlement/API connection и UI показывал disconnected. При этом Yandex replacement продолжал звучать. После восстановления CELIKOM иногда делал ненужный source switch: replacement → original → replacement, слышался click/pop. На некоторых Yandex builds CDP \`kUrl\` вообще отсутствовал, поэтому старый exact-decoder-only hold не мог сработать.

**Причина.** Временный отказ entitlement GET трактовался как обычный Stop/source loss. Bridge lease/metadata сбрасывались, а renderer после reconnect повторно revalidated/reloaded тот же track. Дополнительно повторные Windows adapter route notifications могли перезапускать entitlement checks и удерживать stale route hint.

**Windows-код и итоговая защита.**
1. \`windows-companion/w15/Celikom.Companion/MainWindow.cs\` — \`OnNetworkAddressChanged()\`, \`RecheckAfterRouteSettledAsync()\`, \`StopPlaybackExplicitly()\`.
2. \`NetworkRouteBurstPolicy.cs\`:
   - burst window **8 секунд**;
   - quiet period **3 секунды**;
   - каждый route event увеличивает epoch, поэтому последний сигнал владеет проверкой; дубли не сбрасывают source-hold handshake.
3. \`EntitlementCheckRecovery.cs\`:
   - быстрый post-route GET timeout **5 секунд**;
   - fast-route window **8 секунд**;
   - suspended read-only retry cadence **3 секунды**;
   - healthy entitlement poll остаётся **15 секунд**;
   - только свежий authenticated server response может возобновить работу. 401/403 — denial, а не transient VPN error.
4. \`CompactPopupActions.RefreshCompactAccessAsync()\`:
   - отменяет запрос на старом VPN route;
   - проверяет тот же account/installation generation;
   - после VPN event делает новый короткий GET;
   - на transient failure временно fail-closed выключает entitlement/bridge, сохраняя отдельный recovery intent;
   - возобновляет только после свежего положительного entitlement и совпадающего установленного native module.
5. \`windows-companion/w23/host.cjs\` — держит краткий recovery witness для того же текущего Yandex track, который был mapped и всё ещё PLAYING/PAUSED. Это особенно важно на Yandex builds без CDP \`kUrl\`: host повторно читает read-only current track ID и playback state; witness содержит только track identity, не decoder URL.
6. \`windows-companion/w23/renderer-entry.mjs\` — самостоятельно проверяет тот же currentTrackId, PLAYING/PAUSED и \`adapter.hasMappedTrack(currentTrackId)\`. Только тогда пишет \`NATIVE_ROUTE_RECOVERY_SOURCE_KEPT\` и не вызывает source reload. Hold остаётся UNKNOWN, это НЕ decoder proof.
7. W158 добавил matching recovery epoch/acknowledgement: поздний старый heartbeat не может снять hold, пока resumed renderer не подтвердил доставленное состояние. Next, Stop, player destruction, logout, denial, origin change, invalid/unavailable state и timeout остаются fail-closed. TTL hold ограничен 10 минутами; после потери источника требуется новый mapping.
8. W164 улучшил route burst: 8s coalescing, 3s quiet period, 5s deadline, 8s fast-route window; после свежего успешного ответа route hint очищается, нормальный poll возвращается к 15s.

**Проверенные checkpoints.**
- W152 final code: \`59894be3fe88de0dfecd9d92c9164b509d0c7859\`.
- W157 no-kUrl final code: \`2948c38343cc8fba0027fe2c1a38b104b38a80ca\`.
- W158 owner field regression fix: \`3f6affc242ef570120250d2e20eec791338f2ef9\`.
- W164 route/transition code: \`167cda990f2ddb585731093b5d2e0d381e63e7e9\`, \`5a395c7b0eed1f1718dc2a500cbe5163a8c3e621\`, \`2b7fb2d3627c27c1ec9052e49b7abdb49b87429e\`.
- W169 accepted package source includes all previous fixes: \`c717428a7d9f01fc8e33b482fcf66a9ed1a02947\`.

**Owner acceptance.** On Windows 0.24.51 the owner explicitly reported several hours of listening and VPN switching without music interruption. This is the useful real-world acceptance. Do not reinterpret old VPN/network log entries as audible dropouts if the owner heard continuous music.

**Android переносит принцип, но не Windows code.** Android should observe Android's actual route/connectivity changes and entitlement HTTP failures independently. A network transition is not proof of decoder/source loss. Preserve an already-selected current source only when Android can prove same selected item + same source instance + same generation + PLAYING/PAUSED and same authenticated account/origin. If any of those are unknown, do not fabricate continuity proof; keep source status unknown and fail closed for new grants. Android needs its own source/player lifecycle witness before adding a hold.

### W131/W132 — не перезагружать уже оригинальную песню

**Симптом.** При VPN/entitlement OFF→ON CELIKOM мог послать \`QUALITY_CHANGE\` для трека, который уже вернулся на original source. Это давало ненужный reload, pop или сброс playback position.

**Windows-код.**
- \`windows-companion/w23/renderer-entry.mjs\` — \`__celikomBridgeNativeRecoverSourceLeft(trackId)\`: callback вызывается только после того, как passive native CDP witness подтвердил, что текущий decoder раньше играл exact CELIKOM signed URL, а затем ушёл с него.
- Сначала валидируется currentTrackId, затем старый mapping немедленно инвалидируется через \`adapter.forgetMappedTrack(trackId)\`, даже если одновременно CELIKOM уже disabled. Это предотвращает stale mapping и повторный reload original.
- Новый recovery разрешён только если CELIKOM enabled, тот же трек всё ещё current, player attached; попытка ограничена одним вызовом на трек за 15 секунд.
- W131 code \`5fb5f32d0364d476889bf56d0f8e8fc0e38d71b2\`, regression test \`2f41091d1af072483ed5c79782958002b0ee2101\`.
- W132 \`c02cd4988292598f81e857062279d0179253a42a\` добавил полный test: после verified source-left и VPN A→B, если новый resolve не дал replacement, оригинальный decoder не получает повторный reload, playback state/position сохраняются.

**Android:** source-left должен инвалидировать только exact current mapping до решения о recovery; stale mapping нельзя считать активным после смены source. Но нужен Android-native доказанный source-left callback, а не desktop CDP imitation.

### W125/W89 — не показывать ложное «CELIKOM играет»

**Симптом.** UI показывал зелёный active status, хотя был только mapping/grant/HTTP prefetch, а Yandex мог фактически продолжать играть оригинал. Отдельный случай — «Ты» (13 КАРАТ): presence/mapping были, но exact current media GET/decoder source не подтверждался.

**Windows-код.**
- \`windows-companion/w15/Celikom.Companion/PlaybackSourceEvidence.cs\`:
  - \`Verified()\` требует enabled + \`NATIVE_SOURCE_VERIFIED\` + approved presence.
  - \`MappedButUnverified()\` отдельно описывает mapping без доказанного decoder source.
  - \`OriginalVerified()\` требует отдельного original-source witness.
- \`windows-companion/w23/host.cjs\`: passive CDP сопоставляет current track ID, signed CELIKOM \`kUrl\` и \`kIsPlaying\`; только это даёт \`NATIVE_SOURCE_VERIFIED\`. HTTP 200/206, grant, file-info mapping, heartbeat, network bytes и presence сами по себе недостаточны.
- \`windows-companion/w15/Celikom.Companion/CompactPlaybackPresentation.cs\` — \`ActiveReplacementStatusIsGreen()\` требует current source ACTIVE_REPLACEMENT + PLAYING + exact native verification.
- W125: при CDP detach сразу очищает verified decoder witness, expected audio, media success, observer-ready и cached decoder properties. После потери наблюдателя UI немедленно становится neutral/unverified; не пытается захватить DevTools обратно. Code \`d083218b4adb0b7fb1d1321d09b56245ab40fbd1\`.
- W89: если mapped current track не дал native media GET в ограниченное окно, разрешён один bounded refresh; это не превращает mapping в audible proof.

**Android:** этот принцип критически переносим: grant resolved ≠ file-info mapped ≠ MediaSource created ≠ selected/attached decoder stream ≠ audible PCM. Android evidence должен различать каждую ступень и инвалидироваться на detach/destroy/Next/source change. Не считать MediaSession PLAYING или наличие queue holder доказательством, что именно этот CELIKOM source декодируется.

### W163/W164/W169 — пустой экран и ложные служебные тексты при Next

**Симптом.** На переходе между песнями исчезали title/artist; вместо них мигал \`Track ID …\`, \`Проверяем версию песни CELIKOM…\`, «ожидаем подключение» или другое служебное состояние. Это происходило при обычном Next без реальной потери музыки.

**Windows-код.**
- \`windows-companion/w15/Celikom.Companion/BridgeServer.cs\` — ID-less PLAYING/PAUSED transition metadata сохраняется ограниченно, только если bridge enabled и player не unavailable.
- \`windows-companion/w15/Celikom.Companion/CompactPlaybackPresentation.cs\`:
  - \`TrackTitle()\` не показывает raw ID;
  - \`HoldPreviousTrackDuringGap()\` держит последний реальный title на **2.5 секунды** только при fresh heartbeat, живом player, не во время VPN recovery/Start и допустимых native states;
  - после grace period старое название очищается.
- \`windows-companion/w15/Celikom.Companion/CompactPopup.cs\`: удерживает title/artist/status во время короткого ID/metadata gap; не запускает новую presence display, пока metadata request pending.
- W164 удалил технический Track ID placeholder и скрывает pending «Проверяем версию…».
- W169 добавил регрессионные проверки для Next gap, STOPPED, VPN recovery, stale heartbeat, host error и истечения grace. W169 UI commit \`1ac135ba5312473cc6c7feca8d1f5f57726f5342\`.

**Android:** можно перенести только UI metadata grace: сохранить прежний title/artist на короткое время при подтверждённом transition, но никогда не использовать это как playback/source identity. Новый MediaItem/track должен атомарно заменить старый UI snapshot. При Stop, player destruction, real error или смене generation старое состояние немедленно очищается.

### W158 — autorun falsely reported connected before Yandex player handshake

**Симптом.** Windows после reboot показывал connected, хотя Yandex native host/player ещё не attached; пользователю приходилось нажимать Stop→Start.

**Windows-код.**
- \`MainWindow.Autostart.cs\` — \`ResumeSavedPlaybackAsync()\` отделяет сохранённое намерение Start от реальной готовности. Получает fresh read-only entitlement, проверяет matching native module, поднимает bridge в WAITING состоянии, но не запускает Yandex.
- \`MainWindow.cs\` — отдельный Yandex process pulse + fresh native/player heartbeat; connected отображается только после фактического handshake.
- \`CompactPlaybackPresentation.AutorunNativeConnected()\` — bridge enabled сам по себе не значит connected.
- \`PlaybackStartGate.CanAcceptStart(... recoveryPending)\` — Start блокируется при automatic recovery, Stop остаётся доступным.
- W158 code \`3f6affc242ef570120250d2e20eec791338f2ef9\`; tests cover Yandex already open, Yandex opened later, delayed handshake and explicit Stop.
- Не запускает Yandex при Windows sign-in; explicit Stop отменяет pending resume.

**Android:** полезно разделять desired playback intent, service/bridge alive, Yandex process alive, native Player attached, actual playback state. Foreground service alive не равен player ready. Но Windows registry/StartupApproved/WinForms timer code не переносится.

### W169 — Yandex сам закрывался и открывался около конца песни

**Симптом.** В диагностике было \`PLAYER_CDP_DETACHED\`, затем \`HOST_LOADED\`; это подтверждало host reinitialization, но не причину. В логе не было доказанного CELIKOM reload command, OS crash reason или Yandex update event.

**Windows code guard.**
- \`windows-companion/w23/host.cjs\`:
  - fire-and-forget native relay calls теперь идут через \`scheduleTick(view)\`;
  - внутри \`scheduleTick\`: \`void tick(view).catch(() => note("NATIVE_RELAY_TICK_EXCEPTION"))\`;
  - CDP \`debug.on("message")\` callback обёрнут в try/catch. При malformed/unexpected payload source witness очищается, пишется \`NATIVE_CDP_EVENT_EXCEPTION\`, но player controls не вызываются и Yandex не перезапускается.
- W169 native commit \`b2f9131132e26020fd861dcb71d3c33b8ff9a0c1\`; synthetic malformed CDP event regression added.
- W169 did NOT change native 300ms relay cadence, URL/source decision, media reload, VPN, server/auth or audio.
- Владелец затем несколько часов слушал 0.24.51 без нового перезапуска.

**Evidence boundary:** конкретная старая причина Yandex restart не доказана. Эти guards закрывают crash-capable unhandled async/callback exceptions, но не доказывают, что именно они вызвали тот incident. Если Android process restarts, собирать exact process exit/crash + OS tombstone/ANR + coroutine/Looper exception; не считать простое service reconnect причиной.

### W126/W104 — duplicate activation and native host/version recheck

**Проблема.** При первом Start могла выполняться лишняя повторная activation request; network failure ошибочно выглядел как native module damage. После native HOST_ERROR/нет handshake нужен bounded compatibility recheck, но не бесконечный refresh.

**Windows-код.**
- \`StartupActivationRecovery.ActivateAsync()\` — максимум один bounded retry transient transport/temporary server error только пока тот же Start generation и account активны; 401/403 и 429 не повторяются.
- \`YandexFailureRecheckGate.cs\` — coalesced backoff **2/4/8/15 минут** для native host/start failure; успешный handshake сбрасывает backoff. ORIGINAL/audio 403 не запускает ложный vendor compatibility refresh.
- \`MainWindow.cs\` — host error/отсутствие startup handshake около 22s / native install failure вызывает read-only official Yandex catalog refresh и повторную identity inspection.
- W126 code \`ed41f613640f55c8de4a027a8f6f12ac31a15093\`; W104 code \`9ac9a5ab485c3ce1bebc8aa6a2352b422c0ffa1c\`.

**Android:** reuse bounded retries + same-account/session + generation checks; no retries on authoritative denial. Don't assume Windows vendor catalog logic maps to Android package/signer/split compatibility.

### W101/W109 — safe update and rollback (important pattern, not complete public auto-updater)

**Problem.** A native module/application update can mismatch code/assets, damage Yandex integration or strand an existing user session.

**Windows code.**
- \`StableUpdateManifestVerifier.Verify()\`: P-256/SHA256 detached signature, pinned public key/origin, monotonic version sequence, expiry, package size/hash, publisher identity.
- \`StableUpdateRollbackJournal.PrepareManifestVerified()\`: DPAPI-protected user-scoped journal; exact previous/target payload hashes (app, host, renderer, supervisor), session fingerprint, one transaction lock.
- Journal stages Prepared → InstallerStarted → NewAppObserved → Healthy or RollbackNeeded → RollbackStarted → Restored/ManualRecovery. Ten-minute bounded health window, one rollback attempt; tampered/corrupt/overlapping records fail closed.
- W109 code \`0d90fea82cfd8d95e7c830941e1443cafa594fd3\`; W114 extended exact payload identity.
- **Limit:** W109 journal alone did not execute rollback; production supervisor/signing was still gated. W101 production signing key/AuthentiCode/live stable feed were not enabled. The 0.24.51 installer remains unsigned private beta; don't describe it as signed public GA.

**Android:** reuse immutable version identity, signer verification, atomic staging, in-place upgrade, rollback snapshots and explicit health gates. Keep Android signer/owner APK chain independent; never copy Windows DPAPI, Authenticode or Inno Setup code.

### W90/W93 — gain_db and Big City Life mid-song volume drop (NOT solved as a universal Android/Windows fix)

**Problem.** Windows native path ignored numeric admin \`gain_db\`. It passed Yandex boolean \`gain:false\`, which cannot represent per-track dB. Big City Life had a separate reported mid-song volume dip; its exact trigger was not proven.

**Code/research.**
- W90 showed Windows GrantValidator/SourceGrant did not carry numeric \`gain_db\`; Windows raw media path did not perform the Chrome extension's Web Audio gain.
- W93 built a guarded **offline** ffmpeg pre-render + private sidecar staging/rollback prototype. It was not a general live production fix and not an approved universal runtime DSP.
- Do not change global volume, Yandex boolean gain or original audio bytes. Do not run CPU-heavy ffmpeg from the PHP request path. Do not double-apply gain when source already processed.

**Android:** do not import gain changes without an independent Android audio pipeline/volume contract and acoustic test. This is a known historical problem, not a solved Windows code snippet to copy.

### W58 — Stop means no new mappings, not necessarily instant cancellation of buffered audio

Windows owner confirmed that Stop disables new CELIKOM lookups and invalidates pending responses, but it cannot retract an already-delivered signed URL or media already buffered by Yandex. Existing current audio may finish. This distinction matters: do not force Next/Seek/reload just to fake immediate revert unless a non-destructive native contract is proven.

Android already has the pure-Java lifecycle model:
- \`NativeGrantContract.java\` — strict structural signed grant validation.
- \`NativeReplacementLifecycle.java\` — epoch-fenced source admission; OFF cancels decision eligibility for outstanding work; old completions cannot map a later track.
- Current model does not itself cancel actual transport or change an already buffered player source. Do not claim otherwise.

---

### Дополнение к W76: защита W22 adapter от Next/radio race

В **windows-companion/w22/native-resource-adapter.mjs** есть более низкий уровень тех же гарантий:
- **revision** меняется при track change / enable / disable; **cancel()** увеличивает revision, abort-ит pending requests и очищает очередь.
- **trackChanged(id)** отменяет старые resolve jobs до применения результата новой песни.
- **lookup(id, revisionAtStart)** проверяет enabled/disposed/revision, ограничивает timeout, использует AbortController и не кеширует transient timeout как authoritative ORIGINAL.
- **getFileInfo** сначала вызывает оригинальный Yandex method, параллельно запрашивает grant, а replacement применяет только если **isLive(id, rev)** всё ещё true. Если нет grant/истёк generation — возвращает оригинальный native file-info.
- **getFileInfoBatch** меняет только существующие native response entries с exact matching ID; не создаёт выдуманные metadata entries и не добавляет отсутствующие IDs.
- **dispose()** восстанавливает оригинальные методы prototype, если их hooks всё ещё принадлежат CELIKOM.

Это один из самых полезных Android шаблонов: не применять поздний grant к новой песне, не мутировать чужой/старый response, вернуть оригинал при отсутствии корректного grant и восстановить hook при unload. Но Java/Kotlin реализация должна отменять coroutine/job и проверять собственную generation, а не копировать JS AbortController.

### W60 — Start/Stop для уже загруженной текущей песни

**Симптом.** Bridge успешно переключался OFF→ON, но Yandex не запрашивал новый file-info для уже играющего MediaItem. Поэтому Start мог не применить replacement к текущей оригинальной песне, а Stop не всегда мгновенно возвращал уже загруженный replacement к оригиналу.

**Windows-решение.**
- В disposable desktop Yandex 5.126.1 был read-only подтверждён штатный controller **7123.VE.reloadEntity("QUALITY_CHANGE")**: он заново получает source для того же entity, сохраняет position и различает PLAYING/PAUSED.
- Экспериментальный W60 **windows-companion/w60/current-source-refresh.mjs** был version-pinned к этому controller. Renderer сначала менял adapter state, затем сериализованно просил Yandex сделать source reload; никаких Next/Pause/Seek команд и второго плеера.
- Если controller не найден или version не совпала, операция fail-closed/no-op.
- Owner audio controls baseline 0.24.9 подтвердил Pause/Seek/Next/MyWave; Start/Stop same-track reload был отдельным desktop экспериментом.

**Android:** не копировать **reloadEntity**, его private controller, desktop module ID или предположение о сохранении clock. В Android должен быть отдельно доказан штатный способ сменить source того же MediaItem без второго Player, потери position и pause state. Пока это не доказано, не обещать instant same-track Start/Stop; безопаснее не вмешиваться в уже buffered source.

### W157 — Yandex закрыт, но старый track остаётся в UI

**Симптом.** После полного выхода из Yandex CELIKOM мог показывать прежнюю песню ещё около 30 секунд, пока не истечёт heartbeat lease.

**Windows-решение.**
- **YandexProcessLifecycleTracker.Observe()** замечает переход process running→not running.
- **MainWindow.cs** опрашивает процесс отдельным 1-second pulse.
- W23 selected renderer **destroyed** handler отправляет sequenced **UNAVAILABLE** heartbeat, если выбранный player исчез и другого выбранного playback view нет.
- Bridge очищает title/artist/track/source/playback lease и отвергает heartbeat от retired host/process после reconnect.
- UI показывает «Подключитесь к Яндекс Музыке», а не старый трек и не generic server wait.
- W157 code checkpoint **23538cab793be9d1381790d4c304db3cd4d4b417**; W158 окончательно закрыл handshake/retired-host race на **3f6affc242ef570120250d2e20eec791338f2ef9**.

**Android:** процесс/Service/Player destruction должны иметь отдельные события. Не держать старый MediaItem UI по длинному heartbeat TTL после реального player destruction; не принимать late callbacks старого Player generation после нового Player attach.

### W51/W56 — что было доказано про 403, а что только предполагалось

- W51 owner diagnostic на 0.24.6: **7 реальных Yandex Media GET → 7 HTTP 403, 0 HTTP 200/206**. Обычные оригинальные треки работали, approved replacements не стартовали и быстро уходили в Play/Pause.
- W51 не позволял доказать точную причину: signed query и response body были redacted. Тогда query corruption была гипотезой.
- W56 позже нашёл конкретный vendor query-append mechanism в desktop source flow и добавил узкий native URL guard. Владелец затем подтвердил replacement playback на 0.24.7 и реальные HTTP 206.
- Не путать CELIKOM resource ID в **/api/v1/audio/{replacement_id}** с Yandex track ID. Диагностика должна иметь отдельные **track_id** и **resource_id**, иначе можно обвинить не ту песню.
- W33 ранее исследовал CORS/CSP; публичная web CSP не доказывала native **musicapplication://desktop** CSP. Нельзя отключать **webSecurity**, ослаблять CSP глобально или делать CORS wildcard «на всякий случай». В итоге узкий signed-query issue оказался практическим desktop blocker; это не означает, что любой Android 403 имеет ту же причину.

### W81 — Yandex vendor updates / compatibility

**Проблема.** Официальный Yandex может обновиться и изменить EXE/ASAR/runtime hooks; совпадение версии или наличие официальной подписи само по себе не доказывает совместимость source adapter.

**Windows-решение.**
- Append-only reviewed catalog точных Yandex EXE+ASAR version/hash/publisher pins; новые unknown builds не принимаются автоматически.
- Отдельные v1/v2 catalog schemas сохраняли backward compatibility со старыми клиентами.
- Disposable runner проверяет vendor signature/hash, install→module identity→byte-for-byte restore; после этого developer отдельно подтверждает runtime API/audio compatibility.
- W104 **YandexFailureRecheckGate** делает coalesced 2/4/8/15-minute backoff после native HOST_ERROR/start failure, но ORIGINAL/audio 403 не считается vendor install failure.
- Новый Yandex build нельзя считать рабочим только потому, что официальный updater его установил.

**Android:** pinned original APK/split signer and hashes, ABI/split inventory, owner signer and native hook compatibility должны быть отдельными gates. Не заменять publisher original на неизвестный build и не переносить Windows catalog assumptions.

### Отдельные нерешённые/не доказанные аудио-симптомы

- **Hiss после VPN/403:** W89 видел реальный expired-token 403 → fresh 206 в одном случае, а владелец описал громкий hiss. Точная причина hiss не была установлена. Не считать, что query guard автоматически исправил любой hiss/pop.
- **Big City Life mid-song volume dip:** W90 установил, что Windows native path не применял numeric gain_db; W93 подготовил offline pre-render/sidecar staging, но это не стало универсальным live DSP fix. Само падение громкости посреди песни имело отдельную, не доказанную причину.
- **Instant pause в ранних 0.24.6 builds:** W51 связал не стартовавшие replacements с реальными 403; W56 затем дал практическое исправление signed URL desktop path. Не переносить старые симптомы на текущую Android ветку без воспроизведения.
- **Brave/web renderer fetch/CSP** из W33 — отдельная desktop/browser исследовательская ветка; точный native desktop CSP не был доказан. Это не Android source boundary.

## 3. Windows code map for quick inspection

| Что искать | Файл / метод |
| --- | --- |
| VPN route event + epoch + quiet period | \`w15/Celikom.Companion/MainWindow.cs\`: \`OnNetworkAddressChanged\`, \`RecheckAfterRouteSettledAsync\`, \`StopPlaybackExplicitly\` |
| Route burst/quiet-period policy | \`w15/Celikom.Companion/NetworkRouteBurstPolicy.cs\` |
| Entitlement timeout/retry/resume | \`w15/Celikom.Companion/EntitlementCheckRecovery.cs\`, \`CompactPopupActions.cs:RefreshCompactAccessAsync\` |
| Current-track hold on VPN | \`w23/host.cjs\`, \`w23/renderer-entry.mjs\` |
| Exact current source proof | \`w23/host.cjs:currentDecoderPlayer/capturePlayerProperties\`, \`w15/Celikom.Companion/PlaybackSourceEvidence.cs\` |
| Bounded source retry | \`w23/transient-source-recovery.mjs:createTransientSourceRecovery\` |
| Source-left invalidation | \`w23/renderer-entry.mjs:__celikomBridgeNativeRecoverSourceLeft\` |
| Signed URL compatibility guard | \`w22/native-resource-adapter.mjs:nativePlaybackUrl/toDownloadInfo\` |
| UI metadata handoff | \`w15/Celikom.Companion/CompactPlaybackPresentation.cs:HoldPreviousTrackDuringGap\`, \`CompactPopup.cs\`, \`BridgeServer.cs\` |
| Yandex process/host lifecycle | \`w15/Celikom.Companion/MainWindow.cs\`, \`YandexProcessLifecycleTracker.cs\`, \`w23/host.cjs\` |
| Autorun handshake | \`w15/Celikom.Companion/MainWindow.Autostart.cs:ResumeSavedPlaybackAsync\` |
| Start/Stop recovery gate | \`w15/Celikom.Companion/PlaybackStartGate.cs\` |
| Yandex failure compatibility backoff | \`w15/Celikom.Companion/YandexFailureRecheckGate.cs\` |
| Safe update/rollback patterns | \`StableUpdateManifestVerifier.cs\`, \`StableUpdateRollbackJournal.cs\`, \`AppUpdateManager.cs\` |

Repository prefix for all Windows files: \`windows-companion/\`.

## 4. What Android should reuse — and what it must NOT copy

| Windows pattern | Android decision |
| --- | --- |
| One native player/clock; source-first before prepare | **Reuse as architectural invariant.** Do not create a second player. |
| Exact track identity + generation fence + stale completion rejection | **Reuse.** Android identity must include Track + album/edition + duration + queue/source generation where proven. Track ID alone may not be enough. |
| Fresh authenticated entitlement after network recovery; denial is final | **Reuse.** No offline grant, cached permission or resume after explicit Stop/logout/account change. |
| VPN/network state != audio source loss | **Reuse conceptually.** Need Android-native current source/player evidence before preserving. |
| Bounded retry and source refresh only for exact current item | **Reuse conceptually.** Use Android coroutine/job cancellation and generation; don't copy JS timers. |
| Clear stale mapping after verified source-left | **Reuse conceptually.** Requires exact Android source-left witness. |
| Current decoder proof separate from mapping/network/MediaSession | **Reuse strongly.** Android must prove same selected stream instance reaches active renderer; no status shortcut. |
| Short UI metadata grace | **Optional UI-only reuse.** Never reuse title cache as source identity. |
| Catch async exceptions at process boundary | **Reuse conceptually.** Catch/report coroutine/handler failures without hiding security errors or fabricating success. |
| W56 \`celikom_native_query_guard\` | **DO NOT COPY.** No equivalent Android query corruption demonstrated. |
| Windows Electron CDP \`kUrl\` proof | **DO NOT COPY.** Android uses signed native/Media3 hooks and separate evidence. |
| Yandex \`reloadEntity("QUALITY_CHANGE")\` | **DO NOT COPY.** Android equivalent not proven. |
| Delete \`key/iv\` and force raw MP3 transport from W22 | **DO NOT COPY.** Android FileInfoDto/DRM/codec contract differs; could break playback or integrity. |
| Windows .NET bridge, DPAPI, Authenticode, Inno Setup | **DO NOT COPY.** Use Android-native lifecycle, signer and storage boundaries. |

### Current Android evidence boundary (18 Nov)

NAV31 has a read-only witness around the exact signed Yandex native holder selection/attach/read lifecycle. It separates exact wrapper / null / other / failed outcomes and stores only bounded weak historical links. It does **not** prove current Track+album/edition/duration/generation, active selected MediaPeriod, replacement source or PCM. NAV24's renderer type1/state2 observations and NAV23's stream/queue observations are structural/renderer evidence, not a CELIKOM audible replacement. Current Android NEXT-CHAT is authoritative.

The existing Android files most relevant to the next engineer:
- \`android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeGrantContract.java\`
- \`android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeReplacementLifecycle.java\`
- Current NAV31 exact hook/model files and their tests as referenced by \`docs/android/NEXT-CHAT.md\`.
- \`docs/android/ANDROID-WINDOWS-W28-LESSONS-2026-11-09.md\`
- \`docs/android/ANDROID-WINDOWS-W57-TRANSFERABILITY-2026-11-10.md\`
- \`docs/android/ANDROID-WINDOWS-W58-NATIVE-REUSE-2026-11-10.md\`
- \`docs/android/ANDROID-WINDOWS-W63-AUDIO-PARITY-OWNED-RELOAD-2026-11-10.md\`

## 5. Android engineer's suggested review sequence

1. Read current \`docs/android/NEXT-CHAT.md\` first. Preserve the exact current NAV31 signed baseline, original publisher Yandex, owner signer and backups.
2. Read this playbook and the four Windows↔Android transfer docs above. Treat all Windows values and API names as desktop-only unless Android evidence independently matches.
3. Build an Android-specific state machine that distinguishes: app/service alive, native Yandex process, current Player, current MediaItem/queue identity, selected source, active renderer stream, entitlement and audible output. Do not collapse them into one PLAYING/connected boolean.
4. Finish exact Android identity chain before replacement: selected Track + album/edition + duration + generation → native MediaSource/period → queue holder → currently attached renderer stream. Exclude prefetch/next/old queue nodes.
5. Only then connect the already strict grant contract at the actual pre-prepare boundary. Preserve original fallback, signed URL semantics, MIME/codec/Range and cancellation. No source mutation until same exact current item and entitlement are proven.
6. Test Next/radio/playlist races, pause/seek, app background/foreground, screen lock, Bluetooth route changes, VPN/network loss, player destruction, Stop/logout/denial, process death/restart and update rollback. These Android-specific surfaces need their own device evidence; Windows tests do not cover them.
7. For every incident, record: owner symptom, exact Android stage that failed, sanitized event sequence, code path changed, regression test, real-phone result, rollback point. CI/static DEX proof must never be labeled audible PASS.

## 6. Evidence labels — use these words accurately

- **Owner-confirmed:** user actually heard/observed it on the real device.
- **Code/CI verified:** deterministic source/test/build contract only.
- **Structural/static proof:** original signed DEX relationships; not live runtime identity.
- **Runtime observer:** event/state observed, but not necessarily current audible stream.
- **Audible proof:** current selected replacement is actually decoded/rendered and owner hears the expected sound.
- **Unresolved:** no root cause or successful field reproduction yet.

Never promote:
- signed grant → mapped source;
- mapped source → selected MediaSource;
- HTTP 200/206 → decoder selected it;
- MediaSession PLAYING → CELIKOM source playing;
- queue holder exists → current audible item;
- no-kUrl continuity hold → exact source proof;
- successful CI → audible/owner acceptance.

## 7. Primary source documents

Windows:
- \`docs/windows/W56-NATIVE-TELEMETRY-QUERY-HMAC-GUARD-20261110.md\`
- \`docs/windows/W89-02433-VPN-RECOVERY-AND-FALSE-GREEN-TRACK-20261113.md\`
- \`docs/windows/W90-ALL-ADMIN-GAIN-TRACKS-AUDIT-20261113.md\`
- \`docs/windows/W93-PRIVATE-GAIN-STAGING-AND-ROLLBACK-20261113.md\`
- \`docs/windows/W104-NATIVE-FAILURE-RECHECK-AND-W101-STABLE-MANIFEST-20261114.md\`
- \`docs/windows/W109-DURABLE-SIGNED-ROLLBACK-JOURNAL-20261114.md\`
- \`docs/windows/W125-CDP-DETACH-DECODER-PROOF-INVALIDATION-20261114.md\`
- \`docs/windows/W131-VERIFIED-SOURCE-LEFT-STALE-MAPPING-INVALIDATION-20261114.md\`
- \`docs/windows/W132-VPN-A-TO-B-SOURCE-LEFT-ORIGINAL-REVALIDATION-20261114.md\`
- \`docs/windows/W152-VPN-AUDIO-SOURCE-HANDOFF-RECOVERY-20261115.md\`
- \`docs/windows/W157-OWNER-FOLLOW-UP-VPN-PLAYER-UI-20261115.md\`
- \`docs/windows/W158-OWNER-FIELD-REGRESSION-VPN-AUTORUN-UI-20261116.md\`
- \`docs/windows/W160-VPN-RECOVERY-PLAYBACK-STATUS-20261116.md\`
- \`docs/windows/W163-OWNER-TRACK-TRANSITION-UI-POLISH-20261116.md\`
- \`docs/windows/W164-OWNER-VPN-RECOVERY-TRACK-TRANSITION-20261116.md\`
- \`docs/windows/W169-TRACK-HANDOFF-AND-YANDEX-RESTART-GUARD-20261117.md\`
- \`docs/windows/CURRENT-WORKING-RELEASE.md\`

Android transfer:
- \`docs/android/ANDROID-NATIVE-WINDOWS-W28-LESSONS-2026-11-09.md\`
- \`docs/android/ANDROID-WINDOWS-W57-TRANSFERABILITY-2026-11-10.md\`
- \`docs/android/ANDROID-WINDOWS-W58-NATIVE-REUSE-2026-11-10.md\`
- \`docs/android/ANDROID-WINDOWS-W63-AUDIO-PARITY-OWNED-RELOAD-2026-11-10.md\`

**Итог:** Windows уже дал нам готовый набор инженерных правил против VPN source-jump, stale async responses, ложного source status, лишних reload оригинала, Next flicker, Electron callback crashes и небезопасных update/rollback. Android-разработчик должен перенести эти правила в доказанные Android-native точки, а не переносить desktop hooks/API буквально.
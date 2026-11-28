namespace Celikom.Companion;

public static class CompactPlaybackPresentation
{
    public const string VersionAvailableMessage = "Версия CELIKOM доступна";
    public const string ActiveVersionMessage = "Играет версия CELIKOM";
    public const string IdleTrackPrompt = "Откройте Яндекс Музыку и выберите песню.";
    public const string ServiceEnabledMessage = "Сервис включён";
    // Idle/disabled copy keeps its original breathing room. A real track status
    // stays compact, with only a 2 px gap before the Account card.
    public const int TrackStatusBottomSpacingPx = 18;
    public const int ActiveTrackStatusHeightPx = 28;
    public const int ActiveTrackStatusBottomSpacingPx = 2;
    public static readonly TimeSpan PresenceCacheLifetime = TimeSpan.FromSeconds(15);

    public const string ConnectingMessage = "Подождите, идёт подключение\nк Яндекс Музыке.";

    public static string StaleHeartbeatMessage(string? playbackState) => playbackState switch
    {
        "PLAYING" => "Музыка продолжает играть.",
        "PAUSED" => "Пауза",
        "STOPPED" => "Воспроизведение остановлено.",
        _ => "Проверяем состояние воспроизведения…"
    };

    public static string TrackTitle(string? title, string? previousTitle, bool retainPrevious) =>
        !string.IsNullOrWhiteSpace(title) ? title :
        retainPrevious ? previousTitle ?? "" : "";

    public static string PresenceStatusMessage(string? presenceStatus) => presenceStatus switch
    {
        "checking" => "Проверяем статус версии песни…",
        "approved" => VersionAvailableMessage,
        "pending" => "Версия песни CELIKOM на проверке",
        "none" => "Версия песни CELIKOM ещё не загружена",
        "error" => "Не удалось проверить версию песни CELIKOM",
        _ => ""
    };

    public static bool PresenceCacheFresh(string? presenceStatus,
        DateTimeOffset checkedAt, DateTimeOffset now) =>
        presenceStatus is ("approved" or "pending" or "none") &&
        checkedAt != DateTimeOffset.MinValue && now >= checkedAt &&
        now - checkedAt < PresenceCacheLifetime;

    // W198: while the compact window is visible, recheck only a pending
    // current-track status every two seconds. Approved/absent states retain
    // the shared 15-second cache and never enter this fast refresh path.
    public static bool PendingPresenceRefreshDue(string? presenceStatus,
        DateTimeOffset checkedAt, DateTimeOffset now) =>
        presenceStatus == "pending" &&
        (checkedAt == DateTimeOffset.MinValue ||
         (now >= checkedAt && now - checkedAt >= TimeSpan.FromSeconds(2)));

    public static bool PresenceResponseMatchesCurrent(string? currentTrackId,
        int currentEpoch, string? responseTrackId, int responseEpoch) =>
        GrantValidator.IsTrackId(currentTrackId) &&
        string.Equals(currentTrackId, responseTrackId, StringComparison.Ordinal) &&
        currentEpoch == responseEpoch;

    public const string TransientRendererGapMessage = "Проверяем состояние воспроизведения…";

    // Electron can destroy the selected Yandex WebContents while the same
    // native host is waiting for its replacement. That emits a fresh
    // UNAVAILABLE heartbeat, unlike a real process exit which clears the
    // heartbeat timestamp. Keep the compact UI neutral for this short handoff.
    public static bool IsTransientRendererUnavailable(bool enabled,
        bool heartbeatFresh, bool playerUnavailable, string? nativeStatus,
        DateTimeOffset lastHeartbeatAt, DateTimeOffset now) =>
        enabled && heartbeatFresh && playerUnavailable && nativeStatus == "UNAVAILABLE" &&
        lastHeartbeatAt != DateTimeOffset.MinValue && now >= lastHeartbeatAt &&
        now - lastHeartbeatAt <= TimeSpan.FromMilliseconds(2500);
    public const string NetworkRecoveryMessage = "Связь с сервером восстанавливается.";
    public const string StartupTimeoutMessage =
        "Не удалось подключиться к Яндекс Музыке. Проверьте, что приложение открыто, и попробуйте ещё раз.";

    // A bridge permission is not a native Yandex connection. Only a fresh,
    // actual player/host heartbeat may complete silent Windows autorun.
    public static bool AutorunNativeConnected(bool bridgeEnabled, bool heartbeatFresh,
        bool playerUnavailable, string? nativeStatus) =>
        bridgeEnabled && heartbeatFresh && !playerUnavailable &&
        nativeStatus is "NATIVE_CONNECTED" or "NATIVE_MAPPING_ACCEPTED" or
            "NATIVE_SOURCE_VERIFIED" or "NATIVE_ORIGINAL_SOURCE_VERIFIED";

    public static bool StartupComplete(bool bridgeEnabled, bool heartbeatFresh,
        bool playerUnavailable = false, string? nativeStatus = null) =>
        nativeStatus is null ? bridgeEnabled && heartbeatFresh :
            AutorunNativeConnected(bridgeEnabled, heartbeatFresh,
                playerUnavailable, nativeStatus);

    // Service connection is a live native-host heartbeat, not proof that the
    // current track is using a CELIKOM decoder source. A pending server-route
    // recheck does not make a still-live native host disconnected.
    public static bool ServiceConnected(bool bridgeEnabled, bool heartbeatFresh,
        bool playerUnavailable) =>
        bridgeEnabled && heartbeatFresh && !playerUnavailable;

    public static bool ShouldShowModuleUpdateHint(bool playbackEnabled, bool startInProgress,
        bool autoReconnectBusy, bool moduleMismatch) =>
        !playbackEnabled && !startInProgress && !autoReconnectBusy && moduleMismatch;

    public static bool CanCompleteStartPresentation(bool integrationBusy, bool moduleMatches,
        bool startupComplete) =>
        !integrationBusy && moduleMatches && startupComplete;

    // Green is reserved for proof about the current audible decoder source.
    // Mapping, availability, a connected service or PAUSED state are insufficient.
    public static bool ActiveReplacementStatusIsGreen(bool bridgeEnabled, bool heartbeatFresh,
        string? source, string? playbackState, string? nativeStatus, string? presenceStatus) =>
        heartbeatFresh && source == "ACTIVE_REPLACEMENT" && playbackState == "PLAYING" &&
        PlaybackSourceEvidence.Verified(bridgeEnabled, nativeStatus, presenceStatus);

    // An empty track at initial connection is guidance, not a Next transition.
    public static bool ShouldShowIdleTrackPrompt(bool enabled, bool heartbeatFresh,
        bool playerUnavailable, bool connecting, bool seenTrack,
        string? playbackState, TimeSpan noTrackFor) =>
        enabled && heartbeatFresh && !playerUnavailable && !connecting &&
        !seenTrack && playbackState == "UNKNOWN" &&
        noTrackFor >= TimeSpan.FromMilliseconds(2500);

    // An approved available version and connected pause are positive statuses,
    // but "playing CELIKOM" still requires strict current-decoder proof.
    public static bool StatusIsGreen(string? visibleText,
        bool enabled, bool heartbeatFresh, bool playerUnavailable,
        bool versionApproved, bool replacementVerified) =>
        ServiceConnected(enabled, heartbeatFresh, playerUnavailable) &&
        ((visibleText == ActiveVersionMessage && replacementVerified) ||
         (visibleText == VersionAvailableMessage && versionApproved) ||
         visibleText == "Пауза");

    // W169: bridge/renderer briefly lose track identity while moving between
    // songs. Keep the last displayed real title for a bounded 2.5-second
    // handoff only while the native player is still alive. Do not hide real
    // Stop, app loss, VPN recovery or a failed native host.
    public static bool HoldPreviousTrackDuringGap(bool enabled, bool heartbeatFresh,
        bool playerUnavailable, bool networkRecovering, bool connecting,
        bool previouslyHadTrack, string? previousTitle,
        string? nativeStatus, string? playbackState, TimeSpan elapsed) =>
        enabled && heartbeatFresh && !playerUnavailable &&
        !networkRecovering && !connecting && previouslyHadTrack &&
        !string.IsNullOrWhiteSpace(previousTitle) &&
        nativeStatus is "RESOLVING" or "NATIVE_CONNECTED" or
            "NATIVE_MAPPING_ACCEPTED" or "NATIVE_SOURCE_VERIFIED" or
            "NATIVE_ORIGINAL_SOURCE_VERIFIED" or "NATIVE_RECOVERING" &&
        playbackState is "UNKNOWN" or "PLAYING" or "PAUSED" &&
        elapsed >= TimeSpan.Zero &&
        elapsed <= TimeSpan.FromMilliseconds(2500);

    public static string NetworkRecoveryPlaybackMessage(string? playbackState) => playbackState switch
    {
        "PLAYING" => "Музыка продолжает играть.",
        "PAUSED" => "Музыка на паузе.",
        "STOPPED" => "Воспроизведение остановлено.",
        _ => "Проверяем состояние воспроизведения…"
    };

    public static string TrackPlaceholder(bool bridgeEnabled, bool heartbeatFresh,
        string? playbackState, bool recoveryPending, bool connectionPending, bool signedIn,
        bool playerUnavailable = false)
    {
        if (playerUnavailable) return "Подключитесь к Яндекс Музыке";
        if (!bridgeEnabled)
        {
            if (recoveryPending) return NetworkRecoveryPlaybackMessage(playbackState);
            if (connectionPending) return ConnectingMessage;
            return signedIn
                ? "Подмена выключена. Нажмите «Старт», чтобы подключиться к Яндекс Музыке"
                : "Войдите в аккаунт, чтобы подключить CELIKOM.";
        }

        if (connectionPending) return ConnectingMessage;
        if (!heartbeatFresh) return StaleHeartbeatMessage(playbackState);
        return playbackState switch
        {
            "PLAYING" => "Играет. Данные текущего трека недоступны.",
            "PAUSED" => "Пауза",
            "STOPPED" => "Воспроизведение остановлено",
            _ => ""
        };
    }
}

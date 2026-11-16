namespace Celikom.Companion;

public static class CompactPlaybackPresentation
{
    public const string VersionAvailableMessage = "Версия CELIKOM доступна";
    public const string ActiveVersionMessage = "Играет полная версия CELIKOM";
    public const string ServiceEnabledMessage = "Сервис включён";

    public const string ConnectingMessage = "Подождите, идёт подключение к приложению Яндекса.";
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
    // current track is using a CELIKOM decoder source.
    public static bool ServiceConnected(bool bridgeEnabled, bool heartbeatFresh,
        bool playerUnavailable, bool networkRecoveryPending) =>
        bridgeEnabled && heartbeatFresh && !playerUnavailable && !networkRecoveryPending;

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
        if (!heartbeatFresh) return "Ожидаем подключения Яндекс Музыки…";
        return playbackState switch
        {
            "PLAYING" => "Играет. Данные текущего трека недоступны.",
            "PAUSED" => "Пауза",
            "STOPPED" => "Воспроизведение остановлено",
            _ => "Ожидаем воспроизведения в Яндекс Музыке…"
        };
    }
}

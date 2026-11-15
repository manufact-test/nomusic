namespace Celikom.Companion;

public static class CompactPlaybackPresentation
{
    public const string ConnectingMessage = "Подключаем CELIKOM к текущему плееру…";
    public const string NetworkRecoveryMessage =
        "Проверяем соединение в фоне. Текущий звук не переключаем.";
    public const string StartupTimeoutMessage =
        "Не удалось получить данные текущего плеера. Проверь окно Яндекс.Музыки и подключение CELIKOM.";

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

    public static string TrackPlaceholder(bool bridgeEnabled, bool heartbeatFresh,
        string? playbackState, bool recoveryPending, bool connectionPending, bool signedIn,
        bool playerUnavailable = false)
    {
        if (playerUnavailable) return "Подключитесь к Яндекс Музыке";
        if (!bridgeEnabled)
        {
            if (recoveryPending) return "Данные текущего трека временно недоступны…";
            if (connectionPending) return ConnectingMessage;
            return signedIn
                ? "Подмена выключена. Нажми «Старт», чтобы подключить текущий плеер."
                : "Войди в аккаунт, чтобы подключить CELIKOM.";
        }

        if (!heartbeatFresh) return "Ожидаем данные текущего плеера…";
        return playbackState switch
        {
            "PLAYING" => "Играет. Данные текущего трека недоступны.",
            "PAUSED" => "Пауза",
            "STOPPED" => "Воспроизведение остановлено",
            _ => "Ожидаем текущий трек"
        };
    }
}

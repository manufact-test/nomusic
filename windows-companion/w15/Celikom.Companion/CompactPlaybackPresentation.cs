namespace Celikom.Companion;

public static class CompactPlaybackPresentation
{
    public const string ConnectingMessage = "Подключаем CELIKOM к текущему плееру…";
    public const string StartupTimeoutMessage =
        "Не удалось получить данные текущего плеера. Проверь окно Яндекс.Музыки и подключение CELIKOM.";

    public static bool StartupComplete(bool bridgeEnabled, bool heartbeatFresh) =>
        bridgeEnabled && heartbeatFresh;

    public static string TrackPlaceholder(bool bridgeEnabled, bool heartbeatFresh,
        string? playbackState, bool recoveryPending, bool connectionPending, bool signedIn,
        bool playerUnavailable = false)
    {
        if (!bridgeEnabled)
        {
            if (recoveryPending) return "Восстанавливаем связь с текущим плеером…";
            if (connectionPending) return ConnectingMessage;
            return signedIn
                ? "Подмена выключена. Нажми «Старт», чтобы подключить текущий плеер."
                : "Войди в аккаунт, чтобы подключить CELIKOM.";
        }

        if (playerUnavailable) return "Подключитесь к Яндекс Музыке";
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

using Celikom.NativeInstaller;

namespace Celikom.Companion;

/// <summary>
/// End-user diagnostics, deliberately separate from owner technical logs.
/// Never claim an alternative is audible merely because a URL was accepted.
/// </summary>
public static class UserFacingPlaybackHealth
{
    public enum Severity { Neutral, Good, Warning, Error }
    public sealed record Health(Severity Level, string Message);

    public static Health Host(NativeInstallState native, YandexHostResult? vendor,
        bool moduleMatches)
    {
        if (native == NativeInstallState.Active)
            return moduleMatches
                ? new(Severity.Good, "Яндекс.Музыка подключена.")
                : new(Severity.Neutral, "Нажми «Старт», чтобы обновить модуль CELIKOM.");
        if (native == NativeInstallState.VerifiedVendorUpdate)
            return new(Severity.Warning,
                "Яндекс обновился. Нажми «Старт», чтобы безопасно переподключиться.");
        if (native == NativeInstallState.Interrupted)
            return new(Severity.Error, "Подключение прервано. Требуется восстановление.");
        if (native == NativeInstallState.Changed)
            return vendor?.Status == YandexHostStatus.UnsupportedVersion
                ? new(Severity.Error,
                    "Версия Яндекса пока не поддерживается. Дождись проверки совместимости CELIKOM.")
                : new(Severity.Error,
                    "Файлы Яндекса изменились. Подключение заблокировано для безопасности.");
        if (vendor?.Status == YandexHostStatus.UnsupportedVersion)
            return new(Severity.Error,
                "Версия Яндекса пока не поддерживается. Дождись проверки совместимости CELIKOM.");
        if (vendor?.Status is YandexHostStatus.UntrustedExecutable or YandexHostStatus.UnknownAsar)
            return new(Severity.Error, "Файлы Яндекса не прошли проверку безопасности.");
        if (vendor?.Status is YandexHostStatus.NotInstalled or YandexHostStatus.IncompleteInstallation)
            return new(Severity.Error, "Яндекс.Музыка не найдена или установлена неполностью.");
        return new(Severity.Neutral, "Яндекс ещё не подключён.");
    }

    // W141: this is the current-player view, separate from legacy native
    // transition health. Silence, cached mapping and network bytes alone never
    // prove either replacement or original audio.
    public static Health CurrentTrack(string? nativeStatus, bool enabled,
        string? presence, string? source, string? playbackState)
    {
        if (!enabled) return new(Severity.Neutral, "");
        if (nativeStatus == "HOST_ERROR")
            return new(Severity.Error, "Не удалось подключить модуль Яндекса.");
        if (playbackState == "PAUSED")
            return new(Severity.Neutral, "Пауза.");
        if (playbackState == "STOPPED")
            return new(Severity.Neutral, "Воспроизведение остановлено.");
        if (playbackState == "PLAYING")
        {
            if (source == "ACTIVE_REPLACEMENT" &&
                nativeStatus == "NATIVE_SOURCE_VERIFIED")
                return new(Severity.Good, "Подмена активна · версия CELIKOM");
            if (source == "ORIGINAL" && nativeStatus == "NATIVE_ORIGINAL_SOURCE_VERIFIED")
                return new(Severity.Neutral, presence == "approved"
                    ? "Играет оригинал. Версия CELIKOM доступна."
                    : "Играет оригинал.");
            return new(Severity.Neutral, "Источник текущего трека не подтверждён.");
        }
        if (nativeStatus == "NATIVE_SOURCE_FAILED")
            return new(Severity.Error, "Не удалось подтвердить источник трека.");
        return new(Severity.Neutral, "Ожидаем данные текущего плеера…");
    }

    // Only explicitly observed failures may become customer-facing errors.
    // An unchanged native status is NOT evidence of disconnection: the host
    // sends heartbeats on transitions, not on every poll of a healthy track.
    public static Health Track(string? nativeStatus, bool serviceEnabled,
        string? versionPresence)
    {
        if (!serviceEnabled) return new(Severity.Neutral, "");
        if (nativeStatus == "NATIVE_SOURCE_FAILED")
            return new(Severity.Error, "Подмена не подтвердилась. Источник текущего трека неизвестен.");
        if (nativeStatus == "HOST_ERROR")
            return new(Severity.Error, "Не удалось подключить модуль Яндекса.");
        if (nativeStatus == "NATIVE_ORIGINAL_SOURCE_VERIFIED" && versionPresence == "approved")
            return new(Severity.Neutral, "Оригинальный источник подтверждён. Версия CELIKOM доступна.");
        // RESOLVING, NATIVE_RECOVERING, UNAVAILABLE, accepted mapping, and
        // silence in a steady song are normal/transient. Keep the UI quiet;
        // retain raw status in local diagnostics for investigation.
        return new(Severity.Neutral, "");
    }
}

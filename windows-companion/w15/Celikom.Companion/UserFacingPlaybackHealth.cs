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
                : new(Severity.Error, "Модуль CELIKOM устарел. Нажми «Обновить модуль».");
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

    // Only explicitly observed failures may become customer-facing errors.
    // An unchanged native status is NOT evidence of disconnection: the host
    // sends heartbeats on transitions, not on every poll of a healthy track.
    public static Health Track(string? nativeStatus, bool serviceEnabled,
        string? versionPresence)
    {
        if (!serviceEnabled) return new(Severity.Neutral, "");
        if (nativeStatus == "NATIVE_SOURCE_FAILED")
            return new(Severity.Error, "Подмена не загрузилась. Играет оригинал.");
        if (nativeStatus == "HOST_ERROR")
            return new(Severity.Error, "Не удалось подключить модуль Яндекса.");
        if (nativeStatus == "ORIGINAL" && versionPresence == "approved")
            return new(Severity.Neutral, "Сейчас играет оригинал. Версия CELIKOM доступна.");
        // RESOLVING, NATIVE_RECOVERING, UNAVAILABLE, accepted mapping, and
        // silence in a steady song are normal/transient. Keep the UI quiet;
        // retain raw status in local diagnostics for investigation.
        return new(Severity.Neutral, "");
    }
}

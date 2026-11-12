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

    public static Health Track(string? nativeStatus, bool serviceEnabled,
        string? versionPresence, bool staleHeartbeat = false)
    {
        if (!serviceEnabled) return new(Severity.Neutral, "Подмена выключена.");
        if (staleHeartbeat)
            return new(Severity.Error, "Нет ответа от модуля Яндекса. Проверь соединение.");
        if (nativeStatus == "NATIVE_SOURCE_FAILED")
            return new(Severity.Error,
                "Не удалось загрузить подмену этой песни. Звучание не подтверждено.");
        if (nativeStatus == "HOST_ERROR")
            return new(Severity.Error, "Ошибка подключения к модулю Яндекса.");
        if (nativeStatus == "NATIVE_RECOVERING")
            return new(Severity.Warning, "Восстанавливаем источник текущей песни…");
        if (nativeStatus == "RESOLVING")
            return new(Severity.Warning, "Ищем одобренную версию этой песни…");
        if (nativeStatus == "NATIVE_MAPPING_ACCEPTED" || nativeStatus == "SDK_MAPPING_ACCEPTED")
            return new(Severity.Warning,
                "Подмена передана проигрывателю. Фактический звук ещё не подтверждён.");
        if (nativeStatus == "ORIGINAL")
            return versionPresence == "approved"
                ? new(Severity.Warning, "Версия CELIKOM есть, но сейчас играет оригинал.")
                : new(Severity.Neutral, "Для этой песни играет оригинал.");
        if (nativeStatus == "NATIVE_CONNECTED")
            return new(Severity.Neutral, "Подключено. Ожидаем композицию.");
        if (nativeStatus == "UNAVAILABLE")
            return new(Severity.Warning, "Нет данных о воспроизведении. Ждём Яндекс…");
        return new(Severity.Neutral, "Ожидаем текущую песню Яндекса.");
    }
}

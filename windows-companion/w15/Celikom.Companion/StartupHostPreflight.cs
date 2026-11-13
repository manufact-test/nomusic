using Celikom.NativeInstaller;

namespace Celikom.Companion;

/// <summary>
/// Start is allowed to use the already verified native integration, or must
/// wait for a fresh official-Yandex preflight before offering a first install.
/// "Not yet inspected" must never be reported as "unsupported version".
/// </summary>
public static class StartupHostPreflight
{
    public static string? BlockReason(NativeInstallState state, YandexHostResult? report)
    {
        if (state == NativeInstallState.Active) return null;
        if (state == NativeInstallState.Interrupted)
            return "Предыдущее подключение Яндекс.Музыки прервано. Требуется восстановление.";
        if (state == NativeInstallState.Changed)
            return report?.Status == YandexHostStatus.UnsupportedVersion
                ? "Яндекс.Музыка обновилась. Новая версия пока проходит проверку CELIKOM. Вход и резервные копии сохранены."
                : "Файлы Яндекс.Музыки изменились. Подключение заблокировано для безопасности.";
        return report?.Status switch
        {
            YandexHostStatus.OfficialBaselineVerified => null,
            YandexHostStatus.UnsupportedVersion =>
                "Установленная версия Яндекс.Музыки пока не поддерживается.",
            YandexHostStatus.NotInstalled =>
                "Яндекс.Музыка не найдена. Установи официальное приложение.",
            YandexHostStatus.IncompleteInstallation =>
                "Установка Яндекс.Музыки неполная. Проверь приложение.",
            YandexHostStatus.UntrustedExecutable or YandexHostStatus.UnknownAsar =>
                "Файлы Яндекс.Музыки не совпадают с проверенной версией. Подключение заблокировано.",
            YandexHostStatus.InspectionUnavailable =>
                "Не удалось проверить файлы Яндекс.Музыки. Повтори «Старт».",
            _ => "Проверка Яндекс.Музыки ещё не завершена. Повтори «Старт»."
        };
    }
}

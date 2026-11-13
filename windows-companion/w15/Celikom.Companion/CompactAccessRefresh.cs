namespace Celikom.Companion;

/// <summary>
/// Keep a confirmed entitlement label visible while a read-only polling request
/// is in flight for the same signed-in installation. This is presentation only:
/// every server response still controls the real playback grant and revocation.
/// </summary>
public static class CompactAccessRefresh
{
    public const string Checking = "Проверяем доступ…";

    public static bool SameAccount(string? previousInstallation, string? previousEmail,
        string? installation, string? email) =>
        !string.IsNullOrWhiteSpace(previousInstallation) &&
        !string.IsNullOrWhiteSpace(previousEmail) &&
        string.Equals(previousInstallation, installation, StringComparison.Ordinal) &&
        string.Equals(previousEmail, email, StringComparison.OrdinalIgnoreCase);

    public static string WhileChecking(string currentText, string? previousInstallation,
        string? previousEmail, string? installation, string? email) =>
        SameAccount(previousInstallation, previousEmail, installation, email) &&
        !string.IsNullOrWhiteSpace(currentText)
            ? currentText
            : Checking;

    public static bool NeedsLabelChange(string? currentText, string? nextText) =>
        !string.Equals(currentText, nextText, StringComparison.Ordinal);
}

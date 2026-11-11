namespace Celikom.Companion;

/// <summary>
/// A previously verified staff-only diagnostics button can remain visible
/// across temporary API transport failures. It still MUST revalidate online
/// before reading/copying/exporting a single byte of diagnostics.
/// </summary>
public static class DiagnosticsAccessRecovery
{
    public static bool KeepButtonOnFailure(
        bool previouslyAllowed, bool loggedIn,
        string verifiedOrigin, string verifiedInstallation, string verifiedEmail,
        string currentOrigin, string currentInstallation, string currentEmail,
        Exception error) =>
        previouslyAllowed && loggedIn &&
        string.Equals(verifiedOrigin, currentOrigin, StringComparison.Ordinal) &&
        string.Equals(verifiedInstallation, currentInstallation, StringComparison.Ordinal) &&
        string.Equals(verifiedEmail, currentEmail, StringComparison.OrdinalIgnoreCase) &&
        EntitlementCheckRecovery.IsTransient(error);
}

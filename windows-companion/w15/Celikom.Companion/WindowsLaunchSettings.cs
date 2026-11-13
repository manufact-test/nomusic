using System.Security.Cryptography;
using System.Text;
using Microsoft.Win32;

namespace Celikom.Companion;

/// <summary>
/// HKCU-only Windows login startup; no admin rights, passwords, tokens or
/// automatic server entitlement grants are stored here.
/// RunAtLogin is opt-in; a remembered Start is NOT an authorization to play.
/// </summary>
public static class WindowsLaunchSettings
{
    private const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
    private const string SettingsKey = @"Software\CELIKOM\Windows";
    private const string RunName = "CELIKOM";

    public static string BuildRunCommand(string executablePath) =>
        "\"" + executablePath.Replace("\"", "") + "\" --background";

    public static bool IsRunAtLoginEnabled(string executablePath)
    {
        if (!OperatingSystem.IsWindows()) return false;
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RunKey);
            return string.Equals(key?.GetValue(RunName) as string,
                BuildRunCommand(executablePath), StringComparison.OrdinalIgnoreCase);
        }
        catch (UnauthorizedAccessException) { return false; }
        catch (IOException) { return false; }
    }

    public static bool TrySetRunAtLogin(string executablePath, bool enable)
    {
        if (!OperatingSystem.IsWindows()) return false;
        try
        {
            using var key = Registry.CurrentUser.CreateSubKey(RunKey, writable: true);
            if (key is null) return false;
            if (enable)
                key.SetValue(RunName, BuildRunCommand(executablePath), RegistryValueKind.String);
            else
                key.DeleteValue(RunName, throwOnMissingValue: false);
            return IsRunAtLoginEnabled(executablePath) == enable;
        }
        catch (UnauthorizedAccessException) { return false; }
        catch (IOException) { return false; }
        catch (System.Security.SecurityException) { return false; }
    }

    private static string IdentityFingerprint(string installationId, string email)
    {
        // Hash prevents account email from being written to Windows autorun
        // preferences; this is only an identity guard, never an auth token.
        var bytes = Encoding.UTF8.GetBytes(installationId + "\n" +
            email.Trim().ToLowerInvariant());
        return Convert.ToHexString(SHA256.HashData(bytes));
    }

    public static bool ShouldResume(bool autostartEnabled, bool desiredPlayback,
        string? storedFingerprint, string installationId, string email) =>
        autostartEnabled && desiredPlayback &&
        !string.IsNullOrWhiteSpace(storedFingerprint) &&
        !string.IsNullOrWhiteSpace(installationId) &&
        !string.IsNullOrWhiteSpace(email) &&
        string.Equals(storedFingerprint, IdentityFingerprint(installationId, email),
            StringComparison.Ordinal);

    public static void RememberPlayback(SecretRecord account, bool enabled)
    {
        if (!OperatingSystem.IsWindows()) return;
        try
        {
            using var key = Registry.CurrentUser.CreateSubKey(SettingsKey, writable: true);
            if (key is null) return;
            key.SetValue("PlaybackWanted", enabled ? 1 : 0, RegistryValueKind.DWord);
            if (enabled && !string.IsNullOrWhiteSpace(account.Email))
                key.SetValue("AccountFingerprint",
                    IdentityFingerprint(account.InstallationId, account.Email),
                    RegistryValueKind.String);
            else
                key.DeleteValue("AccountFingerprint", throwOnMissingValue: false);
        }
        catch (UnauthorizedAccessException) { }
        catch (IOException) { }
        catch (System.Security.SecurityException) { }
    }

    public static bool MayResume(SecretRecord account, string executablePath)
    {
        if (!OperatingSystem.IsWindows() ||
            !IsRunAtLoginEnabled(executablePath)) return false;
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(SettingsKey);
            return ShouldResume(true,
                key?.GetValue("PlaybackWanted") is int value && value == 1,
                key?.GetValue("AccountFingerprint") as string,
                account.InstallationId, account.Email);
        }
        catch (UnauthorizedAccessException) { return false; }
        catch (IOException) { return false; }
    }

    // Helper for isolated tests; no registry changes required.
    public static string FingerprintForTest(string installationId, string email) =>
        IdentityFingerprint(installationId, email);
}

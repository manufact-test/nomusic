namespace Celikom.Companion.Core;

public sealed record YandexSnapshot(
    bool IsInstalled,
    bool IsRunning,
    string? ExecutablePath,
    string? FileVersion,
    bool HasAppAsar,
    string State,
    string Detail)
{
    public string SafeReport()
    {
        return string.Join(Environment.NewLine,
            "CELIKOM Companion / Windows discovery (read-only)",
            $"Windows: {Environment.OSVersion.Version}",
            $"Architecture: {System.Runtime.InteropServices.RuntimeInformation.OSArchitecture}",
            $"Yandex installed: {IsInstalled}",
            $"Yandex running: {IsRunning}",
            $"Yandex executable: {YandexProbe.RedactPersonalPath(ExecutablePath)}",
            $"EXE file version: {FileVersion ?? "unknown"}",
            $"Electron app.asar present: {HasAppAsar}",
            $"Probe state: {State}",
            "Integration status: not installed / not tested",
            "No Yandex or CELIKOM passwords, tokens or browser data are included.");
    }
}

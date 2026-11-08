namespace Celikom.Companion.Core;

/// <summary>
/// Deliberately contains only installation metadata and boolean compatibility hints.
/// No source content, account data, media links, personal paths or authentication.
/// </summary>
public sealed record AsarReport(
    string State,
    long SizeBytes,
    string? Sha256,
    string? PackageName,
    string? PackageVersion,
    string? MainEntry,
    bool MainEntryExists,
    int InspectedJsFiles,
    bool HasElectronWindowMarker,
    bool HasFileInfoMarker,
    bool HasWebpackMarker)
{
    public string SafeReport()
    {
        static string Allowed(string? text)
        {
            if (string.IsNullOrWhiteSpace(text) || text.Length > 120)
                return "unknown";
            return text.All(ch => char.IsAsciiLetterOrDigit(ch) || ch is '.' or '/' or '_' or '-')
                ? text : "unknown";
        }

        return string.Join(Environment.NewLine,
            "Read-only Electron ASAR inspection",
            $"ASAR state: {State}",
            $"ASAR size MiB: {SizeBytes / 1048576d:0.00}",
            $"ASAR SHA-256: {Sha256 ?? "unavailable"}",
            $"Package name: {Allowed(PackageName)}",
            $"Package version: {Allowed(PackageVersion)}",
            $"Main entry: {Allowed(MainEntry)}",
            $"Main entry found: {MainEntryExists}",
            $"JS files inspected: {InspectedJsFiles}",
            $"Electron BrowserWindow marker: {HasElectronWindowMarker}",
            $"File-info source marker: {HasFileInfoMarker}",
            $"Webpack marker: {HasWebpackMarker}",
            "Source hook compatibility: NOT YET VERIFIED",
            "No application files were changed; no audio or account data was read.",
            "Marker absence is NOT proof that a source hook is impossible.");
    }
}

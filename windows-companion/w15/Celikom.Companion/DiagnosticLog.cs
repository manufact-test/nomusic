using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace Celikom.Companion;

/// <summary>Owner-exportable, bounded and allowlisted diagnostics. Never records
/// credentials, audio URLs, emails, requests, paths or exception messages.</summary>
public static class DiagnosticLog
{
    private const long Limit = 384 * 1024;
    private const int RingLimit = 256;
    private static readonly object Gate = new();
    private static readonly Queue<string> Recent = new();
    private static readonly Regex Code = new(@"^[A-Z_]{3,48}$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant);
    private static readonly Regex Id = new(@"^[1-9][0-9]{0,17}$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant);
    private static readonly Regex SafeLine = new(
        @"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\|[A-Z_]{3,48}(\|track=[1-9][0-9]{0,17})?$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant);
    public static string DirectoryPath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "CELIKOM", "Windows");

    public static void Record(string code, string? trackId = null)
    {
        if (!Code.IsMatch(code)) return;
        var line = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ",
            CultureInfo.InvariantCulture) + "|" + code +
            (trackId is not null && Id.IsMatch(trackId) ? "|track=" + trackId : "");
        lock (Gate)
        {
            Recent.Enqueue(line);
            while (Recent.Count > RingLimit) Recent.Dequeue();
            try
            {
                Directory.CreateDirectory(DirectoryPath);
                var file = Path.Combine(DirectoryPath, "companion-events.log");
                if (File.Exists(file) && new FileInfo(file).Length >= Limit)
                {
                    if (File.Exists(file + ".1")) File.Delete(file + ".1");
                    File.Move(file, file + ".1");
                }
                using var stream = new FileStream(file, FileMode.Append, FileAccess.Write, FileShare.ReadWrite);
                var buffer = Encoding.UTF8.GetBytes(line + "\n");
                stream.Write(buffer);
            }
            catch (IOException) { /* An in-memory ring survives temporary file lock. */ }
            catch (UnauthorizedAccessException) { }
        }
    }

    /// <summary>Validate again when reading: even a tampered log cannot inject
    /// signed URLs, passwords, or arbitrary text into an owner export.</summary>
    public static bool IsSafeEntry(string? line) =>
        line is not null && line.Length <= 128 && SafeLine.IsMatch(line);

    public static string ExportText(string? yandexVersion, string integration,
        bool bridgeStarted, bool enabled, bool signedIn,
        string? nativeModuleVersion = null, bool? nativeMatchesApplication = null)
    {
        var text = new StringBuilder();
        text.AppendLine("CELIKOM WINDOWS OWNER DIAGNOSTICS — W48");
        text.AppendLine("GeneratedUTC=" + DateTimeOffset.UtcNow.ToString("O", CultureInfo.InvariantCulture));
        text.AppendLine("AppVersion=" + (typeof(DiagnosticLog).Assembly.GetName().Version?.ToString() ?? "unknown"));
        text.AppendLine("NativeModuleVersion=" +
            (nativeModuleVersion is not null && Regex.IsMatch(nativeModuleVersion, @"^[0-9.]{1,24}$")
                ? nativeModuleVersion : "unknown"));
        text.AppendLine("NativeModuleMatchesApp=" +
            (nativeMatchesApplication is null ? "unknown" : nativeMatchesApplication.Value ? "true" : "false"));
        text.AppendLine("CodeBaseline=W48_ACTUAL_PLAYER_ENGINE_DIAGNOSTICS");
        text.AppendLine("YandexVersion=" + (yandexVersion is not null &&
            Regex.IsMatch(yandexVersion, @"^[0-9.]{1,24}$") ? yandexVersion : "unknown"));
        text.AppendLine("NativeIntegration=" + (Code.IsMatch(integration) ? integration : "UNKNOWN"));
        text.AppendLine("BridgeStarted=" + bridgeStarted.ToString().ToLowerInvariant());
        text.AppendLine("Enabled=" + enabled.ToString().ToLowerInvariant());
        text.AppendLine("SignedIn=" + signedIn.ToString().ToLowerInvariant());
        text.AppendLine("AUDIO_PROBE_* is an independent 32-byte diagnostic GET from the Yandex renderer (CSP/CORS), NOT verified playback.");
        text.AppendLine("PLAYER_ENGINE_* and PLAYER_AUDIO_* are Electron webContents events; only PLAYER_AUDIO_AUDIBLE indicates webContents emitted sound, NOT confirmed replacement.");\n        text.AppendLine("MEDIA_* DOM events may remain NOT_OBSERVED for WebAudio. UI Play/Pause label changes are NOT monitored.");\n        text.AppendLine("AUDIO_URL_RESOURCE_UNATTRIBUTED can be the separate 32-byte probe; it is NOT evidence of player playback.");
        text.AppendLine("PNR: NOT_IMPLEMENTED_OR_NOT_IDENTIFIED.");
        text.AppendLine("Events: UTC | allowlisted code | optional numeric track id. No raw request URLs or error messages.");
        text.AppendLine("--- EVENTS ---");
        var count = 0;
        lock (Gate)
        {
            foreach (var name in new[] {
                "companion-events.log.1", "companion-events.log",
                "native-events.log.1", "native-events.log" })
            {
                var file = Path.Combine(DirectoryPath, name);
                try
                {
                    if (!File.Exists(file)) continue;
                    using var stream = new FileStream(file, FileMode.Open, FileAccess.Read,
                        FileShare.ReadWrite | FileShare.Delete);
                    using var reader = new StreamReader(stream, Encoding.UTF8);
                    for (var i = 0; i < 20000 && reader.ReadLine() is { } line; i++)
                    {
                        if (!IsSafeEntry(line)) continue;
                        text.AppendLine(line);
                        count++;
                    }
                }
                catch (IOException) { text.AppendLine("LOG_FILE_UNAVAILABLE"); }
                catch (UnauthorizedAccessException) { text.AppendLine("LOG_FILE_UNAVAILABLE"); }
            }
            if (count == 0)
                foreach (var line in Recent)
                    if (IsSafeEntry(line)) text.AppendLine(line);
        }
        if (count == 0) text.AppendLine("NO_PERSISTENT_EVENTS_AVAILABLE");
        return text.ToString();
    }
}

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
    // High-frequency native status chatter can rotate the main event log
    // before anyone opens the owner diagnostics UI. Preserve only allowlisted
    // incident transitions independently, bounded to 2 x 512 KiB on disk.
    private const long IncidentLogLimit = 512 * 1024;
    private const string IncidentFile = "incident-events.log";
    private static readonly object Gate = new();
    private static readonly Queue<string> Recent = new();
    private static readonly Regex Code = new(@"^[A-Z0-9_]{3,48}$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant);
    private static readonly Regex Id = new(@"^[1-9][0-9]{0,17}$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant);
    private static readonly Regex SafeLine = new(
        @"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\|[A-Z0-9_]{3,48}(\|(?:track|resource_id)=[1-9][0-9]{0,17})?$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant);
    public static string DirectoryPath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "CELIKOM", "Windows");

    public static void Record(string code, string? trackId = null,
        string? diagnosticDirectory = null)
    {
        if (!Code.IsMatch(code)) return;
        var line = DateTimeOffset.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ",
            CultureInfo.InvariantCulture) + "|" + code +
            (trackId is not null && Id.IsMatch(trackId) ? "|track=" + trackId : "");
        lock (Gate)
        {
            Recent.Enqueue(line);
            while (Recent.Count > RingLimit) Recent.Dequeue();
            var directory = diagnosticDirectory ?? DirectoryPath;
            try { AppendBounded(directory, "companion-events.log", Limit, line); }
            catch (IOException) { /* An in-memory ring survives temporary file lock. */ }
            catch (UnauthorizedAccessException) { }
            if (IsIncidentCode(code))
            {
                // Best effort, even if the busy main log cannot be written.
                try { AppendBounded(directory, IncidentFile, IncidentLogLimit, line); }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
        }
    }

    public static bool IsIncidentCode(string code) =>
        Code.IsMatch(code) &&
        ((code is "NATIVE_ELECTRON_EVENT_LOOP_STALL" or "NATIVE_ELECTRON_MEMORY_HIGH" or
             "PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING" or "PLAYER_CURRENT_NATIVE_VOLUME_DROP" or
             "PLAYER_CURRENT_SOURCE_LEFT_CELIKOM") ||
         code.StartsWith("ACTIVE_ENTITLEMENT_", StringComparison.Ordinal) ||
         code.StartsWith("START_ENTITLEMENT_", StringComparison.Ordinal) ||
         code.Contains("DISCONNECT", StringComparison.Ordinal) ||
         code.Contains("NETWORK", StringComparison.Ordinal) ||
         code.Contains("UNAVAILABLE", StringComparison.Ordinal) ||
         code.Contains("SUSPEND", StringComparison.Ordinal) ||
         code.Contains("RECOVER", StringComparison.Ordinal) ||
         code.Contains("FAILED", StringComparison.Ordinal) ||
         code.Contains("ERROR", StringComparison.Ordinal) ||
         code.Contains("REVOKED", StringComparison.Ordinal) ||
         code.Contains("DEFERRED", StringComparison.Ordinal));

    private static void AppendBounded(string directory, string fileName,
        long maxBytes, string line)
    {
        Directory.CreateDirectory(directory);
        var path = Path.Combine(directory, fileName);
        if (File.Exists(path) && new FileInfo(path).Length >= maxBytes)
        {
            if (File.Exists(path + ".1")) File.Delete(path + ".1");
            File.Move(path, path + ".1");
        }
        using var stream = new FileStream(path, FileMode.Append, FileAccess.Write, FileShare.ReadWrite);
        stream.Write(Encoding.UTF8.GetBytes(line + "\n"));
    }

    /// <summary>
    /// Durable allowlisted incident history, independent of high-frequency
    /// native polling. There are no URLs, mail addresses, bearer tokens, paths
    /// or arbitrary exception messages. Per-installation files are bounded.
    /// </summary>
    public static IReadOnlyList<string> ReadIncidentHistory(
        string? diagnosticDirectory = null, DateTimeOffset? asOf = null)
    {
        var directory = diagnosticDirectory ?? DirectoryPath;
        var now = asOf ?? DateTimeOffset.UtcNow;
        var cutoff = now.AddDays(-7);
        var entries = new List<string>();
        lock (Gate)
        {
            foreach (var name in new[] { IncidentFile + ".1", IncidentFile })
            {
                try
                {
                    var path = Path.Combine(directory, name);
                    if (!File.Exists(path)) continue;
                    using var stream = new FileStream(path, FileMode.Open, FileAccess.Read,
                        FileShare.ReadWrite | FileShare.Delete);
                    using var reader = new StreamReader(stream, Encoding.UTF8);
                    for (var i = 0; i < 15000 && reader.ReadLine() is { } line; i++)
                    {
                        if (!IsSafeEntry(line) || line.Length < 24 ||
                            !DateTimeOffset.TryParseExact(line[..24],
                                "yyyy-MM-ddTHH:mm:ss.fffZ",
                                CultureInfo.InvariantCulture,
                                DateTimeStyles.AssumeUniversal, out var timestamp) ||
                            timestamp < cutoff || timestamp > now.AddSeconds(5))
                            continue;
                        var separator = line.IndexOf('|');
                        var codeEnd = line.IndexOf('|', separator + 1);
                        var eventCode = codeEnd < 0 ? line[(separator + 1)..]
                            : line[(separator + 1)..codeEnd];
                        if (IsIncidentCode(eventCode)) entries.Add(line);
                    }
                }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
        }
        entries.Sort(StringComparer.Ordinal);
        return entries.TakeLast(1000).ToArray();
    }

    private static void ArchiveNativeIncidents(string directory, DateTimeOffset now)
    {
        // The Electron host writes its own bounded native-events.log rather than
        // calling the companion's DiagnosticLog.Record. Import only validated,
        // allowlisted native incident lines into the independent 7-day archive
        // when a support snapshot/export is requested.
        var existing = ReadIncidentHistory(directory, now).ToHashSet(StringComparer.Ordinal);
        var cutoff = now.AddDays(-7);
        lock (Gate)
        {
            foreach (var name in new[] { "native-events.log.1", "native-events.log" })
            {
                try
                {
                    var path = Path.Combine(directory, name);
                    if (!File.Exists(path)) continue;
                    using var stream = new FileStream(path, FileMode.Open, FileAccess.Read,
                        FileShare.ReadWrite | FileShare.Delete);
                    using var reader = new StreamReader(stream, Encoding.UTF8);
                    for (var i = 0; i < 20_000 && reader.ReadLine() is { } line; i++)
                    {
                        if (!IsSafeEntry(line) || line.Length < 24 ||
                            !DateTimeOffset.TryParseExact(line[..24], "yyyy-MM-ddTHH:mm:ss.fffZ",
                                CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal,
                                out var timestamp) ||
                            timestamp < cutoff || timestamp > now.AddSeconds(5))
                            continue;
                        var separator = line.IndexOf('|');
                        var codeEnd = line.IndexOf('|', separator + 1);
                        var code = codeEnd < 0 ? line[(separator + 1)..]
                            : line[(separator + 1)..codeEnd];
                        if (!IsIncidentCode(code) || !existing.Add(line)) continue;
                        try { AppendBounded(directory, IncidentFile, IncidentLogLimit, line); }
                        catch (IOException) { }
                        catch (UnauthorizedAccessException) { }
                    }
                }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
        }
    }

    /// <summary>Validate again when reading: even a tampered log cannot inject
    /// signed URLs, passwords, or arbitrary text into an owner export.</summary>
    public static bool IsSafeEntry(string? line) =>
        line is not null && line.Length <= 128 && SafeLine.IsMatch(line);


    /// <summary>
    /// Customer-initiated support snapshot: bounded data from the existing
    /// allowlisted logs. No raw URLs, emails, paths, token fields or messages.
    /// Does not grant the customer the developer-only export UI.
    /// </summary>
    public static object ExportSupportSnapshot(string? yandexVersion, string integration,
        bool bridgeStarted, bool enabled, string? nativeModuleVersion,
        bool? nativeMatchesApplication, string? lastTrackId,
        string? diagnosticDirectory = null)
    {
        var now = DateTimeOffset.UtcNow;
        var cutoff = now.AddMinutes(-15);
        var entries = new List<string>();
        var directory = diagnosticDirectory ?? DirectoryPath;
        ArchiveNativeIncidents(directory, now);
        // Scan the real last-15-minute allowlisted log, not ExportText's
        // owner-friendly last-1600-line display. A busy 180ms native poll can
        // otherwise erase earlier incidents before support filtering begins.
        static bool RecentSafe(string? line, DateTimeOffset after, DateTimeOffset until) =>
            IsSafeEntry(line) && line!.Length >= 24 &&
            DateTimeOffset.TryParseExact(line[..24], "yyyy-MM-ddTHH:mm:ss.fffZ",
                CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal, out var stamp) &&
            stamp >= after && stamp <= until;
        lock (Gate)
        {
            foreach (var name in new[] {
                "companion-events.log.1", "companion-events.log",
                "native-events.log.1", "native-events.log" })
            {
                var file = Path.Combine(directory, name);
                try
                {
                    if (!File.Exists(file)) continue;
                    using var stream = new FileStream(file, FileMode.Open, FileAccess.Read,
                        FileShare.ReadWrite | FileShare.Delete);
                    using var reader = new StreamReader(stream, Encoding.UTF8);
                    for (var i = 0; i < 20_000 && reader.ReadLine() is { } line; i++)
                        if (RecentSafe(line, cutoff, now.AddSeconds(5))) entries.Add(line);
                }
                catch (IOException) { /* Best effort; never block user support. */ }
                catch (UnauthorizedAccessException) { }
            }
            if (entries.Count == 0)
                foreach (var line in Recent)
                    if (RecentSafe(line, cutoff, now.AddSeconds(5))) entries.Add(line);
        }
        entries.Sort(StringComparer.Ordinal);
        // Local state polling runs several times per second. A simple last-64
        // slice would hide three earlier outage events behind hundreds of
        // NATIVE_STATE_RECEIVED/LOCAL_STATE_OK lines. Reserve room for the last
        // 24 incident transitions/current-player anomalies, and 40 contextual events.
        static bool IsPollingChatter(string code) => code is
            "NATIVE_STATE_RECEIVED" or "LOCAL_STATE_OK" or
            "RENDERER_STATE_DELIVERED" or "RENDERER_BRIDGE_STATE_SEEN";
        static bool IsIncident(string code) =>
            (code is "NATIVE_ELECTRON_EVENT_LOOP_STALL" or "NATIVE_ELECTRON_MEMORY_HIGH" or
                "PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING" or "PLAYER_CURRENT_NATIVE_VOLUME_DROP" or
                "PLAYER_CURRENT_SOURCE_LEFT_CELIKOM") ||
            code.StartsWith("ACTIVE_ENTITLEMENT_", StringComparison.Ordinal) ||
            code.Contains("ERROR", StringComparison.Ordinal) ||
            code.Contains("FAILED", StringComparison.Ordinal) ||
            code.Contains("FORBIDDEN", StringComparison.Ordinal) ||
            code.Contains("CORS", StringComparison.Ordinal) ||
            code.Contains("UNAVAILABLE", StringComparison.Ordinal) ||
            code.Contains("DISCONNECT", StringComparison.Ordinal) ||
            code.Contains("SUSPENDED", StringComparison.Ordinal);
        var parsedEvents = entries.Select(line =>
            {
                var parts = line.Split('|');
                var parsed = DateTimeOffset.TryParseExact(parts[0],
                    "yyyy-MM-ddTHH:mm:ss.fffZ", CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal, out var stamp);
                var age = parsed ? Math.Max(0, (int)(now - stamp).TotalSeconds) : 901;
                var identity = parts.Length == 3 ? parts[2].Split('=', 2) : [];
                return new {
                    ageSeconds = age,
                    code = parts[1],
                    trackId = identity.Length == 2 && identity[0] == "track" ? identity[1] : null,
                    resourceId = identity.Length == 2 && identity[0] == "resource_id" ? identity[1] : null
                };
            })
            .Where(e => e.ageSeconds <= 900)
            .ToArray();
        var incidentIndices = Enumerable.Range(0, parsedEvents.Length)
            .Where(i => IsIncident(parsedEvents[i].code))
            .TakeLast(24);
        var contextIndices = Enumerable.Range(0, parsedEvents.Length)
            .Where(i => !IsPollingChatter(parsedEvents[i].code))
            .TakeLast(40);
        var events = incidentIndices.Concat(contextIndices).Distinct()
            .OrderBy(i => i).Select(i => parsedEvents[i]).ToArray();
        static string Version(string? value) =>
            value is not null && Regex.IsMatch(value, @"^[0-9]{1,4}(\.[0-9]{1,4}){1,3}$")
                ? value : "unknown";
        return new {
            platform = "windows",
            appVersion = AppUpdateManager.RunningVersion.ToString(3),
            nativeModuleVersion = Version(nativeModuleVersion),
            yandexVersion = Version(yandexVersion),
            integration = Code.IsMatch(integration) ? integration : "UNKNOWN",
            nativeMatchesApplication,
            bridgeStarted,
            enabled,
            lastTrackId = Id.IsMatch(lastTrackId ?? "") ? lastTrackId : null,
            scopeSeconds = 900,
            events
        };
    }

    public static string ExportText(string? yandexVersion, string integration,
        bool bridgeStarted, bool enabled, bool signedIn,
        string? nativeModuleVersion = null, bool? nativeMatchesApplication = null,
        string? diagnosticDirectory = null)
    {
        // The optional directory permits isolated synthetic export fixtures in
        // contract tests. Real GUI callers always use the fixed user-owned path.
        var readDirectory = diagnosticDirectory ?? DirectoryPath;
        ArchiveNativeIncidents(readDirectory, DateTimeOffset.UtcNow);
        var text = new StringBuilder();
        text.AppendLine("CELIKOM WINDOWS OWNER DIAGNOSTICS — W54");
        text.AppendLine("GeneratedUTC=" + DateTimeOffset.UtcNow.ToString("O", CultureInfo.InvariantCulture));
        text.AppendLine("AppVersion=" + (typeof(DiagnosticLog).Assembly.GetName().Version?.ToString() ?? "unknown"));
        text.AppendLine("NativeModuleVersion=" +
            (nativeModuleVersion is not null && Regex.IsMatch(nativeModuleVersion, @"^[0-9.]{1,24}$")
                ? nativeModuleVersion : "unknown"));
        text.AppendLine("NativeModuleMatchesApp=" +
            (nativeMatchesApplication is null ? "unknown" : nativeMatchesApplication.Value ? "true" : "false"));
        text.AppendLine("CodeBaseline=W54_GAIN_VARIANT_AND_W53_PERFORMANCE_EXPORT_SAFE");
        text.AppendLine("YandexVersion=" + (yandexVersion is not null &&
            Regex.IsMatch(yandexVersion, @"^[0-9.]{1,24}$") ? yandexVersion : "unknown"));
        text.AppendLine("NativeIntegration=" + (Code.IsMatch(integration) ? integration : "UNKNOWN"));
        text.AppendLine("BridgeStarted=" + bridgeStarted.ToString().ToLowerInvariant());
        text.AppendLine("Enabled=" + enabled.ToString().ToLowerInvariant());
        text.AppendLine("SignedIn=" + signedIn.ToString().ToLowerInvariant());
        text.AppendLine("W53 makes NO separate audio probe requests. PLAYER_NET_* is passive CDP observation of Yandex network/preloading, not confirmation of audible playback.");
        text.AppendLine("PLAYER_ENGINE_* and PLAYER_AUDIO_* are Electron webContents events; only PLAYER_AUDIO_AUDIBLE indicates webContents emitted sound, NOT confirmed replacement.");
        text.AppendLine("MEDIA_* DOM events may remain NOT_OBSERVED for WebAudio. UI Play/Pause label changes are NOT monitored.");
        text.AppendLine("PLAYER_AUDIO_RESOURCE_TIMING_SEEN can be preloading. PLAYER_NET_HTTP_PARTIAL/FINISHED does NOT prove audio decoded.");
        text.AppendLine("PLAYER_URL_* compares exact signed origin/path/query in memory, never exports links, tokens, sid, HTTP bodies or keys.");
        text.AppendLine("PLAYER_403_* distinguishes native HTTP denial classes, not confirmed PHP origin unless a fixed PHP error enum is present.");
        text.AppendLine("PNR: NOT_IMPLEMENTED_OR_NOT_IDENTIFIED.");
        text.AppendLine("Events: UTC | allowlisted code | optional numeric track or CELIKOM resource_id. No raw request URLs or error messages.");
        text.AppendLine("--- EVENTS ---");
        // W48: past sessions masked the current failure. Export ONLY recent,
        // verified UTC events, merge native and GUI logs in time order, cap size.
        // No event is interpreted as confirmed replaced sound.
        var entries = new List<string>();
        var cutoff = DateTimeOffset.UtcNow.AddMinutes(-15);
        static bool RecentSafe(string line, DateTimeOffset after) =>
            IsSafeEntry(line) && line.Length >= 24 &&
            DateTimeOffset.TryParseExact(line[..24], "yyyy-MM-ddTHH:mm:ss.fffZ",
                CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal, out var stamp) &&
            stamp >= after;
        lock (Gate)
        {
            foreach (var name in new[] {
                "companion-events.log.1", "companion-events.log",
                "native-events.log.1", "native-events.log" })
            {
                var file = Path.Combine(readDirectory, name);
                try
                {
                    if (!File.Exists(file)) continue;
                    using var stream = new FileStream(file, FileMode.Open, FileAccess.Read,
                        FileShare.ReadWrite | FileShare.Delete);
                    using var reader = new StreamReader(stream, Encoding.UTF8);
                    for (var i = 0; i < 20000 && reader.ReadLine() is { } line; i++)
                        if (RecentSafe(line, cutoff)) entries.Add(line);
                }
                catch (IOException) { text.AppendLine("LOG_FILE_UNAVAILABLE"); }
                catch (UnauthorizedAccessException) { text.AppendLine("LOG_FILE_UNAVAILABLE"); }
            }
            if (entries.Count == 0)
                foreach (var line in Recent)
                    if (RecentSafe(line, cutoff)) entries.Add(line);
        }
        entries.Sort(StringComparer.Ordinal);
        text.AppendLine("DiagnosticScope=LAST_15_MINUTES");
        text.AppendLine("ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING");
        text.AppendLine("EngineFastPauseObserved=" +
            entries.Any(s => s.Contains("|PLAYER_ENGINE_FAST_PAUSE", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("PlayerAudibleEventObserved=" +
            entries.Any(s => s.Contains("|PLAYER_AUDIO_AUDIBLE", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("FastPauseTrackAttribution=NOT_AVAILABLE_WITHOUT_PLAYER_TRACK_ID");
        text.AppendLine("PlayerNetworkRequestObserved=" +
            entries.Any(s => s.Contains("|PLAYER_NET_REQUEST|resource_id=", StringComparison.Ordinal) ||
                s.Contains("|PLAYER_NET_REQUEST|track=", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("PlayerNetworkCorsFailureObserved=" +
            entries.Any(s => s.Contains("|PLAYER_NET_CORS_BLOCKED|resource_id=", StringComparison.Ordinal) ||
                s.Contains("|PLAYER_NET_CORS_BLOCKED|track=", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("NativeAudio403Observed=" +
            entries.Any(s => s.Contains("|PLAYER_NET_HTTP_FORBIDDEN|resource_id=", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("NativeMediaUrlExactMatchObserved=" +
            entries.Any(s => s.Contains("|PLAYER_URL_MATCH|resource_id=", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("NativeMediaUrlSignedFieldsIntactObserved=" +
            entries.Any(s => s.Contains("|PLAYER_URL_SIGNED_FIELDS_INTACT|resource_id=", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("NativeMediaUrlQueryMismatchObserved=" +
            entries.Any(s => s.Contains("|PLAYER_URL_QUERY_MISSING|resource_id=", StringComparison.Ordinal) ||
                s.Contains("|PLAYER_URL_QUERY_CHANGED|resource_id=", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("Native403PhpSignatureRejectionObserved=" +
            entries.Any(s => s.Contains("|PLAYER_403_PHP_INVALID_AUDIO_TOKEN|resource_id=", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("Native403PhpAccessDenialObserved=" +
            entries.Any(s => s.Contains("|PLAYER_403_PHP_ACCESS_DENIED|resource_id=", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("Native403HtmlResponseObserved=" +
            entries.Any(s => s.Contains("|PLAYER_403_HTML|resource_id=", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("DecoderErrorObserved=" +
            entries.Any(s => s.Contains("|PLAYER_CDP_PIPELINE_ERROR", StringComparison.Ordinal) ||
                s.Contains("|PLAYER_CDP_ERROR_MESSAGE", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("ElectronEventLoopStallObserved=" +
            entries.Any(s => s.Contains("|NATIVE_ELECTRON_EVENT_LOOP_STALL", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("ElectronMemoryHighObserved=" +
            entries.Any(s => s.Contains("|NATIVE_ELECTRON_MEMORY_HIGH", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("PlayerGainVariantUrlSelectedObserved=" +
            entries.Any(s => s.Contains("|PLAYER_CURRENT_GAIN_VARIANT_URL_SELECTED", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("PlayerGainVariantUrlMissingObserved=" +
            entries.Any(s => s.Contains("|PLAYER_CURRENT_GAIN_VARIANT_URL_MISSING", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("PlayerNativeVolumeDropObserved=" +
            entries.Any(s => s.Contains("|PLAYER_CURRENT_NATIVE_VOLUME_DROP", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        text.AppendLine("PlayerCelikomSourceLeftObserved=" +
            entries.Any(s => s.Contains("|PLAYER_CURRENT_SOURCE_LEFT_CELIKOM", StringComparison.Ordinal))
                .ToString().ToLowerInvariant());
        foreach (var line in entries.TakeLast(1600)) text.AppendLine(line);
        if (entries.Count == 0) text.AppendLine("NO_RECENT_EVENTS_AVAILABLE");
        text.AppendLine("--- PERSISTENT INCIDENT HISTORY (LAST 7 DAYS, MAX 1000) ---");
        var incidents = ReadIncidentHistory(readDirectory);
        foreach (var line in incidents) text.AppendLine(line);
        if (incidents.Count == 0) text.AppendLine("NO_STORED_INCIDENTS");
        return text.ToString();
    }
}

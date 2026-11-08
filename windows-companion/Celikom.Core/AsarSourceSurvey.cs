using System.Buffers.Binary;
using System.Globalization;
using System.Text;
using System.Text.Json;

namespace Celikom.Companion.Core;

/// <summary>
/// W3: static and bounded inventory of packaged ASAR source seams. Never injects,
/// patches, launches Yandex, reads account data or exports source/URLs/file names.
/// </summary>
public static class AsarSourceSurvey
{
    private const int MaxHeaderBytes = 16 * 1024 * 1024;
    private const int MaxEntries = 40000;
    private const int MaxSingleJs = 12 * 1024 * 1024;
    private const long MaxTotalJs = 96L * 1024 * 1024;
    private sealed record JsEntry(string Path, long Offset, int Size);

    public static AsarSourceSurveyReport Inspect(string asarPath, string? actualSha)
    {
        string identity = string.Equals(actualSha, AsarTopology.OwnerAsarSha256,
            StringComparison.OrdinalIgnoreCase) ? "MATCH_OWNER_W1" : "CHANGED_OR_UNVERIFIED";
        if (!File.Exists(asarPath)) return Empty("NOT_FOUND", identity);
        try
        {
            using var fs = new FileStream(asarPath, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete, 65536, FileOptions.SequentialScan);
            if (fs.Length < 20 || fs.Length > 1024L * 1024 * 1024)
                return Empty("INVALID_OR_OVERSIZE", identity);
            Span<byte> prefix = stackalloc byte[16];
            fs.ReadExactly(prefix);
            uint headerSize = BinaryPrimitives.ReadUInt32LittleEndian(prefix[12..16]);
            if (headerSize == 0 || headerSize > MaxHeaderBytes)
                return Empty("INVALID_HEADER", identity);
            long dataOffset = 16 + (((long)headerSize + 3) & ~3L);
            if (dataOffset >= fs.Length) return Empty("INVALID_HEADER", identity);
            byte[] header = new byte[(int)headerSize];
            fs.ReadExactly(header);
            using var json = JsonDocument.Parse(header, new JsonDocumentOptions { MaxDepth = 64 });
            var entries = new List<JsEntry>();
            int visited = 0;
            Collect(json.RootElement, "", entries, ref visited, 0);
            if (visited > MaxEntries) return Empty("ENTRY_LIMIT", identity);

            int inspected = 0, overLimit = 0;
            long inspectedBytes = 0;
            int method = 0, batch = 0, resource = 0, endpoints = 0, sourceAndWebpack = 0;
            int preloadAndSource = 0, rendererNamedAndSource = 0;
            int remoteBoot = 0, localBoot = 0, audioDescriptor = 0;

            // Inspect relevant packaged code first; never emit filenames or source text.
            foreach (var e in entries.OrderByDescending(x => Priority(x.Path))
                         .ThenBy(x => x.Path, StringComparer.Ordinal))
            {
                if (e.Size > MaxSingleJs || inspectedBytes + e.Size > MaxTotalJs)
                {
                    overLimit++;
                    continue;
                }
                long contentLength = fs.Length - dataOffset;
                if (e.Offset < 0 || e.Offset > contentLength ||
                    e.Size < 0 || e.Size > contentLength - e.Offset)
                    return Empty("INVALID_ENTRY", identity);
                fs.Position = dataOffset + e.Offset;
                var bytes = new byte[e.Size];
                fs.ReadExactly(bytes);
                string s = Encoding.UTF8.GetString(bytes);
                bool hasMethod = Has(s, "getFileInfo");
                bool hasBatch = Has(s, "getFileInfoBatch");
                bool hasResource = Has(s, "GetFileInfoResource");
                bool hasEndpoint = Has(s, "get-file-info") ||
                                   Has(s, "resources/v2/file-info");
                bool hasSource = hasMethod || hasResource || hasEndpoint;
                bool hasWebpack = Has(s, "webpackChunk") || Has(s, "__webpack_require__");
                bool hasLoadUrl = Has(s, "loadURL(");
                bool hasLoadFile = Has(s, "loadFile(");
                bool hasYandexHost = Has(s, "music.yandex.ru") || Has(s, "music.yandex.com");
                bool hasDescriptor = Has(s, "downloadInfo") && Has(s, "codec");
                if (hasMethod) method++;
                if (hasBatch) batch++;
                if (hasResource) resource++;
                if (hasEndpoint) endpoints++;
                if (hasSource && hasWebpack) sourceAndWebpack++;
                if (hasSource && e.Path.Contains("preload", StringComparison.OrdinalIgnoreCase))
                    preloadAndSource++;
                if (hasSource && e.Path.Contains("renderer", StringComparison.OrdinalIgnoreCase))
                    rendererNamedAndSource++;
                if (hasLoadUrl && hasYandexHost) remoteBoot++;
                if (hasLoadFile) localBoot++;
                if (hasDescriptor) audioDescriptor++;
                inspected++;
                inspectedBytes += e.Size;
            }
            return new AsarSourceSurveyReport("OK", identity, entries.Count, inspected,
                overLimit, method, batch, resource, endpoints, sourceAndWebpack,
                preloadAndSource, rendererNamedAndSource, remoteBoot, localBoot,
                audioDescriptor);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or
            JsonException or ArgumentException or NotSupportedException or OverflowException)
        {
            return Empty("READ_FAILED", identity);
        }
    }

    private static bool Has(string s, string marker) =>
        s.Contains(marker, StringComparison.OrdinalIgnoreCase);

    private static int Priority(string path)
    {
        int score = path.Equals("index.js", StringComparison.OrdinalIgnoreCase) ? 200 : 0;
        if (path.Contains("preload", StringComparison.OrdinalIgnoreCase)) score += 100;
        if (path.Contains("renderer", StringComparison.OrdinalIgnoreCase)) score += 100;
        if (path.Contains("main", StringComparison.OrdinalIgnoreCase)) score += 70;
        if (path.Contains("player", StringComparison.OrdinalIgnoreCase)) score += 35;
        if (path.Contains("node_modules/", StringComparison.OrdinalIgnoreCase)) score -= 100;
        return score;
    }

    private static void Collect(JsonElement node, string prefix, List<JsEntry> output,
        ref int visited, int depth)
    {
        if (depth > 24 || visited > MaxEntries || node.ValueKind != JsonValueKind.Object ||
            !node.TryGetProperty("files", out var files) ||
            files.ValueKind != JsonValueKind.Object) return;
        foreach (var p in files.EnumerateObject())
        {
            if (++visited > MaxEntries) return;
            string path = prefix.Length == 0 ? p.Name : prefix + "/" + p.Name;
            var v = p.Value;
            if (v.ValueKind != JsonValueKind.Object) continue;
            if (v.TryGetProperty("files", out _))
            {
                Collect(v, path, output, ref visited, depth + 1);
                continue;
            }
            if (!path.EndsWith(".js", StringComparison.OrdinalIgnoreCase)) continue;
            if (v.TryGetProperty("unpacked", out var unpacked) &&
                unpacked.ValueKind == JsonValueKind.True) continue;
            if (!v.TryGetProperty("size", out var s) || !s.TryGetInt32(out int size) ||
                !v.TryGetProperty("offset", out var o) ||
                o.ValueKind != JsonValueKind.String ||
                !long.TryParse(o.GetString(), NumberStyles.None,
                    CultureInfo.InvariantCulture, out long offset) ||
                size < 0 || offset < 0) continue;
            output.Add(new JsEntry(path, offset, size));
        }
    }

    private static AsarSourceSurveyReport Empty(string state, string identity) =>
        new(state, identity, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
}

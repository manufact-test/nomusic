using System.Buffers.Binary;
using System.Globalization;
using System.Text;
using System.Text.Json;

namespace Celikom.Companion.Core;

/// <summary>
/// Passive inventory of *packaged* JavaScript, never process injection or live traffic capture.
/// Boolean hints must not be mistaken for evidence that the authenticated player is hookable.
/// </summary>
public static class AsarTopology
{
    private const int MaxHeaderBytes = 16 * 1024 * 1024;
    private const int MaxEntries = 40000;
    private const int MaxJsBytesTotal = 28 * 1024 * 1024;
    private const int MaxJsBytesSingle = 6 * 1024 * 1024;
    private const int MaxJsFiles = 100;

    private sealed record Entry(string Path, long Offset, int Size);
    public const string OwnerAsarSha256 = "5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215";

    public static AsarTopologyReport Inspect(string asarPath, string? actualSha)
    {
        string match = string.Equals(actualSha, OwnerAsarSha256, StringComparison.OrdinalIgnoreCase)
            ? "MATCH_OWNER_W1" : "CHANGED_OR_UNVERIFIED";
        bool unpackedDir = Directory.Exists(asarPath + ".unpacked");
        if (!File.Exists(asarPath)) return Empty("NOT_FOUND", match, unpackedDir);

        try
        {
            using var fs = new FileStream(asarPath, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete, 65536, FileOptions.SequentialScan);
            if (fs.Length < 20 || fs.Length > 1024L * 1024 * 1024)
                return Empty("INVALID_OR_OVERSIZE", match, unpackedDir);
            Span<byte> first = stackalloc byte[16];
            fs.ReadExactly(first);
            uint headerBytes = BinaryPrimitives.ReadUInt32LittleEndian(first[12..16]);
            if (headerBytes == 0 || headerBytes > MaxHeaderBytes)
                return Empty("INVALID_HEADER", match, unpackedDir);
            long padded = ((long)headerBytes + 3) & ~3L;
            long dataStart = 16 + padded;
            if (dataStart >= fs.Length)
                return Empty("INVALID_HEADER", match, unpackedDir);
            var header = new byte[(int)headerBytes];
            fs.ReadExactly(header);
            using var root = JsonDocument.Parse(header, new JsonDocumentOptions { MaxDepth = 64 });
            var entries = new List<Entry>();
            int visits = 0;
            Collect(root.RootElement, "", entries, ref visits, 0);
            if (visits > MaxEntries)
                return Empty("ENTRY_LIMIT", match, unpackedDir);

            int jsTotal = entries.Count(x => x.Path.EndsWith(".js", StringComparison.OrdinalIgnoreCase));
            int htmlTotal = entries.Count(x => x.Path.EndsWith(".html", StringComparison.OrdinalIgnoreCase));
            int preloadTotal = entries.Count(x => x.Path.Contains("preload", StringComparison.OrdinalIgnoreCase)
                && x.Path.EndsWith(".js", StringComparison.OrdinalIgnoreCase));

            // Never print names, URL literals, source text, credentials or user-specific content.
            // Only boolean markers from bounded app-packaged files.
            var candidates = entries.Where(x => x.Path.EndsWith(".js", StringComparison.OrdinalIgnoreCase)
                 && x.Size > 0 && x.Size <= MaxJsBytesSingle)
                .OrderByDescending(x => Score(x.Path))
                .ThenBy(x => x.Path, StringComparer.Ordinal);

            bool loadUrl = false, loadFile = false, browserWindow = false, preload = false;
            bool remoteYandex = false, staticYandex = false, localRenderer = false;
            bool sourceApi = false, batchApi = false, webpack = false, autoUpdater = false;
            int count = 0, remaining = MaxJsBytesTotal;

            foreach (var entry in candidates)
            {
                if (count >= MaxJsFiles || remaining < entry.Size) continue;
                if (entry.Offset > fs.Length - dataStart
                    || entry.Size > fs.Length - dataStart - entry.Offset)
                    return Empty("INVALID_ENTRY", match, unpackedDir);

                var bytes = new byte[entry.Size];
                fs.Position = dataStart + entry.Offset;
                fs.ReadExactly(bytes);
                string js = Encoding.UTF8.GetString(bytes);
                browserWindow |= Has(js, "BrowserWindow");
                loadUrl |= Has(js, ".loadURL(") || Has(js, "loadURL(");
                loadFile |= Has(js, ".loadFile(") || Has(js, "loadFile(");
                preload |= Has(js, "preload:");
                remoteYandex |= Has(js, "music.yandex.ru") || Has(js, "music.yandex.com");
                staticYandex |= Has(js, "yastatic") || Has(js, "music-frontend-static");
                localRenderer |= Has(js, ".html") || Has(js, "file://") || Has(js, "app://");
                sourceApi |= Has(js, "getFileInfo") || Has(js, "get-file-info")
                    || Has(js, "GetFileInfoResource") || Has(js, "resources/v2/file-info");
                batchApi |= Has(js, "getFileInfoBatch") || Has(js, "get-file-info/batch");
                webpack |= Has(js, "webpackChunk") || Has(js, "__webpack_require__");
                autoUpdater |= Has(js, "autoUpdater") || Has(js, "electron-updater");
                count++;
                remaining -= entry.Size;
            }
            return new("OK", match, jsTotal, count, htmlTotal, preloadTotal, unpackedDir,
                browserWindow, loadUrl, loadFile, preload,
                remoteYandex, staticYandex, localRenderer, sourceApi, batchApi,
                webpack, autoUpdater, count < jsTotal);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or
            JsonException or ArgumentException or NotSupportedException or OverflowException)
        {
            return Empty("READ_FAILED", match, unpackedDir);
        }
    }

    private static bool Has(string text, string marker) =>
        text.Contains(marker, StringComparison.OrdinalIgnoreCase);

    private static int Score(string path)
    {
        int points = path.Equals("index.js", StringComparison.OrdinalIgnoreCase) ? 300 : 0;
        if (path.Contains("preload", StringComparison.OrdinalIgnoreCase)) points += 130;
        if (path.Contains("renderer", StringComparison.OrdinalIgnoreCase)) points += 110;
        if (path.Contains("main", StringComparison.OrdinalIgnoreCase)) points += 85;
        if (path.Contains("bootstrap", StringComparison.OrdinalIgnoreCase)) points += 65;
        if (path.Contains("index", StringComparison.OrdinalIgnoreCase)) points += 30;
        if (path.Contains("player", StringComparison.OrdinalIgnoreCase)) points += 20;
        if (path.Contains("node_modules/", StringComparison.OrdinalIgnoreCase)) points -= 120;
        return points;
    }

    private static AsarTopologyReport Empty(string state, string match, bool unpacked) =>
        new(state, match, 0, 0, 0, 0, unpacked, false, false, false, false,
            false, false, false, false, false, false, false, false);

    private static void Collect(JsonElement node, string prefix, List<Entry> entries,
        ref int visits, int depth)
    {
        if (depth > 24 || visits > MaxEntries) return;
        if (node.ValueKind != JsonValueKind.Object
            || !node.TryGetProperty("files", out var files)
            || files.ValueKind != JsonValueKind.Object) return;
        foreach (var property in files.EnumerateObject())
        {
            if (++visits > MaxEntries) return;
            var path = prefix.Length == 0 ? property.Name : prefix + "/" + property.Name;
            var value = property.Value;
            if (value.ValueKind != JsonValueKind.Object) continue;
            if (value.TryGetProperty("files", out _))
            {
                Collect(value, path, entries, ref visits, depth + 1);
                continue;
            }
            if (value.TryGetProperty("unpacked", out var unpacked)
                && unpacked.ValueKind == JsonValueKind.True) continue;
            if (!value.TryGetProperty("size", out var s) || !s.TryGetInt32(out int size)
                || !value.TryGetProperty("offset", out var o) || o.ValueKind != JsonValueKind.String
                || !long.TryParse(o.GetString(), NumberStyles.None, CultureInfo.InvariantCulture,
                    out long offset) || size < 0 || offset < 0) continue;
            entries.Add(new(path, offset, size));
        }
    }
}

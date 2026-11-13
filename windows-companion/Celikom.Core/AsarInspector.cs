using System.Buffers.Binary;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Celikom.Companion.Core;

/// <summary>
/// Inspects only the installed Electron archive header and a bounded selection of shipped JS.
/// Never writes to the official application and never exports any file contents.
/// </summary>
public static class AsarInspector
{
    private const int MaxHeaderBytes = 16 * 1024 * 1024;
    private const int MaxPackageBytes = 256 * 1024;
    private const int MaxJsBytesPerFile = 6 * 1024 * 1024;
    private const int MaxJsBytesTotal = 20 * 1024 * 1024;
    private const int MaxTreeEntries = 40000;

    private sealed record Entry(string Path, long Offset, int Size);

    public static AsarReport Inspect(string archivePath)
    {
        if (!File.Exists(archivePath))
            return Empty("NOT_FOUND");

        try
        {
            using var stream = new FileStream(archivePath, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete, 65536, FileOptions.SequentialScan);
            long fileSize = stream.Length;
            if (fileSize < 20)
                return Empty("INVALID_ASAR", fileSize);
            if (fileSize > 1024L * 1024 * 1024)
                return Empty("SIZE_LIMIT", fileSize);

            Span<byte> prelude = stackalloc byte[16];
            stream.ReadExactly(prelude);
            // Standard Electron ASAR is a pickle header, followed by UTF-8 JSON,
            // with the JSON byte count in the fourth little-endian uint32.
            uint jsonSize = BinaryPrimitives.ReadUInt32LittleEndian(prelude[12..16]);
            if (jsonSize is 0 or > MaxHeaderBytes)
                return Empty("INVALID_ASAR_HEADER", fileSize);
            long padded = ((long)jsonSize + 3) & ~3L;
            long contentStart = 16 + padded;
            if (contentStart >= fileSize)
                return Empty("INVALID_ASAR_HEADER", fileSize);

            byte[] jsonBytes = new byte[(int)jsonSize];
            stream.ReadExactly(jsonBytes);
            using var json = JsonDocument.Parse(jsonBytes, new JsonDocumentOptions
            {
                MaxDepth = 64
            });
            var archiveFiles = new List<Entry>();
            int visited = 0;
            Enumerate(json.RootElement, "", archiveFiles, ref visited, 0);
            if (visited > MaxTreeEntries)
                return Empty("HEADER_TOO_LARGE", fileSize);

            string? packageName = null, packageVersion = null, main = null;
            if (TryFind(archiveFiles, "package.json", out var packageEntry)
                && packageEntry.Size <= MaxPackageBytes)
            {
                using var pkg = JsonDocument.Parse(ReadEntry(stream, contentStart, fileSize, packageEntry));
                var root = pkg.RootElement;
                if (root.ValueKind == JsonValueKind.Object)
                {
                    packageName = ReadString(root, "name");
                    packageVersion = ReadString(root, "version");
                    main = ReadString(root, "main");
                }
            }

            main = NormalizeArchivePath(main);
            if (main is null && TryFind(archiveFiles, "index.js", out _))
                main = "index.js";
            bool mainPresent = main is not null && TryFind(archiveFiles, main, out _);

            // The whole-file SHA is useful for pinning an exact supported official build.
            // It is a file identity, NOT an integrity or authenticity attestation.
            stream.Seek(0, SeekOrigin.Begin);
            string sha256 = Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();

            // Source hooks may live in remote frontend bundles, not in app.asar.
            // These are therefore hints only, never affirmative compatibility claims.
            var candidateFiles = archiveFiles
                .Where(f => f.Path.EndsWith(".js", StringComparison.OrdinalIgnoreCase)
                            && f.Size > 0 && f.Size <= MaxJsBytesPerFile)
                .OrderByDescending(f => Score(f.Path, main))
                .ThenBy(f => f.Path, StringComparer.Ordinal)
                .ToList();

            bool foundWindow = false, foundFileInfo = false, foundWebpack = false;
            int inspected = 0, budget = MaxJsBytesTotal;

            foreach (var entry in candidateFiles)
            {
                if (budget < entry.Size || inspected >= 48)
                    continue;
                byte[] bytes = ReadEntry(stream, contentStart, fileSize, entry);
                string source = Encoding.UTF8.GetString(bytes);
                foundWindow |= source.Contains("BrowserWindow", StringComparison.Ordinal);
                foundFileInfo |= source.Contains("getFileInfo", StringComparison.Ordinal)
                    || source.Contains("get-file-info", StringComparison.Ordinal)
                    || source.Contains("GetFileInfoResource", StringComparison.Ordinal);
                foundWebpack |= source.Contains("webpackChunk", StringComparison.Ordinal)
                    || source.Contains("__webpack_require__", StringComparison.Ordinal);
                inspected++;
                budget -= entry.Size;
            }

            return new("OK", fileSize, sha256, packageName, packageVersion, main,
                mainPresent, inspected, foundWindow, foundFileInfo, foundWebpack);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException
            or JsonException or ArgumentException or NotSupportedException or OverflowException)
        {
            return Empty("READ_FAILED");
        }
    }

    private static AsarReport Empty(string state, long size = 0)
        => new(state, size, null, null, null, null, false, 0, false, false, false);

    private static string? ReadString(JsonElement root, string name)
    {
        if (!root.TryGetProperty(name, out var value) || value.ValueKind != JsonValueKind.String)
            return null;
        var text = value.GetString();
        return text is { Length: > 0 and <= 120 } ? text : null;
    }

    private static string? NormalizeArchivePath(string? value)
    {
        if (string.IsNullOrWhiteSpace(value) || value.Length > 120)
            return null;
        var path = value.Replace('\\', '/');
        while (path.StartsWith("./", StringComparison.Ordinal))
            path = path[2..];
        if (path.StartsWith("/", StringComparison.Ordinal)
            || path.Split('/').Any(x => x is "" or "." or ".."))
            return null;
        return path;
    }

    private static bool TryFind(List<Entry> entries, string path, out Entry result)
    {
        foreach (var entry in entries)
        {
            if (entry.Path.Equals(path, StringComparison.Ordinal))
            {
                result = entry;
                return true;
            }
        }
        result = new("", 0, 0);
        return false;
    }

    private static byte[] ReadEntry(FileStream stream, long start, long totalLength, Entry entry)
    {
        if (entry.Size < 0 || entry.Offset < 0
            || start + entry.Offset > totalLength
            || entry.Size > totalLength - (start + entry.Offset))
            throw new IOException("Out-of-bounds ASAR entry.");
        var bytes = new byte[entry.Size];
        stream.Seek(start + entry.Offset, SeekOrigin.Begin);
        stream.ReadExactly(bytes);
        return bytes;
    }

    private static int Score(string path, string? main)
    {
        int score = path.Equals(main, StringComparison.Ordinal) ? 100 : 0;
        if (path.Contains("preload", StringComparison.OrdinalIgnoreCase)) score += 25;
        if (path.Contains("renderer", StringComparison.OrdinalIgnoreCase)) score += 22;
        if (path.Contains("main", StringComparison.OrdinalIgnoreCase)) score += 15;
        if (path.Contains("index", StringComparison.OrdinalIgnoreCase)) score += 10;
        if (path.Contains("player", StringComparison.OrdinalIgnoreCase)) score += 8;
        if (path.Contains("bundle", StringComparison.OrdinalIgnoreCase)) score += 7;
        if (path.Contains("node_modules/", StringComparison.OrdinalIgnoreCase)) score -= 30;
        return score;
    }

    private static void Enumerate(JsonElement node, string path, List<Entry> result, ref int visited, int depth)
    {
        if (visited > MaxTreeEntries || depth > 24) return;
        if (node.ValueKind != JsonValueKind.Object) return;
        if (!node.TryGetProperty("files", out var files) || files.ValueKind != JsonValueKind.Object) return;

        foreach (var item in files.EnumerateObject())
        {
            visited++;
            if (visited > MaxTreeEntries) return;
            var currentPath = path.Length == 0 ? item.Name : path + "/" + item.Name;
            var entry = item.Value;
            if (entry.ValueKind != JsonValueKind.Object) continue;
            if (entry.TryGetProperty("files", out _))
            {
                Enumerate(entry, currentPath, result, ref visited, depth + 1);
                continue;
            }
            if (entry.TryGetProperty("unpacked", out var unpacked) &&
                unpacked.ValueKind == JsonValueKind.True) continue;
            if (!entry.TryGetProperty("size", out var sizeNode)
                || !sizeNode.TryGetInt32(out int size)
                || !entry.TryGetProperty("offset", out var offsetNode)
                || offsetNode.ValueKind != JsonValueKind.String
                || !long.TryParse(offsetNode.GetString(), NumberStyles.None,
                    CultureInfo.InvariantCulture, out long offset)
                || size < 0 || offset < 0) continue;
            result.Add(new(currentPath, offset, size));
        }
    }
}

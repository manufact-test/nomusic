using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Celikom.NativeInstaller;

/// <summary>
/// Builds two staged local host images, never writes to Yandex itself.
/// The already-verified W21 recovery transaction installs/rolls them back.
/// </summary>
public static class NativeAsarImageBuilder
{
    public sealed record Result(byte[] Executable, byte[] Asar,
        string OriginalExeSha256, string OriginalAsarSha256,
        string NewExeSha256, string NewAsarSha256, int EmbeddedHashesChanged);

    private sealed record Archive(JsonObject Tree, byte[] OriginalHeader, byte[] Data);

    public static Result Build(byte[] originalExe, byte[] originalAsar,
        byte[] hostModule, byte[] rendererScript,
        string expectedExeSha256, string expectedAsarSha256)
    {
        RequireHash(expectedExeSha256);
        RequireHash(expectedAsarSha256);
        if (Hash(originalExe) != expectedExeSha256 ||
            Hash(originalAsar) != expectedAsarSha256)
            throw new IOException("ORIGINAL_CHANGED_SINCE_PREFLIGHT");
        if (hostModule.Length is < 100 or > 120_000 ||
            rendererScript.Length is < 1_000 or > 1_000_000)
            throw new IOException("UNEXPECTED_INTEGRATION_PAYLOAD");

        var archive = Split(originalAsar);
        var rootFiles = archive.Tree["files"] as JsonObject ??
            throw new IOException("ASAR_NO_ROOT_FILES");
        if (rootFiles.ContainsKey("celikom"))
            throw new IOException("ALREADY_HAS_CELIKOM_MODULE");

        string main;
        try
        {
            var package = JsonNode.Parse(Encoding.UTF8.GetString(ReadEntry(archive, "package.json")));
            main = package?["main"]?.GetValue<string>()?.TrimStart('.', '/') ?? "";
        }
        catch (Exception e) when (e is JsonException or InvalidOperationException)
        {
            throw new IOException("NO_VALID_PACKAGE_MAIN", e);
        }
        if (main.Length is < 1 or > 200 ||
            !(main.EndsWith(".js", StringComparison.Ordinal) ||
              main.EndsWith(".cjs", StringComparison.Ordinal)))
            throw new IOException("UNSUPPORTED_MAIN_SCRIPT");
        var mainNode = Entry(archive.Tree, main);
        var mainOld = ReadEntry(archive, main);
        var snippet = Encoding.UTF8.GetBytes(
            "\n;try { require(require('node:path').join(require('electron').app.getAppPath(),'celikom','host.cjs')); } catch(_) {}\n");
        var mainNew = new byte[mainOld.Length + snippet.Length];
        mainOld.CopyTo(mainNew, 0);
        snippet.CopyTo(mainNew, mainOld.Length);
        var oldStart = EntryOffset(mainNode);
        var oldSize = mainOld.Length;
        var delta = snippet.Length;
        if (oldStart + oldSize > archive.Data.Length)
            throw new IOException("ASAR_MAIN_OFFSET_INVALID");

        var dataLength = checked(archive.Data.Length + delta + hostModule.Length + rendererScript.Length);
        var newData = new byte[dataLength];
        Buffer.BlockCopy(archive.Data, 0, newData, 0, oldStart);
        Buffer.BlockCopy(mainNew, 0, newData, oldStart, mainNew.Length);
        Buffer.BlockCopy(archive.Data, oldStart + oldSize,
            newData, oldStart + mainNew.Length, archive.Data.Length - oldStart - oldSize);
        var hostOffset = archive.Data.Length + delta;
        var rendererOffset = hostOffset + hostModule.Length;
        Buffer.BlockCopy(hostModule, 0, newData, hostOffset, hostModule.Length);
        Buffer.BlockCopy(rendererScript, 0, newData, rendererOffset, rendererScript.Length);

        WalkEntries(rootFiles, node =>
        {
            var offset = EntryOffset(node);
            if (offset + EntrySize(node) > archive.Data.Length)
                throw new IOException("ASAR_FILE_OUTSIDE_DATA");
            if (ReferenceEquals(node, mainNode))
            {
                node["size"] = mainNew.Length;
                node["integrity"] = Integrity(mainNew);
            }
            else if (offset > oldStart)
                node["offset"] = (offset + delta).ToString(System.Globalization.CultureInfo.InvariantCulture);
        });
        rootFiles["celikom"] = new JsonObject
        {
            ["files"] = new JsonObject
            {
                ["host.cjs"] = new JsonObject {
                    ["size"] = hostModule.Length,
                    ["offset"] = hostOffset.ToString(System.Globalization.CultureInfo.InvariantCulture),
                    ["integrity"] = Integrity(hostModule)
                },
                ["renderer.js"] = new JsonObject {
                    ["size"] = rendererScript.Length,
                    ["offset"] = rendererOffset.ToString(System.Globalization.CultureInfo.InvariantCulture),
                    ["integrity"] = Integrity(rendererScript)
                }
            }
        };
        var newHeader = Encoding.UTF8.GetBytes(archive.Tree.ToJsonString(
            new JsonSerializerOptions { WriteIndented = false }));
        var padding = checked((newHeader.Length + 3) & ~3);
        var patchedAsar = new byte[checked(16 + padding + newData.Length)];
        BinaryPrimitives.WriteUInt32LittleEndian(patchedAsar.AsSpan(0, 4), 4);
        BinaryPrimitives.WriteUInt32LittleEndian(patchedAsar.AsSpan(4, 4), (uint)(padding + 8));
        BinaryPrimitives.WriteUInt32LittleEndian(patchedAsar.AsSpan(8, 4), (uint)(padding + 4));
        BinaryPrimitives.WriteUInt32LittleEndian(patchedAsar.AsSpan(12, 4), (uint)newHeader.Length);
        newHeader.CopyTo(patchedAsar, 16);
        newData.CopyTo(patchedAsar, 16 + padding);

        var exe = (byte[])originalExe.Clone();
        var originalNeedle = Encoding.ASCII.GetBytes(Hash(archive.OriginalHeader));
        var newNeedle = Encoding.ASCII.GetBytes(Hash(newHeader));
        var changes = 0;
        for (var i = 0; i + originalNeedle.Length <= exe.Length; i++)
        {
            if (exe[i] != originalNeedle[0] ||
                !exe.AsSpan(i, originalNeedle.Length).SequenceEqual(originalNeedle))
                continue;
            newNeedle.CopyTo(exe, i);
            changes++;
            i += originalNeedle.Length - 1;
        }
        if (changes is < 1 or > 8)
            throw new IOException("EMBEDDED_ASAR_HASH_NOT_UNIQUE");
        var check = Split(patchedAsar);
        if (!ReadEntry(check, main).AsSpan().SequenceEqual(mainNew) ||
            !ReadEntry(check, "celikom/host.cjs").AsSpan().SequenceEqual(hostModule) ||
            !ReadEntry(check, "celikom/renderer.js").AsSpan().SequenceEqual(rendererScript))
            throw new IOException("BUILT_IMAGE_FAILED_INTEGRITY_TEST");

        return new Result(exe, patchedAsar, expectedExeSha256, expectedAsarSha256,
            Hash(exe), Hash(patchedAsar), changes);
    }

    public static string Hash(byte[] bytes) =>
        Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();

    private static Archive Split(byte[] asar)
    {
        if (asar.Length < 16 ||
            BinaryPrimitives.ReadUInt32LittleEndian(asar.AsSpan(0, 4)) != 4)
            throw new IOException("INVALID_ASAR_FORMAT");
        var jsonSize = BinaryPrimitives.ReadUInt32LittleEndian(asar.AsSpan(12, 4));
        if (jsonSize == 0 || jsonSize > 30 * 1024 * 1024)
            throw new IOException("INVALID_ASAR_HEADER_SIZE");
        var padded = checked((int)((jsonSize + 3) & ~3U));
        if (16L + padded > asar.Length) throw new IOException("TRUNCATED_ASAR_HEADER");
        var header = asar.AsSpan(16, (int)jsonSize).ToArray();
        try
        {
            var parsed = JsonNode.Parse(Encoding.UTF8.GetString(header)) as JsonObject ??
                throw new IOException("ASAR_NO_JSON_OBJECT");
            return new Archive(parsed, header, asar.AsSpan(16 + padded).ToArray());
        }
        catch (JsonException e) { throw new IOException("ASAR_INVALID_JSON", e); }
    }

    private static JsonObject Entry(JsonObject tree, string filename)
    {
        var parts = filename.Split('/');
        if (parts.Length == 0 || parts.Any(p => p.Length == 0 || p is "." or ".."))
            throw new IOException("INVALID_ASAR_ENTRY_PATH");
        JsonObject node = tree;
        foreach (var part in parts)
        {
            var files = node["files"] as JsonObject ??
                throw new IOException("ASAR_DIRECTORY_NOT_FOUND");
            node = files[part] as JsonObject ??
                throw new IOException("ASAR_ENTRY_NOT_FOUND");
        }
        return node;
    }

    private static int EntryOffset(JsonObject node)
    {
        var offset = node["offset"]?.GetValue<string>();
        if (!long.TryParse(offset, out var result) ||
            result < 0 || result > int.MaxValue)
            throw new IOException("ASAR_BAD_ENTRY_OFFSET");
        return (int)result;
    }

    private static int EntrySize(JsonObject node)
    {
        if (node["size"] is null ||
            !int.TryParse(node["size"]!.ToString(), out var size) || size < 0)
            throw new IOException("ASAR_BAD_ENTRY_SIZE");
        return size;
    }

    private static byte[] ReadEntry(Archive archive, string filename)
    {
        var node = Entry(archive.Tree, filename);
        if (node["unpacked"]?.GetValue<bool>() == true)
            throw new IOException("ASAR_UNPACKED_ENTRY_UNSUPPORTED");
        var offset = EntryOffset(node);
        var size = EntrySize(node);
        if ((long)offset + size > archive.Data.Length)
            throw new IOException("ASAR_ENTRY_OUTSIDE_ARCHIVE");
        return archive.Data.AsSpan(offset, size).ToArray();
    }

    private static void WalkEntries(JsonObject files, Action<JsonObject> action)
    {
        foreach (var item in files)
        {
            if (item.Value is not JsonObject node)
                throw new IOException("ASAR_MALFORMED_FILE_TREE");
            if (node["files"] is JsonObject nested) WalkEntries(nested, action);
            else if (node["offset"] is not null && node["unpacked"]?.GetValue<bool>() != true)
                action(node);
        }
    }

    private static JsonNode Integrity(byte[] bytes)
    {
        const int block = 4 * 1024 * 1024;
        var list = new List<string>();
        for (var i = 0; i < bytes.Length; i += block)
            list.Add(Hash(bytes.AsSpan(i, Math.Min(block, bytes.Length - i)).ToArray()));
        return JsonSerializer.SerializeToNode(new {
            algorithm = "SHA256", hash = Hash(bytes), blockSize = block, blocks = list
        })!;
    }

    private static void RequireHash(string value)
    {
        if (value is not { Length: 64 } ||
            value.Any(c => c is not (>= '0' and <= '9' or >= 'a' and <= 'f')))
            throw new IOException("INVALID_EXPECTED_HASH");
    }
}

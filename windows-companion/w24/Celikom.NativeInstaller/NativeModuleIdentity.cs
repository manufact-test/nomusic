using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace Celikom.NativeInstaller;

/// <summary>
/// Read-only identity of the native module ACTUALLY inside Yandex app.asar.
/// A changed executable or invalid ASAR is never treated as a matching module.
/// No mutation of Yandex files and no owner/account data are accessed.
/// </summary>
public sealed record NativeModuleIdentity(string Version, bool MatchesApplication)
{
    public static NativeModuleIdentity Unknown => new("unknown", false);

    private static readonly Regex VersionMarker = new(
        "const CELIKOM_NATIVE_VERSION = \"([0-9]+\\.[0-9]+\\.[0-9]+)\";",
        RegexOptions.CultureInvariant | RegexOptions.Compiled);

    public static NativeModuleIdentity Inspect(NativeInstallState state,
        string? installationRoot = null, string? integrationAssets = null)
    {
        if (state != NativeInstallState.Active) return Unknown;
        try
        {
            var asarPath = Path.Combine(installationRoot ??
                NativeIntegrationManager.DefaultYandexDirectory, "resources", "app.asar");
            var scripts = ReadEmbedded(asarPath);
            if (scripts == null) return Unknown;
            var versionMatch = VersionMarker.Match(Encoding.UTF8.GetString(scripts.Value.Host));
            var version = versionMatch.Success ? versionMatch.Groups[1].Value : "unknown";
            var assets = integrationAssets ?? NativeIntegrationManager.DefaultIntegrationAssets;
            using var host = File.OpenRead(Path.Combine(assets, "host.cjs"));
            using var renderer = File.OpenRead(Path.Combine(assets, "renderer.js"));
            var hostHash = SHA256.HashData(host);
            var rendererHash = SHA256.HashData(renderer);
            bool same = hostHash.AsSpan().SequenceEqual(SHA256.HashData(scripts.Value.Host)) &&
                rendererHash.AsSpan().SequenceEqual(SHA256.HashData(scripts.Value.Renderer));
            return new(version, same);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or
            InvalidOperationException or ArgumentException or System.Text.Json.JsonException or OverflowException)
        {
            return Unknown;
        }
    }

    // ASAR offsets are relative to the data section following the padded header.
    // Only the two CELIKOM scripts are read, not the full Yandex archive.
    private static (byte[] Host, byte[] Renderer)? ReadEmbedded(string path)
    {
        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
        Span<byte> prefix = stackalloc byte[16];
        stream.ReadExactly(prefix);
        if (BinaryPrimitives.ReadUInt32LittleEndian(prefix[..4]) != 4) return null;
        var headerLength = BinaryPrimitives.ReadUInt32LittleEndian(prefix[12..16]);
        if (headerLength == 0 || headerLength > 30 * 1024 * 1024) return null;
        var header = new byte[(int)headerLength];
        stream.ReadExactly(header);
        var tree = JsonNode.Parse(Encoding.UTF8.GetString(header)) as JsonObject;
        var files = tree?["files"]?["celikom"]?["files"] as JsonObject;
        if (files is null) return null;
        var dataOffset = 16 + ((long)headerLength + 3 & ~3L);
        byte[]? ReadFile(string name, int maxLength)
        {
            if (files[name] is not JsonObject node ||
                !long.TryParse(node["offset"]?.ToString(), out var offset) || offset < 0 ||
                !int.TryParse(node["size"]?.ToString(), out var count) ||
                count < 1 || count > maxLength) return null;
            var start = checked(dataOffset + offset);
            if (start < dataOffset || start > stream.Length ||
                count > stream.Length - start) return null;
            stream.Position = start;
            var data = new byte[count];
            stream.ReadExactly(data);
            return data;
        }
        var host = ReadFile("host.cjs", 120_000);
        var renderer = ReadFile("renderer.js", 1_000_000);
        return host is null || renderer is null ? null : (host, renderer);
    }
}

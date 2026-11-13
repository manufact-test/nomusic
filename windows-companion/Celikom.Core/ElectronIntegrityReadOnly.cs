using System.Buffers.Binary;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace Celikom.Companion.Core;

/// <summary>
/// Strictly read-only inspection of Electron's documented fuse sentinel and
/// optional Windows ElectronAsar Integrity resource. No executable, ASAR,
/// account files, processes or OS settings are ever modified or exported.
/// </summary>
public static class ElectronIntegrityReadOnly
{
    private static readonly byte[] Sentinel =
        Encoding.ASCII.GetBytes("dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX");
    private const long MaxExeBytes = 1024L * 1024 * 1024;
    private const int MaxAsarHeader = 16 * 1024 * 1024;
    private const uint LoadLibraryAsDataFile = 0x00000002;
    private const uint LoadLibraryAsImageResource = 0x00000020;

    public sealed record Result(
        string FuseWireState,
        string EmbeddedAsarIntegrityFuse,
        string OnlyLoadAppFromAsarFuse,
        string EmbeddedAsarResource,
        string HeaderResourceMatch)
    {
        public string SafeReport() => string.Join(Environment.NewLine,
            "W10: official Electron integrity evidence (READ-ONLY)",
            $"Electron fuse wire: {FuseWireState}",
            $"Embedded ASAR validation fuse: {EmbeddedAsarIntegrityFuse}",
            $"OnlyLoadAppFromAsar fuse: {OnlyLoadAppFromAsarFuse}",
            $"EXE ElectronAsar resource: {EmbeddedAsarResource}",
            $"EXE resource vs ASAR header: {HeaderResourceMatch}",
            "Compatibility: UNPROVEN; no official file modifications authorized.",
            "No passwords, tokens, application bytes, paths or personal data exported.",
            "W10 never modifies the Yandex executable, ASAR or running player.");
    }

    public static Result Inspect(string exePath, string asarPath)
    {
        var fuses = InspectFuseFile(exePath);
        string? headerHash = ReadAsarHeaderHash(asarPath);
        var resource = ReadWindowsIntegrityResource(exePath, headerHash);
        return new Result(fuses.State, fuses.Integrity, fuses.OnlyLoad,
            resource.Resource, resource.Match);
    }

    private sealed record FuseSummary(string State, string Integrity, string OnlyLoad);
    private static FuseSummary Unknown(string state) =>
        new(state, "UNKNOWN", "UNKNOWN");

    /// <summary>Used for synthetic CI fixtures only. Parses the published V1 layout.</summary>
    public static (string State, string Integrity, string OnlyLoad) InspectSyntheticFuseBytes(
        ReadOnlySpan<byte> bytes)
    {
        var found = new List<int>();
        int from = 0;
        while (from <= bytes.Length - Sentinel.Length)
        {
            int relative = bytes[from..].IndexOf(Sentinel);
            if (relative < 0) break;
            int index = from + relative;
            found.Add(index);
            from = index + Sentinel.Length;
        }
        if (found.Count != 1) return (found.Count == 0 ? "NOT_FOUND" : "AMBIGUOUS",
            "UNKNOWN", "UNKNOWN");
        var summary = ParseFuseBytes(bytes[(found[0] + Sentinel.Length)..]);
        return (summary.State, summary.Integrity, summary.OnlyLoad);
    }

    private static FuseSummary ParseFuseBytes(ReadOnlySpan<byte> bytes)
    {
        if (bytes.Length < 2) return Unknown("TRUNCATED");
        int version = bytes[0], length = bytes[1];
        if (version != 1) return Unknown("UNSUPPORTED_SCHEMA");
        if (length < 6 || bytes.Length < 2 + length) return Unknown("TRUNCATED");
        return new FuseSummary("V1_FOUND",
            FuseStatus(bytes[2 + 4]), FuseStatus(bytes[2 + 5]));
    }

    private static string FuseStatus(byte value) => value switch
    {
        (byte)'1' => "ENABLED",
        (byte)'0' => "DISABLED",
        (byte)'r' => "REMOVED_OR_UNSUPPORTED",
        _ => "UNKNOWN"
    };

    private static FuseSummary InspectFuseFile(string path)
    {
        try
        {
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete, 131072, FileOptions.SequentialScan);
            if (stream.Length < Sentinel.Length || stream.Length > MaxExeBytes)
                return Unknown("SIZE_NOT_SUPPORTED");
            var buffer = new byte[131072 + Sentinel.Length];
            var positions = new HashSet<long>();
            long position = 0;
            int carry = 0;
            while (true)
            {
                int read = stream.Read(buffer, carry, 131072);
                if (read <= 0) break;
                int total = carry + read;
                long windowStart = position - carry;
                var span = buffer.AsSpan(0, total);
                int cursor = 0;
                while (cursor <= total - Sentinel.Length)
                {
                    int relative = span[cursor..].IndexOf(Sentinel);
                    if (relative < 0) break;
                    int local = cursor + relative;
                    positions.Add(windowStart + local);
                    cursor = local + Sentinel.Length;
                    if (positions.Count > 1) return Unknown("AMBIGUOUS");
                }
                position += read;
                carry = Math.Min(Sentinel.Length - 1, total);
                Buffer.BlockCopy(buffer, total - carry, buffer, 0, carry);
            }
            if (positions.Count == 0) return Unknown("NOT_FOUND");
            long offset = positions.Single() + Sentinel.Length;
            stream.Seek(offset, SeekOrigin.Begin);
            Span<byte> raw = stackalloc byte[257];
            int filled = 0;
            while (filled < raw.Length)
            {
                int n = stream.Read(raw[filled..]);
                if (n <= 0) break;
                filled += n;
            }
            return ParseFuseBytes(raw[..filled]);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException
            or ArgumentException or NotSupportedException)
        {
            return Unknown("READ_FAILED");
        }
    }

    public static string? SyntheticAsarHeaderHash(ReadOnlySpan<byte> bytes)
    {
        if (bytes.Length < 20) return null;
        uint length = BinaryPrimitives.ReadUInt32LittleEndian(bytes[12..16]);
        if (length == 0 || length > MaxAsarHeader || bytes.Length < 16L + length)
            return null;
        return Convert.ToHexString(SHA256.HashData(bytes.Slice(16, (int)length))).ToLowerInvariant();
    }

    private static string? ReadAsarHeaderHash(string path)
    {
        try
        {
            using var file = new FileStream(path, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete);
            if (file.Length < 20) return null;
            Span<byte> prelude = stackalloc byte[16];
            file.ReadExactly(prelude);
            uint length = BinaryPrimitives.ReadUInt32LittleEndian(prelude[12..16]);
            if (length == 0 || length > MaxAsarHeader || file.Length < 16L + length)
                return null;
            var json = new byte[(int)length];
            file.ReadExactly(json);
            return Convert.ToHexString(SHA256.HashData(json)).ToLowerInvariant();
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException
            or ArgumentException or NotSupportedException)
        {
            return null;
        }
    }

    public static (string Resource, string Match) InspectSyntheticIntegrityJson(
        string? json, string? asarHeaderSha)
    {
        if (string.IsNullOrWhiteSpace(json)) return ("EMPTY", "UNKNOWN");
        try
        {
            using var doc = JsonDocument.Parse(json);
            if (doc.RootElement.ValueKind != JsonValueKind.Array)
                return ("UNRECOGNIZED_FORMAT", "UNKNOWN");
            foreach (var obj in doc.RootElement.EnumerateArray())
            {
                if (obj.ValueKind != JsonValueKind.Object ||
                    !obj.TryGetProperty("file", out var path) ||
                    !obj.TryGetProperty("alg", out var algorithm) ||
                    !obj.TryGetProperty("value", out var value)) continue;
                string? file = path.GetString()?.Replace('/', '\\');
                if (!string.Equals(file, @"resources\app.asar",
                        StringComparison.OrdinalIgnoreCase)) continue;
                if (!string.Equals(algorithm.GetString(), "sha256",
                        StringComparison.OrdinalIgnoreCase))
                    return ("PRESENT", "UNSUPPORTED_ALGORITHM");
                var stored = value.GetString();
                if (stored is null || stored.Length != 64 ||
                    !stored.All(Uri.IsHexDigit))
                    return ("PRESENT", "INVALID_EMBEDDED_HASH");
                if (asarHeaderSha is null || asarHeaderSha.Length != 64)
                    return ("PRESENT", "UNKNOWN");
                return ("PRESENT",
                    string.Equals(stored, asarHeaderSha,
                        StringComparison.OrdinalIgnoreCase) ? "MATCH" : "MISMATCH");
            }
            return ("PRESENT_NO_APP_ASAR_ENTRY", "UNKNOWN");
        }
        catch (Exception e) when (e is JsonException or InvalidOperationException)
        {
            return ("UNRECOGNIZED_FORMAT", "UNKNOWN");
        }
    }

    private static (string Resource, string Match) ReadWindowsIntegrityResource(
        string executablePath, string? headerHash)
    {
        if (!OperatingSystem.IsWindows()) return ("PLATFORM_NOT_WINDOWS", "UNKNOWN");
        IntPtr module = IntPtr.Zero;
        try
        {
            // LOAD_LIBRARY_AS_DATAFILE + IMAGE_RESOURCE does NOT load/execute
            // EXE code or its dependencies. Windows resource inspection only.
            module = LoadLibraryExW(executablePath, IntPtr.Zero,
                LoadLibraryAsDataFile | LoadLibraryAsImageResource);
            if (module == IntPtr.Zero) return ("RESOURCE_READ_FAILED", "UNKNOWN");
            IntPtr resource = FindResourceW(module, "ElectronAsar", "Integrity");
            if (resource == IntPtr.Zero) return ("NOT_FOUND", "UNKNOWN");
            uint length = SizeofResource(module, resource);
            if (length == 0 || length > 1024 * 1024)
                return ("RESOURCE_SIZE_NOT_SUPPORTED", "UNKNOWN");
            IntPtr handle = LoadResource(module, resource);
            if (handle == IntPtr.Zero) return ("RESOURCE_READ_FAILED", "UNKNOWN");
            IntPtr address = LockResource(handle);
            if (address == IntPtr.Zero) return ("RESOURCE_READ_FAILED", "UNKNOWN");
            var copy = new byte[(int)length];
            Marshal.Copy(address, copy, 0, copy.Length);
            var text = (copy.Length > 1 && copy[0] == (byte)'[' && copy[1] == 0)
                ? Encoding.Unicode.GetString(copy) : Encoding.UTF8.GetString(copy);
            return InspectSyntheticIntegrityJson(text.TrimEnd('\0'), headerHash);
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException
            or ArgumentException or JsonException or System.ComponentModel.Win32Exception)
        {
            return ("RESOURCE_READ_FAILED", "UNKNOWN");
        }
        finally { if (module != IntPtr.Zero) FreeLibrary(module); }
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode,
        EntryPoint = "LoadLibraryExW", SetLastError = true)]
    private static extern IntPtr LoadLibraryExW(
        string fileName, IntPtr unused, uint flags);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode,
        EntryPoint = "FindResourceW", SetLastError = true)]
    private static extern IntPtr FindResourceW(
        IntPtr module, string name, string type);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint SizeofResource(IntPtr module, IntPtr resource);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr LoadResource(IntPtr module, IntPtr resource);

    [DllImport("kernel32.dll")]
    private static extern IntPtr LockResource(IntPtr resource);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool FreeLibrary(IntPtr module);
}

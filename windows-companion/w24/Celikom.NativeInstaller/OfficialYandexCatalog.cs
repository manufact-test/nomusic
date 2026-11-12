using System.Collections.Immutable;
using System.Diagnostics;
using System.Net;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Celikom.NativeInstaller;

/// <summary>
/// A data-only, read-only list of independently reviewed Yandex official builds.
/// New validated versions can be enabled without a CELIKOM EXE update.
/// A remote entry NEVER authorizes arbitrary scripts or binaries: installed
/// files must also have an intact Windows signature from YANDEX LLC and exactly
/// match both recorded SHA256 hashes and the version.
/// </summary>
public static class OfficialYandexCatalog
{
    public const string FeedUrl =
        "https://raw.githubusercontent.com/manufact-test/nomusic/support/windows-yandex-compatibility/windows-companion/w24/compatibility/official-yandex-builds-v1.json";

    public sealed record Build(string Version, string ExeSha256, string AsarSha256);
    private sealed record Document(int Schema, string? Purpose, Entry[]? Builds);
    private sealed record Entry(string? Version, string? ExeSha256, string? AsarSha256,
        string? Status, string? Proof);

    private static readonly Build Known51270 = new(
        NativeIntegrationManager.Official51270Version,
        NativeIntegrationManager.Official51270ExeSha256,
        NativeIntegrationManager.Official51270AsarSha256);

    private static readonly SemaphoreSlim Gate = new(1, 1);
    private static ImmutableDictionary<string, Build> _known =
        ImmutableDictionary<string, Build>.Empty.Add(Known51270.Version, Known51270);
    private static DateTimeOffset _nextCheck = DateTimeOffset.MinValue;

    public static bool TryGet(string? version, out Build build)
    {
        if (version != null && _known.TryGetValue(version, out var value))
        {
            build = value;
            return true;
        }
        build = Known51270;
        return false;
    }

    /// <summary>Read-only bounded network refresh; failures retain known pins.</summary>
    public static async Task RefreshAsync(CancellationToken cancellationToken = default)
    {
        if (DateTimeOffset.UtcNow < _nextCheck) return;
        await Gate.WaitAsync(cancellationToken);
        try
        {
            if (DateTimeOffset.UtcNow < _nextCheck) return;
            _nextCheck = DateTimeOffset.UtcNow.AddMinutes(15);
            using var handler = new HttpClientHandler { AllowAutoRedirect = false };
            using var client = new HttpClient(handler)
            {
                Timeout = TimeSpan.FromSeconds(4)
            };
            using var response = await client.GetAsync(FeedUrl,
                HttpCompletionOption.ResponseHeadersRead, cancellationToken);
            if (response.StatusCode != HttpStatusCode.OK ||
                response.Content.Headers.ContentLength is > 16_384)
                return;
            await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
            using var memory = new MemoryStream();
            var chunk = new byte[4096];
            int read;
            while ((read = await stream.ReadAsync(chunk, cancellationToken)) > 0)
            {
                if (memory.Length + read > 16_384) return;
                memory.Write(chunk, 0, read);
            }
            var parsed = ParseVerifiedFeed(memory.ToArray());
            // Strict parse is all-or-nothing: a malformed or duplicate feed
            // never loses the already shipped/previously verified versions.
            var known = _known;
            foreach (var pair in parsed)
            {
                if (known.TryGetValue(pair.Key, out var old) && old != pair.Value)
                    return; // immutable pins: no silent redefinition
                known = known.SetItem(pair.Key, pair.Value);
            }
            _known = known;
        }
        catch (Exception ex) when (ex is HttpRequestException or TaskCanceledException
            or IOException or JsonException or InvalidDataException)
        {
            // Offline/VPN/invalid registry must not affect existing music.
            // Caller uses only previously verified entries.
        }
        finally { Gate.Release(); }
    }

    /// <summary>Pure validator, usable by Windows CI for malformed feeds.</summary>
    public static IReadOnlyDictionary<string, Build> ParseVerifiedFeed(byte[] json)
    {
        if (json.Length is < 30 or > 16_384)
            throw new InvalidDataException("CATALOG_SIZE_INVALID");
        var doc = JsonSerializer.Deserialize<Document>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });
        if (doc == null || doc.Schema != 1 ||
            doc.Purpose != "celikom-windows-yandex-official-baselines" ||
            doc.Builds is not { Length: >= 1 and <= 32 })
            throw new InvalidDataException("CATALOG_SCHEMA_INVALID");
        var entries = new Dictionary<string, Build>(StringComparer.Ordinal);
        foreach (var item in doc.Builds)
        {
            if (item.Version is not { Length: <= 60 } version ||
                !Regex.IsMatch(version, @"^5\.[0-9]{3,4}\.[0-9]{1,3}\.r[0-9]{5,12}$",
                    RegexOptions.CultureInvariant) ||
                !ValidHash(item.ExeSha256) || !ValidHash(item.AsarSha256) ||
                item.Status != "verified" || string.IsNullOrEmpty(item.Proof) ||
                !item.Proof.StartsWith("https://github.com/manufact-test/nomusic/actions/runs/",
                    StringComparison.Ordinal) ||
                !Uri.TryCreate(item.Proof, UriKind.Absolute, out var proofUri) ||
                proofUri.Host != "github.com" || proofUri.Query.Length > 0 ||
                proofUri.Fragment.Length > 0)
                throw new InvalidDataException("CATALOG_UNVERIFIED_ENTRY");
            if (!entries.TryAdd(version, new Build(version, item.ExeSha256!, item.AsarSha256!)))
                throw new InvalidDataException("CATALOG_DUPLICATE_VERSION");
        }
        if (!entries.TryGetValue(Known51270.Version, out var builtIn) ||
            builtIn != Known51270)
            throw new InvalidDataException("CATALOG_BUILTIN_PIN_REMOVED");
        return entries;
    }

    private static bool ValidHash(string? value) =>
        value is { Length: 64 } &&
        value.All(c => c is >= '0' and <= '9' or >= 'a' and <= 'f');

    public static bool IsExactTrustedVendorPair(string exe, string asar,
        string? exeSha256 = null, string? asarSha256 = null)
    {
        try
        {
            var version = FileVersionInfo.GetVersionInfo(exe).FileVersion;
            if (!TryGet(version, out var build)) return false;
            if ((exeSha256 ?? Celikom.WindowsRecovery.PairRecovery.Hash(exe)) != build.ExeSha256 ||
                (asarSha256 ?? Celikom.WindowsRecovery.PairRecovery.Hash(asar)) != build.AsarSha256)
                return false;
            if (!NativeHostSignature.IsValid(exe)) return false;
            // WinVerifyTrust validates the bytes; constrain the *publisher* too.
            using var signer = X509Certificate.CreateFromSignedFile(exe);
            var subject = signer.Subject;
            return subject.Contains("CN=YANDEX LLC", StringComparison.OrdinalIgnoreCase) &&
                subject.Contains("O=YANDEX LLC", StringComparison.OrdinalIgnoreCase);
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or
            CryptographicException or ArgumentException or System.ComponentModel.Win32Exception)
        {
            return false;
        }
    }
}

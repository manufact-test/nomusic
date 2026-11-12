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

    // Signed originals extracted only on disposable Windows CI from Yandex's
    // official S3 installer archives. The native image builder was exercised
    // for each version. These are additive; new releases never retire old pins.
    private static readonly Build[] Known2026 =
    {
        new("5.86.0.r18727399",
            "daed6ed88335e47f554b15053f8e9a18e0d03bbffbc7f98075d05abe0982cfa9",
            "f625fa9b9dc23eeadea3a601320f0997cab8f4247eb635f4d323ef6e3729f22d"),
        new("5.102.0.r19615975",
            "69fea666ee5b84c009a812135e23ed13b0b57ab51fde16db1508fd406c",
            "70eac5bc098fe37cb870fedf421906fc8e38d6fc70f1a0d060abc774a748fdfb"),
        new("5.121.2.e45430462d786ebc235511f243ef24745909c790",
            "7d14b31cba80923f896b1cab97d7300cca241d6734266c7fccfe841ae672cda3",
            "90546e261281d3d9ec32478a910f3876ade4f657a34e16ae28bcac807dfe9fc1"),
        new("5.126.1.56270518164a6ebd4b974971490df41224a69d68",
            "f5fb2817e331aa0b2dd0a6c7b0a360c89b5ae96afc535ca085abe514f8de4ae4",
            "5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215"),
        Known51270
    };

    private static readonly SemaphoreSlim Gate = new(1, 1);
    private static ImmutableDictionary<string, Build> _known =
        Known2026.ToImmutableDictionary(x => x.Version, StringComparer.Ordinal);
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
                response.Content.Headers.ContentLength is > 65_536)
                return;
            await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
            using var memory = new MemoryStream();
            var chunk = new byte[4096];
            int read;
            while ((read = await stream.ReadAsync(chunk, cancellationToken)) > 0)
            {
                if (memory.Length + read > 65_536) return;
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
            // Retry an unavailable feed soon, but never hammer it every tick.
            _nextCheck = DateTimeOffset.UtcNow.AddMinutes(1);
        }
        finally { Gate.Release(); }
    }

    /// <summary>Pure validator, usable by Windows CI for malformed feeds.</summary>
    public static IReadOnlyDictionary<string, Build> ParseVerifiedFeed(byte[] json)
    {
        if (json.Length is < 30 or > 65_536)
            throw new InvalidDataException("CATALOG_SIZE_INVALID");
        var doc = JsonSerializer.Deserialize<Document>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        });
        if (doc == null || doc.Schema != 1 ||
            doc.Purpose != "celikom-windows-yandex-official-baselines" ||
            doc.Builds is not { Length: >= 1 and <= 128 })
            throw new InvalidDataException("CATALOG_SCHEMA_INVALID");
        var entries = new Dictionary<string, Build>(StringComparer.Ordinal);
        foreach (var item in doc.Builds)
        {
            if (item.Version is not { Length: <= 60 } version ||
                !Regex.IsMatch(version, @"^5\.[0-9]{1,4}\.[0-9]{1,3}\.(?:r[0-9]{5,12}|[0-9a-f]{20,64})$",
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
        foreach (var pin in Known2026)
            if (entries.TryGetValue(pin.Version, out var remotelyRedefined) &&
                remotelyRedefined != pin)
                throw new InvalidDataException("CATALOG_BUILTIN_PIN_CHANGED");
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
            // X509CertificateLoader loads certificate containers, not signer
            // certificates embedded in an Authenticode-signed PE image.
#pragma warning disable SYSLIB0057
            using var signer = X509Certificate.CreateFromSignedFile(exe);
#pragma warning restore SYSLIB0057
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

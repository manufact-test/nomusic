using System.Globalization;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Celikom.Companion;

/// <summary>
/// W101 trust contract for a future stable updater. This does NOT fetch or
/// execute packages. No automatic update is enabled until a release-signing
/// public key is pinned, the EXE is Authenticode-signed, and health/rollback
/// and idle-playback gates are independently verified.
/// </summary>
public static class StableUpdateManifestVerifier
{
    public sealed record VerifiedRelease(
        Version Version, long Sequence, Uri PackageUri,
        long PackageSize, string Sha256, DateTimeOffset ExpiresAt,
        bool Mandatory, string Notes);

    private sealed record Manifest(
        int Schema, string? Channel, string? Version, long Sequence,
        string? PackageUrl, long PackageSize, string? Sha256,
        string? Publisher, string? PublishedAt, string? ExpiresAt,
        string? MinimumVersion, bool Mandatory, string? Notes,
        JsonElement? Rollback);

    public static VerifiedRelease Verify(
        byte[] document, byte[] detachedSignature, byte[] pinnedPublicKey,
        Uri officialOrigin, Version runningVersion, long lastAcceptedSequence,
        DateTimeOffset now)
    {
        if (document is not { Length: >= 100 and <= 16_384 } ||
            detachedSignature is not { Length: >= 64 and <= 80 } ||
            pinnedPublicKey is not { Length: >= 64 and <= 256 })
            throw new InvalidDataException("STABLE_MANIFEST_SIZE_INVALID");
        try
        {
            using var key = ECDsa.Create();
            key.ImportSubjectPublicKeyInfo(pinnedPublicKey, out int consumed);
            if (consumed != pinnedPublicKey.Length || key.KeySize != 256 ||
                !key.VerifyData(document, detachedSignature,
                    HashAlgorithmName.SHA256,
                    DSASignatureFormat.Rfc3279DerSequence))
                throw new InvalidDataException("STABLE_MANIFEST_SIGNATURE_INVALID");
        }
        catch (CryptographicException)
        {
            throw new InvalidDataException("STABLE_MANIFEST_SIGNATURE_INVALID");
        }

        Manifest? raw;
        try
        {
            raw = JsonSerializer.Deserialize<Manifest>(document,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
        }
        catch (JsonException)
        {
            throw new InvalidDataException("STABLE_MANIFEST_JSON_INVALID");
        }
        if (raw is null || raw.Schema != 1 || raw.Channel != "stable" ||
            raw.Publisher != "CELIKOM" || raw.Sequence <= lastAcceptedSequence ||
            raw.Sequence <= 0 ||
            (raw.Rollback.HasValue && raw.Rollback.Value.ValueKind is not
                (JsonValueKind.Null or JsonValueKind.Undefined)))
            throw new InvalidDataException("STABLE_MANIFEST_POLICY_INVALID");
        if (!TryVersion(raw.Version, out var target) ||
            target <= Normalize(runningVersion))
            throw new InvalidDataException("STABLE_MANIFEST_VERSION_INVALID");
        if (!string.IsNullOrWhiteSpace(raw.MinimumVersion) &&
            (!TryVersion(raw.MinimumVersion, out var minimum) ||
             Normalize(runningVersion) < minimum))
            throw new InvalidDataException("STABLE_MANIFEST_MINIMUM_VERSION_INVALID");

        var published = ParseUtc(raw.PublishedAt);
        var expires = ParseUtc(raw.ExpiresAt);
        if (published > now.AddMinutes(5) || expires <= now ||
            expires <= published || expires > published.AddDays(30))
            throw new InvalidDataException("STABLE_MANIFEST_EXPIRED");

        if (raw.PackageSize is < 10_000 or > 125_000_000 ||
            raw.Sha256 is not { Length: 64 } ||
            !Regex.IsMatch(raw.Sha256, "^[a-f0-9]{64}$", RegexOptions.CultureInvariant) ||
            !Uri.TryCreate(raw.PackageUrl, UriKind.Absolute, out var url) ||
            !officialOrigin.IsAbsoluteUri ||
            officialOrigin.Scheme != Uri.UriSchemeHttps ||
            url.Scheme != Uri.UriSchemeHttps ||
            !string.Equals(url.Host, officialOrigin.Host, StringComparison.OrdinalIgnoreCase) ||
            url.Port != officialOrigin.Port ||
            url.UserInfo.Length > 0 || url.Query.Length > 0 || url.Fragment.Length > 0 ||
            url.AbsolutePath.Contains('%') ||
            !url.AbsolutePath.StartsWith(
                "/CELIKOM/Windows/Updates/stable/" + target.ToString(3) + "/",
                StringComparison.Ordinal) ||
            !url.AbsolutePath.EndsWith(".exe", StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("STABLE_MANIFEST_PACKAGE_INVALID");

        if (raw.Notes is { Length: > 240 })
            throw new InvalidDataException("STABLE_MANIFEST_NOTES_INVALID");
        return new VerifiedRelease(target, raw.Sequence, url, raw.PackageSize,
            hash, expires, raw.Mandatory, raw.Notes ?? "");
    }

    private static bool TryVersion(string? text, out Version result)
    {
        result = new Version(0, 0, 0, 0);
        if (text is null ||
            !Regex.IsMatch(text, @"^[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,5}(?:\.[0-9]{1,5})?$",
                RegexOptions.CultureInvariant) ||
            !Version.TryParse(text, out var parsed))
            return false;
        result = Normalize(parsed);
        return true;
    }

    private static Version Normalize(Version value) => new(
        value.Major, value.Minor, Math.Max(value.Build, 0), Math.Max(value.Revision, 0));

    private static DateTimeOffset ParseUtc(string? text)
    {
        if (text is null || !text.EndsWith("Z", StringComparison.Ordinal) ||
            !DateTimeOffset.TryParse(text, CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal, out var value))
            throw new InvalidDataException("STABLE_MANIFEST_DATE_INVALID");
        return value;
    }
}

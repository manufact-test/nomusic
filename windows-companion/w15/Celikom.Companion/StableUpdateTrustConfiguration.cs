using System.Security.Cryptography;

namespace Celikom.Companion;

/// <summary>
/// Immutable build-pinned trust for the CELIKOM stable updater.
/// Only the P-256 public key is embedded in the client. The private signing
/// key stays in protected release infrastructure. Empty values fail closed.
/// </summary>
public sealed class StableUpdateTrustConfiguration
{
    // Public production identifiers are embedded only in the final bootstrap.
    // Never commit a private key or a temporary/staging origin here.
    private const string ProductionFeedOrigin = "";
    private const string ProductionManifestPublicKeyDerBase64 = "";

    private readonly byte[] _manifestPublicKeyDer;

    public Uri OfficialOrigin { get; }
    public string ManifestPublicKeySha256 { get; }
    public byte[] ManifestPublicKeyDer => (byte[])_manifestPublicKeyDer.Clone();

    private StableUpdateTrustConfiguration(Uri officialOrigin, byte[] manifestPublicKeyDer)
    {
        OfficialOrigin = officialOrigin;
        _manifestPublicKeyDer = (byte[])manifestPublicKeyDer.Clone();
        ManifestPublicKeySha256 = Convert.ToHexString(
            SHA256.HashData(_manifestPublicKeyDer)).ToLowerInvariant();
    }

    public static bool TryGetProduction(out StableUpdateTrustConfiguration? configuration) =>
        TryCreate(ProductionFeedOrigin, ProductionManifestPublicKeyDerBase64,
            out configuration);

    internal static bool TryCreate(
        string? feedOrigin, string? manifestPublicKeyDerBase64,
        out StableUpdateTrustConfiguration? configuration)
    {
        configuration = null;
        if (string.IsNullOrWhiteSpace(feedOrigin) ||
            string.IsNullOrWhiteSpace(manifestPublicKeyDerBase64) ||
            !Uri.TryCreate(feedOrigin, UriKind.Absolute, out var origin) ||
            origin.Scheme != Uri.UriSchemeHttps ||
            !string.Equals(origin.IdnHost, "celikom.com", StringComparison.OrdinalIgnoreCase) ||
            !origin.IsDefaultPort || origin.UserInfo.Length != 0 ||
            origin.Query.Length != 0 || origin.Fragment.Length != 0 ||
            origin.AbsolutePath != "/" || string.IsNullOrWhiteSpace(origin.Host))
            return false;

        byte[] publicKeyDer;
        try { publicKeyDer = Convert.FromBase64String(manifestPublicKeyDerBase64); }
        catch (FormatException) { return false; }
        if (publicKeyDer.Length is < 64 or > 256) return false;

        try
        {
            using var key = ECDsa.Create();
            key.ImportSubjectPublicKeyInfo(publicKeyDer, out var consumed);
            var parameters = key.ExportParameters(false);
            if (consumed != publicKeyDer.Length || key.KeySize != 256 ||
                parameters.Curve.Oid.Value != "1.2.840.10045.3.1.7")
                return false;
        }
        catch (Exception e) when (e is CryptographicException or ArgumentException)
        {
            return false;
        }

        configuration = new StableUpdateTrustConfiguration(origin, publicKeyDer);
        return true;
    }
}

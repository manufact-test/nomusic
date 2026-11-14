using System.Security.Cryptography;

namespace Celikom.Companion;

/// <summary>
/// One immutable, build-pinned trust tuple shared by the GUI and independent
/// update supervisor. The manifest private key is NEVER included here.
/// Empty production values deliberately disable every automatic update path.
/// </summary>
public sealed class StableUpdateTrustConfiguration
{
    // These are public trust identifiers, not secrets. Populate only after
    // the owner approves the official feed and production signing identities.
    // The P-256 signing PRIVATE key remains in protected release infrastructure.
    private const string ProductionFeedOrigin = "";
    private const string ProductionManifestPublicKeyDerBase64 = "";
    private const string ProductionSignerCertificateSha256 = "";

    private readonly byte[] _manifestPublicKeyDer;

    public Uri OfficialOrigin { get; }
    public string SignerCertificateSha256 { get; }
    public byte[] ManifestPublicKeyDer => (byte[])_manifestPublicKeyDer.Clone();

    private StableUpdateTrustConfiguration(
        Uri officialOrigin, byte[] manifestPublicKeyDer, string signerCertificateSha256)
    {
        OfficialOrigin = officialOrigin;
        _manifestPublicKeyDer = (byte[])manifestPublicKeyDer.Clone();
        SignerCertificateSha256 = signerCertificateSha256;
    }

    public static bool TryGetProduction(out StableUpdateTrustConfiguration? configuration) =>
        TryCreate(ProductionFeedOrigin, ProductionManifestPublicKeyDerBase64,
            ProductionSignerCertificateSha256, out configuration);

    internal static bool TryCreate(
        string? feedOrigin, string? manifestPublicKeyDerBase64,
        string? signerCertificateSha256,
        out StableUpdateTrustConfiguration? configuration)
    {
        configuration = null;
        if (string.IsNullOrWhiteSpace(feedOrigin) ||
            string.IsNullOrWhiteSpace(manifestPublicKeyDerBase64) ||
            signerCertificateSha256 is not { Length: 64 } ||
            !signerCertificateSha256.All(Uri.IsHexDigit) ||
            !Uri.TryCreate(feedOrigin, UriKind.Absolute, out var origin) ||
            origin.Scheme != Uri.UriSchemeHttps || origin.UserInfo.Length != 0 ||
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

        configuration = new StableUpdateTrustConfiguration(
            origin, publicKeyDer, signerCertificateSha256.ToLowerInvariant());
        return true;
    }
}

using System.Buffers;
using System.Net;

namespace Celikom.Companion;

/// <summary>
/// W107: read-only discovery of a cryptographically signed stable manifest.
/// Does not download an EXE, touch Yandex, enable playback or launch an updater.
/// Until an audited public signing key is pinned in the shipped application
/// there is deliberately no automatic call site for this service.
/// </summary>
public static class StableUpdateManifestFetcher
{
    private const string LatestPath = "/CELIKOM/Windows/Updates/stable/latest.json";
    private const int ManifestMaxBytes = 16_384;
    private const int SignatureMaxBytes = 80;

    public static async Task<StableUpdateManifestVerifier.VerifiedRelease> FetchSignedAsync(
        Uri officialOrigin, byte[] pinnedPublicKey, Version currentVersion,
        long lastAcceptedSequence, CancellationToken cancellationToken = default)
    {
        ValidateOrigin(officialOrigin);
        if (pinnedPublicKey is not { Length: >= 64 and <= 256 })
            throw new InvalidDataException("STABLE_FEED_KEY_NOT_PINNED");
        using var handler = new HttpClientHandler
        {
            AllowAutoRedirect = false,
            UseCookies = false,
            UseDefaultCredentials = false
        };
        using var http = new HttpClient(handler) { Timeout = TimeSpan.FromSeconds(6) };
        return await FetchSignedWithClientAsync(officialOrigin, pinnedPublicKey,
            currentVersion, lastAcceptedSequence, DateTimeOffset.UtcNow,
            http, cancellationToken);
    }

    /// <summary>
    /// Internal deterministic transport seam for CI. Caller must supply a
    /// build-time pinned public key, never a key received from this feed.
    /// </summary>
    internal static async Task<StableUpdateManifestVerifier.VerifiedRelease> FetchSignedWithClientAsync(
        Uri officialOrigin, byte[] pinnedPublicKey, Version currentVersion,
        long lastAcceptedSequence, DateTimeOffset now, HttpClient client,
        CancellationToken cancellationToken = default)
    {
        ValidateOrigin(officialOrigin);
        if (pinnedPublicKey is not { Length: >= 64 and <= 256 })
            throw new InvalidDataException("STABLE_FEED_KEY_NOT_PINNED");
        var manifestUrl = new Uri(officialOrigin, LatestPath);
        var signatureUrl = new Uri(officialOrigin, LatestPath + ".sig");
        var manifest = await ReadBoundedAsync(client, manifestUrl, ManifestMaxBytes,
            cancellationToken);
        var signature = await ReadBoundedAsync(client, signatureUrl, SignatureMaxBytes,
            cancellationToken);
        return StableUpdateManifestVerifier.Verify(manifest, signature,
            pinnedPublicKey, officialOrigin, currentVersion, lastAcceptedSequence, now);
    }

    private static void ValidateOrigin(Uri origin)
    {
        if (origin is null || !origin.IsAbsoluteUri ||
            origin.Scheme != Uri.UriSchemeHttps || origin.UserInfo.Length != 0 ||
            origin.Query.Length != 0 || origin.Fragment.Length != 0 ||
            origin.AbsolutePath != "/" || string.IsNullOrWhiteSpace(origin.Host))
            throw new InvalidDataException("STABLE_FEED_ORIGIN_INVALID");
    }

    private static async Task<byte[]> ReadBoundedAsync(
        HttpClient client, Uri expected, int maximum, CancellationToken ct)
    {
        using var request = new HttpRequestMessage(HttpMethod.Get, expected);
        using var response = await client.SendAsync(request,
            HttpCompletionOption.ResponseHeadersRead, ct);
        if (response.StatusCode != HttpStatusCode.OK ||
            response.RequestMessage?.RequestUri != expected ||
            response.Content.Headers.ContentLength is long len && (len < 1 || len > maximum))
            throw new InvalidDataException("STABLE_FEED_HTTP_INVALID");

        await using var stream = await response.Content.ReadAsStreamAsync(ct);
        using var buffer = new MemoryStream();
        var rented = ArrayPool<byte>.Shared.Rent(4096);
        try
        {
            int read;
            while ((read = await stream.ReadAsync(rented.AsMemory(0, 4096), ct)) > 0)
            {
                if (buffer.Length + read > maximum)
                    throw new InvalidDataException("STABLE_FEED_TOO_LARGE");
                buffer.Write(rented, 0, read);
            }
        }
        finally { ArrayPool<byte>.Shared.Return(rented, clearArray: true); }
        return buffer.ToArray();
    }
}

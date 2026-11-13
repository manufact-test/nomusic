using System.Globalization;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Celikom.Companion;

public sealed record SourceGrant(string TrackId, bool Approved, bool Entitled,
    string AudioUrl, long ExpiresAt, string MimeType, double GainDb, bool GainApplied);

/// <summary>
/// Converts the actual server ResolveService contract into a narrow,
/// validated SDK grant. Fail closed on origins, expiry, session-bound sid,
/// token syntax, unexpected query parameters, or unsupported audio format.
/// </summary>
public static class GrantValidator
{
    private static readonly Regex TrackIdPattern = new(@"^[1-9][0-9]{0,23}$", RegexOptions.CultureInvariant);
    private static readonly Regex AudioPathPattern = new(@"^/api/v1/audio/[1-9][0-9]{0,17}$", RegexOptions.CultureInvariant);
    private static readonly Regex HexTokenPattern = new(@"^[a-f0-9]{64}$", RegexOptions.CultureInvariant);
    private static readonly Regex UnixPattern = new(@"^[0-9]{9,12}$", RegexOptions.CultureInvariant);

    public static bool IsTrackId(string? id) => id != null && TrackIdPattern.IsMatch(id);

    public static Uri NormalizeOrigin(string raw)
    {
        if (!Uri.TryCreate(raw.Trim(), UriKind.Absolute, out var uri) ||
            uri.Scheme != Uri.UriSchemeHttps ||
            uri.UserInfo.Length != 0 || uri.AbsolutePath != "/" ||
            uri.Query.Length != 0 || uri.Fragment.Length != 0 ||
            uri.Host.Length == 0)
            throw new ArgumentException("API origin must be a HTTPS site address without path or query.");
        return new Uri(uri.GetLeftPart(UriPartial.Authority) + "/");
    }

    public static SourceGrant? FromResolve(JsonElement response, string trackId,
        Uri origin, DateTimeOffset now)
    {
        if (!IsTrackId(trackId) || response.ValueKind != JsonValueKind.Object ||
            !response.TryGetProperty("found", out var found) ||
            found.ValueKind != JsonValueKind.True) return null;

        if (!response.TryGetProperty("audio_url", out var audioProperty) ||
            audioProperty.ValueKind != JsonValueKind.String ||
            !response.TryGetProperty("expires_at", out var expiryProperty) ||
            expiryProperty.ValueKind != JsonValueKind.Number ||
            !expiryProperty.TryGetInt64(out var expiresSeconds) ||
            !response.TryGetProperty("duration_ms", out var duration) ||
            duration.ValueKind != JsonValueKind.Number ||
            !duration.TryGetInt32(out var ms) || ms <= 0 ||
            !response.TryGetProperty("mime_type", out var mime) ||
            mime.ValueKind != JsonValueKind.String ||
            (mime.GetString() != "audio/mpeg" && mime.GetString() != "audio/mp4"))
            return null;

        var nowSeconds = now.ToUnixTimeSeconds();
        if (expiresSeconds <= nowSeconds + 5 || expiresSeconds > nowSeconds + 1800)
            return null;

        var raw = audioProperty.GetString();
        if (raw == null || raw.Length > 1400 || !raw.StartsWith("/api/v1/audio/", StringComparison.Ordinal) ||
            raw.StartsWith("//", StringComparison.Ordinal) ||
            !Uri.TryCreate(origin, raw, out var link) ||
            link.Scheme != Uri.UriSchemeHttps ||
            link.GetLeftPart(UriPartial.Authority) != origin.GetLeftPart(UriPartial.Authority) ||
            link.UserInfo.Length != 0 || link.Fragment.Length != 0 ||
            !AudioPathPattern.IsMatch(link.AbsolutePath))
            return null;

        var args = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var segment in link.Query.TrimStart('?').Split('&'))
        {
            var parts = segment.Split('=', 2);
            if (parts.Length != 2 || !args.TryAdd(parts[0], parts[1])) return null;
        }
        if (args.Keys.Any(key => key is not ("expires" or "token" or "sid" or "variant")) ||
            !args.TryGetValue("expires", out var exp) || !UnixPattern.IsMatch(exp) ||
            !long.TryParse(exp, NumberStyles.None, CultureInfo.InvariantCulture, out var urlExp) ||
            urlExp != expiresSeconds ||
            !args.TryGetValue("token", out var token) || !HexTokenPattern.IsMatch(token) ||
            !args.TryGetValue("sid", out var sid) ||
            !Regex.IsMatch(sid, @"^[1-9][0-9]{0,17}$",
                RegexOptions.CultureInvariant))
            return null;

        // PHP supplies gain_db; Yandex file-info 'gain' is only a bool.
        // Passing this numeric value is NOT yet native DSP/audible amplification.
        var gainDb = 0.0;
        if (response.TryGetProperty("gain_db", out var gain))
        {
            if (gain.ValueKind != JsonValueKind.Number ||
                !gain.TryGetDouble(out gainDb) || !double.IsFinite(gainDb) ||
                gainDb < -12 || gainDb > 12 ||
                Math.Abs(gainDb * 10 - Math.Round(gainDb * 10)) > 0.00001)
                return null;
        }
        var applied = false;
        if (response.TryGetProperty("gain_applied", out var appliedField))
        {
            if (appliedField.ValueKind is not (JsonValueKind.True or JsonValueKind.False))
                return null;
            applied = appliedField.ValueKind == JsonValueKind.True;
        }
        var variant = args.TryGetValue("variant", out var variantName);
        if (applied != variant || (variant && (variantName != "windows_gain_v1" ||
            !double.IsFinite(gainDb) || gainDb == 0)))
            return null;
        return new SourceGrant(trackId, true, true, link.AbsoluteUri, expiresSeconds * 1000,
            mime.GetString()!, gainDb, applied);
    }
}

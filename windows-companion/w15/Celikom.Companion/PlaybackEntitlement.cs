using System.Globalization;
using System.Text.Json;

namespace Celikom.Companion;

/// <summary>
/// Defense-in-depth display/start gate. The server still authorizes EACH
/// resolve and signed audio Range; client wall clock is never authoritative.
/// An absent/garbled response, missing expiry or incident must fail closed.
/// </summary>
public static class PlaybackEntitlement
{
    public static bool Allowed(JsonElement data, DateTimeOffset now)
    {
        if (data.ValueKind != JsonValueKind.Object ||
            !data.TryGetProperty("allowed", out var allowed) ||
            allowed.ValueKind != JsonValueKind.True ||
            !data.TryGetProperty("source", out var sourceValue) ||
            sourceValue.ValueKind != JsonValueKind.String ||
            !data.TryGetProperty("valid_until", out var until))
            return false;
        var source = sourceValue.GetString();
        if (source is not ("trial" or "promo" or "subscription"))
            return false;
        if (data.TryGetProperty("reason", out var reason) &&
            reason.ValueKind == JsonValueKind.String &&
            reason.GetString() == "service_incident")
            return false;
        if (until.ValueKind == JsonValueKind.Null)
            return source == "promo"; // only a verified server promo may be permanent
        return until.ValueKind == JsonValueKind.String &&
            DateTimeOffset.TryParse(until.GetString(), CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal,
                out var deadline) && deadline > now;
    }
}

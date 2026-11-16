namespace Celikom.Companion;

/// <summary>
/// A successful signed grant, 206 response or file-info mapping can come from
/// Yandex prefetching. Only the exact current Media player's signed decoder
/// URL (CDP kUrl or its own direct DOM src) plus same-player PLAYING state
/// can light green.
/// </summary>
public static class PlaybackSourceEvidence
{
    public static bool Verified(bool enabled, string? status, string? presence) =>
        enabled && status == "NATIVE_SOURCE_VERIFIED" && presence == "approved";

    public static bool ActiveReplacement(bool enabled, bool heartbeatFresh,
        string? status, string? source, string? playbackState, string? presence) =>
        heartbeatFresh && playbackState == "PLAYING" && source == "ACTIVE_REPLACEMENT" &&
        Verified(enabled, status, presence);

    public static bool MappedButUnverified(bool enabled, string? status, string? presence) =>
        enabled && presence == "approved" &&
        (status == "NATIVE_MAPPING_ACCEPTED" || status == "SDK_MAPPING_ACCEPTED");

    // A renderer's ORIGINAL hint or a missing replacement grant is not proof.
    // Only a dedicated native current-decoder verification may identify original audio.
    public static bool OriginalVerified(bool enabled, string? status, string? source) =>
        enabled && status == "NATIVE_ORIGINAL_SOURCE_VERIFIED" && source == "ORIGINAL";
}

namespace Celikom.Companion;

/// <summary>
/// A successful signed grant, 206 response or file-info mapping can come from
/// Yandex prefetching. Only matching current decoder kUrl plus kIsPlaying
/// (verified independently in the native CDP observer) can light green.
/// </summary>
public static class PlaybackSourceEvidence
{
    public static bool Verified(bool enabled, string? status, string? presence) =>
        enabled && status == "NATIVE_SOURCE_VERIFIED" && presence == "approved";

    public static bool MappedButUnverified(bool enabled, string? status, string? presence) =>
        enabled && presence == "approved" &&
        (status == "NATIVE_MAPPING_ACCEPTED" || status == "SDK_MAPPING_ACCEPTED");

    // A renderer's ORIGINAL hint or a missing replacement grant is not proof.
    // Only a dedicated native current-decoder verification may identify original audio.
    public static bool OriginalVerified(bool enabled, string? status, string? source) =>
        enabled && status == "NATIVE_ORIGINAL_SOURCE_VERIFIED" && source == "ORIGINAL";
}

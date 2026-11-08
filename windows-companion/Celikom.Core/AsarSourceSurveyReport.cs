namespace Celikom.Companion.Core;

/// <summary>Only aggregated counts. No source, filenames, URL literals or credentials.</summary>
public sealed record AsarSourceSurveyReport(
    string State,
    string OwnerHashMatch,
    int PackagedJsFiles,
    int InspectedJsFiles,
    int SkippedJsFiles,
    int GetFileInfoMethodFiles,
    int GetFileInfoBatchFiles,
    int GetFileInfoResourceFiles,
    int ResourceEndpointFiles,
    int SourceAndWebpackSameFile,
    int SourceAndPreloadNamedFile,
    int SourceAndRendererNamedFile,
    int RemoteLoadUrlAndYandexHostSameFile,
    int LoadFileFiles,
    int AudioDescriptorHintFiles)
{
    public string SafeReport() => string.Join(Environment.NewLine,
        "W3: packaged source-seam survey (read-only, no live hooking)",
        $"Survey state: {State}",
        $"Owner W1 archive identity: {OwnerHashMatch}",
        $"Packaged JS files: {PackagedJsFiles}",
        $"Inspected JS files: {InspectedJsFiles}",
        $"Skipped JS files (size/budget): {SkippedJsFiles}",
        $"getFileInfo identifier files: {GetFileInfoMethodFiles}",
        $"getFileInfoBatch identifier files: {GetFileInfoBatchFiles}",
        $"GetFileInfoResource identifier files: {GetFileInfoResourceFiles}",
        $"file-info endpoint string files: {ResourceEndpointFiles}",
        $"Source marker + Webpack marker in SAME file: {SourceAndWebpackSameFile}",
        $"Source marker in preload-named JS: {SourceAndPreloadNamedFile}",
        $"Source marker in renderer-named JS: {SourceAndRendererNamedFile}",
        $"loadURL + Yandex host in SAME file: {RemoteLoadUrlAndYandexHostSameFile}",
        $"loadFile string files: {LoadFileFiles}",
        $"downloadInfo + codec in SAME file: {AudioDescriptorHintFiles}",
        $"Survey complete: {State == "OK" && SkippedJsFiles == 0}",
        "IMPORTANT: co-located strings are NOT proof of active source interception.",
        "W3 never patches, injects, reads live requests, credentials or audio.",
        "No scripts, paths, domains, URLs or user data are exported.");
}

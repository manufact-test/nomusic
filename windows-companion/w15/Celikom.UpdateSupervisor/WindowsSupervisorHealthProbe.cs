using System.ComponentModel;
using System.Diagnostics;
using System.Net;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text.Json;
using Celikom.Companion;
using Celikom.NativeInstaller;

namespace Celikom.UpdateSupervisor;

/// <summary>
/// The external process independently obtains health evidence: signed
/// installed EXE and running process, authenticated local bridge, readable
/// current-user DPAPI session and matching native integration. No account
/// network calls, Yandex startup or media changes.
/// </summary>
public sealed class WindowsSupervisorHealthProbe(string pinnedSignerSha256)
    : ISupervisorHealthProbe
{
    private static readonly string InstallRoot = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "Programs", "CELIKOM");
    private static readonly string InstalledExe =
        Path.Combine(InstallRoot, "CELIKOM.Companion.exe");
    private static readonly string InstalledNativeHost =
        Path.Combine(InstallRoot, "integration", "host.cjs");
    private static readonly string InstalledRenderer =
        Path.Combine(InstallRoot, "integration", "renderer.js");
    private static readonly string InstalledSupervisor =
        Path.Combine(InstallRoot, "CELIKOM.UpdateSupervisor.exe");

    public async Task<StableUpdateRollbackJournal.HealthEvidence> CheckAsync(
        Version expected, string originalSessionFingerprint,
        string expectedApplicationSha256, string expectedNativeHostSha256,
        string expectedRendererSha256, string expectedSupervisorSha256,
        CancellationToken cancellationToken)
    {
        // The manifest pins the exact bytes of all files copied by Inno Setup.
        var installedAndRunning = IsExpectedSignedProcess(expected,
            expectedApplicationSha256, expectedNativeHostSha256,
            expectedRendererSha256, expectedSupervisorSha256);
        // A fresh session.dpapi is decryptable but is NOT preserved login.
        var session = SignedUpdateSessionIdentity.ReadExisting();
        var sessionPreserved = originalSessionFingerprint.Length == 64 &&
            string.Equals(SignedUpdateSessionIdentity.Fingerprint(session),
                originalSessionFingerprint, StringComparison.Ordinal);
        var bridgeReady = installedAndRunning && session is not null &&
            await CheckAuthenticatedBridgeAsync(session.BridgeToken, cancellationToken);
        var nativeReady = false;
        if (installedAndRunning)
        {
            try
            {
                var state = NativeIntegrationManager.Inspect();
                nativeReady = state == NativeInstallState.Active &&
                    NativeModuleIdentity.Inspect(state).MatchesApplication;
            }
            catch (Exception e) when (e is IOException or UnauthorizedAccessException or
                InvalidOperationException or ArgumentException or CryptographicException)
            {
                nativeReady = false;
            }
        }
        return new StableUpdateRollbackJournal.HealthEvidence(
            installedAndRunning, bridgeReady, sessionPreserved, nativeReady);
    }

    public bool SafeForRollback()
    {
        if (!OperatingSystem.IsWindows()) return false;
        try
        {
            // Even if the audio bridge says "off", do not terminate a
            // currently playing or unknown Yandex process for an app update.
            using var yandexProcesses = new ProcessSnapshot("Яндекс Музыка");
            using var companionProcesses = new ProcessSnapshot("CELIKOM.Companion");
            return yandexProcesses.Count == 0 && companionProcesses.Count == 0;
        }
        catch (Exception e) when (e is Win32Exception or InvalidOperationException or
            UnauthorizedAccessException) { return false; }
    }

    private bool IsExpectedSignedProcess(Version expected,
        string applicationSha256, string nativeHostSha256, string rendererSha256,
        string supervisorSha256)
    {
        if (!OperatingSystem.IsWindows() ||
            !StableUpdatePayloadVerifier.MatchesFile(InstalledNativeHost,
                nativeHostSha256, 32_000_000) ||
            !StableUpdatePayloadVerifier.MatchesFile(InstalledRenderer,
                rendererSha256, 32_000_000) ||
            !IsExpectedSignedExecutable(InstalledExe, expected, applicationSha256) ||
            !IsExpectedSignedExecutable(InstalledSupervisor, expected, supervisorSha256))
            return false;
        try
        {
            using var found = new ProcessSnapshot("CELIKOM.Companion");
            foreach (var process in found.Processes)
            {
                try
                {
                    if (!process.HasExited &&
                        string.Equals(Path.GetFullPath(process.MainModule?.FileName ?? ""),
                            Path.GetFullPath(InstalledExe), StringComparison.OrdinalIgnoreCase))
                        return true;
                }
                catch (Exception e) when (e is Win32Exception or InvalidOperationException or
                    UnauthorizedAccessException or ArgumentException) { }
            }
        }
        catch (Exception e) when (e is Win32Exception or InvalidOperationException or
            UnauthorizedAccessException) { }
        return false;
    }

    private bool IsExpectedSignedExecutable(string path, Version expected,
        string expectedApplicationSha256)
    {
        try
        {
            if (!StableUpdatePayloadVerifier.MatchesFile(path,
                    expectedApplicationSha256) ||
                !NativeHostSignature.IsValid(path))
                return false;
            var pe = FileVersionInfo.GetVersionInfo(path);
            if (!Version.TryParse(pe.FileVersion?.Trim(), out var version) ||
                version != expected ||
                !string.Equals(pe.CompanyName?.Trim(), "CELIKOM", StringComparison.Ordinal) ||
                !string.Equals(pe.ProductName?.Trim(), "CELIKOM", StringComparison.Ordinal))
                return false;
#pragma warning disable SYSLIB0057
            using var signer = X509Certificate.CreateFromSignedFile(path);
#pragma warning restore SYSLIB0057
            var installedCert = SHA256.HashData(signer.GetRawCertData());
            var pinnedCert = Convert.FromHexString(pinnedSignerSha256);
            return CryptographicOperations.FixedTimeEquals(installedCert, pinnedCert);
        }
        catch (Exception e) when (e is IOException or Win32Exception or CryptographicException or
            ArgumentException or UnauthorizedAccessException or InvalidOperationException)
        {
            return false;
        }
    }

    private static async Task<bool> CheckAuthenticatedBridgeAsync(
        string bridgeToken, CancellationToken cancellationToken)
    {
        try
        {
            using var handler = new HttpClientHandler
            {
                AllowAutoRedirect = false,
                UseProxy = false,
                UseCookies = false,
                UseDefaultCredentials = false
            };
            using var client = new HttpClient(handler)
            {
                Timeout = TimeSpan.FromSeconds(2)
            };
            using var request = new HttpRequestMessage(HttpMethod.Get,
                "http://127.0.0.1:21471/v1/state");
            request.Headers.TryAddWithoutValidation("Origin", "https://music.yandex.ru");
            request.Headers.TryAddWithoutValidation(
                "X-Celikom-Bridge-Token", bridgeToken);
            using var response = await client.SendAsync(request,
                HttpCompletionOption.ResponseHeadersRead, cancellationToken);
            if (response.StatusCode != HttpStatusCode.OK ||
                response.Content.Headers.ContentLength is > 4096)
                return false;
            await using var input = await response.Content.ReadAsStreamAsync(cancellationToken);
            var buffer = new byte[4097];
            var total = 0;
            int read;
            while ((read = await input.ReadAsync(buffer.AsMemory(total), cancellationToken)) > 0)
            {
                total += read;
                if (total >= 4096) return false;
            }
            using var document = JsonDocument.Parse(buffer.AsMemory(0, total));
            return document.RootElement.TryGetProperty("transport", out var transport) &&
                transport.GetString() == "paired";
        }
        catch (Exception e) when (e is IOException or HttpRequestException or
            TaskCanceledException or OperationCanceledException or JsonException or
            InvalidOperationException) { return false; }
    }

    private sealed class ProcessSnapshot : IDisposable
    {
        public Process[] Processes { get; }
        public int Count => Processes.Length;
        public ProcessSnapshot(string processName) =>
            Processes = Process.GetProcessesByName(processName);
        public void Dispose()
        {
            foreach (var process in Processes) process.Dispose();
        }
    }
}

public sealed class WindowsSignedRollbackLauncher : ISupervisorRollbackLauncher
{
    public void Launch(string signedPreviousInstaller)
    {
        // The caller MUST have just passed the full journal and Authenticode
        // verifier. This class refuses unrelated names, roots or symlinks.
        var root = Path.GetFullPath(Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "CELIKOM", "Windows", "StableRollback"));
        var file = Path.GetFullPath(signedPreviousInstaller);
        if (!file.StartsWith(root + Path.DirectorySeparatorChar,
                StringComparison.OrdinalIgnoreCase) ||
            Path.GetFileName(file) != "previous-signed-setup.exe" ||
            !File.Exists(file) || new FileInfo(file).Attributes.HasFlag(FileAttributes.ReparsePoint))
            throw new IOException("SUPERVISOR_INSTALLER_PATH_INVALID");
        if (Process.Start(new ProcessStartInfo(file)
        {
            UseShellExecute = true,
            Arguments = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /CLOSEAPPLICATIONS /CELIKOMAPPUPDATE=1"
        }) is null)
            throw new IOException("SUPERVISOR_ROLLBACK_LAUNCH_FAILED");
    }
}

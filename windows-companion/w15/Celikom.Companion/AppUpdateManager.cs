using System.Diagnostics;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.RegularExpressions;

namespace Celikom.Companion;

/// <summary>
/// Owner-chosen offline upgrade of the ONE installed CELIKOM application.
/// An Inno Setup EXE is staged out of a single-exe GitHub artifact ZIP and
/// installed over the existing AppId/InstallDir. Never uninstalls CELIKOM,
/// deletes the owner's encrypted account, or accesses Yandex audio files.
/// Only local CELIKOM update artifacts can be selected; binaries are currently
/// INTERNAL and UNSIGNED, so authenticity is not cryptographically guaranteed.
/// </summary>
public static class AppUpdateManager
{
    private static readonly Regex ExpectedInstaller = new(
        @"^CELIKOM-W[0-9]{1,3}-[A-Z0-9-]{3,80}-UNSIGNED\.exe$",
        RegexOptions.Compiled | RegexOptions.CultureInvariant | RegexOptions.IgnoreCase);
    private static string StateDirectory => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "CELIKOM", "Windows");
    private static string TicketPath => Path.Combine(StateDirectory, "pending-app-upgrade.txt");
    public static Version RunningVersion =>
        typeof(AppUpdateManager).Assembly.GetName().Version ?? new Version(0, 0, 0, 0);

    public sealed record StagedInstaller(string Path, Version Version);

    public static StagedInstaller Stage(string selected, Version currentVersion)
    {
        if (!File.Exists(selected) || new FileInfo(selected).Length is < 10_000 or > 125_000_000)
            throw new IOException("UPDATE_FILE_INVALID");
        var staging = Path.Combine(StateDirectory, "Updates", Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(staging);
        var stagedPath = "";
        try
        {
            var extension = Path.GetExtension(selected);
            if (extension.Equals(".zip", StringComparison.OrdinalIgnoreCase))
            {
                using var zip = ZipFile.OpenRead(selected);
                var candidates = zip.Entries.Where(e =>
                    e.Name.EndsWith(".exe", StringComparison.OrdinalIgnoreCase)).ToArray();
                if (candidates.Length != 1 || candidates[0].FullName != candidates[0].Name ||
                    !ExpectedInstaller.IsMatch(candidates[0].Name) ||
                    candidates[0].Length is < 10_000 or > 125_000_000)
                    throw new IOException("UPDATE_PACKAGE_INVALID");
                stagedPath = Path.Combine(staging, candidates[0].Name);
                using var from = candidates[0].Open();
                using var to = new FileStream(stagedPath, FileMode.CreateNew, FileAccess.Write, FileShare.None);
                from.CopyTo(to);
            }
            else if (extension.Equals(".exe", StringComparison.OrdinalIgnoreCase) &&
                     ExpectedInstaller.IsMatch(Path.GetFileName(selected)))
            {
                stagedPath = Path.Combine(staging, Path.GetFileName(selected));
                File.Copy(selected, stagedPath);
            }
            else throw new IOException("UPDATE_PACKAGE_INVALID");

            // PE metadata is a compatibility guard, not an Authenticode trust claim.
            var metadata = FileVersionInfo.GetVersionInfo(stagedPath);
            // Inno Setup pads PE version-info strings with spaces on Windows.
            if (!Version.TryParse(metadata.FileVersion?.Trim(), out var version) ||
                !string.Equals(metadata.ProductName?.Trim(), "CELIKOM", StringComparison.Ordinal) ||
                !string.Equals(metadata.CompanyName?.Trim(), "CELIKOM", StringComparison.Ordinal))
                throw new IOException("UPDATE_NOT_CELIKOM");
            if (version <= currentVersion)
                throw new IOException("UPDATE_NOT_NEWER");
            return new StagedInstaller(stagedPath, version);
        }
        catch
        {
            try { Directory.Delete(staging, recursive: true); } catch {}
            throw;
        }
    }

    public static void MarkPending(Version targetVersion)
    {
        Directory.CreateDirectory(StateDirectory);
        File.WriteAllText(TicketPath,
            targetVersion + "|" + DateTimeOffset.UtcNow.ToUnixTimeSeconds());
    }

    public static bool TryConsumePending(Version runningVersion)
    {
        try
        {
            if (!File.Exists(TicketPath)) return false;
            var line = File.ReadAllText(TicketPath);
            File.Delete(TicketPath);
            var values = line.Split('|');
            return values.Length == 2 &&
                Version.TryParse(values[0], out var expected) &&
                expected == runningVersion &&
                long.TryParse(values[1], out var seconds) &&
                DateTimeOffset.UtcNow.ToUnixTimeSeconds() - seconds is >= 0 and <= 1200;
        }
        catch { return false; }
    }

    // Staff/manual updates obey the same no-music-interruption rule as the
    // future stable updater. Unknown process state fails closed.
    public static bool CanLaunchWithoutPlaybackInterrupt(bool bridgeEnabled)
    {
        if (bridgeEnabled || !OperatingSystem.IsWindows()) return false;
        try
        {
            var hosts = Process.GetProcessesByName("Яндекс Музыка");
            try { return hosts.Length == 0; }
            finally { foreach (var host in hosts) host.Dispose(); }
        }
        catch { return false; }
    }

    public static void ClearPending()
    {
        try { if (File.Exists(TicketPath)) File.Delete(TicketPath); }
        catch { /* Pending ticket still expires; no installer was executed. */ }
    }

    public static void Launch(StagedInstaller item)
    {
        if (!CanLaunchWithoutPlaybackInterrupt(bridgeEnabled: false))
            throw new IOException("UPDATE_DEFER_YANDEX_RUNNING");
        LaunchInstallerProcess(item.Path);
    }

    internal static void LaunchVerifiedSigned(
        string verifiedPath,
        StableUpdateManifestVerifier.VerifiedRelease release,
        string pinnedSignerCertificateSha256)
    {
        if (!StableUpdateTrustConfiguration.TryGetProduction(out var trust) ||
            trust is null ||
            !string.Equals(trust.SignerCertificateSha256, pinnedSignerCertificateSha256,
                StringComparison.OrdinalIgnoreCase))
            throw new IOException("STABLE_UPDATE_TRUST_NOT_CONFIGURED");

        var record = StableUpdateRollbackJournal.Read(
            StableUpdateRollbackJournal.DefaultPrivateRoot);
        var expectedPath = StableUpdateRollbackJournal.GetTargetInstallerPath(
            StableUpdateRollbackJournal.DefaultPrivateRoot, record.Id);
        if (record.Schema != 2 ||
            record.State != StableUpdateRollbackJournal.Phase.InstallerStarted ||
            record.RollbackAttempts != 0 ||
            !string.Equals(Path.GetFullPath(verifiedPath), Path.GetFullPath(expectedPath),
                StringComparison.OrdinalIgnoreCase) ||
            !string.Equals(record.TargetVersion, release.Version.ToString(4), StringComparison.Ordinal) ||
            record.TargetSequence != release.Sequence ||
            record.TargetSize != release.PackageSize ||
            !string.Equals(record.TargetSha256, release.Sha256, StringComparison.OrdinalIgnoreCase) ||
            !string.Equals(record.SignerSha256, pinnedSignerCertificateSha256,
                StringComparison.OrdinalIgnoreCase))
            throw new IOException("STABLE_UPDATE_TARGET_NOT_JOURNALED");

        StableUpdatePackageStager.VerifyInstaller(
            verifiedPath, release, pinnedSignerCertificateSha256);
        if (!CanLaunchWithoutPlaybackInterrupt(bridgeEnabled: false))
            throw new IOException("UPDATE_DEFER_YANDEX_RUNNING");
        LaunchInstallerProcess(verifiedPath);
    }

    private static void LaunchInstallerProcess(string path)
    {
        // Invoke the installed application's normal Inno AppId upgrade path,
        // never the uninstaller. The installer restarts the new app with
        // --complete-update via a custom explicit-upgrade Inno parameter.
        if (Process.Start(new ProcessStartInfo(path)
        {
            UseShellExecute = true,
            Arguments = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- /CLOSEAPPLICATIONS /CELIKOMAPPUPDATE=1"
        }) is null)
            throw new IOException("UPDATE_LAUNCH_FAILED");
    }
}

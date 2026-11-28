using System.Diagnostics;
using System.Security.Cryptography;
using Celikom.Companion;

internal static class StableOtaLiveRepro
{
    private const string OfficialOrigin = "https://celikom.com/";
    private const string PublicKeyBase64 =
        "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEKkv9HmP1A82irw71mA8JIRnhiSuiHc/eW4xF+SQvM4EulG9b9E1TsSU4GtJjY6Bj9E3AvuW36JUOcxuksjNLsw==";
    private const string PublicKeySha256 =
        "46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95";

    public static async Task RunAsync(Action<bool, string> test, string scratchRoot)
    {
        if (!OperatingSystem.IsWindows())
            throw new PlatformNotSupportedException("W196_LIVE_REPRO_REQUIRES_WINDOWS");

        var key = Convert.FromBase64String(PublicKeyBase64);
        test(string.Equals(
                Convert.ToHexString(SHA256.HashData(key)).ToLowerInvariant(),
                PublicKeySha256, StringComparison.Ordinal),
            "W196 live test uses the already pinned production P-256 public key");

        var origin = new Uri(OfficialOrigin, UriKind.Absolute);
        var installedVersion = new Version(0, 24, 62, 0);
        var current = await StableUpdateManifestFetcher.FetchSignedVersionAsync(
            origin, key, installedVersion);
        test(current.Version == installedVersion && current.Sequence == 9,
            "W196 .NET client authenticates immutable installed 0.24.62 / sequence 9");
        Console.WriteLine($"W196_DOTNET_CURRENT_MANIFEST_OK version={current.Version} sequence={current.Sequence}");

        var latest = await StableUpdateManifestFetcher.FetchSignedIfNewerAsync(
            origin, key, installedVersion, current.Sequence);
        test(latest is not null &&
             latest.Version == new Version(0, 24, 63, 0) &&
             latest.Sequence == 10,
            "W196 .NET client authenticates public latest 0.24.63 / sequence 10");
        if (latest is null)
            throw new InvalidDataException("W196_LIVE_LATEST_NOT_NEWER");
        Console.WriteLine($"W196_DOTNET_LATEST_MANIFEST_OK version={latest.Version} sequence={latest.Sequence}");

        StableUpdatePackageStager.VerifiedInstaller? currentPackage = null;
        StableUpdatePackageStager.VerifiedInstaller? latestPackage = null;
        try
        {
            currentPackage = await StableUpdatePackageStager.FetchVerifiedAsync(current);
            latestPackage = await StableUpdatePackageStager.FetchVerifiedAsync(latest);
            test(File.Exists(currentPackage.Path) && File.Exists(latestPackage.Path),
                "W196 .NET package stager downloads both exact signed installers");
            Console.WriteLine("W196_DOTNET_CURRENT_AND_LATEST_INSTALLERS_SHA256_AND_PE_OK");

            var extractionRoot = Path.Combine(scratchRoot, "w196-02462-installer-extract");
            Directory.CreateDirectory(extractionRoot);
            ExtractWithInnoUnp(currentPackage.Path, extractionRoot);

            var app = FindSingle(extractionRoot, "CELIKOM.Companion.exe");
            var nativeHost = FindSingle(extractionRoot, "host.cjs");
            var renderer = FindSingle(extractionRoot, "renderer.js");
            var supervisor = FindSingle(extractionRoot, "CELIKOM.UpdateSupervisor.exe");

            test(StableUpdatePayloadVerifier.MatchesFile(app, current.ApplicationSha256),
                "W196 extracted 0.24.62 application matches signed installed-payload hash");
            test(StableUpdatePayloadVerifier.MatchesFile(nativeHost, current.NativeHostSha256),
                "W196 extracted 0.24.62 native host matches signed installed-payload hash");
            test(StableUpdatePayloadVerifier.MatchesFile(renderer, current.RendererSha256),
                "W196 extracted 0.24.62 renderer matches signed installed-payload hash");
            test(StableUpdatePayloadVerifier.MatchesFile(supervisor, current.SupervisorSha256),
                "W196 extracted 0.24.62 supervisor matches signed installed-payload hash");
            Console.WriteLine("W196_DOTNET_02462_ALL_FOUR_SIGNED_PAYLOAD_HASHES_OK");

            var emptyJournalRoot = Path.Combine(scratchRoot, "w196-empty-lkg");
            var seeded = StableUpdateRollbackJournal.SeedInitialLastKnownGoodCore(
                emptyJournalRoot, current, currentPackage.Path, PublicKeySha256,
                installedVersion, app, nativeHost, renderer, supervisor,
                DateTimeOffset.UtcNow, StableUpdatePackageStager.VerifyInstaller,
                (path, hash) => StableUpdatePayloadVerifier.MatchesFile(path, hash));
            var cached = StableUpdateRollbackJournal.GetLastKnownGoodCore(
                emptyJournalRoot, PublicKeySha256, StableUpdatePackageStager.VerifyInstaller);
            test(seeded.State == StableUpdateRollbackJournal.Phase.Seeded &&
                 cached.Release.Version == installedVersion &&
                 cached.Release.Sequence == current.Sequence,
                "W196 exact 0.24.62 .NET bootstrap succeeds with a missing LKG journal");
            Console.WriteLine("W196_DOTNET_EMPTY_LKG_BOOTSTRAP_OK");

            // Synthetic only: model a completed old-version journal left behind
            // when the current app was installed outside the supervised OTA flow.
            // No owner-device journal is read or inferred by this test.
            var staleRoot = Path.Combine(scratchRoot, "w196-synthetic-stale-lkg");
            var staleVersion = new Version(0, 24, 55, 0);
            var staleRelease = current with
            {
                Version = staleVersion,
                Sequence = 2,
                PackageUri = new Uri(
                    origin,
                    "CELIKOM/Windows/Updates/stable/0.24.55/CELIKOM-Windows-0.24.55.exe"),
                ExpiresAt = DateTimeOffset.UtcNow.AddDays(1)
            };
            _ = StableUpdateRollbackJournal.SeedInitialLastKnownGoodCore(
                staleRoot, staleRelease, currentPackage.Path, PublicKeySha256,
                staleVersion, app, nativeHost, renderer, supervisor,
                DateTimeOffset.UtcNow, static (_, _) => { },
                (path, hash) => StableUpdatePayloadVerifier.MatchesFile(path, hash));
            var staleCached = StableUpdateRollbackJournal.GetLastKnownGoodCore(
                staleRoot, PublicKeySha256, static (_, _) => { });
            test(staleCached.Release.Version == staleVersion &&
                 staleCached.LastAcceptedSequence == 2,
                "W196 synthetic completed older LKG journal is readable and retains its sequence");

            var staleRebaseDenied = false;
            try
            {
                StableUpdateRollbackJournal.SeedInitialLastKnownGoodCore(
                    staleRoot, current, currentPackage.Path, PublicKeySha256,
                    installedVersion, app, nativeHost, renderer, supervisor,
                    DateTimeOffset.UtcNow, StableUpdatePackageStager.VerifyInstaller,
                    (path, hash) => StableUpdatePayloadVerifier.MatchesFile(path, hash));
            }
            catch (IOException e) when (
                e.Message == "STABLE_ROLLBACK_BOOTSTRAP_ALREADY_INITIALIZED")
            {
                staleRebaseDenied = true;
            }
            test(staleRebaseDenied &&
                 (staleCached.Release.Version != installedVersion ||
                  staleCached.Release.Sequence != current.Sequence),
                "W196 current bootstrap rejects a completed stale LKG instead of safely reconciling it");
            Console.WriteLine("W196_SYNTHETIC_STALE_LKG_BLOCK_REPRODUCED");
        }
        finally
        {
            if (currentPackage is not null)
                StableUpdatePackageStager.CleanupVerifiedStage(currentPackage);
            if (latestPackage is not null)
                StableUpdatePackageStager.CleanupVerifiedStage(latestPackage);
        }
    }

    private static void ExtractWithInnoUnp(string installerPath, string destination)
    {
        var sevenZip = Environment.GetEnvironmentVariable("CELIKOM_INNOUNP_PATH");
        if (string.IsNullOrWhiteSpace(sevenZip))
            sevenZip = "innounp.exe";

        using var process = Process.Start(new ProcessStartInfo
        {
            FileName = sevenZip,
            UseShellExecute = false,
            CreateNoWindow = true,
            ArgumentList =
            {
                "-x",
                "-d" + destination,
                installerPath
            }
        });
        if (process is null)
            throw new IOException("W196_INNOUNP_PROCESS_START_FAILED");
        process.WaitForExit();
        if (process.ExitCode != 0)
            throw new IOException("W196_INNOUNP_EXTRACT_FAILED");
    }

    private static string FindSingle(string root, string fileName)
    {
        var matches = Directory.EnumerateFiles(
            root, fileName, SearchOption.AllDirectories).ToArray();
        if (matches.Length != 1)
            throw new IOException("W196_EXTRACTED_PAYLOAD_COUNT_INVALID_" + fileName);
        return matches[0];
    }
}

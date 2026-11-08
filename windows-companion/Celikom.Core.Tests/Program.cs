using System.Buffers.Binary;
using System.Text;
using System.Text.Json;
using Celikom.Companion.Core;

int passed = 0;
void Check(bool condition, string message)
{
    if (!condition) throw new Exception("FAIL: " + message);
    passed++;
    Console.WriteLine("PASS " + message);
}

static byte[] TestAsar(string package, string mainCode)
{
    // Handcrafted minimal Electron ASAR container. These are synthetic files, NOT Yandex bytes.
    var data0 = Encoding.UTF8.GetBytes(package);
    var data1 = Encoding.UTF8.GetBytes(mainCode);
    var header = new
    {
        files = new Dictionary<string, object>
        {
            ["package.json"] = new { size = data0.Length, offset = "0" },
            ["index.js"] = new { size = data1.Length, offset = data0.Length.ToString() }
        }
    };
    byte[] json = JsonSerializer.SerializeToUtf8Bytes(header);
    int padded = (json.Length + 3) & ~3;
    using var stream = new MemoryStream();
    byte[] preamble = new byte[16];
    BinaryPrimitives.WriteUInt32LittleEndian(preamble.AsSpan(0, 4), 4);
    BinaryPrimitives.WriteUInt32LittleEndian(preamble.AsSpan(4, 4), (uint)(padded + 8));
    BinaryPrimitives.WriteUInt32LittleEndian(preamble.AsSpan(8, 4), (uint)(padded + 4));
    BinaryPrimitives.WriteUInt32LittleEndian(preamble.AsSpan(12, 4), (uint)json.Length);
    stream.Write(preamble);
    stream.Write(json);
    stream.Write(new byte[padded - json.Length]);
    stream.Write(data0);
    stream.Write(data1);
    return stream.ToArray();
}

string dir = Path.Combine(Path.GetTempPath(), "celikom-probe-fixture-" + Guid.NewGuid().ToString("N"));
try
{
    Directory.CreateDirectory(dir);
    Check(YandexProbe.FindExecutable(new[] { dir }) is null, "empty directory is not installed");
    File.WriteAllText(Path.Combine(dir, "Updater.exe"), "dummy");
    Check(YandexProbe.FindExecutable(new[] { dir }) is null, "do not mistake updater for Yandex Music");
    Check(!YandexProbe.IsAllowedExecutableName("malware.exe"), "strict allowlist");
    Check(YandexProbe.IsAllowedExecutableName("Яндекс Музыка.exe"), "Cyrillic filename recognized");
    Check(YandexProbe.IsAllowedExecutableName("YandexMusic.exe"), "Latin filename recognized");
    string fake = Path.Combine(dir, "Яндекс Музыка.exe");
    File.WriteAllText(fake, "fake; never executed");
    Check(YandexProbe.FindExecutable(new[] { dir }) == Path.GetFullPath(fake), "detect filename, no execution");
    Check(YandexProbe.FindExecutable(new[] { fake }) == Path.GetFullPath(fake), "detect exact registry DisplayIcon executable");
    Check(YandexProbe.RedactPersonalPath(null) == "not found", "safe unknown path");
    Check(YandexProbe.RedactPersonalPath(@"Z:\\Somebody\\secret\\Яндекс Музыка.exe")
            == "<custom installation path>", "hide unknown absolute path");
    var fakeSnapshot = new YandexSnapshot(true, false, fake, "1.2.3", true, "CLOSED", "fixture");
    string report = fakeSnapshot.SafeReport();
    Check(!report.Contains(dir, StringComparison.OrdinalIgnoreCase), "do not leak temp/user path");
    Check(report.Contains("Integration status: not installed / not tested"), "do not claim source hook");

    string asarPath = Path.Combine(dir, "app.asar");
    Check(AsarInspector.Inspect(asarPath).State == "NOT_FOUND", "missing ASAR is safe");
    File.WriteAllBytes(asarPath, new byte[12]);
    Check(AsarInspector.Inspect(asarPath).State == "INVALID_ASAR", "truncated ASAR is safe");

    string synthetic = """{"name":"test.yandex","version":"5.126.1","main":"index.js"}""";
    File.WriteAllBytes(asarPath, TestAsar(synthetic,
        "const { BrowserWindow } = require('electron'); const getFileInfo = () => 1;"));
    var inspected = AsarInspector.Inspect(asarPath);
    Check(inspected.State == "OK", "valid synthetic ASAR parsed");
    Check(inspected.MainEntryExists && inspected.MainEntry == "index.js", "main entry validated");
    Check(inspected.PackageVersion == "5.126.1", "package version read");
    Check(inspected.HasFileInfoMarker && inspected.HasElectronWindowMarker, "source hook hints detected");
    Check(inspected.InspectedJsFiles == 1, "bounded JS inspection");
    Check(inspected.Sha256?.Length == 64, "ASAR hash computed");
    Check(!inspected.SafeReport().Contains(dir, StringComparison.OrdinalIgnoreCase), "no local path in ASAR report");
    Check(inspected.SafeReport().Contains("NOT YET VERIFIED"), "report does not claim source hook works");

    string noHook = """{"name":"safe","version":"1.0","main":"index.js"}""";
    File.WriteAllBytes(asarPath, TestAsar(noHook, "console.log('no hooks')"));
    inspected = AsarInspector.Inspect(asarPath);
    Check(inspected.State == "OK" && !inspected.HasFileInfoMarker, "absence is handled conservatively");

    // W2: read-only source topology must only return boolean hints, never source text.
    var topology = AsarTopology.Inspect(asarPath, AsarTopology.OwnerAsarSha256);
    Check(topology.State == "OK", "W2 ASAR topology parsed");
    Check(topology.OwnerHashMatch == "MATCH_OWNER_W1", "W2 recognizes pinned owner W1 identity");
    Check(topology.TotalPackagedJsFiles == 1 && topology.InspectedJsFiles == 1, "W2 bounded packaged JS inventory");
    Check(!topology.HasFileInfoMarker, "W2 no-hook fixture stays negative");
    Check(!topology.SafeReport().Contains(dir, StringComparison.OrdinalIgnoreCase), "W2 redacts local filesystem path");
    Check(!topology.SafeReport().Contains("console.log", StringComparison.Ordinal), "W2 never exports JavaScript source");
    Check(!topology.InspectionIncomplete, "W2 synthetic one-file scan completes");

    string topologySource = "BrowserWindow.loadURL('https://music.yandex.ru'); " +
        "const preload = true; const marker = 'yastatic'; " +
        "const endpoint = 'getFileInfoBatch'; const update = 'autoUpdater';";
    File.WriteAllBytes(asarPath, TestAsar(synthetic, topologySource));
    topology = AsarTopology.Inspect(asarPath, "0");
    Check(topology.OwnerHashMatch == "CHANGED_OR_UNVERIFIED", "W2 recognizes changed archive hash");
    Check(topology.HasYandexMusicHostMarker && topology.HasYandexStaticHostMarker, "W2 remote renderer hints detected");
    Check(topology.HasLoadUrlMarker && topology.HasFileInfoBatchMarker, "W2 source and batch hints detected");
    Check(topology.HasAutoUpdaterMarker, "W2 updater hint detected");
    // W3: fuller packaged-source survey, still no real Yandex files, keys or hook.
    var seam = AsarSourceSurvey.Inspect(asarPath, "0");
    Check(seam.State == "OK", "W3 source survey parses synthetic ASAR");
    Check(seam.GetFileInfoBatchFiles == 1 && seam.GetFileInfoMethodFiles == 1,
        "W3 identifies source and batch method names");
    Check(seam.RemoteLoadUrlAndYandexHostSameFile == 1,
        "W3 distinguishes co-located remote loader hint");
    Check(seam.SkippedJsFiles == 0, "W3 bounded fixture inspected completely");
    Check(!seam.SafeReport().Contains(dir, StringComparison.OrdinalIgnoreCase),
        "W3 never prints local filesystem paths");
    File.WriteAllBytes(asarPath, TestAsar(synthetic,
        "const webpackChunk = []; const getFileInfo = 'test';" +
        "const privateSecret = 'must_never_be_exported';"));
    seam = AsarSourceSurvey.Inspect(asarPath, "0");
    Check(seam.SourceAndWebpackSameFile == 1, "W3 counts same-file source and Webpack");
    Check(!seam.SafeReport().Contains("must_never_be_exported", StringComparison.Ordinal),
        "W3 exports counts, never script bodies");

    // W3 offline source-selection contract; deliberately does NOT decode audio.
    var gate = new SourceSwapGate(new Uri("https://api.example.test/"));
    gate.Enable();
    long generation = gate.StartTrack("50163040");
    var valid = new SourceTicket("50163040",
        new Uri("https://api.example.test/api/v1/audio/123?token=synthetic"),
        DateTimeOffset.UtcNow.AddMinutes(4), true, true, true, true);
    Check(gate.Choose(generation, valid, DateTimeOffset.UtcNow).UseReplacement,
        "W3 chooses only valid exact-ID candidate");
    Check(!gate.Choose(generation, valid with { TrackId = "999" }, DateTimeOffset.UtcNow).UseReplacement,
        "W3 never substitutes another track");
    Check(!gate.Choose(generation, valid with { Entitled = false }, DateTimeOffset.UtcNow).UseReplacement,
        "W3 entitlement rejection preserves original");
    Check(!gate.Choose(generation, valid with { DurationMatched = false }, DateTimeOffset.UtcNow).UseReplacement,
        "W3 duration mismatch preserves original");
    Check(!gate.Choose(generation, valid with {
        AudioUrl = new Uri("https://other.example.test/api/v1/audio/123") },
        DateTimeOffset.UtcNow).UseReplacement,
        "W3 foreign origin cannot receive a source");
    Check(!gate.Choose(generation, valid with { ExpiresAt = DateTimeOffset.UtcNow.AddSeconds(5) },
        DateTimeOffset.UtcNow).UseReplacement,
        "W3 expiring URL preserves original");
    gate.Original();
    Check(!gate.Choose(generation, valid, DateTimeOffset.UtcNow).UseReplacement,
        "W3 Original cancels pending substitution");
    long latest = gate.StartTrack("222");
    Check(!gate.Choose(generation, valid, DateTimeOffset.UtcNow).UseReplacement,
        "W3 Next invalidates previous generation");
    Check(!gate.Choose(latest, valid, DateTimeOffset.UtcNow).UseReplacement,
        "W3 previous song cannot hijack new track");
    gate.Stop();
    Check(!gate.Choose(latest, valid, DateTimeOffset.UtcNow).UseReplacement,
        "W3 Stop forbids substitution");

    File.WriteAllBytes(asarPath, new byte[12]);
    Check(AsarTopology.Inspect(asarPath, null).State == "INVALID_OR_OVERSIZE", "W2 malformed archive is safe");
    Console.WriteLine($"CELIKOM W2 read-only probe: {passed} checks passed.");
}
finally
{
    if (Directory.Exists(dir)) Directory.Delete(dir, recursive: true);
}

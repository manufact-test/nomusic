using Celikom.Companion.Core;

int passed = 0;
void Check(bool condition, string message)
{
    if (!condition) throw new Exception("FAIL: " + message);
    passed++;
    Console.WriteLine("PASS " + message);
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
    Console.WriteLine($"CELIKOM read-only probe: {passed} checks passed.");
}
finally
{
    if (Directory.Exists(dir)) Directory.Delete(dir, recursive: true);
}

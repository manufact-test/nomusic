using Celikom.NativeInstaller;
using System.Text.Json;

// Internal build tool only. The distributed CELIKOM application uses the same
// .NET builder library directly, without Node or command-line setup.
if (args.Length != 7)
{
    Console.Error.WriteLine("Usage: stage <exe> <asar> <host.cjs> <renderer.js> <exe-sha> <asar-sha> <empty-outdir>");
    return 2;
}
try
{
    var image=NativeAsarImageBuilder.Build(
        File.ReadAllBytes(args[0]), File.ReadAllBytes(args[1]),
        File.ReadAllBytes(args[2]), File.ReadAllBytes(args[3]), args[4], args[5]);
    var folder=Path.GetFullPath(args[6]);
    if (Directory.Exists(folder) || File.Exists(folder))
        throw new IOException("OUTPUT_MUST_NOT_EXIST");
    Directory.CreateDirectory(folder);
    File.WriteAllBytes(Path.Combine(folder, "app.asar"), image.Asar);
    File.WriteAllBytes(Path.Combine(folder, "YandexMusic.patched.exe"), image.Executable);
    var report=new {
        originalExeSha=image.OriginalExeSha256,
        originalAsarSha=image.OriginalAsarSha256,
        modifiedExeSha=image.NewExeSha256,
        modifiedAsarSha=image.NewAsarSha256,
        integrityOccurrences=image.EmbeddedHashesChanged
    };
    File.WriteAllText(Path.Combine(folder,"W24-image-hashes.json"),
        JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true}));
    Console.WriteLine("W24_STAGED_IMAGES_READY");
    return 0;
}
catch (Exception ex) when (ex is IOException or ArgumentException or InvalidOperationException
    or JsonException or OverflowException or OutOfMemoryException)
{
    Console.Error.WriteLine("W24_STAGE_FAILED: "+ex.Message);
    return 1;
}

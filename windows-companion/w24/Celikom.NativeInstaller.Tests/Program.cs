using Celikom.NativeInstaller;
using Celikom.WindowsRecovery;
using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

int pass=0;
void Check(bool v,string note) { if(!v) throw new Exception("W24_FAIL "+note); pass++; }
void Reject(Action action,string note) {
  var rejected=false;
  try {action();} catch(IOException) {rejected=true;}
  Check(rejected,note);
}
string Hash(byte[] value)=>NativeAsarImageBuilder.Hash(value);
byte[] MakeArchive() {
  var contents=new Dictionary<string,string> {
    ["package.json"]="{\"main\":\"./main/index.js\",\"name\":\"yandex-test\"}",
    ["main/index.js"]="console.log('original');",
    ["main/after.js"]="console.log('after');",
    ["static/config.json"]="{\"ok\":true}"
  };
  var tree=new Dictionary<string,object>();
  var root=new Dictionary<string,object>();
  tree["files"]=root;
  var bytes=new List<byte>();
  foreach(var (name,content) in contents) {
    var parts=name.Split('/');
    var files=root;
    for(var i=0;i<parts.Length-1;i++) {
      if(!files.TryGetValue(parts[i],out var node)) {
        node=new Dictionary<string,object>{{"files",new Dictionary<string,object>()}};
        files[parts[i]]=node;
      }
      files=(Dictionary<string,object>)((Dictionary<string,object>)node)["files"];
    }
    var data=Encoding.UTF8.GetBytes(content);
    files[parts[^1]]=new Dictionary<string,object> {
      ["size"]=data.Length,["offset"]=bytes.Count.ToString()
    };
    bytes.AddRange(data);
  }
  var json=Encoding.UTF8.GetBytes(JsonSerializer.Serialize(tree));
  var padded=(json.Length+3)&~3;
  var archive=new byte[16+padded+bytes.Count];
  BinaryPrimitives.WriteUInt32LittleEndian(archive.AsSpan(0,4),4);
  BinaryPrimitives.WriteUInt32LittleEndian(archive.AsSpan(4,4),(uint)(padded+8));
  BinaryPrimitives.WriteUInt32LittleEndian(archive.AsSpan(8,4),(uint)(padded+4));
  BinaryPrimitives.WriteUInt32LittleEndian(archive.AsSpan(12,4),(uint)json.Length);
  json.CopyTo(archive,16);
  bytes.ToArray().CopyTo(archive,16+padded);
  return archive;
}
var asar=MakeArchive();
var headerLength=BinaryPrimitives.ReadUInt32LittleEndian(asar.AsSpan(12,4));
var headerHash=Hash(asar.AsSpan(16,(int)headerLength).ToArray());
var exe=Encoding.ASCII.GetBytes("MZ_FAKE_SIGNED_"+headerHash+"_END");
var host=Encoding.ASCII.GetBytes("const CELIKOM_NATIVE_VERSION = \"0.24.4\";\\n"+"host:"+new string('h',240));
var renderer=Encoding.ASCII.GetBytes("renderer:"+new string('r',1600));
var originalAsarHash=Hash(asar);
var originalExeHash=Hash(exe);
var changed=NativeAsarImageBuilder.Build(exe,asar,host,renderer,originalExeHash,originalAsarHash);
Check(changed.EmbeddedHashesChanged==1,"single embedded original hash changed");
Check(Hash(asar)==originalAsarHash&&Hash(exe)==originalExeHash,"original images immutable");
Check(Hash(changed.Executable)==changed.NewExeSha256,"patched EXE hash consistent");
Check(Hash(changed.Asar)==changed.NewAsarSha256,"patched ASAR hash consistent");
Check(!changed.Executable.SequenceEqual(exe),"EXE patch applied");
Check(!changed.Asar.SequenceEqual(asar),"ASAR patch applied");
Check(changed.Executable.AsSpan().IndexOf(Encoding.ASCII.GetBytes(headerHash)) < 0,"old embedded hash removed");
Check(changed.Asar.Length>asar.Length+host.Length+renderer.Length,"new content embedded");
var identityRoot = Path.Combine(Path.GetTempPath(),"celikom-native-identity-"+Guid.NewGuid().ToString("N"));
var identityAssets = Path.Combine(identityRoot,"assets");
Directory.CreateDirectory(Path.Combine(identityRoot,"resources"));
Directory.CreateDirectory(identityAssets);
try {
  File.WriteAllBytes(Path.Combine(identityRoot,"resources","app.asar"),changed.Asar);
  File.WriteAllBytes(Path.Combine(identityAssets,"host.cjs"),host);
  File.WriteAllBytes(Path.Combine(identityAssets,"renderer.js"),renderer);
  var identity = NativeModuleIdentity.Inspect(NativeInstallState.Active,identityRoot,identityAssets);
  Check(identity.Version=="0.24.4"&&identity.MatchesApplication,
      "installed ASAR host/renderer hashes and native version match actual installed app");
  File.AppendAllText(Path.Combine(identityAssets,"renderer.js"),"changed");
  var mismatch = NativeModuleIdentity.Inspect(NativeInstallState.Active,identityRoot,identityAssets);
  Check(mismatch.Version=="0.24.4"&&!mismatch.MatchesApplication,
      "old or modified native module is marked mismatched");
  Check(NativeModuleIdentity.Inspect(NativeInstallState.NotInstalled,identityRoot,identityAssets).Version=="unknown",
      "no installed module never claims version");
} finally { Directory.Delete(identityRoot,true); }

Reject(()=>NativeAsarImageBuilder.Build(exe,asar,host,renderer,new string('0',64),originalAsarHash),
  "wrong exe original blocked");
Reject(()=>NativeAsarImageBuilder.Build(exe,asar,host,renderer,originalExeHash,new string('0',64)),
  "wrong asar original blocked");
Reject(()=>NativeAsarImageBuilder.Build(exe,asar,host,Encoding.ASCII.GetBytes("x"),
  originalExeHash,originalAsarHash),"short renderer blocked");
var noHeader=Encoding.ASCII.GetBytes("MZ_NO_ASAR_HASH");
Reject(()=>NativeAsarImageBuilder.Build(noHeader,asar,host,renderer,
  Hash(noHeader),originalAsarHash),"missing embedded header blocked");
Check(changed.OriginalExeSha256==originalExeHash,"original exe fingerprint recorded");

// W80: only a reviewed, canonical, data-only compatibility feed may extend
// host identities. Unsupported, conflicting or malformed entries fail closed.
var verifiedFeedFile=Path.Combine("windows-companion","w24","compatibility","official-yandex-builds-v1.json");
if (File.Exists(verifiedFeedFile))
{
  var feedBytes=File.ReadAllBytes(verifiedFeedFile);
  var entries=OfficialYandexCatalog.ParseVerifiedFeed(feedBytes);
  Check(entries.Count==1 &&
    entries.TryGetValue(NativeIntegrationManager.Official51270Version,out var knownBuild) &&
    knownBuild.ExeSha256==NativeIntegrationManager.Official51270ExeSha256,
    "W80 signed 5.127 catalog builtin immutable pin accepted");
  var feedText=Encoding.UTF8.GetString(feedBytes);
  Reject(()=>OfficialYandexCatalog.ParseVerifiedFeed(Encoding.UTF8.GetBytes(
    feedText.Replace("\"verified\"","\"unverified\""))),
    "W80 arbitrary unreviewed new version rejected");
  Reject(()=>OfficialYandexCatalog.ParseVerifiedFeed(Encoding.UTF8.GetBytes(
    feedText.Replace(NativeIntegrationManager.Official51270AsarSha256,new string('b',64)))),
    "W80 known official hash cannot be silently redefined");
  Reject(()=>OfficialYandexCatalog.ParseVerifiedFeed(Encoding.UTF8.GetBytes(
    feedText.Replace("43289688797","43289688797\", \"extra\": \"foo"))),
    "W80 broken compatibility document rejected");
}

// W79 optional real-vendor test. CI extracts the independently signed official
// 5.127.0 installer into a disposable runner; nothing touches a user install.
var officialExe = Environment.GetEnvironmentVariable("CELIKOM_W79_OFFICIAL_51270_EXE");
var officialAsar = Environment.GetEnvironmentVariable("CELIKOM_W79_OFFICIAL_51270_ASAR");
var officialAssets = Environment.GetEnvironmentVariable("CELIKOM_W79_NATIVE_ASSETS");
if (!string.IsNullOrEmpty(officialExe) && !string.IsNullOrEmpty(officialAsar) &&
    !string.IsNullOrEmpty(officialAssets))
{
  Check(OperatingSystem.IsWindows(), "W79 authentic vendor test is Windows only");
  Check(PairRecovery.Hash(officialExe) == NativeIntegrationManager.Official51270ExeSha256 &&
        PairRecovery.Hash(officialAsar) == NativeIntegrationManager.Official51270AsarSha256,
        "W79 signed 5.127.0 official exact baseline hashes");
  Check(NativeHostSignature.IsValid(officialExe) &&
        System.Diagnostics.FileVersionInfo.GetVersionInfo(officialExe).FileVersion ==
        NativeIntegrationManager.Official51270Version, "W79 signed official version identity");
  var lab = Path.Combine(Path.GetTempPath(),"celikom-w79-recovery-"+Guid.NewGuid().ToString("N"));
  var installRoot = Path.Combine(lab,"YandexMusic");
  var snapshot = Path.Combine(lab,"NativeHost","snapshot");
  var labExe = Path.Combine(installRoot,PairRecovery.ExeName);
  var labAsar = Path.Combine(installRoot,"resources","app.asar");
  Directory.CreateDirectory(Path.Combine(installRoot,"resources"));
  try
  {
    // Reproduce manifest RESTORED from legacy 5.126.1 snapshot, then Yandex
    // 5.127.0 overwriting both current files (the actual owner handoff state).
    File.WriteAllText(labExe,"old-5.126-exe-byte-fixture");
    File.WriteAllText(labAsar,"old-5.126-asar-byte-fixture");
    var legacyExe = PairRecovery.Hash(labExe);
    var legacyAsar = PairRecovery.Hash(labAsar);
    PairRecovery.Capture(installRoot,snapshot,legacyExe,legacyAsar);
    File.WriteAllText(labExe,"old-0.24.23-integrated-exe");
    File.WriteAllText(labAsar,"old-0.24.23-integrated-asar");
    PairRecovery.RegisterApplied(installRoot,snapshot,PairRecovery.Hash(labExe),
      PairRecovery.Hash(labAsar));
    PairRecovery.Restore(installRoot,snapshot);
    File.Copy(officialExe,labExe,overwrite:true);
    File.Copy(officialAsar,labAsar,overwrite:true);
    Check(NativeIntegrationManager.Inspect(installRoot,snapshot) ==
        NativeInstallState.VerifiedVendorUpdate,
        "W79 exact owner RESTORED+changed pair recognized as signed official 5.127");
    Check(NativeIntegrationManager.Install(installRoot,officialAssets,snapshot) ==
        NativeInstallState.Active, "W79 reinstalls native bridge on actual 5.127 without downgrade");
    Check(NativeModuleIdentity.Inspect(NativeInstallState.Active,installRoot,officialAssets)
        .MatchesApplication, "W79 5.127 native module embedded and matches installed bundle");
    var archivedLegacy = Directory.GetDirectories(Path.Combine(lab,"NativeHost"),"previous-*");
    Check(archivedLegacy.Length==1 &&
        PairRecovery.Hash(Path.Combine(archivedLegacy[0],"original.exe"))==legacyExe &&
        PairRecovery.Hash(Path.Combine(archivedLegacy[0],"original.asar"))==legacyAsar,
        "W79 old 5.126.1 original snapshot kept intact in separate archived directory");
    Check(PairRecovery.Hash(Path.Combine(snapshot,"original.exe")) ==
        NativeIntegrationManager.Official51270ExeSha256 &&
        PairRecovery.Hash(Path.Combine(snapshot,"original.asar")) ==
        NativeIntegrationManager.Official51270AsarSha256,
        "W79 new 5.127 originals captured and verified separately");

    // Refresh module in-place without ever restoring the old 5.127 original
    // between two known active patch versions.
    var assets2=Path.Combine(lab,"new-module");
    Directory.CreateDirectory(assets2);
    File.Copy(Path.Combine(officialAssets,"host.cjs"),Path.Combine(assets2,"host.cjs"));
    File.Copy(Path.Combine(officialAssets,"renderer.js"),Path.Combine(assets2,"renderer.js"));
    File.AppendAllText(Path.Combine(assets2,"host.cjs"),"\n/* W79 module refresh test */");
    File.AppendAllText(Path.Combine(assets2,"renderer.js"),"\n/* W79 module refresh test */");
    Check(NativeIntegrationManager.Upgrade(installRoot,assets2,snapshot) ==
        NativeInstallState.Active, "W79 active native pair upgraded safely on signed 5.127");
    Check(NativeModuleIdentity.Inspect(NativeInstallState.Active,installRoot,assets2)
        .MatchesApplication, "W79 refreshed 5.127 modules matched");
    Check(Directory.GetDirectories(Path.Combine(snapshot,"upgrades")).Length==1,
        "W79 old 5.127 applied pair preserved separately for interrupted upgrade rollback");

    // W80: a genuine Yandex auto-update can overwrite a *previously ACTIVE*
    // patch. The old implementation treated this as Changed and permanently
    // blocked Start; the new one recognizes only exact official reviewed bytes.
    File.Copy(officialExe,labExe,overwrite:true);
    var halfVendorExe=PairRecovery.Hash(labExe);
    Check(NativeIntegrationManager.Inspect(installRoot,snapshot) == NativeInstallState.Changed,
        "W80 halfway Yandex EXE update rejected while ASAR still patched");
    Check(PairRecovery.Hash(labExe)==halfVendorExe,
        "W80 partial vendor update not modified by inspection");
    File.Copy(officialAsar,labAsar,overwrite:true);
    Check(NativeIntegrationManager.Inspect(installRoot,snapshot) ==
        NativeInstallState.VerifiedVendorUpdate &&
        NativeIntegrationManager.IsPreviouslyApprovedVendorUpdate(installRoot,snapshot),
        "W80 exact vendor update over ACTIVE accepted with existing consent");
    Check(NativeIntegrationManager.Install(installRoot,officialAssets,snapshot) ==
        NativeInstallState.Active,
        "W80 next Start reattaches approved vendor update without CELIKOM EXE reinstall");
    Check(NativeModuleIdentity.Inspect(NativeInstallState.Active,installRoot,officialAssets)
        .MatchesApplication,
        "W80 auto-reconnected module matches original CELIKOM bundle");
    Check(Directory.GetDirectories(Path.Combine(lab,"NativeHost"),"previous-*").Length==2,
        "W80 every superseded vendor snapshot archived without overwriting originals");

    Check(NativeIntegrationManager.Restore(installRoot,snapshot) ==
        NativeInstallState.Restored &&
        PairRecovery.Hash(labExe)==NativeIntegrationManager.Official51270ExeSha256 &&
        PairRecovery.Hash(labAsar)==NativeIntegrationManager.Official51270AsarSha256,
        "W79 exact signed 5.127 originals restored after active upgrade");
    File.WriteAllText(labAsar,"unrecognized-vendor-update-after-5.127");
    var unknownAsar=PairRecovery.Hash(labAsar);
    Check(NativeIntegrationManager.Inspect(installRoot,snapshot)==NativeInstallState.Changed,
        "W79 unrecognized future update remains blocked");
    Reject(()=>NativeIntegrationManager.Install(installRoot,officialAssets,snapshot),
        "W79 unknown ASAR never allowed through signed 5.127 recovery");
    Check(PairRecovery.Hash(labAsar)==unknownAsar &&
        PairRecovery.Hash(Path.Combine(snapshot,"original.asar"))==
        NativeIntegrationManager.Official51270AsarSha256,
        "W79 rejected update leaves host and both vendor backups intact");
    Console.WriteLine("W79_OWNER_STATE_51270_REAL_INSTALL_RECOVERY_PASS");
  }
  finally { if (Directory.Exists(lab)) Directory.Delete(lab,true); }
}

Console.WriteLine("W24_NATIVE_IMAGE_BUILDER_PASS "+pass);

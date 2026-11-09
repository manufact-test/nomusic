using Celikom.NativeInstaller;
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
var host=Encoding.ASCII.GetBytes("host:"+new string('h',240));
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
Console.WriteLine("W24_NATIVE_IMAGE_BUILDER_PASS "+pass);

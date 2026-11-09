/**
 * W23 offline ASAR/EXE image builder. Outputs STAGED COPIES only.
 * No writes to the installed Yandex files, no Windows security controls.
 * A separate consented/verified transaction must install or restore images.
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
const Hash = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const align = n => (n+3)&~3;
function assert(cond, code) { if(!cond) throw new Error(code); }
const shaPattern=/^[0-9a-f]{64}$/;
function normalizedHash(value) {
  assert(typeof value==="string"&&shaPattern.test(value),"W23_INVALID_SHA");
  return value;
}
function split(buffer) {
  assert(Buffer.isBuffer(buffer)&&buffer.length>=16,"W23_INVALID_ASAR");
  const jsize=buffer.readUInt32LE(12), end=16+align(jsize);
  assert(buffer.readUInt32LE(0)===4&&jsize>0&&jsize<30*1024*1024&&end<=buffer.length,"W23_INVALID_HEADER");
  const raw=buffer.subarray(16,16+jsize);
  let tree;
  try{tree=JSON.parse(raw.toString("utf8"));}catch{throw Error("W23_HEADER_NOT_JSON");}
  assert(tree?.files&&typeof tree.files==="object","W23_NO_FILES");
  return {tree,raw,data:buffer.subarray(end)};
}
function getNode(root, name) {
  const parts=name.split("/");
  assert(parts.length>0&&parts.every(x=>x&&![".",".."].includes(x)),"W23_INVALID_ASAR_PATH");
  let files=root.files,node;
  for (const [i,p] of parts.entries()) {
    node=files?.[p];
    assert(node&&typeof node==="object","W23_ASAR_FILE_MISSING");
    if(i<parts.length-1)files=node.files;
  }
  return node;
}
function getContent(archive,name) {
  const node=getNode(archive.tree,name);
  assert(!node.unpacked&&Number.isSafeInteger(node.size)&&node.size>=0&&
      /^[0-9]+$/.test(node.offset),"W23_UNSUPPORTED_FILE_ENTRY");
  const at=Number(node.offset);
  assert(Number.isSafeInteger(at)&&at+node.size<=archive.data.length,"W23_BAD_FILE_OFFSET");
  return archive.data.subarray(at,at+node.size);
}
function integrity(bytes) {
  const blockSize=4*1024*1024;
  const blocks=[];
  for(let pos=0;pos<bytes.length;pos+=blockSize)
    blocks.push(Hash(bytes.subarray(pos,Math.min(bytes.length,pos+blockSize))));
  return {algorithm:"SHA256",hash:Hash(bytes),blockSize,blocks};
}
function walk(files, fn) {
  for (const [name,node] of Object.entries(files)) {
    assert(node&&typeof node==="object","W23_MALFORMED_ASAR_TREE");
    if(node.files)walk(node.files,fn);
    else if(!node.unpacked&&node.offset!==undefined)fn(name,node);
  }
}
function assemble(tree, data) {
  const json=Buffer.from(JSON.stringify(tree),"utf8");
  const padded=align(json.length);
  const head=Buffer.alloc(16+padded);
  head.writeUInt32LE(4,0);
  head.writeUInt32LE(padded+8,4);
  head.writeUInt32LE(padded+4,8);
  head.writeUInt32LE(json.length,12);
  json.copy(head,16);
  return {bytes:Buffer.concat([head,data]),newHeaderHash:Hash(json)};
}
export function buildImages({asar,exe,host,renderer,expectedAsar,expectedExe}) {
  normalizedHash(expectedAsar);normalizedHash(expectedExe);
  assert(Buffer.isBuffer(asar)&&Hash(asar)===expectedAsar,"W23_ASAR_CHANGED_OR_UNSUPPORTED");
  assert(Buffer.isBuffer(exe)&&Hash(exe)===expectedExe,"W23_EXE_CHANGED");
  assert(Buffer.isBuffer(host)&&host.length>100&&host.length<120000,"W23_INVALID_HOST");
  assert(Buffer.isBuffer(renderer)&&renderer.length>1000&&renderer.length<1000000,"W23_INVALID_RENDERER");
  const src=split(asar);
  assert(!src.tree.files.celikom,"W23_ALREADY_INTEGRATED");
  let pkg;
  try{pkg=JSON.parse(getContent(src,"package.json").toString("utf8"));}
  catch{throw Error("W23_PACKAGE_JSON_MISSING");}
  const main=(typeof pkg.main==="string"?pkg.main:"").replace(/^\.\//,"");
  assert(main&&main.endsWith(".js")&&main.length<200,"W23_UNSUPPORTED_ENTRY");
  const mainNode=getNode(src.tree,main);
  assert(!mainNode.unpacked&&Number.isSafeInteger(mainNode.size)&&/^[0-9]+$/.test(mainNode.offset),
    "W23_INVALID_MAIN");
  const oldMain=getContent(src,main);
  const injected=Buffer.from("\n;try { require(require('node:path').join(require('electron').app.getAppPath(),'celikom','host.cjs')); } catch(_) {}\n");
  const newMain=Buffer.concat([oldMain,injected]);
  const delta=newMain.length-oldMain.length;
  const start=Number(mainNode.offset), stop=start+mainNode.size;
  const prefix=src.data.subarray(0,start), suffix=src.data.subarray(stop);
  const inserted=Buffer.concat([prefix,newMain,suffix]);
  const hostOffset=inserted.length, rendererOffset=hostOffset+host.length;
  walk(src.tree.files,(_name,node)=>{
    const offset=Number(node.offset);
    assert(Number.isSafeInteger(offset)&&offset>=0&&offset+node.size<=src.data.length,
      "W23_ASAR_CONTENT_OUT_OF_RANGE");
    if(node===mainNode){
      node.size=newMain.length;
      node.integrity=integrity(newMain);
    }else if(offset>start)node.offset=String(offset+delta);
  });
  src.tree.files.celikom={files:{
    "host.cjs":{size:host.length,offset:String(hostOffset),integrity:integrity(host)},
    "renderer.js":{size:renderer.length,offset:String(rendererOffset),integrity:integrity(renderer)}
  }};
  const archive=assemble(src.tree,Buffer.concat([inserted,host,renderer]));
  const oldHash=Hash(src.raw), newHash=archive.newHeaderHash;
  const oldNeedle=Buffer.from(oldHash,"ascii");
  const newNeedle=Buffer.from(newHash,"ascii");
  let count=0;
  const patchedExe=Buffer.from(exe);
  for(let i=0;i+oldNeedle.length<=patchedExe.length;i++) {
    if(patchedExe.compare(oldNeedle,0,oldNeedle.length,i,i+oldNeedle.length)===0){
      newNeedle.copy(patchedExe,i);count++;i+=oldNeedle.length-1;
    }
  }
  assert(count>0&&count<=8,"W23_EMBEDDED_INTEGRITY_RESOURCE_UNEXPECTED");
  // Full archive round trip: ASAR header, app main, and bundled scripts.
  const output=split(archive.bytes);
  assert(getContent(output,main).equals(newMain)&&
    getContent(output,"celikom/host.cjs").equals(host)&&
    getContent(output,"celikom/renderer.js").equals(renderer),
    "W23_PATCHED_ASAR_ROUNDTRIP_FAILED");
  return {
    asar:archive.bytes,exe:patchedExe,
    originalAsarSha:expectedAsar,originalExeSha:expectedExe,
    modifiedAsarSha:Hash(archive.bytes),modifiedExeSha:Hash(patchedExe),
    integrityOccurrences:count,originalHeaderHash:oldHash,newHeaderHash:newHash
  };
}
export function makeFixture(files, main="main/index.js") {
  const tree={files:{}},data=[];
  let pos=0;
  for(const [filename,body] of Object.entries(files)) {
    const parts=filename.split("/");
    let listing=tree.files;
    for(let i=0;i<parts.length-1;i++) {
      listing[parts[i]]??={files:{}};
      listing=listing[parts[i]].files;
    }
    const bytes=Buffer.from(body);
    listing[parts.at(-1)]={size:bytes.length,offset:String(pos),integrity:integrity(bytes)};
    data.push(bytes);pos+=bytes.length;
  }
  return assemble(tree,Buffer.concat(data)).bytes;
}
export function inspectAsar(buffer,filename) {return getContent(split(buffer),filename);}
if(process.argv[1]&&path.resolve(process.argv[1])===path.resolve(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/,"$1"))) {
  const args=process.argv.slice(2);
  const named={};
  for(let i=0;i<args.length;i+=2) {
    assert(args[i]?.startsWith("--")&&args[i+1],"W23_MISSING_ARGUMENT");
    named[args[i].slice(2)]=args[i+1];
  }
  for(const key of ["asar","exe","host","renderer","out","asar-sha","exe-sha"])
    assert(named[key],"W23_MISSING_"+key);
  const result=buildImages({
    asar:fs.readFileSync(named.asar),exe:fs.readFileSync(named.exe),
    host:fs.readFileSync(named.host),renderer:fs.readFileSync(named.renderer),
    expectedAsar:named["asar-sha"],expectedExe:named["exe-sha"]
  });
  const out=path.resolve(named.out);
  assert(!fs.existsSync(out),"W23_OUTPUT_ALREADY_EXISTS");
  fs.mkdirSync(out,{recursive:true});
  fs.writeFileSync(path.join(out,"app.asar"),result.asar,{flag:"wx"});
  fs.writeFileSync(path.join(out,"YandexMusic.patched.exe"),result.exe,{flag:"wx"});
  const report={
    originalAsarSha:result.originalAsarSha,
    originalExeSha:result.originalExeSha,
    modifiedAsarSha:result.modifiedAsarSha,
    modifiedExeSha:result.modifiedExeSha,
    integrityOccurrences:result.integrityOccurrences
  };
  fs.writeFileSync(path.join(out,"W23-image-hashes.json"),JSON.stringify(report,null,2),{flag:"wx"});
  console.log("W23_STAGED_IMAGE_PAIR_PASS",JSON.stringify(report));
}

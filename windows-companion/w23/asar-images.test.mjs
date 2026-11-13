import test from "node:test";
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {buildImages,makeFixture,inspectAsar} from "./asar-images.mjs";

const hash = b => createHash("sha256").update(b).digest("hex");
const main = "main/index.js";
const original = makeFixture({
  "package.json":JSON.stringify({name:"test-yandex",main:"./"+main}),
  "main/index.js":"require('electron'); console.log('original');",
  "main/after.txt":"after",
  "other/config.js":"module.exports = 1;"
});
const getHeader = bytes => {
  const n=bytes.readUInt32LE(12);
  return hash(bytes.subarray(16,16+n));
};
const needle=getHeader(original);
const exe=Buffer.from("MZ_____ASAR_"+needle+"____signed_test_payload");
const host=Buffer.from("host-test-"+ "H".repeat(250));
const renderer=Buffer.from("renderer-test-"+ "R".repeat(1100));
function patch(asar=original,override={}) {
  return buildImages({asar,exe,host,renderer,
    expectedAsar:hash(original),expectedExe:hash(exe),...override});
}
test("exact official image pair staged, never written in place",()=>{
 const copy=Buffer.from(original),origExe=Buffer.from(exe);
 const out=patch();
 assert.equal(out.integrityOccurrences,1);
 assert.equal(out.originalAsarSha,hash(original));
 assert.equal(out.originalExeSha,hash(exe));
 assert.notEqual(hash(out.asar),hash(original));
 assert.equal(hash(out.exe),out.modifiedExeSha);
 assert.deepEqual(original,copy);assert.deepEqual(exe,origExe);
});
test("main script retains original, appends narrow first-party host",()=>{
 const output=patch().asar;
 const mainResult=inspectAsar(output,main).toString();
 assert.ok(mainResult.startsWith("require('electron'); console.log('original');"));
 assert.ok(mainResult.includes("'celikom','host.cjs'"));
});
test("native files are embedded intact in the ASAR",()=>{
 const out=patch().asar;
 assert.deepEqual(inspectAsar(out,"celikom/host.cjs"),host);
 assert.deepEqual(inspectAsar(out,"celikom/renderer.js"),renderer);
 assert.equal(inspectAsar(out,"main/after.txt").toString(),"after");
 assert.equal(inspectAsar(out,"other/config.js").toString(),"module.exports = 1;");
});
test("new header integrity hash is in staged exe only",()=>{
 const out=patch();
 assert.ok(out.exe.includes(Buffer.from(out.newHeaderHash)));
 assert.ok(!out.exe.includes(Buffer.from(out.originalHeaderHash)));
 assert.ok(exe.includes(Buffer.from(out.originalHeaderHash)));
});
test("changed original ASAR is rejected before output",()=>{
 const modified=Buffer.from(original);modified[modified.length-1]^=0xff;
 assert.throws(()=>patch(modified),/W23_ASAR_CHANGED_OR_UNSUPPORTED/);
});
test("changed EXE is rejected before output",()=>{
 assert.throws(()=>patch(original,{expectedExe:"a".repeat(64)}),/W23_EXE_CHANGED/);
});
test("no embedded official header hash rejects patch",()=>{
 assert.throws(()=>patch(original,{exe:Buffer.from("MZ_____NO_HASH"),expectedExe:hash(Buffer.from("MZ_____NO_HASH"))}),
  /W23_EMBEDDED_INTEGRITY_RESOURCE_UNEXPECTED/);
});
test("double-integration refuses to patch existing altered ASAR",()=>{
 const once=patch();
 assert.throws(()=>patch(once.asar,{expectedAsar:hash(once.asar),exe:once.exe,expectedExe:hash(once.exe)}),
  /W23_ALREADY_INTEGRATED/);
});
test("broken host and renderer images fail",()=>{
 assert.throws(()=>patch(original,{host:Buffer.from("no")}),/W23_INVALID_HOST/);
 assert.throws(()=>patch(original,{renderer:Buffer.from("no")}),/W23_INVALID_RENDERER/);
});

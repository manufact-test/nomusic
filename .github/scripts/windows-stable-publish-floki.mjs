import { lstat, mkdir, mkdtemp, readFile, readlink, readdir, copyFile, chmod, rename, rm, rmdir, symlink } from "node:fs/promises";
import { constants } from "node:fs";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";
import { verifyPreparedStableRelease } from "./windows-stable-release-verify.mjs";
import { verifyExistingStableLatest } from "./windows-stable-existing-latest.mjs";

const origin = "https://celikom.com";
const versionRe = /^(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,4})$/;
const fail = code => { throw Error("FLOKI_WINDOWS_FEED_" + code); };
async function exists(path) {
  try { return await lstat(path); } catch (e) { if (e.code === "ENOENT") return null; throw e; }
}
async function safeDirectory(path, uid, privateOnly = false) {
  const info = await lstat(path);
  if (!info.isDirectory() || info.uid !== uid || (info.mode & (privateOnly ? 0o077 : 0o022))) fail("UNSAFE_DIRECTORY");
}
async function safeFile(path, uid, max) {
  const info = await lstat(path);
  if (!info.isFile() || info.uid !== uid || (info.mode & 0o022) || info.nlink !== 1 ||
      info.size < 1 || info.size > max) fail("UNSAFE_FILE");
}
function newer(a, b) {
  const x=a.split(".").map(Number), y=b.split(".").map(Number);
  for (let i=0;i<3;i++) if(x[i]!==y[i]) return x[i]>y[i];
  return false;
}

// Root-owned local promotion only. No network, SSH keys, CI credentials,
// signing secrets or automatic publication. Nginx must allowlist paths separately.
export async function promoteLocalFeed({source, root, version, sequence, pinnedPublicKeyDerBase64, uid=process.getuid()}) {
  source=resolve(source); root=resolve(root);
  if (!versionRe.test(version) || !Number.isSafeInteger(sequence) || sequence<1) fail("INVALID_IDENTITY");
  if (source===root || source.startsWith(root+"/") || root.startsWith(source+"/")) fail("OVERLAPPING_ROOTS");
  await safeDirectory(source,uid,true);
  await safeDirectory(join(source,version),uid,true);
  await safeDirectory(root,uid);
  const versions=join(root,"versions");
  if (!await exists(versions)) await mkdir(versions,{mode:0o755});
  await safeDirectory(versions,uid);
  const lock=join(root,".publish-lock");
  await mkdir(lock,{mode:0o700}); // concurrent publication fails closed
  let stage;
  try {
    const current=join(root,"current");
    const prior=await exists(current);
    if (prior) {
      if (!prior.isSymbolicLink() || prior.uid!==uid) fail("UNSAFE_CURRENT");
      const target=await readlink(current);
      const oldVersion=target.startsWith("versions/")?target.slice(9):"";
      if (!versionRe.test(oldVersion)) fail("UNSAFE_CURRENT");
      const old=join(versions,oldVersion);
      await safeDirectory(old,uid);
      await safeFile(join(old,"manifest.json"),uid,16384);
      await safeFile(join(old,"manifest.json.sig"),uid,80);
      const bytes=await readFile(join(old,"manifest.json"));
      const sig=await readFile(join(old,"manifest.json.sig"));
      const identity=verifyExistingStableLatest(bytes,sig,{origin,pinnedPublicKeyDerBase64});
      if (JSON.parse(bytes.toString("utf8")).version!==oldVersion ||
          sequence<=identity.sequence || !newer(version,oldVersion)) fail("NON_MONOTONIC");
    } else if ((await readdir(versions)).length) {
      // Never reset the sequence floor merely because the current pointer vanished.
      fail("MISSING_CURRENT_WITH_EXISTING_VERSIONS");
    }
    if (await exists(join(versions,version))) fail("IMMUTABLE_VERSION_EXISTS");
    stage=await mkdtemp(join(root,".incoming-"));
    await chmod(stage,0o700);
    await mkdir(join(stage,version),{mode:0o700});
    const exe="CELIKOM-Windows-"+version+".exe";
    const files=[
      ["latest.json",16384],["latest.json.sig",80],["manifest-public-key.der",256],
      [version+"/manifest.json",16384],[version+"/manifest.json.sig",80],
      [version+"/"+exe,125000000]
    ];
    for (const [name,max] of files) {
      await safeFile(join(source,name),uid,max);
      await copyFile(join(source,name),join(stage,name),constants.COPYFILE_EXCL);
    }
    const verified=await verifyPreparedStableRelease(stage,{origin,version,sequence,pinnedPublicKeyDerBase64});
    // Only immutable manifest/signature/installer enter the served tree.
    // The latest pair resolves through one atomic current-generation pointer.
    const prepared=join(stage,version);
    for (const name of [exe,"manifest.json","manifest.json.sig"]) await chmod(join(prepared,name),0o644);
    await chmod(prepared,0o755);
    await rename(prepared,join(versions,version));
    await symlink("versions/"+version,join(stage,"current-next"));
    await rename(join(stage,"current-next"),current);
    return verified;
  } finally {
    if (stage) await rm(stage,{recursive:true,force:true});
    await rmdir(lock);
  }
}

if(process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href) {
  if(process.getuid()!==0 || process.argv.length!==6) fail("ROOT_AND_ARGS_REQUIRED");
  const [source,version,seq,pin]=process.argv.slice(2);
  if (!/^\/root\/celikom-release-import\/[a-zA-Z0-9._-]+$/.test(source) || pin!=="/root/celikom-secrets/windows-stable-public.der") fail("PATH_NOT_APPROVED");
  for (const d of ["/root","/root/celikom-release-import","/root/celikom-secrets","/srv","/srv/celikom-releases","/srv/celikom-releases/windows","/srv/celikom-releases/windows/stable"]) await safeDirectory(d,0);
  await safeFile(pin,0,256);
  const result=await promoteLocalFeed({source,root:"/srv/celikom-releases/windows/stable",version,sequence:Number(seq),pinnedPublicKeyDerBase64:(await readFile(pin)).toString("base64"),uid:0});
  console.log("FLOKI_WINDOWS_FEED_LOCAL_PROMOTION_OK",JSON.stringify(result));
}

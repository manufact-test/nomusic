#!/bin/bash
set -Eeuo pipefail
# Isolated, unprivileged build of exact extension source; existing container/config untouched.
python3 <<'PY'
import subprocess,json,posixpath,urllib.request,hashlib
source="0e28cba5221c0f345bb1e3502d186016a614f54b"
git=["git","-c","safe.directory=/home/celikom-mirror/github-mirror.git","--git-dir=/home/celikom-mirror/github-mirror.git"]
subprocess.run(git+["merge-base","--is-ancestor",source,"refs/heads/main"],check=True,capture_output=True,timeout=15)
base=["docker","exec","--user","1000","celikom-floki-ci01"]
r=subprocess.run(base+["bash","-c","find /home/runner /opt /actions-runner /runner -maxdepth 10 -type f -name node 2>/dev/null | head -30"],capture_output=True,text=True,timeout=30)
node=None
for path in r.stdout.splitlines():
 if not path.startswith("/"):continue
 v=subprocess.run(base+[path,"--version"],capture_output=True,text=True,timeout=10)
 if v.returncode==0 and v.stdout.startswith("v24."):node=path;break
if node is None:
 r=subprocess.run(base+["mktemp","-d","/tmp/celikom-extension96-node.XXXXXXXX"],capture_output=True,text=True,check=True,timeout=15)
 runtime=r.stdout.strip()
 assert runtime.startswith("/tmp/celikom-extension96-node.") and runtime.count("/")==2
 name="node-v24.22.3-linux-x64.tar.xz"
 origin="https://nodejs.org/dist/v24.22.3/"
 with urllib.request.urlopen(origin+"SHASUMS256.txt",timeout=45) as response:checks=response.read(65536).decode()
 expected=next(line.split()[0] for line in checks.splitlines() if line.split()[-1]==name)
 with urllib.request.urlopen(origin+name,timeout=60) as response:binary=response.read(80*1024*1024+1)
 assert len(binary)<=80*1024*1024 and hashlib.sha256(binary).hexdigest()==expected
 subprocess.run(["docker","exec","-i","--user","1000","celikom-floki-ci01","tar","-xJf","-","-C",runtime,"--strip-components=1"],input=binary,capture_output=True,check=True,timeout=45)
 node=runtime+"/bin/node"
 print("EXTENSION_096_TEMPORARY_PINNED_NODE_VERIFIED",expected)

r=subprocess.run(base+["mktemp","-d","/tmp/celikom-extension96-owner.XXXXXXXX"],capture_output=True,text=True,check=True,timeout=15)
directory=r.stdout.strip()
assert directory.startswith("/tmp/celikom-extension96-owner.") and directory.count("/")==2
archive=subprocess.run(git+["archive",source,"extension","scripts","package.json","package-lock.json","server/composer.json",".github/scripts/floki-private-build-spool.mjs"],capture_output=True,check=True,timeout=60).stdout
assert len(archive)<64*1024*1024
subprocess.run(["docker","exec","-i","--user","1000","celikom-floki-ci01","tar","-xf","-","-C",directory],input=archive,check=True,capture_output=True,timeout=30)
js=r"""
import {spawnSync} from 'node:child_process';
import {readdirSync,readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
const env={...process.env,CELIKOM_API_BASE_URL:'https://api.celikom.com',PATH:path.dirname(process.execPath)+':'+process.env.PATH};
function run(args){
 const r=spawnSync(process.execPath,args,{env,encoding:'utf8',timeout:240000,maxBuffer:8*1024*1024});
 if(r.status!==0){console.log((r.stdout||'').slice(-3500),(r.stderr||'').slice(-2000));throw Error('ISOLATED_BUILD_CHECK_FAILED');}
 console.log((r.stdout||'').slice(-1200));
 return r.stdout||'';
}
run(['--disable-warning=ExperimentalWarning','extension/scripts/build.mjs','--unpacked-only']);
const tests=readdirSync('extension/tests').filter(x=>x.endsWith('.test.mjs')).map(x=>'extension/tests/'+x);
const report=run(['--test','--test-concurrency=2',...tests]);
if(!/pass 471/.test(report))throw Error('EXPECTED_471_TESTS');
run(['--disable-warning=ExperimentalWarning','extension/scripts/build.mjs']);
run(['extension/scripts/validate-manifest.mjs']);
run(['scripts/security-audit.mjs']);
const zip=readFileSync('extension/dist/celikom-extension-0.4.96.zip');
const sha=createHash('sha256').update(zip).digest('hex');
if(zip.length!==2506160||sha!=='2503ea6f3a2326394dbd3e67859064a051db30125a035f44cff22c35aefc1379')throw Error('PACKAGE_MISMATCH');
writeFileSync('private-owner-build-verified.json',JSON.stringify({source:'0e28cba5221c0f345bb1e3502d186016a614f54b',tests:471,size:zip.length,sha256:sha}));
console.log('EXTENSION_096_ISOLATED_BUILD_CHECKS_PASS',sha,zip.length);
"""
r=subprocess.run(["docker","exec","-i","--user","1000","--workdir",directory,"celikom-floki-ci01",node,"--input-type=module","-"],input=js,capture_output=True,text=True,timeout=600)
print(r.stdout[-12000:],end="")
assert r.returncode==0,"UNPRIVILEGED_EXTENSION_BUILD_FAILED"
print("EXTENSION_096_ISOLATED_BUILD_LOCATION",json.dumps({"directory":directory,"node":node,"source":source}))
PY

import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, symlink, readlink, readdir, rm } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import os from 'node:os';

const source = await readFile('.github/scripts/hostinger-activate.sh', 'utf8');
const php = spawnSync('sh', ['-c', 'command -v php'], {encoding:'utf8'}).stdout.trim();
assert.ok(php, 'PHP 8.3 is needed for the deployment lifecycle test');
const sha='a'.repeat(40), releaseId='0.4.0-'+sha;
for (const failHealth of [false,true]) {
  const root=await mkdtemp(path.join(os.tmpdir(),'celikom-activate-'));
  try {
    const site=path.join(root,'site'), app=path.join(site,'celikom'), pub=path.join(site,'public_html');
    const incoming=path.join(app,'incoming',releaseId), fixture=path.join(root,'fixture'), bin=path.join(root,'bin');
    for (const dir of [pub,incoming,bin,path.join(app,'releases','previous'),path.join(fixture,'public'),path.join(fixture,'deploy'),path.join(fixture,'bin')]) await mkdir(dir,{recursive:true});
    await symlink(path.join(app,'releases','previous'),path.join(app,'current'));
    await writeFile(path.join(pub,'index.php'),'previous public entry');
    await writeFile(path.join(pub,'.htaccess'),'previous rules');
    await writeFile(path.join(fixture,'public','index.php'),'<?php');
    await writeFile(path.join(fixture,'public','.htaccess'),'RewriteEngine On\n');
    await writeFile(path.join(fixture,'deploy','public-entry.php'),'candidate public entry');
    await writeFile(path.join(fixture,'deploy','initialize-private-test.php'),'<?php stream_get_contents(STDIN); echo "Fixture configuration ready\\n";');
    await writeFile(path.join(fixture,'bin','migrate.php'),'<?php echo "Fixture schema ready\\n";');
    const zip=spawnSync('zip',['-q','-r',path.join(incoming,'package.zip'),'.'],{cwd:fixture}); assert.equal(zip.status,0);
    const checksum=spawnSync('sha256sum',['package.zip'],{cwd:incoming,encoding:'utf8'}); assert.equal(checksum.status,0);
    await writeFile(path.join(incoming,'package.zip.sha256'),checksum.stdout);
    await writeFile(path.join(bin,'curl'),`#!/usr/bin/env bash
set -eu
url="\${@: -1}"
case "$url" in
  *celikom-runtime*) echo '{"php_version":"8.3.0","php_version_id":80300,"database":true,"pdo_mysql":true,"fileinfo":true}' ;;
  */api/v1/health) if [[ "\${FAIL_HEALTH:-0}" == 1 ]]; then exit 22; fi; echo '{"service":"celikom-api","version":"0.4.0"}' ;;
  */api/v1/config) echo '{"features":{"replacements":false,"analytics":false}}' ;;
  *) exit 1 ;;
esac
`,{mode:0o755});
    const script=source.replace("site='/home/u235811320/domains/darkred-camel-588676.hostingersite.com'",`site='${site}'`).replace("php_bin='/opt/alt/php83/usr/bin/php'",`php_bin='${php}'`);
    const file=path.join(root,'activate.sh'); await writeFile(file,script);
    const run=spawnSync('bash',[file,releaseId],{input:'{}',encoding:'utf8',env:{...process.env,PATH:bin+':'+process.env.PATH,FAIL_HEALTH:failHealth?'1':'0'}});
    assert.equal(run.status,failHealth?22:0,run.stdout+run.stderr);
    assert.equal(await readlink(path.join(app,'current')),path.join(app,'releases',failHealth?'previous':releaseId));
    assert.equal(await readFile(path.join(pub,'index.php'),'utf8'),failHealth?'previous public entry':'candidate public entry');
    if (failHealth) assert.equal(await readFile(path.join(pub,'.htaccess'),'utf8'),'previous rules');
    assert.ok(!(await readdir(pub)).some(name=>name.startsWith('celikom-runtime-')),'Temporary public probes must be removed');
  } finally { await rm(root,{recursive:true,force:true}); }
}
console.log('Deployment activation and failed-HTTPS rollback passed with isolated filesystem/HTTP fixtures.');

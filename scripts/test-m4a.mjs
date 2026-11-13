import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {inspectM4a} from '../extension/dist/unpacked/upload/m4a.js';
const dir=await mkdtemp(join(tmpdir(),'celikom-m4a-'));
try {
 const file=join(dir,'sine.m4a');
 const encode=spawnSync('ffmpeg',['-v','error','-f','lavfi','-i','sine=frequency=660:duration=3','-c:a','aac','-b:a','128k',file]);
 assert.equal(encode.status,0,'Disposable AAC fixture encoder');
 const original=await readFile(file),buffer=b=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
 const result=inspectM4a(buffer(original));assert.ok(Math.abs(result.durationMs-3000)<100);
 const script=join(dir,'probe.php');await writeFile(script,`<?php require ${JSON.stringify(process.cwd()+'/server/bootstrap.php')}; echo json_encode((new Celikom\\Application\\M4aInspector())->durationMs($argv[1]));`);
 const php=spawnSync('php',['--version']);
 if(php.error?.code!=='ENOENT'){
  const probe=path=>{const p=spawnSync('php',[script,path],{encoding:'utf8'});assert.equal(p.status,0,p.stderr);return JSON.parse(p.stdout);};
  assert.equal(probe(file),result.durationMs,'Independent server duration agrees');
  const bad=join(dir,'bad.m4a');
  for(const mutation of [b=>b.subarray(0,b.length-100),b=>{b.write('vide',b.indexOf('soun'));return b;},b=>{b.write('enca',b.indexOf('mp4a'));return b;},b=>{b.writeUInt32BE(0xffffffff,b.indexOf('stco')+12);return b;},b=>{b.writeUInt32BE(0xffffffff,b.indexOf('stsz')+12);return b;},b=>{b.write('https://external.invalid',b.indexOf('mdat')+4);b.write('url ',b.indexOf('url '));b.writeUInt32BE(0,b.indexOf('url ')+4);return b;},b=>Buffer.alloc(2048)]){
   await writeFile(bad,mutation(Buffer.from(original)));assert.equal(probe(bad),null,'Reject malformed/encrypted/video/external/table mismatch');
  }
  if(process.env.DB_NAME){const integration=spawnSync('php',['server/tests/m4a.php',file],{stdio:'inherit'});assert.equal(integration.status,0,'M4A database/Range regression');}
  console.log('PASS independent PHP M4A duration and malformed-container rejection');
 }else if(process.env.CI)throw Error('PHP required in CI');
 else console.log('PHP M4A runtime deferred to CI');
 assert.throws(()=>inspectM4a(buffer(original.subarray(0,-100))));
 console.log('PASS real AAC M4A preflight without transcoding');
}finally{await rm(dir,{recursive:true,force:true});}

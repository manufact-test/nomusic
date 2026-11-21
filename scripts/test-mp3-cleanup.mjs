import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';
import {execFileSync,spawnSync} from 'node:child_process';
import {inspectMp3} from '../extension/dist/unpacked/upload/mp3-duration.js';
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'celikom-cleanup-'));
const concat=(...chunks)=>Buffer.concat(chunks.map(x=>Buffer.from(x)));
const tag=Buffer.from([73,68,51,4,0,0,0,0,0,0]);
const hash=p=>execFileSync('ffmpeg',['-v','error','-i',p,'-map','0:a:0','-f','hash','-hash','sha256','-'],{encoding:'utf8'}).trim();
const frameSize=b=>{const h=b.readUInt32BE(0),v=(h>>>19)&3,rate=[44100,48000,32000][(h>>>10)&3]/(v===3?1:v===2?2:4),br=(v===3?[0,32,40,48,56,64,80,96,112,128,160,192,224,256,320]:[0,8,16,24,32,40,48,56,64,80,96,112,128,144])[(h>>>12)&15];return Math.floor((v===3?144:72)*br*1000/rate)+((h>>>9)&1);};
try {
 for(const [rate,bitrate] of [[44100,'128k'],[48000,'192k'],[22050,'64k']]){
  const source=path.join(tmp,`source-${rate}.mp3`);
  execFileSync('ffmpeg',['-v','error','-f','lavfi','-i',`sine=frequency=997:duration=2:sample_rate=${rate}`,'-ac','2','-c:a','libmp3lame','-b:a',bitrate,source]);
  const clean=inspectMp3(fs.readFileSync(source));assert.ok(clean);
  const raw=Buffer.from(clean.bytes),n=frameSize(raw),info=raw.subarray(0,n),audio=raw.subarray(n);
  const input=path.join(tmp,`tagged-${rate}.mp3`);
  fs.writeFileSync(input,concat(tag,info,tag,info,audio,Buffer.from('TAG'+'Ж'.repeat(27)+'x'.repeat(97)),[7]));
  assert.deepEqual(Buffer.from(inspectMp3(fs.readFileSync(input)).bytes),raw);
  execFileSync('php',['server/tests/mp3-cleanup.php',input],{stdio:'inherit'});
  assert.deepEqual(fs.readFileSync(input+'.clean.mp3'),raw);
  assert.equal(hash(source),hash(input+'.clean.mp3'));
  assert.equal(hash(source),hash(input));
  const bad=Buffer.from(raw);let p=n;
  for(let i=0;i<15;i++){const len=frameSize(bad.subarray(p));bad.fill(255,p+4,p+len);p+=len;}
  const corrupt=path.join(tmp,`corrupt-${rate}.mp3`);fs.writeFileSync(corrupt,bad);
  assert.ok(inspectMp3(bad),'frame-only inspection cannot detect damaged Huffman payload');
  const result=spawnSync('php',['server/tests/mp3-cleanup.php',corrupt],{encoding:'utf8'});
  assert.notEqual(result.status,0,'decoder must reject valid headers with damaged audio');
  assert.match(result.stderr,/invalid_mp3/);
 }
 console.log('MP3_JS_PHP_PCM_AND_CORRUPTION_PASS: MPEG1, MPEG2, 44.1/48/22.05kHz; identical decoded PCM; broken payload denied');
}finally{fs.rmSync(tmp,{recursive:true,force:true});}

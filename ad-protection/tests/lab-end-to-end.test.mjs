import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, writeFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const alignCli=path.join(root,'analysis/align-observation.mjs');
const diffCli=path.join(root,'analysis/compare-har.mjs');
const base=Date.parse('2026-10-20T11:00:00Z');
const ordinary='https://music.yandex.ru/api/player?access_token=PRIVATE_USER_TOKEN';
const audio='https://cdn.yandex.net/audio/segment?sign=SECRET_SIGNATURE';
const candidate='https://ads.example.invalid/creative?id=SECRET_PRIVATE_CAMPAIGN';
function record(t,url,mime='application/json',status=200){
  return {
    startedDateTime:new Date(base+t*1000).toISOString(),time:10,_resourceType:mime.startsWith('audio/')?'media':'fetch',
    request:{method:'GET',url,headers:status===206?[{name:'Range',value:'bytes=0-4096'}]:[]},
    response:{status,content:{mimeType:mime},headers:[{name:'Set-Cookie',value:'session=SECRET'}]}
  };
}
function har(type){
  const entries=[
    record(0,ordinary),
    record(8,audio,'audio/mpeg',206),
    record(20,ordinary)
  ];
  if(type==='ad')entries.push(record(35,candidate,'video/mp4'));
  else entries.push(record(35,ordinary));
  entries.push(record(42,audio,'audio/mpeg',206));
  return {log:{version:'1.2',entries}};
}
const observer={
 schema:'celikom-ad-observer-v1',ageSeconds:70,
 markers:[{s:25,kind:'normal-music'},{s:40,kind:'ad-heard'},{s:45,kind:'normal-music'}],
 recent:[{category:'private',url:ordinary,note:'PRIVATE_EMAIL@example.com'}]
};
function call(file,args){return JSON.parse(execFileSync(process.execPath,[file,...args],{encoding:'utf8',timeout:20000,maxBuffer:1024*1024}));}
async function inTemp(fn){
 const dir=await mkdtemp(path.join(tmpdir(),'celikom-adlab-'));
 try{return await fn(dir)}finally{await rm(dir,{recursive:true,force:true})}
}
test('full local evidence route: observer JSON + HAR become a strictly sanitized report',async()=>{
 await inTemp(async dir=>{
  const p1=path.join(dir,'observer.json'),p2=path.join(dir,'normal.har');
  await writeFile(p1,JSON.stringify(observer));
  await writeFile(p2,JSON.stringify(har('normal')));
  // Observer is 5 seconds ahead of HAR-relative events in this fabricated capture.
  const result=call(alignCli,[p1,p2,'--offset=-5','--radius=3']);
  assert.equal(result.decision,'UNKNOWN');
  assert.equal(result.markers[0].harSecond,20);
  assert.equal(result.markers[1].harSecond,35);
  assert.equal(result.markers.length,3);
  const safe=JSON.stringify(result);
  for(const needle of ['SECRET','PRIVATE','access_token','/audio/','/api/','PRIVATE_EMAIL','session='])assert.equal(safe.includes(needle),false,needle);
 });
});

test('multiple ad/control HAR files produce local-only fingerprint comparison',async()=>{
 await inTemp(async dir=>{
  const ad1=path.join(dir,'ad1.har'),ad2=path.join(dir,'ad2.har'),normal=path.join(dir,'normal.har');
  await writeFile(ad1,JSON.stringify(har('ad')));
  await writeFile(ad2,JSON.stringify(har('ad')));
  await writeFile(normal,JSON.stringify(har('normal')));
  const report=call(diffCli,['--ad='+ad1+'@35','--ad='+ad2+'@35','--normal='+normal+'@35','--radius=3']);
  assert.equal(report.decision,'UNKNOWN');
  assert.equal(report.input.adCaptures,2);
  assert.equal(report.input.normalCaptures,1);
  assert.ok(report.groups.some(x=>x.evidenceHint==='differential-candidate-only'));
  assert.ok(report.groups.every(x=>x.forbiddenForBlocking===true));
  const safe=JSON.stringify(report);
  for(const needle of ['SECRET','PRIVATE','access_token','/audio/','/creative','session='])assert.equal(safe.includes(needle),false,needle);
 });
});

test('CLI rejects sync-less or malformed inputs (no silent guessed offset)',async()=>{
 await inTemp(async dir=>{
  const p1=path.join(dir,'observer.json'),p2=path.join(dir,'session.har');
  await writeFile(p1,JSON.stringify(observer));await writeFile(p2,JSON.stringify(har('ad')));
  assert.throws(()=>execFileSync(process.execPath,[alignCli,p1,p2],{encoding:'utf8',stdio:['ignore','pipe','pipe'],timeout:20000}));
  assert.throws(()=>execFileSync(process.execPath,[diffCli,'--ad='+p2+'@35'],{encoding:'utf8',stdio:['ignore','pipe','pipe'],timeout:20000}));
 });
});

test('non-research standalone manifest remains inert; analyzer cannot modify network requests',async()=>{
 const fs=await import('node:fs/promises');
 const manifest=JSON.parse(await fs.readFile(path.join(root,'standalone/manifest.json'),'utf8'));
 const observerManifest=JSON.parse(await fs.readFile(path.join(root,'observer/manifest.json'),'utf8'));
 assert.ok(!('content_scripts' in manifest));
 assert.ok(!('host_permissions' in observerManifest));
 assert.ok(!('permissions' in observerManifest));
 assert.deepEqual(observerManifest.content_scripts[0].matches,['https://music.yandex.ru/*']);
 for(const f of ['har-evidence.mjs','evidence-correlation.mjs','align-observation-core.mjs']){
  const source=await fs.readFile(path.join(root,'analysis',f),'utf8');
  for(const forbidden of ['chrome.declarativeNetRequest','chrome.webRequest','window.fetch','document.cookie'])
   assert.equal(source.includes(forbidden),false,f+': '+forbidden);
 }
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {createNativeResourceAdapter} from './native-resource-adapter.mjs';

const now = 1800000000000;
const url = 'https://api.celikom.example/api/v1/audio/22?token='+'a'.repeat(64)+'&expires='+Math.floor((now+180000)/1000);
const grant = (id='123', overrides={}) => ({
  trackId:id, approved:true, entitled:true, audioUrl:url,
  expiresAt:now+180000, mimeType:'audio/mpeg', ...overrides
});
const orig = {
  downloadInfo:{trackId:'123',key:'drm',codec:'aac',
    urls:['https://official.example/native'],url:'https://official.example/native'},
  responseTime:41
};
function resource() {
  const stats={single:0,batch:0};
  const proto={
    getFileInfo:async function(params) {
      stats.single++;
      return structuredClone({...orig,downloadInfo:{...orig.downloadInfo,trackId:String(params.trackId)}});
    },
    getFileInfoBatch:async function() {
      stats.batch++;
      return {downloadInfos:[{trackId:'123',key:'secret',codec:'aac',url:'https://official.example/'}]};
    }
  };
  return {proto,stats};
}
const create=(resolve=async id=>grant(id), settings={})=>createNativeResourceAdapter({
  resolve,allowedOrigin:'https://api.celikom.example',now:()=>now,
  deadlineMs:150,...settings
});

test('disabled is transparent: no CELIKOM request',async()=>{
  let calls=0;const a=create(async()=>{calls++;return grant()});const {proto}=resource();a.attach(proto);
  assert.deepEqual(await proto.getFileInfo({trackId:'123'}),orig);
  assert.equal(calls,0);a.dispose();
});
test('approved mp3 changes only source, leaves native response intact',async()=>{
  const a=create();const {proto}=resource();a.attach(proto);a.enable();
  const r=await proto.getFileInfo({trackId:'123'});
  assert.equal(r.responseTime,41);assert.equal(r.downloadInfo.url,url);
  assert.deepEqual(r.downloadInfo.urls,[url]);assert.equal(r.downloadInfo.codec,'mp3');
  assert.equal(r.downloadInfo.transport,'raw');assert.equal(r.downloadInfo.key,undefined);
  assert.equal(a.status,'SOURCE_MAPPING_RETURNED_NOT_AUDIO_VERIFIED');a.dispose();
});
test('approved MP4 uses AAC codec, not MP3',async()=>{
  const a=create(async id=>grant(id,{mimeType:'audio/mp4'}));const {proto}=resource();a.attach(proto);a.enable();
  assert.equal((await proto.getFileInfo({trackId:'123'})).downloadInfo.codec,'aac-mp4');a.dispose();
});
test('rejects unapproved, entitlement denied, wrong origin, wrong track',async()=>{
  for(const bad of [grant('123',{approved:false}),
    grant('123',{audioUrl:'https://evil.example/m.mp3'}),
    grant('42'),grant('123',{entitled:false})]) {
    const a=create(async()=>bad);const {proto}=resource();a.attach(proto);a.enable();
    assert.deepEqual(await proto.getFileInfo({trackId:'123'}),orig);a.dispose();
  }
});
test('if original fails but approved grant exists, native source response is built',async()=>{
  const a=create();const {proto}=resource();
  proto.getFileInfo=async()=>{throw new Error('native unavailable')};
  a.attach(proto);a.enable();
  assert.equal((await proto.getFileInfo({trackId:'123'})).downloadInfo.url,url);a.dispose();
});
test('original error propagates when CELIKOM has no valid grant',async()=>{
  const a=create(async()=>null);const {proto}=resource();
  proto.getFileInfo=async()=>{throw new Error('native unavailable')};
  a.attach(proto);a.enable();
  await assert.rejects(()=>proto.getFileInfo({trackId:'123'}),/native unavailable/);a.dispose();
});
test('deadline avoids indefinite native playback stall',async()=>{
  const a=create(async()=>new Promise(resolve=>setTimeout(()=>resolve(grant()),90)),{deadlineMs:20});
  const {proto}=resource();a.attach(proto);a.enable();
  const t=Date.now();const r=await proto.getFileInfo({trackId:'123'});
  assert.equal(r.downloadInfo.url,'https://official.example/native');
  assert.ok(Date.now()-t<85);
  await new Promise(resolve=>setTimeout(resolve,105));
  assert.equal((await proto.getFileInfo({trackId:'123'})).downloadInfo.url,'https://official.example/native');a.dispose();
});
test('Next invalidates previous in-flight track grant',async()=>{
  let release;const a=create(id=>id==='123'
    ? new Promise(resolve=>{release=resolve}) : Promise.resolve(null));
  const {proto}=resource();a.attach(proto);a.enable();
  const first=proto.getFileInfo({trackId:'123'});
  await new Promise(resolve=>setTimeout(resolve,3));
  assert.equal((await proto.getFileInfo({trackId:'456'})).downloadInfo.trackId,'456');
  release(grant('123'));
  assert.equal((await first).downloadInfo.url,'https://official.example/native');a.dispose();
});
test('Stop cancels unresolved grant and preserves native source',async()=>{
  let release;const a=create(()=>new Promise(resolve=>{release=resolve}));
  const {proto}=resource();a.attach(proto);a.enable();
  const first=proto.getFileInfo({trackId:'123'});
  await new Promise(resolve=>setTimeout(resolve,3));a.disable();release(grant());
  assert.equal((await first).downloadInfo.url,'https://official.example/native');a.dispose();
});
test('prefetch enables batch mapping for current exact ID',async()=>{
  const a=create();const {proto,stats}=resource();a.attach(proto);a.enable();
  a.trackChanged('123');assert.equal(await a.prime('123'),true);
  const r=await proto.getFileInfoBatch({trackIds:['123','456']});
  assert.equal(r.downloadInfos[0].url,url);assert.equal(stats.batch,1);a.dispose();
});
test('batch-first playback resolves CELIKOM without requiring single-file event',async()=>{
  let calls=0;const a=create(async()=>{calls++;return grant()});
  const {proto}=resource();a.attach(proto);a.enable();
  const r=await proto.getFileInfoBatch({trackIds:['123']});
  assert.equal(r.downloadInfos[0].url,url);
  assert.equal(r.downloadInfos[0].key,undefined);
  assert.equal(calls,1);a.dispose();
});
test('Next in batch resolves exact future track without changing Yandex queue',async()=>{
  const queried=[];
  const a=create(async id=>{queried.push(id);return grant(id);});
  const {proto}=resource();a.attach(proto);a.enable();
  const r=await proto.getFileInfoBatch({trackIds:['123','456','789']});
  assert.deepEqual(queried,['123','456','789']);
  assert.equal(r.downloadInfos.length,3);
  assert.equal(r.downloadInfos[0].url,url);
  assert.deepEqual(r.downloadInfos.map(x=>x.trackId),['123','456','789']);
  a.dispose();
});
test('batch lookup bounded to three exact ids and never expands arbitrary input',async()=>{
  const queried=[];
  const a=create(async id=>{queried.push(id);return grant(id);});
  const {proto}=resource();a.attach(proto);a.enable();
  await proto.getFileInfoBatch({trackIds:['1','2','3','4','1','bogus']});
  assert.deepEqual(queried,['1','2','3']);
  a.dispose();
});
test('Stop during pending batch reverts to Yandex native batch',async()=>{
  let release;
  const a=create(()=>new Promise(resolve=>{release=resolve;}));
  const {proto}=resource();a.attach(proto);a.enable();
  const pending=proto.getFileInfoBatch({trackIds:['123']});
  await new Promise(resolve=>setTimeout(resolve,3));
  a.disable();
  release(grant('123'));
  const r=await pending;
  assert.equal(r.downloadInfos[0].url,'https://official.example/');
  a.dispose();
});
test('batch timeout preserves original and does not hang Next',async()=>{
  const a=create(()=>new Promise(()=>{}),{deadlineMs:15});
  const {proto}=resource();a.attach(proto);a.enable();
  const started=Date.now();
  const r=await proto.getFileInfoBatch({trackIds:['123']});
  assert.ok(Date.now()-started<100);
  assert.equal(r.downloadInfos[0].url,'https://official.example/');
  a.dispose();
});

test('cleanup restores original resource methods',async()=>{
  const a=create();const {proto}=resource();
  const originalSingle=proto.getFileInfo, originalBatch=proto.getFileInfoBatch;
  a.attach(proto);a.enable();a.dispose();
  assert.equal(proto.getFileInfo,originalSingle);
  assert.equal(proto.getFileInfoBatch,originalBatch);
  assert.throws(()=>a.attach(proto),/W22_UNSUPPORTED_RESOURCE/);
});
test('never maps fuzzy IDs or arbitrary input',async()=>{
  const a=create();const {proto}=resource();a.attach(proto);a.enable();
  for(const id of ['01','x:12','../2','',null]){
    const r=await proto.getFileInfo({trackId:id});
    assert.equal(r.downloadInfo.url,'https://official.example/native');
  }
  a.dispose();
});

test('native source with stalled Yandex file-info resolves from approved grant',async()=>{
  const a=create(async id=>grant(id));const {proto}=resource();
  proto.getFileInfo=()=>new Promise(()=>{});
  a.attach(proto);a.enable();
  const start=Date.now();
  const reply=await proto.getFileInfo({trackId:'123'});
  assert.equal(reply.downloadInfo.url,url);
  assert.equal(reply.responseTime,0);
  assert.equal(reply.url,'');
  assert.equal(reply.downloadInfo.bitrate,320);
  assert.ok(Date.now()-start<450,'approved grant must not stall behind Yandex');
  a.dispose();
});
test('native resource throws; CELIKOM source preserves official response shape',async()=>{
  const a=create();const {proto}=resource();
  proto.getFileInfo=async()=>{throw new Error('unavailable')};
  a.attach(proto);a.enable();
  const info=await proto.getFileInfo({trackId:'123'});
  assert.deepEqual(Object.keys(info).sort(),['downloadInfo','responseTime','url'].sort());
  assert.equal(info.downloadInfo.transport,'raw');
  a.dispose();
});
test('no approved grant never cuts off a slow native Yandex original',async()=>{
  let release;
  const a=create(async()=>null);const {proto}=resource();
  proto.getFileInfo=()=>new Promise(r=>{release=r});
  a.attach(proto);a.enable();
  let settled=false;
  const wait=proto.getFileInfo({trackId:'123'}).then(x=>{settled=true;return x});
  await new Promise(resolve=>setTimeout(resolve,50));
  assert.equal(settled,false);
  const official={downloadInfo:{trackId:'123',url:'https://official.example/native'}};
  release(official);
  assert.deepEqual(await wait,official);
  a.dispose();
});

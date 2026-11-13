import test from 'node:test';
import assert from 'node:assert/strict';
import { createSignedAudioProbe } from './audio-probe.mjs';

const base = 'https://api.celikom.example';
const source = base + '/api/v1/audio/7?token=' + 'a'.repeat(64) + '&expires=1800000180&sid=8';
function setup(fetcher) {
  const events = [];
  const probe = createSignedAudioProbe({
    getOrigin: () => base, fetcher,
    onEvent: (code, id) => events.push([code, id])
  });
  return { events, probe };
}
test('browser-context GET Range verifies signed MP3 bytes and never exports URL or bytes', async () => {
  const calls = [];
  const { events, probe } = setup(async (url, options) => {
    calls.push({ url, options });
    return { status: 206, headers: { get: () => 'audio/mpeg' },
      body: { getReader: () => ({ read: async () => ({
        value: new Uint8Array([0x49,0x44,0x33,0x03]) }),
        cancel: () => Promise.resolve() }) } };
  });
  await probe.run(source,'42498653');
  await probe.run(source,'42498653'); // deduplication
  assert.equal(calls.length,1);
  assert.equal(calls[0].options.headers.Range,'bytes=0-31');
  assert.equal(calls[0].options.credentials,'omit');
  assert.equal(calls[0].options.mode,'cors');
  const codes = events.map(x=>x[0]);
  assert.ok(codes.includes('AUDIO_PROBE_HTTP_PARTIAL'));
  assert.ok(codes.includes('AUDIO_PROBE_MIME_MPEG'));
  assert.ok(codes.includes('AUDIO_PROBE_BYTES_MPTHREE'));
  assert.ok(events.every(x=>x[1]==='42498653'));
  const text = JSON.stringify(events);
  assert.ok(!text.includes('token=') && !text.includes('api.celikom.example') && !text.includes('ID3'));
});
test('fail closed: foreign URL, invalid signature and non-audio routes are never fetched', async () => {
  let count=0;const { events, probe }=setup(async()=>{count++;return{status:206}});
  await probe.run('https://other.example/api/v1/audio/7?token='+'a'.repeat(64)+'&expires=1800000180','1');
  await probe.run(base+'/api/v1/auth/login?token='+'a'.repeat(64)+'&expires=1800000180','2');
  await probe.run(base+'/api/v1/audio/7?token=abc&expires=1800000180','3');
  assert.equal(count,0);assert.equal(events.length,0);
});
test('server 403 is distinguishable from opaque CORS/CSP fetch failure',async()=>{
  const denied=setup(async()=>({status:403}));
  await denied.probe.run(source,'123');
  assert.ok(denied.events.some(x=>x[0]==='AUDIO_PROBE_HTTP_FORBIDDEN'));
  const blocked=setup(async()=>{throw Error('network containing secret token=not_logged')});
  await blocked.probe.run(source,'124');
  assert.ok(blocked.events.some(x=>x[0]==='AUDIO_PROBE_FETCH_BLOCKED'));
  assert.ok(!JSON.stringify(blocked.events).includes('token='));
});
test('HTTPS MP4 positive sniff and MIME checks',async()=>{
  const item=setup(async()=>({status:200,headers:{get:()=> 'audio/mp4; codecs=mp4a.40.2'},
    body:{getReader:()=>({read:async()=>({value:new Uint8Array([0,0,0,24,102,116,121,112])}),cancel:()=>Promise.resolve()})}
  }));
  await item.probe.run(source,'130');
  assert.ok(item.events.some(x=>x[0]==='AUDIO_PROBE_BYTES_MPFOUR'));
  assert.ok(item.events.some(x=>x[0]==='AUDIO_PROBE_MIME_MPFOUR'));
});
test('missing browser fetch is reported without making a network request',async()=>{
  const item=setup(null);
  await item.probe.run(source,'8');
  assert.ok(item.events.some(x=>x[0]==='AUDIO_PROBE_UNAVAILABLE'));
});

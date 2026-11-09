import test from 'node:test';
import assert from 'node:assert/strict';
import {alignObservation,validateObserverSnapshot} from '../analysis/align-observation-core.mjs';
import {parseAlignArgs} from '../analysis/align-observation.mjs';

const observer={
  schema:'celikom-ad-observer-v1',
  ageSeconds:240,
  markers:[{s:80,kind:'normal-music'},{s:120,kind:'ad-heard'},{s:145,kind:'video-ad-seen'}],
  recent:[{url:'https://SHOULD_NOT_BE_EXPORTED.test/?token=SECRET'}]
};
const har={log:{entries:[0,50,90,115].map((sec,index)=>({
  startedDateTime:new Date(Date.UTC(2026,9,20,12,0,0)+sec*1000).toISOString(),
  time:100,request:{url:'https://music.yandex.ru/private?token=SECRET',method:'GET',headers:[
    {name:'Authorization',value:'Bearer SECRET_TOKEN'}]},
  response:{status:index===2?206:200,content:{mimeType:index===2?'audio/mpeg':'application/json'}}
}))}};

test('offset aligns manual marks to HAR local clock while keeping UNKNOWN decision',()=>{
  const output=alignObservation(observer,har,{offsetSeconds:-30,radiusSeconds:4});
  assert.equal(output.decision,'UNKNOWN');
  assert.equal(output.markers.length,3);
  assert.deepEqual(output.markers.map(m=>m.harSecond),[50,90,115]);
  assert.equal(output.markers[1].counts.partial206,1);
  assert.equal(output.markers[0].marker,'normal-music');
  assert.equal(output.radiusSeconds,4);
});

test('sanitizer strips full links, token, request path, observation metadata',()=>{
  const report=alignObservation(observer,har,{offsetSeconds:-30});
  const text=JSON.stringify(report);
  for(const secret of ['SECRET','SHOULD_NOT_BE_EXPORTED','music.yandex.ru','Authorization','Bearer','/private']) {
    assert.equal(text.includes(secret),false,secret);
  }
});

test('reject forged marker, invalid times, missing offset and too many entries',()=>{
  assert.throws(()=>alignObservation(observer,har));
  assert.throws(()=>alignObservation(observer,har,{offsetSeconds:'-30'}));
  assert.throws(()=>alignObservation(observer,har,{offsetSeconds:100000}));
  assert.throws(()=>alignObservation(observer,har,{offsetSeconds:-121,radiusSeconds:0}));
  assert.throws(()=>validateObserverSnapshot({...observer,markers:[{kind:'SECRET',s:3}]}));
  assert.throws(()=>validateObserverSnapshot({...observer,markers:[{kind:'ad-heard',s:Infinity}]}));
  assert.throws(()=>validateObserverSnapshot({...observer,markers:[{kind:'ad-heard',s:-1}]}));
  assert.throws(()=>validateObserverSnapshot({...observer,markers:[{kind:'ad-heard',s:241},{kind:'ad-heard',s:2}]}));
  assert.throws(()=>validateObserverSnapshot({...observer,markers:Array(25).fill({kind:'ad-heard',s:3})}));
});

test('no label string or arbitrary user-controlled text enters report',()=>{
  const modified={...observer,markers:[{s:5,kind:'ad-heard',note:'very private email@example.com'}],ageSeconds:10};
  const out=JSON.stringify(alignObservation(modified,har,{offsetSeconds:0}));
  assert.equal(out.includes('email@example.com'),false);
});

test('CLI requires intentional explicit anchor offset and local JSON inputs',()=>{
  const args=parseAlignArgs(['observer.json','session.har','--offset=-30','--radius=4']);
  assert.equal(args.offsetSeconds,-30);
  assert.equal(args.radiusSeconds,4);
  for(const a of [
    ['observer.json','session.har'],['observer.json','session.har','--offset=abc'],
    ['observer.json','session.har','--offset=Infinity'],['observer.json','session.har','--offset=20','--radius=121'],
    ['--offset=0','session.har','observer.json']
  ])assert.throws(()=>parseAlignArgs(a));
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {assessAudioSafety} from '../analysis/audio-safety.mjs';
import {correlateCaptures} from '../analysis/evidence-correlation.mjs';
const base=Date.parse('2026-10-20T12:00:00Z');
function event(t,url,status=200,mime='application/json'){
 return {startedDateTime:new Date(base+t*1000).toISOString(),request:{url,method:'GET',headers:status===206?[{name:'Range',value:'bytes=0-19'}]:[]},response:{status,content:{mimeType:mime}}};
}
const music='https://music.yandex.ru/music?priv=redacted';
const candidate='https://example.invalid/aud?priv=redacted';
function capture(role,url,status=200,mime='application/json'){
 return {role,markers:[20],har:{log:{entries:[event(0,music),event(20,url,status,mime)]}}};
}
function inspect(captures){return assessAudioSafety(correlateCaptures(captures,{key:Buffer.alloc(32,8),radiusSeconds:2}));}
test('even repeated separate ad candidates never authorize blocking',()=>{
 const r=inspect([capture('ad',candidate),capture('ad',candidate),capture('normal',music),capture('normal',music)]);
 assert.equal(r.gate,'HOLD');assert.equal(r.blockingAllowed,false);assert.equal(r.rulesProposed,0);
 assert.equal(r.observations.differentialCandidates,1);
});
test('audio 206 and Range requests explicitly raise playback risk',()=>{
 const r=inspect([capture('ad',candidate,206,'audio/mpeg'),capture('ad',candidate,206,'audio/mpeg'),capture('normal',music)]);
 assert.equal(r.observations.mediaRangeRisk,1);
 assert.ok(r.reasons.some(x=>x.includes('Range')));
 assert.ok(r.reasons.some(x=>x.includes('normal playback controls')));
});
test('shared music endpoint in ad and control is ambiguous',()=>{
 const r=inspect([capture('ad',music),capture('ad',music),capture('normal',music),capture('normal',music)]);
 assert.equal(r.observations.differentialCandidates,0);
 assert.equal(r.observations.ordinaryOverlap,1);
 assert.equal(r.rulesProposed,0);
});
test('forged inputs and missing safety fields are rejected',()=>{
 assert.throws(()=>assessAudioSafety({}));
 assert.throws(()=>assessAudioSafety({schema:'celikom-local-differential-v1',decision:'GO',groups:[],input:{adCaptures:2,normalCaptures:2}}));
 assert.throws(()=>assessAudioSafety({schema:'celikom-local-differential-v1',decision:'UNKNOWN',groups:[{forbiddenForBlocking:true}],input:{adCaptures:2,normalCaptures:2}}));
});
test('safety assessment never includes raw URIs or original metadata',()=>{
 const result=inspect([capture('ad',candidate),capture('ad',candidate),capture('normal',music)]);
 const text=JSON.stringify(result);
 for(const term of ['example.invalid','music.yandex.ru','priv=','/aud?'])assert.equal(text.includes(term),false,term);
});

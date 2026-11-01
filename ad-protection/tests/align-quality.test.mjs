import test from 'node:test';
import assert from 'node:assert/strict';
import {alignObservation} from '../analysis/align-observation-core.mjs';
const base=Date.parse('2026-10-20T12:00:00Z');
function entry(sec,status){
 return {startedDateTime:new Date(base+sec*1000).toISOString(),
 request:{method:'GET',url:'https://example.invalid/media?private=redacted',headers:[]},
 response:{status,content:{mimeType:'audio/mpeg'}}};
}
test('manual clock offsets cannot turn empty windows into ad evidence',()=>{
 const obs={schema:'celikom-ad-observer-v1',ageSeconds:130,markers:[{kind:'ad-heard',s:10},{kind:'ad-heard',s:120}]};
 const har={log:{entries:[entry(0,200),entry(120,206)]}};
 const result=alignObservation(obs,har,{offsetSeconds:0,radiusSeconds:2});
 assert.equal(result.alignmentQuality.emptyWindows,1);
 assert.equal(result.alignmentQuality.partialContentWindows,1);
 assert.equal(result.alignmentQuality.requestCorrelationProvesAdvertising,false);
 assert.equal(result.alignmentQuality.synchronization,'manual-offset-not-independently-verified');
 assert.equal(result.decision,'UNKNOWN');
 assert.equal(JSON.stringify(result).includes('private=redacted'),false);
});

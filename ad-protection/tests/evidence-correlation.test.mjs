import test from 'node:test';
import assert from 'node:assert/strict';
import {correlateCaptures} from '../analysis/evidence-correlation.mjs';
import {parseCompareArgs} from '../analysis/compare-har.mjs';

function har(rows) {
 const stamp=Date.parse('2026-10-20T12:00:00Z');
 return {log:{entries: rows.map(([second,url,mime='application/json',status=200],i)=>({
    startedDateTime:new Date(stamp+second*1000).toISOString(),
    request:{url,method:'GET',headers:status===206?[{name:'Range',value:'bytes=0-9'}]:[]},
    response:{status,content:{mimeType:mime},headers:[{name:'Set-Cookie',value:'very-private-secret'}]},
    _resourceType:mime.startsWith('audio/')?'media':'fetch'
 }))}};
}
const adurl='https://media.yandex.net/observed?token=TOPSECRET&sig=PRIVATE';
const ordinary='https://music.yandex.ru/api/song?auth=PRIVATE';
const samples=[
{role:'ad',markers:[10],har:har([[0,ordinary],[10,adurl,'audio/mpeg',206]])},
{role:'ad',markers:[11],har:har([[0,ordinary],[11,adurl,'audio/mpeg',206]])},
{role:'normal',markers:[10],har:har([[0,ordinary],[10,ordinary,'application/json',200]])}
];

test('comparing two possible ad windows with negative controls is still not proof',()=>{
 const output=correlateCaptures(samples,{radiusSeconds:3,key:Buffer.from('a'.repeat(32))});
 assert.equal(output.decision,'UNKNOWN');
 assert.equal(output.input.adCaptures,2);
 assert.equal(output.input.normalCaptures,1);
 const candidate=output.groups.find(g=>g.adCaptures===2);
 assert.equal(candidate.adRequests,2);
 assert.equal(candidate.normalRequests,0);
 assert.equal(candidate.evidenceHint,'differential-candidate-only');
 assert.equal(candidate.forbiddenForBlocking,true);
 assert.equal(candidate.partial206Requests,2);
});

test('no raw host, path, signed URL, token, cookie, credentials or hash key survives',()=>{
 const secret=Buffer.from('something-private-salt-for-testing!');
 const text=JSON.stringify(correlateCaptures(samples,{radiusSeconds:3,key:secret}));
 for(const s of ['TOPSECRET','PRIVATE','very-private','media.yandex.net','music.yandex.ru','/observed','/song','sig=','token=','something-private-salt']) assert.equal(text.includes(s),false,s);
 assert.match(text,/"fingerprint":"[0-9a-f]{16}"/);
});

test('fresh salt yields different identities but identical safe statistics',()=>{
 const a=correlateCaptures(samples,{key:Buffer.from('a'.repeat(32))});
 const b=correlateCaptures(samples,{key:Buffer.from('b'.repeat(32))});
 assert.notEqual(a.groups[0].fingerprint,b.groups[0].fingerprint);
 assert.deepEqual(a.input,b.input);
});

test('input constraints and corrupt HAR rejection',()=>{
 assert.throws(()=>correlateCaptures([{role:'ad',markers:[1],har:har([])}]));
 assert.throws(()=>correlateCaptures([{role:'ad',markers:[1],har:har([])},{role:'normal',markers:[1],har:{}}]));
 assert.throws(()=>correlateCaptures(samples,{radiusSeconds:0}));
 assert.throws(()=>correlateCaptures(samples,{radiusSeconds:100}));
 assert.throws(()=>correlateCaptures([...samples.slice(0,2),{role:'normal',markers:[-1],har:har([])}]));
 assert.throws(()=>correlateCaptures([...samples.slice(0,2),{role:'other',markers:[1],har:har([])}]));
});

test('CLI parses two classes and rejects ambiguous/malformed marker inputs',()=>{
 const p=parseCompareArgs(['--ad=ad.har@12','--normal=normal.har@19.5','--radius=8']);
 assert.equal(p.samples.length,2); assert.equal(p.radiusSeconds,8);
 assert.deepEqual(p.samples.map(s=>s.role),['ad','normal']);
 for(const args of [['--ad=a.har@3'],['--ad=a.har@-5','--normal=b.har@2'],['--normal=b.har@a','--ad=a.har@3'],['--bad=x'],['--radius=500']]) assert.throws(()=>parseCompareArgs(args));
});

test('overlapping markers never duplicate a request in the same capture',()=>{
 const samples2=[
   {role:'ad',markers:[10,11],har:har([[0,ordinary],[10,adurl,'audio/mpeg']])},
   {role:'normal',markers:[30],har:har([[0,ordinary],[30,ordinary]])}
 ];
 const out=correlateCaptures(samples2,{radiusSeconds:3,key:Buffer.alloc(32,4)});
 const g=out.groups.find(g=>g.adRequests>0);
 assert.equal(g.adRequests,1);
 assert.equal(out.input.selectedEvents,2);
});

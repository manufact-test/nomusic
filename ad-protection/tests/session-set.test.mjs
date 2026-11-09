import test from 'node:test';
import assert from 'node:assert/strict';
import {assessSessionSet,parseSessionArgs,runSessionSet} from '../analysis/assess-session-set.mjs';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';

function observation(marks,overrides={}) {
  const media=Object.fromEntries(['audio','video'].map(kind=>
    [kind,Object.fromEntries(['play','playing','pause','ended','waiting','stalled','error'].map(event=>[event,0]))]));
  return {schema:'celikom-ad-observer-v1',ageSeconds:80,droppedRoots:0,
    candidates:{banner:0,overlay:0,video:0,audio:0},media,
    markers:marks.map((kind,i)=>({s:10+i*5,kind})),recent:[],...overrides};
}
function cap(role,marks,overrides={}) {return {role,report:observation(marks,overrides)};}

test('two audio-ad observations and two clean ordinary controls reach manual comparison only, never GO',()=>{
  const result=assessSessionSet([
    cap('ad',['ad-heard']),cap('ad',['normal-music','ad-heard']),
    cap('normal',['normal-music']),cap('normal',['normal-music'])]);
  assert.equal(result.summary.minimumManualAudioComparison,true);
  assert.equal(result.summary.cleanAudioAdSessions,2);
  assert.equal(result.summary.cleanNormalSessions,2);
  assert.equal(result.gate,'HOLD');
  assert.equal(result.blockingAllowed,false);
  assert.equal(result.decision,'UNKNOWN');
});

test('dropped DOM roots, filled marker history and contaminated negatives block clean evidence',()=>{
  const result=assessSessionSet([
    cap('ad',['ad-heard'],{droppedRoots:5}),
    cap('normal',['normal-music','ad-heard']),
    cap('ad',Array(20).fill('ad-heard'),{ageSeconds:200}),
    cap('normal',['normal-music'])]);
  assert.equal(result.summary.minimumManualAudioComparison,false);
  assert.equal(result.summary.cleanAudioAdSessions,0);
  assert.deepEqual(result.sessions[0].issues,['dropped-dom-roots']);
  assert.ok(result.sessions[1].issues.includes('ad-mark-in-negative-control'));
  assert.ok(result.sessions[2].issues.includes('marker-cap-reached'));
});

test('candidate CSS and media events cannot be mistaken for a witnessed advertisement',()=>{
  const result=assessSessionSet([
    cap('ad',[],{candidates:{banner:99,overlay:0,video:0,audio:99}}),
    cap('normal',['normal-music'])]);
  assert.equal(result.summary.cleanAudioAdSessions,0);
  assert.ok(result.sessions[0].issues.includes('missing-manual-ad-mark'));
});

test('strict validation rejects marker tampering, wrong counters and malformed input',()=>{
  assert.throws(()=>assessSessionSet([cap('ad',["SECRET_TOKEN"]),cap('normal',['normal-music'])]));
  assert.throws(()=>assessSessionSet([cap('ad',['ad-heard'],{droppedRoots:-1}),cap('normal',['normal-music'])]));
  assert.throws(()=>assessSessionSet([cap('ad',['ad-heard'],{ageSeconds:1}),cap('normal',['normal-music'])]));
  assert.throws(()=>assessSessionSet([cap('ad',['ad-heard'],{media:{}}),cap('normal',['normal-music'])]));
  assert.throws(()=>assessSessionSet([cap('normal',['normal-music']),cap('normal',['normal-music'])]));
  assert.throws(()=>parseSessionArgs(['https://example.com','--ad=x.json']));
});

test('CLI uses only local JSON, outputs aggregated allowlisted fields and never account details',async()=>{
  const dir=await mkdtemp(path.join(tmpdir(),'ad-triage-'));
  try {
    const ad=path.join(dir,'ad.json'),normal=path.join(dir,'normal.json');
    await writeFile(ad,JSON.stringify(observation(['ad-heard'],{accountToken:'HIDDEN_TOKEN',markers:[{s:15,kind:'ad-heard',url:'HIDDEN_URL'}]})));
    await writeFile(normal,JSON.stringify(observation(['normal-music'])));
    const chunks=[];
    const original=process.stdout.write;
    process.stdout.write=(s)=>{chunks.push(s);return true;};
    let result;
    try {result=await runSessionSet(['--ad='+ad,'--normal='+normal]);}
    finally {process.stdout.write=original;}
    assert.equal(result.gate,'HOLD');
    assert.ok(chunks.join('').includes('celikom-session-set-triage-v1'));
    for(const secret of ['HIDDEN_TOKEN','HIDDEN_URL',dir])
      assert.equal(chunks.join('').includes(secret),false);
  } finally {await rm(dir,{recursive:true,force:true});}
});

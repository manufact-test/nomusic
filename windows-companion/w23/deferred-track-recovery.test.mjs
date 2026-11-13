import test from 'node:test';
import assert from 'node:assert/strict';
import {createDeferredTrackRecovery} from './deferred-track-recovery.mjs';
const KISHLAK='102494056';
const OTHER='59633283';
test('W77: exact Kishlak preload misses while another song plays; recovers only when observed current',()=>{
 let now=1000,current=OTHER,enabled=true;
 const calls=[],events=[];
 const handoff=createDeferredTrackRecovery({
   currentTrackId:()=>current,active:()=>enabled,
   schedule:id=>{calls.push(id);return true;},
   now:()=>now,onEvent:(code,id)=>events.push([code,id])
 });
 assert.equal(handoff.record(KISHLAK),true);
 assert.equal(handoff.record(KISHLAK),false,'duplicate 1s timeout and transient have one candidate');
 assert.equal(handoff.check(),false);
 assert.deepEqual(calls,[],'never reload a preloaded non-current Kishlak');
 now+=110000;
 current=KISHLAK;
 assert.equal(handoff.check(),true,'start of actual Kishlak raises bounded recovery');
 assert.deepEqual(calls,[KISHLAK]);
 assert.equal(handoff.check(),false,'status polls cannot retry same timeout forever');
 assert.equal(handoff.candidateCount,0);
 assert.ok(events.some(x=>x[0]==='SOURCE_DEFERRED_PROMOTED'&&x[1]===KISHLAK));
});
test('W77: stopped, logged out or different audio never plays queued candidate',()=>{
 let enabled=true,current=OTHER;
 const calls=[];
 const handoff=createDeferredTrackRecovery({
   currentTrackId:()=>current,active:()=>enabled,
   schedule:id=>{calls.push(id);return true;}
 });
 handoff.record(KISHLAK);enabled=false;
 assert.equal(handoff.check(),false);
 handoff.cancel();enabled=true;current=KISHLAK;
 assert.equal(handoff.check(),false);
 assert.deepEqual(calls,[]);
});
test('W77: 12-minute TTL, max 12 candidates and no synthetic IDs',()=>{
 let now=1000,current=KISHLAK,calls=[];
 const handoff=createDeferredTrackRecovery({
   currentTrackId:()=>current,active:()=>true,
   schedule:id=>{calls.push(id);return true;},now:()=>now,
   ttlMs:120000,maxCandidates:2
 });
 assert.equal(handoff.record('../bad'),false);
 handoff.record(KISHLAK);handoff.record(OTHER);handoff.record('126749933');
 assert.equal(handoff.candidateCount,2);
 assert.equal(handoff.check(),false,'bounded map evicts oldest candidate');
 now+=120001;current=OTHER;
 assert.equal(handoff.check(),false,'expired candidate never triggers reload');
 assert.deepEqual(calls,[]);
});
test('W77: negative catalog response never gets recorded as a transient miss',()=>{
 const handoff=createDeferredTrackRecovery({
   currentTrackId:()=>KISHLAK,active:()=>true,
   schedule:()=>{throw Error('a 404 must not be promoted');}
 });
 assert.equal(handoff.candidateCount,0);
 assert.equal(handoff.check(),false);
});

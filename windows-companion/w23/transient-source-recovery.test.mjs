import test from "node:test";
import assert from "node:assert/strict";
import { createTransientSourceRecovery } from "./transient-source-recovery.mjs";

const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

test("W76: 13 KARAT Ty id=106040459 recovers after one local HTTP timeout", async () => {
  let current="106040459", active=true, tries=0, reloads=0;
  const events=[];
  const recovery=createTransientSourceRecovery({
    active:()=>active,
    currentTrackId:()=>current,
    prime:async id=>{ assert.equal(id,"106040459"); tries++; return tries===2; },
    reload:async()=>{ reloads++; return true; },
    onEvent:(code,id)=>events.push([code,id]),
    delays:[2,2]
  });
  assert.equal(recovery.schedule("106040459"),true);
  assert.equal(recovery.schedule("106040459"),false,"duplicate local misses dedupe");
  await pause(50);
  assert.equal(tries,2);
  assert.equal(reloads,1,"Yandex source refresh exactly once");
  assert.equal(recovery.pendingCount,0);
  assert.ok(events.some(x=>x[0]==="SOURCE_RECOVERY_RELOAD_OK"&&x[1]==="106040459"));
});

test("W96: verified decoder cancels pending redundant 403 reload before it can pop",async()=>{
  const events=[], id="40371622";
  let primeCalls=0, reloadCalls=0;
  const recovery=createTransientSourceRecovery({
    active:()=>true,currentTrackId:()=>id,
    prime:async()=>{primeCalls++;return true;},
    reload:async()=>{reloadCalls++;return true;},
    delays:[45],onEvent:(code,track)=>events.push([code,track])
  });
  assert.equal(recovery.schedule(id),true);
  assert.equal(recovery.confirmedCurrentSource(id),true);
  assert.equal(recovery.pendingCount,0);
  assert.equal(recovery.confirmedCurrentSource(id),false);
  await pause(90);
  assert.equal(primeCalls,0);
  assert.equal(reloadCalls,0);
  assert.ok(events.some(([code,track])=>code==="SOURCE_RECOVERY_DECODER_ALREADY_PLAYING"&&track===id));
});
test("W96: wrong or stale decoder proof cannot stop actual recovery",async()=>{
  let current="89285816", calls=0;
  const recovery=createTransientSourceRecovery({
    active:()=>true,currentTrackId:()=>current,
    prime:async()=>{calls++;return true;},
    reload:async()=>true, delays:[10]
  });
  assert.equal(recovery.schedule(current),true);
  assert.equal(recovery.confirmedCurrentSource("40371622"),false);
  current="109";
  assert.equal(recovery.confirmedCurrentSource("89285816"),false);
  await pause(30);
  assert.equal(calls,0,"do not fetch or reload for switched-away tracks");
});
test("W99: verified source cancels a retry while its fresh grant is resolving",async()=>{
  let started, finish, reloads=0;
  const entered=new Promise(resolve=>started=resolve);
  const recovery=createTransientSourceRecovery({
    active:()=>true,currentTrackId:()=>"40371622",
    prime:()=>{started();return new Promise(resolve=>{finish=resolve})},
    reload:async()=>{reloads++;return true;},delays:[1]
  });
  recovery.schedule("40371622");
  await entered;
  assert.equal(recovery.confirmedCurrentSource("40371622"),true);
  finish(true);
  await pause(10);
  assert.equal(reloads,0,"confirmed current decoder must not be reloaded a second time");
  assert.equal(recovery.pendingCount,0);
});
test("W99: verified source cannot interrupt a reload that already started",async()=>{
  let started, finish, reloads=0;
  const entered=new Promise(resolve=>started=resolve);
  const recovery=createTransientSourceRecovery({
    active:()=>true,currentTrackId:()=>"40371622",
    prime:async()=>true,
    reload:()=>{reloads++;started();return new Promise(resolve=>{finish=resolve})},
    delays:[1]
  });
  recovery.schedule("40371622");
  await entered;
  assert.equal(recovery.confirmedCurrentSource("40371622"),false);
  finish(true);
  await pause(10);
  assert.equal(reloads,1);
  assert.equal(recovery.pendingCount,0);
});

test("W76: no source reload if user switched songs before delayed retry",async()=>{
  let current="106040459", calls=0;
  const recovery=createTransientSourceRecovery({
    active:()=>true,currentTrackId:()=>current,
    prime:async()=>{calls++;return true;},
    reload:async()=>{throw Error("wrong song reload");},
    delays:[8]
  });
  assert.equal(recovery.schedule(current),true);
  current="27323616";
  await pause(35);
  assert.equal(calls,0);
  assert.equal(recovery.pendingCount,0);
});
test("W76: no reload after Stop, logout or route invalidation while resolving",async()=>{
  let active=true, finish;
  let reloads=0;
  const recovery=createTransientSourceRecovery({
    active:()=>active,currentTrackId:()=> "106040459",
    prime:()=>new Promise(resolve=>{finish=resolve;}),
    reload:async()=>{reloads++;return true;},
    delays:[2]
  });
  recovery.schedule("106040459");
  await pause(15);
  active=false;
  recovery.cancel();
  finish(true);
  await pause(10);
  assert.equal(reloads,0);
  assert.equal(recovery.pendingCount,0);
});
test("W76: absent replacement never schedules recovery by itself",async()=>{
  let reloads=0;
  const recovery=createTransientSourceRecovery({
    active:()=>true,currentTrackId:()=> "106040459",
    prime:async()=>{throw Error("no request expected");},
    reload:async()=>{reloads++;return true;}
  });
  assert.equal(recovery.schedule("not-a-track"),false);
  assert.equal(recovery.pendingCount,0);
  assert.equal(reloads,0);
});
test("W76: at most two retry attempts after sustained network outage",async()=>{
  let attempts=0;
  const events=[];
  const recovery=createTransientSourceRecovery({
    active:()=>true,currentTrackId:()=> "106040459",
    prime:async()=>{attempts++;return false;},
    reload:async()=>{throw Error("must not reload");},
    onEvent:(code)=>events.push(code),delays:[1,1]
  });
  recovery.schedule("106040459");
  await pause(30);
  assert.equal(attempts,2);
  assert.ok(events.includes("SOURCE_RECOVERY_EXHAUSTED"));
  assert.equal(recovery.pendingCount,0);
});

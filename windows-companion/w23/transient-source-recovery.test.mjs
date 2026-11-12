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

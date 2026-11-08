import { test } from "node:test";
import assert from "node:assert/strict";
import { createNativeOriginalRecovery } from "./native-original-recovery.mjs";

const original = id => ({ trackId: String(id), codec: "mp3", transport: "raw",
  url: "https://synthetic.invalid/original/" + id });
function setup(hooks={}) {
  const state={originalCalled:0,stopCalled:0,applied:0,events:[]};
  const bridge={original(){state.originalCalled++;state.events.push("gate");},
    stop(){state.stopCalled++;}};
  const rec=createNativeOriginalRecovery({
    sourceGate:bridge,
    reacquireOriginal: async id=>{
      state.events.push("resolve");
      if(hooks.resolve) return hooks.resolve(id);
      return original(id);
    },
    applyToSameDecoder: async options=>{
      state.events.push("apply");
      if(hooks.apply)return hooks.apply(options);
      state.applied++;return options.isCurrent();
    }
  });
  rec.setTrack("1001");
  return {state,rec};
}
const state={positionSec:17.25,wasPlaying:true};

test("W8 one successful one-decoder recovery preserves exact position/play", async()=>{
  const {rec,state:s}=setup({
    apply:async ({original:info,snapshot,isCurrent})=>{
      assert.equal(info.trackId,"1001");assert.deepEqual(snapshot,state);
      assert.equal(isCurrent(),true);return true;
    }
  });
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"RESTORED_ORIGINAL");
  assert.deepEqual(s.events,["gate","resolve","apply"]);
  assert.equal(rec.diagnostics().successful,1);
});

test("W8 duplicate same-track events cannot retry failed decoder",async()=>{
  const {rec,state:s}=setup();
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"RESTORED_ORIGINAL");
  rec.setTrack("1001");
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"ALREADY_ATTEMPTED");
  assert.equal(s.originalCalled,1);assert.equal(s.applied,1);
});

test("W8 new real track permits new recovery only for that ID",async()=>{
  const {rec,state:s}=setup();
  await rec.onNativeDecodeError("1001",state);
  rec.setTrack("2002");
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"STALE_TRACK");
  assert.equal((await rec.onNativeDecodeError("2002",{positionSec:4,wasPlaying:false})).status,"RESTORED_ORIGINAL");
  assert.equal(s.originalCalled,2);
});

test("W8 never runs on arbitrary ID or invalid seek snapshot",async()=>{
  const {rec,state:s}=setup();
  for(const wrong of ["999","abc","","111111111111111111111111"])
    assert.equal((await rec.onNativeDecodeError(wrong,state)).status,"STALE_TRACK");
  for(const invalid of [{positionSec:-1,wasPlaying:true},{positionSec:Infinity,wasPlaying:true},
    {positionSec:0,wasPlaying:1},{positionSec:9000,wasPlaying:false}])
    assert.equal((await rec.onNativeDecodeError("1001",invalid)).status,"INVALID_SNAPSHOT");
  assert.equal(s.originalCalled,0);assert.equal(s.applied,0);
});

test("W8 source returns wrong track -- refuse to load it",async()=>{
  const {rec,state:s}=setup({resolve:async()=>original("2002")});
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"INVALID_ORIGINAL_DESCRIPTOR");
  assert.equal(s.applied,0);assert.equal(rec.diagnostics().failures,1);
});

test("W8 original fetch rejection is a hard stop, not an invented success",async()=>{
  const {rec,state:s}=setup({resolve:async()=>{throw Error("synthetic original unavailable");}});
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"RESTORE_FAILED");
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"ALREADY_ATTEMPTED");
  assert.equal(s.applied,0);assert.equal(s.originalCalled,1);
});

test("W8 decoder assignment rejection is a hard stop without loops",async()=>{
  const {rec,state:s}=setup({apply:async()=>{throw Error("synthetic decoder fault");}});
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"RESTORE_FAILED");
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"ALREADY_ATTEMPTED");
  assert.equal(s.originalCalled,1);
});

test("W8 Next during delayed original resolution never stomps new track",async()=>{
  let finish;const wait=new Promise(ok=>{finish=ok;});
  const {rec,state:s}=setup({resolve:async id=>{await wait;return original(id);}});
  const pending=rec.onNativeDecodeError("1001",state);
  rec.setTrack("2002");finish();
  assert.equal((await pending).status,"STALE_TRACK");
  assert.equal(s.applied,0);
});

test("W8 stopped during pending recovery never changes native source",async()=>{
  let finish;const wait=new Promise(ok=>{finish=ok;});
  const {rec,state:s}=setup({resolve:async id=>{await wait;return original(id);}});
  const pending=rec.onNativeDecodeError("1001",state);
  rec.stop();finish();
  assert.equal((await pending).status,"STALE_TRACK");
  assert.equal(s.applied,0);assert.equal(s.stopCalled,1);
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"STOPPED");
});

test("W8 disposed during recovery never restarts old track",async()=>{
  let finish;const wait=new Promise(ok=>{finish=ok;});
  const {rec,state:s}=setup({resolve:async id=>{await wait;return original(id);}});
  const pending=rec.onNativeDecodeError("1001",state);
  rec.dispose();finish();
  assert.equal((await pending).status,"STALE_TRACK");
  assert.equal(s.applied,0);
  assert.equal((await rec.onNativeDecodeError("1001",state)).status,"DISPOSED");
});

test("W8 decoder callback sees freshness guard",async()=>{
  let finish,signalEntered;const wait=new Promise(ok=>{finish=ok;});
  const entered=new Promise(ok=>{signalEntered=ok;});
  let guardWasFresh=true;
  const {rec}=setup({apply:async({isCurrent})=>{
    signalEntered();
    await wait;guardWasFresh=isCurrent();return guardWasFresh;}});
  const pending=rec.onNativeDecodeError("1001",state);
  await entered; // ensure source assignment callback is already in flight
  rec.setTrack("2002");finish();
  assert.equal((await pending).status,"STALE_TRACK");
  assert.equal(guardWasFresh,false);
});

test("W8 diagnostics contains no media URL or account data",async()=>{
  const {rec}=setup();
  await rec.onNativeDecodeError("1001",state);
  const diagnostic=JSON.stringify(rec.diagnostics());
  assert.equal(diagnostic.includes("synthetic.invalid"),false);
  assert.equal(diagnostic.includes("1001"),false);
  assert.equal(diagnostic.includes("token"),false);
});

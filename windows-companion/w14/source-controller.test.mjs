import test from "node:test";
import assert from "node:assert/strict";
import { exactTrackId, validateCelikomGrant, createCelikomSourceController } from "./source-controller.mjs";
const ORIGIN = "https://celikom.example";
const NOW = 1794168000000;
const grant = id => ({
  trackId:id, approved:true, entitled:true, expiresAt:NOW+120000,
  audioUrl: ORIGIN + "/api/v1/audio/approved_123?token=abcDEF0123456789_abcdef&expires=1794168120"
});
const tick = () => new Promise(r=>setImmediate(r));
function fixture(resolve = async id => grant(id), initial = {id:"123"}) {
  let watch = () => {};
  const calls = [];
  const api = {
    signal: new AbortController().signal,
    player: {
      getSnapshot:async () => ({track:initial}),
      onTrackChange:fn => {watch=fn;return () => {watch=()=>{}};}
    },
    client: {
      clearTrackReplacements:async ()=>{calls.push(["clear"]);},
      setTrackReplacements:async map=>{calls.push(["set",map]);}
    }
  };
  const controller = createCelikomSourceController({api,resolve,allowedOrigin:ORIGIN,now:()=>NOW});
  return {api,controller,calls,change:track=>watch(track)};
}
test("exact ID: never guess from song name or fuzzy ID",()=>{
  assert.equal(exactTrackId({id:123}),"123");
  assert.equal(exactTrackId({id:"123:456"}),"123:456");
  assert.equal(exactTrackId({title:"A",artist:"B"}),null);
  for(const id of ["foo","00123","../42","1?token=abc",1.1,NaN,0])
    assert.equal(exactTrackId({id}),null);
});
test("signed grant: exact ID, entitlement and approved required",()=>{
  assert.equal(validateCelikomGrant(grant("123"),"123",ORIGIN,NOW)?.startsWith(ORIGIN),true);
  for(const patch of [
    {trackId:"other"},{approved:false},{entitled:false},{expiresAt:NOW-10},
    {expiresAt:NOW+1000},{expiresAt:NOW+10000000},{audioUrl:"http://celikom.example/api/v1/audio/a?token=abcDEF0123456789_abcdef&expires=1794168120"},
    {audioUrl:"https://evil.example/api/v1/audio/a?token=abcDEF0123456789_abcdef&expires=1794168120"},
    {audioUrl:"https://celikom.example.evil.com/api/v1/audio/a?token=abcDEF0123456789_abcdef&expires=1794168120"},
    {audioUrl:"https://celikom.example@evil.example/api/v1/audio/a?token=abcDEF0123456789_abcdef&expires=1794168120"},
    {audioUrl:"https://celikom.example/redirect?token=abcDEF0123456789_abcdef&expires=1794168120"},
    {audioUrl:"https://celikom.example/api/v1/audio/a?token=abcDEF0123456789_abcdef&expires=1794168120&next=http://evil.example"}
  ]) assert.equal(validateCelikomGrant({...grant("123"),...patch},"123",ORIGIN,NOW),null,JSON.stringify(patch));
});
test("fail closed when SDK or resolver is missing",()=>{
  assert.throws(()=>createCelikomSourceController({api:{},resolve:()=>{},allowedOrigin:ORIGIN}),/UNSUPPORTED/);
});
test("off by default, SDK receives exactly ONE map and no second player",async()=>{
  const x=fixture();
  await x.controller.start();
  assert.equal(x.calls.some(c=>c[0]==="set"),false);
  x.controller.enable();
  await x.controller.flush();
  assert.deepEqual(x.calls.filter(c=>c[0]==="set").map(c=>Object.keys(c[1])),[["123"]]);
  assert.equal(x.controller.status,"REPLACEMENT_SET");
  await x.controller.dispose();
  assert.equal(x.calls.at(-1)[0],"clear");
});
test("unknown track remains original",async()=>{
  const x=fixture(async()=>null);
  await x.controller.start();x.controller.enable();await x.controller.flush();
  assert.equal(x.calls.some(c=>c[0]==="set"),false);
  assert.equal(x.controller.status,"ORIGINAL");
  await x.controller.dispose();
});
test("Next cancels delayed stale resolve, only new exact song is hooked",async()=>{
  let release;
  const slow = new Promise(r=>{release=r});
  const x=fixture(async id=>id==="123"?slow:grant(id));
  await x.controller.start();
  x.controller.enable();
  await tick();
  x.change({id:"234"});
  release(grant("123"));
  await tick();await x.controller.flush();
  const sets=x.calls.filter(c=>c[0]==="set");
  assert.deepEqual(sets.map(c=>Object.keys(c[1])),[["234"]]);
  await x.controller.dispose();
});
test("Original persists for SAME song, next track re-arms",async()=>{
  const x=fixture();
  await x.controller.start();x.controller.enable();await x.controller.flush();
  x.controller.original(); await x.controller.flush();
  const before=x.calls.filter(c=>c[0]==="set").length;
  x.change({id:"123"});await x.controller.flush();
  assert.equal(x.calls.filter(c=>c[0]==="set").length,before);
  x.change({id:"234"});await x.controller.flush();
  assert.equal(x.calls.filter(c=>c[0]==="set").length,before+1);
  await x.controller.dispose();
});
test("Stop clears source even when resolver is pending",async()=>{
  let release;
  const slow=new Promise(r=>{release=r});
  const x=fixture(async()=>slow);
  await x.controller.start();x.controller.enable();await tick();
  x.controller.disable();release(grant("123"));
  await x.controller.flush();
  assert.equal(x.calls.some(c=>c[0]==="set"),false);
  assert.equal(x.calls.at(-1)[0],"clear");
  await x.controller.dispose();
});
test("unsupported entitlement and expired links never set replacement",async()=>{
  const x=fixture(async id=>({...grant(id), entitled:false}));
  await x.controller.start();x.controller.enable();await x.controller.flush();
  assert.equal(x.calls.some(c=>c[0]==="set"),false);
  await x.controller.dispose();
});
test("cleanup/abort cannot write late replacement",async()=>{
  let release;
  const slow=new Promise(r=>{release=r});
  const x=fixture(async()=>slow);
  await x.controller.start();x.controller.enable();await tick();
  await x.controller.dispose();
  release(grant("123"));await tick();await x.controller.flush();
  assert.equal(x.calls.some(c=>c[0]==="set"),false);
});
test("SDK setter failure is not reported as active replacement",async()=>{
  const x=fixture();
  x.api.client.setTrackReplacements=async()=>{throw Error("synthetic sdk failure")};
  await x.controller.start();x.controller.enable();await x.controller.flush();
  assert.notEqual(x.controller.status,"REPLACEMENT_SET");
  await x.controller.dispose();
});

import test from "node:test";
import assert from "node:assert/strict";
import {createUploadJournal, KEY} from "../dist/unpacked/upload/upload-journal.js";

const id = n => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
function fixture() {
  let stored = {};
  const storage = {
    async get() { return {...stored}; },
    async set(value) { stored = {...stored, ...value}; }
  };
  return {journal: createUploadJournal(storage), stored: () => stored};
}
test("upload attempt has bounded, sanitized phases and survives another journal instance", async () => {
  const f = fixture(), journal = f.journal;
  await journal.record(id(1), "checking", {trackId:"50163063", bytes:10300000, token:"secret", filename:"hidden.mp3"});
  await journal.record(id(1), "transferring", {sent:700,percent:25, code:"progress"});
  await journal.record(id(1), "failed", {httpStatus:503,code:"http_error", response:"secret"});
  const attempts = await createUploadJournal({get:async()=>f.stored(),set:async()=>{}}).snapshot();
  assert.equal(attempts.length,1);
  assert.equal(attempts[0].events.length,3);
  assert.equal(attempts[0].events[2].httpStatus,503);
  assert.equal(attempts[0].trackId,"50163063");
  const json=JSON.stringify(attempts);
  assert.doesNotMatch(json,/secret|hidden|filename|response|token/);
  assert.ok(f.stored()[KEY]);
});
test("upload journal limits attempts and entries, omits malformed IDs",async()=>{
 const {journal}=fixture();
 await journal.record("bad-token","failed",{token:"secret"});
 for(let n=1;n<=30;n++)await journal.record(id(n),"connecting");
 const records=await journal.snapshot();
 assert.equal(records.length,25);
 assert.equal(records[0].id,id(30));
 for(let n=0;n<40;n++)await journal.record(id(30),"waiting",{percent:n%100});
 const newRecord=(await journal.snapshot())[0];
 assert.equal(newRecord.events.length,20);
});

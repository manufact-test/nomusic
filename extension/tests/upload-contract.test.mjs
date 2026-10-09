import test from "node:test";
import assert from "node:assert/strict";
import { uploadTargetFromStatus, validMp3Selection, privateUploadApiOrigin }
  from "../dist/unpacked/upload/contract.js";

const state = (id, confidence = 240, ambiguous = false, durationMs = 180872) =>
  ({ track: { id, confidence, ambiguous, metadata: { title: "CI", artist: "CI", album: "CI", durationMs } } });

test("Stage7 upload accepts only confident exact currently observed track", () => {
  assert.equal(uploadTargetFromStatus(state("144530503")).id, "144530503");
  for (const bad of ["", "0", "001", "12 OR 1=1", "2".repeat(25)]) {
    assert.equal(uploadTargetFromStatus(state(bad)), null);
  }
  assert.equal(uploadTargetFromStatus(state("144530503", 50)), null);
  assert.equal(uploadTargetFromStatus(state("144530503", undefined)), null);
  assert.equal(uploadTargetFromStatus(state("144530503", NaN)), null);
  assert.equal(uploadTargetFromStatus({track:{id:"144530503",confidence:200,metadata:{durationMs:180872}}}), null);
  assert.equal(uploadTargetFromStatus({track:{id:"144530503",confidence:200,ambiguous:"false",metadata:{durationMs:180872}}}), null);
  assert.equal(uploadTargetFromStatus(state("144530503", 240, true)), null);
  assert.equal(uploadTargetFromStatus(state("144530503", 240, false, 0)), null);
  assert.equal(uploadTargetFromStatus(null), null);
});
test("Stage7 malformed media metadata cannot become multipart object strings", () => {
  const input = state("144530503");
  input.track.metadata.artist = {toString(){ throw new Error("untrusted"); }};
  input.track.metadata.title = "z".repeat(2000);
  const target = uploadTargetFromStatus(input);
  assert.equal(target.artist, "");
  assert.equal(target.title.length, 240);
});
test("Stage7 file chooser validates size and suffix; server still validates bytes", () => {
  assert.equal(validMp3Selection({ name: "track.MP3", size: 2048 }), true);
  assert.equal(validMp3Selection({ name: "track.mp3", size: 31457281 }), false);
  assert.equal(validMp3Selection({ name: "track.exe", size: 2000 }), false);
  assert.equal(validMp3Selection({ name: "track.mp3", size: 0 }), false);
  assert.equal(validMp3Selection(null), false);
});
test("Stage7 upload target is pinned to safe configured API origin", () => {
  assert.equal(privateUploadApiOrigin("https://celikom.example/"), "https://celikom.example");
  assert.equal(privateUploadApiOrigin("http://127.0.0.1:8800/"), "http://127.0.0.1:8800");
  for (const bad of ["http://celikom.example/", "https://a.example/path", "https://a.example/?token=x",
    "https://user:secret@a.example/", "javascript:alert(1)", "ftp://example.com/", null]) {
    assert.throws(() => privateUploadApiOrigin(bad));
  }
});

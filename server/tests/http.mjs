import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { access } from "node:fs/promises";
import { createServer } from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomBytes, randomUUID } from "node:crypto";
import { ApiClient } from "../../extension/dist/unpacked/api/api-client.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const probe = createServer();
await new Promise(resolve => probe.listen(0, "127.0.0.1", resolve));
const port = probe.address().port; await new Promise(resolve => probe.close(resolve));
const origin = `http://127.0.0.1:${port}`;
const accessToken = randomBytes(24).toString("hex");
const ownerUploadToken = randomBytes(40).toString("hex");
const server = spawn("php", ["-S", `127.0.0.1:${port}`, "-t", path.join(root, "public"), path.join(root, "tests/http-router.php")], {
  env: { ...process.env, APP_ENV: "test", FEATURE_REPLACEMENTS: "1", AUDIO_SIGNING_KEY: randomBytes(32).toString("hex"), API_TEST_TOKEN: accessToken, FEATURE_OWNER_UPLOADS: "1", UPLOAD_OWNER_TOKEN: ownerUploadToken, CELIKOM_TEST_ORIGIN: origin }, stdio: ["ignore", "ignore", "pipe"]
});
let diagnostics = "";
server.stderr.on("data", chunk => { diagnostics = (diagnostics + chunk).slice(-4000); });
try {
  let healthy = false;
  for (let i = 0; i < 60; i++) {
    try { healthy = (await fetch(origin + "/api/v1/health")).ok; } catch (_) { /* server starts asynchronously */ }
    if (healthy) break; await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.equal(healthy, true, "PHP test server did not start");
  const client = new ApiClient(origin, { accessToken });
  const asset = await client.resolve("yandex", "1944599");
  assert.equal(asset.found, true); assert.equal(asset.durationMs, 1000);
  assert.equal((await client.resolve("yandex", "888888")).found, false);
  const full = await fetch(asset.url, { headers: { Origin: "https://music.yandex.ru" } });
  assert.equal(full.status, 200); assert.equal(full.headers.get("access-control-allow-origin"), "https://music.yandex.ru");
  const data = new Uint8Array(await full.arrayBuffer());
  assert.equal(data.length, Number(full.headers.get("content-length"))); assert.equal(data.length, 8044);
  for (const [range, start, end] of [["bytes=0-43", 0, 43], ["bytes=3000-3999", 3000, 3999], ["bytes=-64", data.length - 64, data.length - 1]]) {
    const response = await fetch(asset.url, { headers: { Range: range } });
    assert.equal(response.status, 206);
    assert.equal(response.headers.get("content-range"), `bytes ${start}-${end}/${data.length}`);
    assert.deepEqual(new Uint8Array(await response.arrayBuffer()), data.slice(start, end + 1));
  }
  const invalid = await fetch(asset.url, { headers: { Range: "bytes=99999-" } });
  assert.equal(invalid.status, 416); assert.equal(invalid.headers.get("content-range"), "bytes */8044");
  assert.equal((await fetch(asset.url, { method: "HEAD" })).headers.get("content-length"), "8044");
  const badToken = new URL(asset.url); badToken.searchParams.set("token", "a".repeat(64));
  assert.equal((await fetch(badToken)).status, 403);
  console.log("PASS real PHP HTTP + MySQL resolve and byte-exact 200/206/416/HEAD");

  // Real PHP SAPI multipart: tests is_uploaded_file(), header gate, and pending isolation.
  const frame = Buffer.concat([Buffer.from("fffb9064", "hex"), Buffer.alloc(413)]);
  const syntheticMp3 = Buffer.concat(Array.from({ length: 100 }, () => frame));
  const ownerHeaders = { Authorization: "Bearer " + ownerUploadToken };
  const requestId = randomUUID();
  function uploadBody(trackId, id = requestId, filename = "synthetic.mp3") {
    const form = new FormData();
    for (const [key, value] of Object.entries({ service: "yandex", track_id: trackId, duration_ms: "2606",
      artist: "CI", title: "Synth", album: "", declaration: "1", request_id: id })) form.set(key, value);
    form.set("file", new Blob([syntheticMp3], { type: "audio/mpeg" }), filename);
    return form;
  }
  assert.equal((await fetch(origin + "/api/v1/uploads", { method: "POST", body: uploadBody("799101") })).status, 401);
  assert.equal((await fetch(origin + "/api/v1/uploads", {
    method: "POST", headers: { Authorization: "Bearer " + accessToken }, body: uploadBody("799101")
  })).status, 401, "Read-only resolve token cannot upload");
  const pendingResponse = await fetch(origin + "/api/v1/uploads", { method: "POST",
    headers: ownerHeaders, body: uploadBody("799101") });
  assert.equal(pendingResponse.status, 202, "Multipart accepted: " + pendingResponse.status);
  const pending = await pendingResponse.json();
  assert.equal(pending.status, "pending"); assert.equal(pending.duplicate, false);
  const replay = await fetch(origin + "/api/v1/uploads", { method: "POST",
    headers: ownerHeaders, body: uploadBody("799101", requestId, "renamed.mp3") });
  assert.equal(replay.status, 202);
  assert.equal((await replay.json()).duplicate, true, "Rename or retry cannot bypass SHA dedupe");
  const second = await fetch(origin + "/api/v1/uploads", { method: "POST",
    headers: ownerHeaders, body: uploadBody("799102", randomUUID()) });
  assert.equal(second.status, 202);
  assert.notEqual((await second.json()).replacement_id, pending.replacement_id, "Separate exact Track ID link");
  assert.equal((await client.resolve("yandex", "799101")).found, false, "Pending must never resolve");
  assert.equal((await fetch(origin + "/api/v1/audio/" + pending.replacement_id)).status, 404,
    "Pending is never streamable");
  const invalidBody = uploadBody("799103", randomUUID(), "fake.mp3");
  invalidBody.set("file", new Blob([Buffer.from("not mp3 ".repeat(300))], { type: "audio/mpeg" }), "fake.mp3");
  const invalidUpload = await fetch(origin + "/api/v1/uploads", { method: "POST",
    headers: ownerHeaders, body: invalidBody });
  assert.equal(invalidUpload.status, 415, "Forged MP3 rejected");
  const request = new FormData(); request.set("service", "yandex"); request.set("track_id", "799199");
  const suggestion = await fetch(origin + "/api/v1/track-requests", {
    method: "POST", headers: ownerHeaders, body: request });
  assert.equal(suggestion.status, 202); assert.equal((await suggestion.json()).status, "pending");
  console.log("PASS Stage 7 real PHP multipart owner gate, MP3 validation, retry, multi-track pending isolation");

  let browserBinary = null;
  for (const binary of [process.env.CELIKOM_BROWSER_BINARY, "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium"]) {
    if (binary && await access(binary).then(() => true, () => false)) { browserBinary = binary; break; }
  }
  if (browserBinary) {
    const browser = spawn(browserBinary, ["--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--autoplay-policy=no-user-gesture-required", "--virtual-time-budget=12000", "--dump-dom", origin + "/browser-fixture"], { stdio: ["ignore", "pipe", "ignore"] });
    let dom = ""; browser.stdout.on("data", chunk => { dom += chunk; });
    const code = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => { browser.kill("SIGKILL"); reject(new Error("Browser audio check timed out")); }, 45000);
      browser.on("error", error => { clearTimeout(timer); reject(error); });
      browser.on("close", code => { clearTimeout(timer); resolve(code); });
    });
    assert.equal(code, 0); assert.match(dom, /data-audio-result="ok"/, "Native browser audio could not load/seek/play the signed WAV");
    console.log("PASS native Chromium HTMLAudioElement decodes, seeks and plays signed Range audio");
  } else if (process.env.REQUIRE_BROWSER_AUDIO === "1") {
    throw new Error("CI must provide a Chromium binary for native Audio seek");
  } else {
    console.log("Native Chromium audio check deferred to CI (no local browser binary)");
  }
} catch (error) {
  // PHP access logs include URL query tokens; never copy them into CI output.
  console.error(String(error.message));
  console.error(diagnostics.replace(/token=[^&\s]+/g, "token=[redacted]"));
  process.exitCode = 1;
} finally {
  if (server.exitCode === null && server.signalCode === null) {
    const closed = new Promise(resolve => server.once("close", resolve));
    server.kill("SIGTERM"); await closed;
  }
}

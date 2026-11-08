"use strict";
// W5: isolated Electron renderer host. Never opens or edits installed Yandex.
const { app, BrowserWindow } = require("electron");
const { createServer } = require("node:http");
const { readFile, mkdtemp, rm } = require("node:fs/promises");
const { createHmac, randomBytes } = require("node:crypto");
const { tmpdir } = require("node:os");
const { join, resolve } = require("node:path");
const { spawnSync } = require("node:child_process");
const ffmpeg = require("ffmpeg-static");

app.commandLine.appendSwitch("autoplay-policy", "no-user-gesture-required");
app.commandLine.appendSwitch("disable-background-timer-throttling");

const fixtureDir = resolve(__dirname, "out");
const secret = randomBytes(32);
const sign = (id, expires) => createHmac("sha256", secret)
  .update(id + ":" + expires).digest("hex");
const sound = new Map();
const failures = [];
let server, window, tempDir;

const runFfmpeg = (file, seconds, frequency) => {
  const args = ["-hide_banner", "-loglevel", "error", "-f", "lavfi",
    "-i", "sine=frequency=" + frequency + ":sample_rate=44100",
    "-t", String(seconds), "-ac", "1", "-c:a", "libmp3lame",
    "-b:a", "128k", "-y", file];
  const child = spawnSync(ffmpeg, args, { timeout: 30000, encoding: "utf8" });
  if (child.status !== 0) throw Error("synthetic MP3 generation failed: " + child.stderr);
};

function respond(res, code, headers, body) {
  res.writeHead(code, { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", ...headers });
  res.end(body);
}

const host = async (req, res) => {
  const u = new URL(req.url, "http://127.0.0.1");
  const path = u.pathname;
  try {
    if (path === "/") return respond(res, 200, { "Content-Type": "text/html; charset=utf-8",
      "Content-Security-Policy": "default-src 'none'; script-src 'self'; connect-src 'self'; media-src 'self' blob:" },
      '<!doctype html><html><head><meta charset="utf-8"><title>CELIKOM W5 isolated</title></head>' +
      '<body><script src="/webpack-fixture.js"></script><script type="module" src="/runner.mjs"></script></body></html>');
    const files = {
      "/webpack-fixture.js": join(fixtureDir, "webpack-fixture.js"),
      "/runner.mjs": join(__dirname, "w5-electron-renderer.mjs"),
      "/bridge.mjs": resolve(__dirname, "../bridge/w4-source-resource-adapter.mjs")
    };
    if (files[path]) {
      const bytes = await readFile(files[path]);
      return respond(res, 200, { "Content-Type": path.endsWith(".mjs") ?
        "text/javascript; charset=utf-8" : "application/javascript; charset=utf-8" }, bytes);
    }
    if (path.startsWith("/ticket/")) {
      const id = path.split("/")[2];
      if (!sound.has(id)) return respond(res, 404, {}, "");
      const ttl = Number(u.searchParams.get("ttl") ?? "60");
      if (!Number.isFinite(ttl) || ttl < -30 || ttl > 120) return respond(res, 400, {}, "");
      const expires = Date.now() + ttl * 1000;
      const origin = "http://" + req.headers.host;
      const audio = origin + "/audio/" + id + "?expires=" + expires +
        "&signature=" + sign(id, expires);
      return respond(res, 200, { "Content-Type": "application/json" }, JSON.stringify({ url: audio, expiresAt: expires }));
    }
    if (path.startsWith("/audio/")) {
      const id = path.split("/")[2], data = sound.get(id);
      if (!data) return respond(res, 404, {}, "");
      const expires = Number(u.searchParams.get("expires")), actual = u.searchParams.get("signature");
      if (!Number.isSafeInteger(expires) || expires <= Date.now() ||
          actual !== sign(id, expires))
        return respond(res, 403, {}, "");
      const range = req.headers.range;
      if (!range) return respond(res, 200, {
        "Content-Type": "audio/mpeg", "Content-Length": data.length, "Accept-Ranges": "bytes"
      }, data);
      const match = /^bytes=(\d+)-(\d*)$/.exec(range);
      if (!match) return respond(res, 416, { "Content-Range": "bytes */" + data.length }, "");
      const start = Number(match[1]), end = match[2] ? Number(match[2]) : data.length - 1;
      if (start < 0 || start >= data.length || end < start)
        return respond(res, 416, { "Content-Range": "bytes */" + data.length }, "");
      const last = Math.min(end, data.length - 1), chunk = data.subarray(start, last + 1);
      return respond(res, 206, {
        "Content-Type": "audio/mpeg", "Accept-Ranges": "bytes",
        "Content-Range": "bytes " + start + "-" + last + "/" + data.length,
        "Content-Length": chunk.length
      }, chunk);
    }
    return respond(res, 404, {}, "");
  } catch (error) {
    failures.push("fixture server: " + error.name);
    return respond(res, 500, {}, "");
  }
};

async function run() {
  tempDir = await mkdtemp(join(tmpdir(), "celikom-w5-"));
  for (const [id, duration, freq] of [["1001", 9, 440], ["2002", 36, 523]]) {
    const file = join(tempDir, id + ".mp3");
    runFfmpeg(file, duration, freq);
    sound.set(id, await readFile(file));
  }
  await readFile(join(fixtureDir, "webpack-fixture.js"));
  server = createServer((req, res) => { void host(req, res); });
  await new Promise(ok => server.listen(0, "127.0.0.1", ok));
  const address = "http://127.0.0.1:" + server.address().port;
  window = new BrowserWindow({
    width: 500, height: 400, show: false,
    webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true,
      backgroundThrottling: false, webSecurity: true }
  });
  window.webContents.on("render-process-gone", (_, details) =>
    failures.push("renderer terminated: " + details.reason));
  window.webContents.on("did-fail-load", (_, code) =>
    failures.push("renderer load failed: " + code));
  await window.loadURL(address);
  const timeoutMs = 120_000;
  const started = Date.now();
  let result;
  while (Date.now() - started < timeoutMs && !failures.length) {
    try {
      result = await window.webContents.executeJavaScript("window.__CELIKOM_W5_RESULT__ || null");
      if (result) break;
    } catch (error) { failures.push("renderer query failed: " + error.name); }
    await new Promise(r => setTimeout(r, 250));
  }
  if (!result || failures.length) throw Error("W5 timeout/crash: " + JSON.stringify({ failures, hasResult: !!result }));
  if (!result.passed) throw Error("W5 assertions failed: " + JSON.stringify(result));
  console.log(JSON.stringify({ passed: true, electron: process.versions.electron,
    renderer: "real pinned public Yandex source classes inside isolated Electron",
    assertions: result.assertions, checks: result.checks,
    noYandexInstallationModified: true, actualOfficialAppTested: false }, null, 2));
}

app.whenReady().then(async () => {
  let exitCode = 0;
  try { await run(); }
  catch (e) {
    console.error("W5 ISOLATED ELECTRON FAILURE:", e.stack || e.message);
    exitCode = 1;
  } finally {
    window?.destroy();
    if (server) await new Promise(ok => server.close(ok));
    if (tempDir) await rm(tempDir, { recursive: true, force: true });
    // Electron app.quit() may reset process.exitCode; explicitly mark red CI.
    app.exit(exitCode);
  }
});

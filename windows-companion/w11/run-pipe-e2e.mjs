/**
 * W11: proof that an external subprocess can attach over private Chromium CDP
 * stdio pipe, no TCP debugger, to a strictly synthetic Electron W7/W8 fixture.
 *
 * This launches generic Electron from W5 dependencies and W7's own test app.
 * It never launches, reads, debugs or changes installed Yandex Music.
 */
import { createRequire } from "node:module";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { randomBytes } from "node:crypto";
import { spawn } from "node:child_process";
import { createPipeTransport, exactFixtureTarget } from "./pipe-protocol.mjs";

if (process.platform !== "win32") throw Error("W11_WINDOWS_CI_ONLY");
const require = createRequire(new URL("../w5/package.json", import.meta.url));
const executable = require("electron");
const main = resolve(import.meta.dirname, "../w7/electron-main.cjs");
const nonce = randomBytes(16).toString("hex");
const profile = await mkdtemp(join(tmpdir(), "celikom-w11-private-pipe-"));
let child, pipe, readyOrigin, childExited = false;
const die = code => { throw Error("W11_" + code); };
const wait = ms => new Promise(r => setTimeout(r, ms));

try {
  const env = {
    ...process.env,
    CELIKOM_W11_PIPE_ONLY: "YES",
    CELIKOM_W11_NONCE: nonce,
    NODE_NO_WARNINGS: "1"
  };
  delete env.ELECTRON_RUN_AS_NODE;
  delete env.NODE_OPTIONS;
  child = spawn(executable, [
    main, "--remote-debugging-pipe", "--user-data-dir=" + profile
  ], {
    cwd: resolve(import.meta.dirname, "../w5"),
    env, windowsHide: true, shell: false,
    stdio: ["ignore", "pipe", "pipe", "pipe", "pipe"]
  });
  child.once("exit", () => { childExited = true; });
  let lines = "", failure = null;
  const readyPromise = new Promise((resolveReady, rejectReady) => {
    const timeout = setTimeout(() => rejectReady(Error("W11_FIXTURE_START_TIMEOUT")), 20000);
    child.once("error", () => {
      clearTimeout(timeout);
      rejectReady(Error("W11_ELECTRON_SPAWN_FAILED"));
    });
    child.once("exit", code => {
      clearTimeout(timeout);
      rejectReady(Error("W11_ELECTRON_EARLY_EXIT_" + Number(code)));
    });
    child.stdout.on("data", part => {
      lines += part.toString("utf8");
      if (lines.length > 12000) {
        clearTimeout(timeout); rejectReady(Error("W11_UNEXPECTED_STDOUT")); return;
      }
      let end;
      while ((end = lines.indexOf("\n")) !== -1) {
        const item = lines.slice(0,end).trim();
        lines = lines.slice(end+1);
        if (!item.startsWith("W11_FIXTURE_READY=")) continue;
        let parsed;
        try { parsed = JSON.parse(item.slice("W11_FIXTURE_READY=".length)); }
        catch { clearTimeout(timeout); rejectReady(Error("W11_BAD_FIXTURE_READY")); return; }
        if (parsed.nonce !== nonce || !/^http:\/\/127\.0\.0\.1:\d{2,5}$/.test(parsed.origin)) {
          clearTimeout(timeout);rejectReady(Error("W11_INVALID_FIXTURE_IDENTITY"));return;
        }
        clearTimeout(timeout);
        resolveReady(parsed.origin);
      }
    });
    child.stderr.on("data", () => { /* never print process/renderer/account paths */ });
  });
  readyOrigin = await readyPromise;
  pipe = createPipeTransport(child.stdio[3], child.stdio[4]);

  const version = await pipe.send("Browser.getVersion", {}, { timeoutMs: 10000 });
  if (!/Chrome|Chromium|Electron/.test(version?.product || "")) die("NOT_CHROMIUM_CDP_PIPE");
  let targets = [];
  for (let i=0; i<10; i++) {
    const reply = await pipe.send("Target.getTargets");
    targets = (reply?.targetInfos || []).filter(t => exactFixtureTarget(t,readyOrigin,nonce));
    if (targets.length) break;
    await wait(150);
  }
  if (targets.length !== 1) die("TARGET_NOT_EXACT_SYNTHETIC");
  const attached = await pipe.send("Target.attachToTarget", {
    targetId: targets[0].targetId, flatten: true
  });
  if (typeof attached?.sessionId !== "string" || attached.sessionId.length < 5)
    die("NO_CDP_SESSION");
  const sessionId = attached.sessionId;
  await pipe.send("Runtime.enable",{}, {sessionId});
  const expression='({origin:location.origin,title:document.title,nonceMatch:'+
    '(new URL(location.href)).searchParams.get("nonce")==='+JSON.stringify(nonce)+','+
    'publicFactories:Boolean(window.__nativeFixture?.req)})';
  const handshake = await pipe.send("Runtime.evaluate", {
    expression, awaitPromise:true, returnByValue:true, silent:true
  }, {sessionId});
  const observed=handshake?.result?.value;
  if (handshake?.exceptionDetails ||
      observed?.origin !== readyOrigin ||
      observed.title !== "CELIKOM W7 isolated attach" ||
      observed.nonceMatch !== true || observed.publicFactories !== true)
    die("INVALID_RENDERER_HANDSHAKE");
  const activated = await pipe.send("Runtime.evaluate", {
    expression:'import("/activation.mjs").then(m=>m.runW7('+JSON.stringify(nonce)+'))',
    awaitPromise:true, returnByValue:true, silent:true
  }, {sessionId,timeoutMs:90000});
  if (activated?.exceptionDetails || activated?.result?.value?.passed !== true ||
      activated.result.value.scope !== "ISOLATED_FIXTURE_ONLY" ||
      activated.result.value.officialAppTested !== false ||
      activated.result.value.assertions < 30)
    die("W7_W8_AUDIO_ASSERTIONS_FAILED");
  console.log(JSON.stringify({
    w11:"PASS", transport:"CHROMIUM_PRIVATE_PIPE_NO_TCP_PORT",
    chromium:version.product,
    nativeYandexPublicClasses:"V1+V2_FIXTURE",
    assertions:activated.result.value.assertions,
    checks:activated.result.value.checks,
    onlyEphemeralTestSession:true,
    officialYandexUsed:false,
    officialExeModified:false,
    installedYandexFilesRead:false,
    realAuthenticatedRendererHooked:false
  },null,2));
} finally {
  pipe?.close();
  if (readyOrigin) {
    try {
      await fetch(readyOrigin+"/__w11_done?nonce="+nonce,
        {method:"POST",signal:AbortSignal.timeout(2000)});
    } catch { /* fixture may already have exited */ }
  }
  if (child && !childExited) {
    await Promise.race([
      new Promise(resolveExit=>child.once("exit",resolveExit)),
      wait(3500).then(()=>{ if(!childExited) child.kill(); })
    ]);
  }
  await rm(profile,{recursive:true,force:true});
}

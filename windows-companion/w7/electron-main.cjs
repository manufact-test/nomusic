/**
 * W7 standalone Electron lab, NOT an official Yandex launcher.
 * Only ephemeral loopback resources, synthetic audio, blank CI user session.
 * Developer port deliberately ENABLED FOR THIS EPHEMERAL FIXTURE ONLY.
 */
"use strict";
const { app, BrowserWindow, session } = require("electron");
const { createServer } = require("node:http");
const { readFile, mkdtemp, rm } = require("node:fs/promises");
const { tmpdir } = require("node:os");
const { join, resolve } = require("node:path");
const { spawn, spawnSync } = require("node:child_process");
const { randomBytes, randomInt } = require("node:crypto");
const ffmpeg = require("../w5/node_modules/ffmpeg-static");

const debugPort = randomInt(19000, 61000);
const nonce = randomBytes(16).toString("hex");
app.commandLine.appendSwitch("remote-debugging-port", String(debugPort));
app.commandLine.appendSwitch("remote-debugging-address", "127.0.0.1");
app.commandLine.appendSwitch("autoplay-policy", "no-user-gesture-required");
const media = new Map();
let tmp, server, win, allowedOrigin;

function respond(res, status, headers, bytes) {
  res.writeHead(status, { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", ...headers });
  res.end(bytes);
}

async function handle(req, res) {
  try {
    const url = new URL(req.url, "http://127.0.0.1");
    if (url.pathname === "/" && url.searchParams.get("nonce") === nonce)
      return respond(res, 200, {
        "Content-Type": "text/html; charset=utf-8",
        "Content-Security-Policy": "default-src 'none'; script-src 'self'; connect-src 'self'; media-src 'self' blob:; object-src 'none'; base-uri 'none'"
      }, '<!doctype html><meta charset="utf-8"><title>CELIKOM W7 isolated attach</title><script src="/webpack-fixture.js"></script>');
    const modules = new Map([
      ["/webpack-fixture.js", resolve(__dirname, "../w5/out/webpack-fixture.js")],
      ["/bridge.mjs", resolve(__dirname, "../bridge/w4-source-resource-adapter.mjs")],
      ["/activation.mjs", resolve(__dirname, "activation.mjs")],
      ["/recovery.mjs", resolve(__dirname, "../w8/native-original-recovery.mjs")]
    ]);
    if (modules.has(url.pathname)) {
      const buffer = await readFile(modules.get(url.pathname));
      return respond(res, 200, { "Content-Type": "text/javascript; charset=utf-8" }, buffer);
    }
    if (url.pathname.startsWith("/media/")) {
      const bytes = media.get(url.pathname);
      if (!bytes) return respond(res, 404, {}, "");
      const range=req.headers.range;
      if (!range) return respond(res, 200, {
        "Content-Type":"audio/mpeg", "Content-Length":bytes.length, "Accept-Ranges":"bytes"
      },bytes);
      const match=/^bytes=(\d+)-(\d*)$/.exec(range);
      if (!match) return respond(res,416,{"Content-Range":"bytes */"+bytes.length},"");
      const from=Number(match[1]), to=match[2]?Number(match[2]):bytes.length-1;
      if(from<0||from>=bytes.length||to<from)
        return respond(res,416,{"Content-Range":"bytes */"+bytes.length},"");
      const end=Math.min(to,bytes.length-1);
      return respond(res,206,{
        "Content-Type":"audio/mpeg","Content-Length":end-from+1,
        "Content-Range":"bytes "+from+"-"+end+"/"+bytes.length,
        "Accept-Ranges":"bytes"
      },bytes.subarray(from,end+1));
    }
    return respond(res,404,{},"");
  }catch {return respond(res,500,{},"");}
}

async function createAudio() {
  tmp=await mkdtemp(join(tmpdir(),"celikom-w7-only-"));
  for(const [name,seconds,frequency] of [
    ["orig1001",10,330],["alt1001",10,440],
    ["orig2002",30,494],["alt2002",30,587]
  ]) {
    const file=join(tmp,name+".mp3");
    const command=spawnSync(ffmpeg,[
      "-hide_banner","-loglevel","error",
      "-f","lavfi","-i","sine=frequency="+frequency+":sample_rate=44100",
      "-t",String(seconds),"-ac","1","-c:a","libmp3lame","-b:a","128k",
      "-y",file
    ],{encoding:"utf8",timeout:30000});
    if(command.status!==0)throw Error("W7_SYNTHETIC_ENCODER_FAILED");
    media.set("/media/"+name+".mp3",await readFile(file));
  }
}

function externalSidecar(origin) {
  return new Promise((resolvePromise,rejectPromise)=>{
    const child=spawn("node",[join(__dirname,"sidecar.mjs"),String(debugPort),origin,nonce],{
      cwd:__dirname,shell:false,windowsHide:true,
      env:{...process.env,NODE_NO_WARNINGS:"1"}
    });
    let stdout="",stderr="";
    const timer=setTimeout(()=>{child.kill();rejectPromise(Error("W7_SIDECAR_TIMEOUT"));},110000);
    child.stdout.on("data",chunk=>{stdout+=chunk.toString("utf8").slice(0,10000);});
    child.stderr.on("data",chunk=>{stderr+=chunk.toString("utf8").slice(0,2000);});
    child.on("error",()=>{clearTimeout(timer);rejectPromise(Error("W7_CANNOT_LAUNCH_NODE_SIDECAR"));});
    child.on("close",code=>{
      clearTimeout(timer);
      if(code!==0){
        console.error("W7 sidecar reported:",stderr.trim().slice(0,300));
        rejectPromise(Error("W7_CDP_SIDECAR_FAILED"));
        return;
      }
      try {
        const result=JSON.parse(stdout.trim());
        if(result.result!=="PASS"||result.scope!=="W7_LOCAL_DEBUG_FIXTURE_ONLY"||
           result.officialYandexTouched!==false||result.assertions<20)
          throw Error("W7_BAD_RESULT");
        resolvePromise(result);
      }catch{rejectPromise(Error("W7_SIDECAR_RESULT_INVALID"));}
    });
  });
}

async function run() {
  await createAudio();
  await readFile(resolve(__dirname,"../w5/out/webpack-fixture.js"));
  server=createServer((req,res)=>{void handle(req,res);});
  await new Promise(resolvePromise=>server.listen(0,"127.0.0.1",resolvePromise));
  allowedOrigin="http://127.0.0.1:"+server.address().port;
  // Never let the synthetic fixture load a live Yandex domain or account.
  session.defaultSession.webRequest.onBeforeRequest((details,callback)=>{
    if(details.url.startsWith(allowedOrigin+"/")||details.url.startsWith("blob:"+allowedOrigin+"/"))
      callback({cancel:false});
    else callback({cancel:true});
  });
  session.defaultSession.setPermissionRequestHandler((_, __, callback)=>callback(false));
  win=new BrowserWindow({show:false,width:600,height:400,
    webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false,
      webSecurity:true,backgroundThrottling:false}});
  win.webContents.setWindowOpenHandler(()=>({action:"deny"}));
  await win.loadURL(allowedOrigin+"/?nonce="+nonce);
  const result=await externalSidecar(allowedOrigin);
  console.log(JSON.stringify({
    w7:"PASS", cdpsidecar:"external Node process dynamically activated W4",
    assertions:result.assertions,checks:result.checks,
    target:"ephemeral CI-only Electron fixture",
    installedYandexTouched:false,liveYandexDebuggingAuthorized:false
  },null,2));
}

app.whenReady().then(async()=>{
  let code=0;
  try{await run();}
  catch(error){
    code=1;
    console.error("W7 ISOLATED ATTACH FAILURE:",String(error?.message||"UNKNOWN").slice(0,200));
  }finally{
    win?.destroy();
    if(server)await new Promise(resolvePromise=>server.close(resolvePromise));
    if(tmp)await rm(tmp,{recursive:true,force:true});
    app.exit(code);
  }
});

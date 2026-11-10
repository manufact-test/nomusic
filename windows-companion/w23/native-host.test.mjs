import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { EventEmitter } from "node:events";

const source = fs.readFileSync(new URL("./host.cjs", import.meta.url), "utf8");

async function runHost(url, { queue = [], token = "b".repeat(64),
  debuggerDriver = null, stateOverride = null } = {}) {
  const diagnostics = [], evaluated = [], network = [];
  let drained = false;
  const viewEvents = new Map();
  const view = {
    isDestroyed: () => false,
    getURL: () => url,
    debugger: debuggerDriver,
    on: (name, handler) => { const handlers = viewEvents.get(name) || []; handlers.push(handler); viewEvents.set(name, handlers); },
    executeJavaScript: async script => {
      evaluated.push(script);
      if (script.includes("return !!window.__celikomBridgeNativeDrain")) return true;
      if (script.includes("__celikomBridgeNativeDrain?.()")) {
        if (drained) return [];
        drained = true;
        return queue;
      }
      if (script.includes("__celikomBridgeNativeStatus?.()")) return "ORIGINAL";
      return true;
    }
  };
  const fakeFs = {
    mkdirSync: () => {},
    statSync: () => { throw Object.assign(new Error("NOT_FOUND"), { code: "ENOENT" }); },
    readFileSync: file => file.includes("renderer.js")
      ? "window.__celikomBridgeNativeDrain=()=>[];" : token,
    appendFileSync: (_file, line) => diagnostics.push(line.trim())
  };
  const fakeHttp = {
    request: (options, callback) => {
      network.push({ ...options });
      const req = new EventEmitter();
      req.write = () => {};
      req.end = () => {
        queueMicrotask(() => {
          const resp = new EventEmitter();
          resp.statusCode = 200;
          resp.resume = () => {};
          callback(resp);
          const value = options.path.startsWith("/v1/resolve")
            ? {found:true,grant:{
              trackId:"123",approved:true,entitled:true,
              audioUrl:"https://api.celikom.example/api/v1/audio/1?token="+ "a".repeat(64) + "&expires=1800000180",
              expiresAt:1800000180000,mimeType:"audio/mpeg"
            }}
            : (stateOverride ?? {enabled:false,signedIn:false,apiOrigin:""});
          resp.emit("data", Buffer.from(JSON.stringify(value)));
          resp.emit("end");
        });
      };
      req.destroy = () => req.emit("error",new Error("closed"));
      return req;
    }
  };
  const fakePath = {join: (...parts) => parts.join("\\")};
  const fakeElectron = {
    app:{getAppPath:()=>"/virtual",on:()=>{}},
    webContents:{getAllWebContents:()=>[view]}
  };
  const context = {
    require: name => name==="electron" ? fakeElectron :
      name==="node:fs" ? fakeFs :
      name==="node:path" ? fakePath :
      name==="node:http" ? fakeHttp : null,
    process:{env:{
      LOCALAPPDATA:"C:\\Users\\test",
      CELIKOM_W23_DEV_DIAG:"diagnostics.log"
    }},
    URL,WeakMap,WeakSet,Set,JSON,Buffer,Date,Promise,console,encodeURIComponent,
    setInterval:callback=>{callback();return{unref(){}}}
  };
  vm.runInNewContext(source,context,{timeout:1200});
  await new Promise(resolve=>setTimeout(resolve,35));
  return {diagnostics,evaluated,network,
    emitView: (name,...args) => {
      for(const handler of viewEvents.get(name) || []) handler({},...args);
    },
    witnessCount: name => (viewEvents.get(name)||[]).length
  };
}

test("trusted native Yandex scheme connects via Electron main process",async()=>{
  for (const url of [
    "musicapplication://desktop/",
    "musicapplication://Desktop/",
    "MUSICAPPLICATION://DESKTOP/"
  ]) {
    const {diagnostics,evaluated,network}=await runHost(url);
    assert.ok(diagnostics.includes("APPROVED_VIEW"),url);
    assert.ok(diagnostics.includes("RENDERER_INJECTED"),url);
    assert.ok(diagnostics.includes("BOOTSTRAP_KEY_PRESENT"),url);
    assert.ok(diagnostics.includes("LOCAL_STATE_OK"),url);
    assert.ok(diagnostics.includes("RENDERER_STATE_DELIVERED"),url);
    assert.ok(network.some(r=>r.path==="/v1/state"),url);
    assert.ok(network.every(r=>r.host==="127.0.0.1" && r.port===21471),url);
    assert.ok(evaluated.every(js=>!js.includes("b".repeat(64))),"token never leaked to renderer");
  }
});
test("unrelated or spoofed desktop renderer never gets native bridge",async()=>{
  for(const url of [
    "https://unrelated.example/",
    "musicapplication://evil/",
    "file:///C:/index.html"
  ]) {
    const {evaluated,network}=await runHost(url);
    assert.equal(evaluated.length,0,url);
    assert.equal(network.length,0,url);
  }
});
test("approved exact-ID grant is relayed, not CELIKOM login tokens",async()=>{
  const {diagnostics,evaluated,network}=await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123"}]
  });
  assert.ok(network.some(r=>r.path==="/v1/resolve?track_id=123"));
  assert.ok(diagnostics.includes("LOCAL_RESOLVE_REPLY"));
  assert.ok(evaluated.some(s=>s.includes("__celikomBridgeNativeReceive")));
  assert.ok(evaluated.every(s=>!s.includes("b".repeat(64))),"bridge capability never injected");
});
test("foreign track ID cannot trigger a localhost resolve request",async()=>{
  const {network}=await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123/../../admin"}]
  });
  assert.equal(network.filter(r=>r.path.startsWith("/v1/resolve")).length,0);
});

test("normal native diagnostic events contain only code/id, no signed audio URL",async()=>{
  const {diagnostics}=await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123"}]
  });
  assert.ok(diagnostics.some(x=>/\\|RESOLVE_REQUEST\\|track=123$/.test(x)));
  assert.ok(diagnostics.every(x=>!x.includes("token=")&&!x.includes("audioUrl")));
});

test("W48 genuine Electron media events reveal fast start-pause and real audible state", async () => {
  const r=await runHost("musicapplication://desktop/");
  assert.equal(r.witnessCount("media-started-playing"),1);
  assert.equal(r.witnessCount("media-paused"),1);
  assert.equal(r.witnessCount("audio-state-changed"),1);
  r.emitView("media-started-playing");
  r.emitView("media-paused");
  r.emitView("audio-state-changed",false);
  r.emitView("audio-state-changed",true);
  const codes=r.diagnostics;
  for(const code of ["PLAYER_ENGINE_STARTED","PLAYER_ENGINE_PAUSED",
    "PLAYER_ENGINE_FAST_PAUSE","PLAYER_AUDIO_SILENT","PLAYER_AUDIO_AUDIBLE"]) {
    assert.ok(codes.includes(code),code);
  }
  assert.ok(codes.every(line=>!line.includes("token=")&&!line.includes("audioUrl")));
});
test("W48 untrusted Yandex-like renderer receives no media observer", async () => {
  const r=await runHost("musicapplication://evil/");
  for(const name of ["media-started-playing","media-paused","audio-state-changed"])
    assert.equal(r.witnessCount(name),0);
  r.emitView("media-started-playing");
  assert.ok(!r.diagnostics.includes("PLAYER_ENGINE_STARTED"));
});
test("W48 media witness attaches once per view across repeated host tick cycles", async () => {
  const r=await runHost("musicapplication://desktop/");
  for(const name of ["media-started-playing","media-paused","audio-state-changed"])
    assert.equal(r.witnessCount(name),1);
});

test("W48 passive Media CDP reports player error and fixed events without sensitive payload",async()=>{
  const debug=new EventEmitter();
  const sent=[];
  let attached=false;
  debug.isAttached=()=>attached;
  debug.attach=version=>{ assert.equal(version,"1.3"); attached=true; };
  debug.detach=()=>{attached=false;};
  debug.sendCommand=async name=>{ sent.push(name); };
  const r=await runHost("musicapplication://desktop/",{debuggerDriver:debug});
  assert.ok(r.diagnostics.includes("PLAYER_CDP_READY"));
  assert.ok(sent.includes("Media.enable"));
  assert.ok(sent.includes("Network.enable"));
  debug.emit("message",{}, "Media.playerErrorsRaised",
    {errors:[{message:"TOKEN_SECRET_EXAMPLE",errorCode:"DRM-PRIVATE"}]});
  debug.emit("message",{}, "Media.playerEventsAdded",
    {events:[{value:'{"event":"kPlay"}'},{value:'{"event":"kPause"}'}]});
  debug.emit("message",{}, "Media.playerPropertiesChanged",
    {properties:[{name:"kIsPlaying",value:"true"},{name:"kIsPlaying",value:"false"}]});
  debug.emit("message",{}, "Media.playerMessagesLogged",
    {messages:[{level:"error",message:"PRIVATE_SIGNED_AUDIO_URL"}]});
  for(const code of ["PLAYER_CDP_PIPELINE_ERROR","PLAYER_CDP_EVENT_START",
    "PLAYER_CDP_EVENT_PAUSE","PLAYER_CDP_STATE_PLAYING",
    "PLAYER_CDP_STATE_NOT_PLAYING","PLAYER_CDP_ERROR_MESSAGE"])
    assert.ok(r.diagnostics.includes(code),code);
  const exported=JSON.stringify(r.diagnostics);
  assert.ok(!exported.includes("TOKEN_SECRET_EXAMPLE"));
  assert.ok(!exported.includes("PRIVATE_SIGNED_AUDIO_URL"));
  assert.ok(!exported.includes("DRM-PRIVATE"));
});
test("W48 read-only CDP witness skips a debug session already attached",async()=>{
  const debug=new EventEmitter();
  let attachCalls=0;
  debug.isAttached=()=>true;
  debug.attach=()=>{attachCalls++;};
  debug.sendCommand=async()=>{throw Error("MUST_NOT_SEND");};
  const r=await runHost("musicapplication://desktop/",{debuggerDriver:debug});
  assert.equal(attachCalls,0);
  assert.ok(r.diagnostics.includes("PLAYER_CDP_UNAVAILABLE"));
});

test("W50 CDP tracks only Yandex's real signed audio request after no CELIKOM probe",async()=>{
  const debug=new EventEmitter();
  let attached=false;const commands=[];
  debug.isAttached=()=>attached;
  debug.attach=()=>{attached=true;};
  debug.detach=()=>{attached=false;};
  debug.sendCommand=async cmd=>{commands.push(cmd);};
  const r=await runHost("musicapplication://desktop/",{
    debuggerDriver:debug,
    stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
  });
  assert.ok(commands.includes("Media.enable"));
  assert.ok(commands.includes("Network.enable"));
  assert.ok(r.diagnostics.includes("PLAYER_NET_READY"));
  const media="https://api.celikom.example/api/v1/audio/42498653?token="+
    "a".repeat(64)+"&expires=1800000180&sid=7";
  debug.emit("message",{},"Network.requestWillBeSent",{
    requestId:"req1",request:{url:media,method:"GET"},type:"Fetch"
  });
  debug.emit("message",{},"Network.responseReceived",{
    requestId:"req1",response:{status:206,headers:{"Content-Type":"audio/mpeg"}}
  });
  debug.emit("message",{},"Network.loadingFinished",{requestId:"req1"});
  assert.ok(r.diagnostics.includes("PLAYER_NET_REQUEST|track=42498653"),JSON.stringify({diag:r.diagnostics,network:r.network}));
  assert.ok(r.diagnostics.includes("PLAYER_NET_GET|track=42498653"));
  assert.ok(r.diagnostics.includes("PLAYER_NET_FETCH|track=42498653"));
  assert.ok(r.diagnostics.includes("PLAYER_NET_HTTP_PARTIAL|track=42498653"));
  assert.ok(r.diagnostics.includes("PLAYER_NET_FINISHED|track=42498653"));
  assert.ok(r.diagnostics.every(x=>!x.includes("token=")&&!x.includes("expires=")
    &&!x.includes("api.celikom.example")&&!x.includes("Content-Type")));
});
test("W50 identifies actual CORS credential and CSP failures without showing request URLs",async()=>{
  const debug=new EventEmitter();let connected=false;
  debug.isAttached=()=>connected;debug.attach=()=>{connected=true;};
  debug.detach=()=>{connected=false;};debug.sendCommand=async()=>{};
  const r=await runHost("musicapplication://desktop/",{
    debuggerDriver:debug,
    stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
  });
  const media="https://api.celikom.example/api/v1/audio/85025192?token="+
    "b".repeat(64)+"&expires=1800000180";
  debug.emit("message",{},"Network.requestWillBeSent",{
    requestId:"req2",request:{url:media,method:"GET"},type:"Media"
  });
  debug.emit("message",{},"Network.loadingFailed",{
    requestId:"req2",
    corsErrorStatus:{corsError:"InvalidAllowCredentials",failedParameter:"SECRET"}
  });
  for(const code of ["PLAYER_NET_REQUEST","PLAYER_NET_MEDIA","PLAYER_NET_FAILED",
    "PLAYER_NET_CORS_BLOCKED","PLAYER_NET_CORS_CREDENTIALS"])
    assert.ok(r.diagnostics.includes(code+"|track=85025192"),code+" "+JSON.stringify({diag:r.diagnostics,network:r.network}));
  debug.emit("message",{},"Network.requestWillBeSent",{
    requestId:"req3",request:{url:media,method:"GET"},type:"Fetch"
  });
  debug.emit("message",{},"Network.loadingFailed",{
    requestId:"req3",blockedReason:"csp",errorText:"PASSWORD OR SIGNED URL"
  });
  assert.ok(r.diagnostics.includes("PLAYER_NET_CSP_BLOCKED|track=85025192"));
  assert.ok(!JSON.stringify(r.diagnostics).includes("SECRET"));
  assert.ok(!JSON.stringify(r.diagnostics).includes("PASSWORD"));
});
test("W50 network observer ignores all foreign, unsigned, unknown and auth URLs",async()=>{
  const debug=new EventEmitter();let connected=false;
  debug.isAttached=()=>connected;debug.attach=()=>{connected=true;};
  debug.detach=()=>{connected=false;};debug.sendCommand=async()=>{};
  const r=await runHost("musicapplication://desktop/",{
    debuggerDriver:debug,
    stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
  });
  for(const uri of [
    "https://another.example/api/v1/audio/9?token=secret",
    "https://api.celikom.example/api/v1/auth/login?token=secret",
    "https://api.celikom.example/api/v1/audio/9extra?token=secret",
    "https://evil.example/track.mp3"
  ])debug.emit("message",{},"Network.requestWillBeSent",{
    requestId:uri,request:{url:uri,method:"GET"},type:"Fetch"
  });
  assert.ok(!r.diagnostics.some(x=>x.startsWith("PLAYER_NET_REQUEST")));
  assert.ok(!r.diagnostics.some(x=>x.includes("secret")));
});

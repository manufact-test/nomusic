import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { EventEmitter } from "node:events";

const source = fs.readFileSync(new URL("./host.cjs", import.meta.url), "utf8");

async function runHost(url, { queue = [], token = "b".repeat(64),
  debuggerDriver = null, stateOverride = null, grantOverride = null, clock = Date } = {}) {
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
            ? {found:true,grant:grantOverride ?? {
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
    URL,WeakMap,WeakSet,Set,JSON,Buffer,Date:clock,Promise,console,encodeURIComponent,
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
  assert.ok(r.diagnostics.some(line=>line.endsWith("|PLAYER_NET_REQUEST|resource_id=42498653")),JSON.stringify({diag:r.diagnostics,network:r.network}));
  assert.ok(r.diagnostics.some(line=>line.endsWith("|PLAYER_NET_GET|resource_id=42498653")));
  assert.ok(r.diagnostics.some(line=>line.endsWith("|PLAYER_NET_FETCH|resource_id=42498653")));
  assert.ok(r.diagnostics.some(line=>line.endsWith("|PLAYER_NET_HTTP_PARTIAL|resource_id=42498653")));
  assert.ok(r.diagnostics.some(line=>line.endsWith("|PLAYER_NET_FINISHED|resource_id=42498653")));
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
    assert.ok(r.diagnostics.some(line=>line.endsWith("|"+code+"|resource_id=85025192")),code+" "+JSON.stringify({diag:r.diagnostics,network:r.network}));
  debug.emit("message",{},"Network.requestWillBeSent",{
    requestId:"req3",request:{url:media,method:"GET"},type:"Fetch"
  });
  debug.emit("message",{},"Network.loadingFailed",{
    requestId:"req3",blockedReason:"csp",errorText:"PASSWORD OR SIGNED URL"
  });
  assert.ok(r.diagnostics.some(line=>line.endsWith("|PLAYER_NET_CSP_BLOCKED|resource_id=85025192")));
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

function w52Grant(resourceId, trackId="123", seconds=120, sid="7") {
  const expires = Math.floor(Date.now()/1000) + seconds;
  const audioUrl = "https://api.celikom.example/api/v1/audio/" + resourceId +
    "?token=" + "e".repeat(64) + "&expires=" + expires +
    (sid ? "&sid=" + sid : "");
  return { trackId, approved:true, entitled:true, audioUrl,
    expiresAt: expires * 1000, mimeType:"audio/mpeg" };
}
function w52Debugger(body = '{"error":"invalid_audio_token"}') {
  const debug = new EventEmitter(), commands = [];
  let attached = false;
  debug.isAttached = () => attached;
  debug.attach = () => { attached=true; };
  debug.detach = () => { attached=false; };
  debug.sendCommand = async (command, args) => {
    commands.push([command,args]);
    if (command === "Network.getResponseBody") return {body,base64Encoded:false};
    return {};
  };
  return {debug,commands};
}
test("W52 compares actual native Media URL to in-memory signed grant, never writes the grant", async () => {
  const grant = w52Grant("139");
  const {debug,commands} = w52Debugger();
  const r = await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123"}], debuggerDriver:debug,
    grantOverride:grant,
    stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
  });
  const requests = [
    ["full", grant.audioUrl, "PLAYER_URL_MATCH"],
    ["missing",grant.audioUrl.split("?")[0], "PLAYER_URL_QUERY_MISSING"],
    ["changed",grant.audioUrl.replace("sid=7","sid=8"),"PLAYER_URL_QUERY_CHANGED"],
    ["unknown",grant.audioUrl.replace("/139?","/89?"),"PLAYER_URL_EXPECTATION_MISSING"]
  ];
  for(const [requestId,url,expected] of requests) {
    debug.emit("message",{},"Network.requestWillBeSent",{
      requestId, request:{url,method:"GET"}, type:"Media"
    });
    const id = requestId === "unknown" ? "89" : "139";
    assert.ok(r.diagnostics.some(x=>x.endsWith("|"+expected+"|resource_id="+id)),
      expected+" "+JSON.stringify(r.diagnostics));
  }
  assert.ok(r.diagnostics.some(x=>x.endsWith("|RESOLVE_REQUEST|track=123")));
  assert.ok(!r.diagnostics.some(x=>x.includes("|PLAYER_NET_REQUEST|track=")));
  assert.ok(!JSON.stringify(r.diagnostics).includes(grant.audioUrl));
  assert.ok(!JSON.stringify(r.diagnostics).includes("sid=7"));
  assert.ok(!JSON.stringify(r.diagnostics).includes("token="));
  assert.ok(!commands.some(([name])=>name==="Network.getResponseBody"),
    "URL comparison alone must not inspect response bodies");
});
test("W52 categorizes only bounded real native audio 403 JSON responses", async () => {
  for (const [body,classification] of [
    ['{"error":"invalid_audio_token"}',"PLAYER_403_PHP_INVALID_AUDIO_TOKEN"],
    ['{"error":"access_denied"}',"PLAYER_403_PHP_ACCESS_DENIED"],
    ['{"error":"some_unknown_error"}',"PLAYER_403_JSON_UNCLASSIFIED"]
  ]) {
    const grant = w52Grant("139");
    const {debug,commands} = w52Debugger(body);
    const r = await runHost("musicapplication://desktop/",{
      queue:[{requestId:"1",trackId:"123"}], debuggerDriver:debug,
      grantOverride:grant,
      stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
    });
    debug.emit("message",{},"Network.requestWillBeSent",{
      requestId:"native1", request:{url:grant.audioUrl,method:"GET"}, type:"Media"
    });
    debug.emit("message",{},"Network.responseReceived",{
      requestId:"native1",
      response:{status:403,headers:{"Content-Type":"application/json; charset=utf-8","Content-Length":"31"}}
    });
    debug.emit("message",{},"Network.loadingFinished",{requestId:"native1"});
    await new Promise(resolve=>setTimeout(resolve,5));
    assert.ok(r.diagnostics.some(x=>x.endsWith("|"+classification+"|resource_id=139")),
      classification+" "+JSON.stringify(r.diagnostics));
    assert.equal(commands.filter(([name])=>name==="Network.getResponseBody").length,1);
    assert.ok(!JSON.stringify(r.diagnostics).includes(body));
  }
});
test("W52 never reads foreign, successful, HTML, or oversized 403 response bodies",async()=>{
  const grant=w52Grant("139"), {debug,commands}=w52Debugger("PRIVATE_TOKEN_EXAMPLE");
  const r=await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123"}], debuggerDriver:debug,
    grantOverride:grant,
    stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
  });
  for (const [requestId,url,status,headers] of [
    ["success",grant.audioUrl,206,{"Content-Type":"audio/mpeg"}],
    ["html",grant.audioUrl,403,{"Content-Type":"text/html"}],
    ["oversized",grant.audioUrl,403,{"Content-Type":"application/json","Content-Length":"1000"}],
    ["foreign","https://not-celikom.example/api/v1/audio/139",403,{"Content-Type":"application/json"}]
  ]) {
    debug.emit("message",{},"Network.requestWillBeSent",{
      requestId, request:{url,method:"GET"},type:"Media"
    });
    debug.emit("message",{},"Network.responseReceived",{
      requestId,response:{status,headers}
    });
    debug.emit("message",{},"Network.loadingFinished",{requestId});
  }
  await new Promise(resolve=>setTimeout(resolve,5));
  assert.equal(commands.filter(([name])=>name==="Network.getResponseBody").length,0);
  assert.ok(r.diagnostics.some(x=>x.endsWith("|PLAYER_403_HTML|resource_id=139")));
  assert.ok(!JSON.stringify(r.diagnostics).includes("PRIVATE_TOKEN_EXAMPLE"));
});
test("W52 expired expected grant is distinguished without leaking signed URL",async()=>{
  const grant=w52Grant("139","123",30), {debug}=w52Debugger();
  let fakeNow=Date.now();
  class FakeDate extends Date {static now(){return fakeNow;}}
  const r=await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123"}], debuggerDriver:debug,
    grantOverride:grant,clock:FakeDate,
    stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
  });
  fakeNow=grant.expiresAt+1;
  debug.emit("message",{},"Network.requestWillBeSent",{
    requestId:"tooLate", request:{url:grant.audioUrl,method:"GET"},type:"Media"
  });
  assert.ok(r.diagnostics.some(x=>x.endsWith("|PLAYER_URL_EXPIRED_AT_REQUEST|resource_id=139")));
});

test("W53 retains repeated 403 and URL classifications per resource, without leaking URLs",async()=>{
  const grant=w52Grant("139"),{debug}=w52Debugger();
  const r=await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123"}],debuggerDriver:debug,grantOverride:grant,
    stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
  });
  for(const [rid,url] of [["native1",grant.audioUrl],["native2",grant.audioUrl]]) {
    debug.emit("message",{},"Network.requestWillBeSent",{
      requestId:rid,request:{url,method:"GET"},type:"Media"
    });
    debug.emit("message",{},"Network.responseReceived",{
      requestId:rid,response:{status:403,headers:{"Content-Type":"text/html"}}
    });
    debug.emit("message",{},"Network.loadingFinished",{requestId:rid});
  }
  assert.equal(r.diagnostics.filter(x=>x.endsWith("|PLAYER_URL_MATCH|resource_id=139")).length,2);
  assert.equal(r.diagnostics.filter(x=>x.endsWith("|PLAYER_403_HTML|resource_id=139")).length,2);
  assert.ok(!JSON.stringify(r.diagnostics).includes(grant.audioUrl));
});
test("W53 body classifier is bounded by known header size or actual transfer length",async()=>{
  const grant=w52Grant("139"),{debug,commands}=w52Debugger('{"error":"invalid_audio_token"}');
  const r=await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123"}],debuggerDriver:debug,grantOverride:grant,
    stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
  });
  for(const [rid,bytes] of [["unbounded",undefined],["too-large",40000],["bounded",240]]) {
    debug.emit("message",{},"Network.requestWillBeSent",{
      requestId:rid,request:{url:grant.audioUrl,method:"GET"},type:"Media"
    });
    debug.emit("message",{},"Network.responseReceived",{
      requestId:rid,response:{status:403,headers:{"Content-Type":"application/json"}}
    });
    debug.emit("message",{},"Network.loadingFinished",
      {requestId:rid,...(bytes===undefined?{}:{encodedDataLength:bytes})});
  }
  await new Promise(resolve=>setTimeout(resolve,6));
  assert.equal(commands.filter(([cmd])=>cmd==="Network.getResponseBody").length,1,
    "unknown and oversized JSON must not be requested for body inspection");
  assert.ok(r.diagnostics.some(x=>x.endsWith("|PLAYER_403_PHP_INVALID_AUDIO_TOKEN|resource_id=139")));
});

test("W53 signed fields are distinguished from harmless order or unrelated query",async()=>{
  const grant=w52Grant("139"), {debug}=w52Debugger();
  const r=await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123"}],debuggerDriver:debug,grantOverride:grant,
    stateOverride:{enabled:true,signedIn:true,apiOrigin:"https://api.celikom.example"}
  });
  const expected=new URL(grant.audioUrl),token=expected.searchParams.get("token");
  const exp=expected.searchParams.get("expires"),sid=expected.searchParams.get("sid");
  for(const [requestId,url,classification] of [
    ["reordered","https://api.celikom.example/api/v1/audio/139?sid="+sid+
      "&expires="+exp+"&token="+token,"PLAYER_URL_SIGNED_FIELDS_INTACT"],
    ["additional",grant.audioUrl+"&locale=en","PLAYER_URL_SIGNED_FIELDS_INTACT"],
    ["damaged",grant.audioUrl.replace("sid="+sid,"sid="+sid+"?vsid=abc"),
      "PLAYER_URL_QUERY_CHANGED"],
    ["duplicate",grant.audioUrl+"&sid=8","PLAYER_URL_QUERY_CHANGED"]
  ]){
    debug.emit("message",{},"Network.requestWillBeSent",{
      requestId,request:{url,method:"GET"},type:"Media"
    });
    assert.ok(r.diagnostics.some(x=>x.endsWith("|"+classification+"|resource_id=139")),classification);
  }
  assert.ok(!JSON.stringify(r.diagnostics).includes(token));
  assert.ok(!JSON.stringify(r.diagnostics).includes(sid+"?vsid"));
});

test("W66 host sanitizer cannot discard D or other letters, still rejects controls",()=>{
  const sourceRegex = source.match(/value\.length <= 720 && !\/([^\n]+)\/\.test\(value\)/);
  assert.ok(sourceRegex,"host has expected bounded display metadata filter");
  const invalid=new RegExp(sourceRegex[1]);
  for (const safe of ["D","TRITIA","kavabanga Depo kolibri",
      "ABCDFHJLNPRTVXZ 02468", "中文 и русский"]) {
    assert.equal(invalid.test(safe),false,"safe title/artist preserved: "+safe);
  }
  assert.equal(invalid.test("\u0000"),true,"NUL still rejected");
  assert.equal(invalid.test("\n"),true,"line break still rejected");
});

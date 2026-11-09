"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const EventEmitter = require("node:events");
const source = fs.readFileSync(path.join(__dirname, "w33-runtime-probe.cjs"), "utf8");

function harness({ initialUrl = "", loading = true, failOnce = false, cdp = false } = {}) {
  const events = [];
  const intervals = [];
  const timeouts = [];
  const app = new EventEmitter();
  let url = initialUrl, isLoading = loading, executions = 0, testUrl = "";
  const debuggerEvents = new EventEmitter();
  let debugAttached = false;
  debuggerEvents.isAttached = () => debugAttached;
  debuggerEvents.attach = () => { debugAttached = true; };
  debuggerEvents.detach = () => { debugAttached = false; };
  debuggerEvents.sendCommand = async () => ({});
  const debuggerMock = Object.assign(new EventEmitter(), {
    attached: false,
    attach() { this.attached = true; },
    detach() { this.attached = false; },
    isAttached() { return this.attached; },
    async sendCommand(_method) { return {}; }
  });
  const view = Object.assign(new EventEmitter(), {
    ...(cdp ? { debugger: debuggerMock } : {}),
    id: 42,
    ...(cdp ? {debugger: debuggerEvents} : {}),
    isDestroyed: () => false,
    getURL: () => url,
    isLoadingMainFrame: () => isLoading,
    executeJavaScript: async () => {
      executions++;
      if (failOnce && executions === 1) throw new Error("navigation");
      if (cdp) {
        const rid = "fake-request-7";
        const invalid = testUrl;
        debuggerEvents.emit("message", {}, "Network.requestWillBeSent", {
          requestId:rid, request:{url:invalid,method:"GET",
            headers:{Origin:"https://unexpected.example",Range:"bytes=0-31"}}
        });
        debuggerEvents.emit("message", {}, "Network.requestWillBeSentExtraInfo", {
          requestId:rid, headers:{Origin:"null"}
        });
        debuggerEvents.emit("message", {}, "Network.responseReceivedExtraInfo", {
          requestId:rid, statusCode:403, headers:{"content-type":"application/json"}
        });
        debuggerEvents.emit("message", {}, "Network.loadingFailed", {
          requestId:rid, corsErrorStatus:{
            corsError:"MissingAllowOriginHeader",
            failedParameter:"UNSAFE_CREDENTIAL_VALUE_NEVER_EMIT"
          }
        });
      }
      return {type:"NATIVE", outcome:"HTTP_403_VISIBLE", csp:"NONE"};
    }
  });
  const request = new EventEmitter();
  request.destroy = () => {};
  const fakeHttps = {
    get: (_url, opts, callback) => {
      assert.equal(opts.headers.Range, "bytes=0-31");
      assert.match(_url, /token=0{64}/);
      testUrl = _url;
      queueMicrotask(() => callback({
        statusCode:403,
        headers:{"access-control-allow-origin":"musicapplication://desktop"},
        resume() {}
      }));
      return request;
    }
  };
  const fakeFs = { appendFileSync(_filename, value) {
    assert.match(value, /^W33_RT_[A-Z0-9_]+\n$/);
    events.push(value.trim());
  }};
  const fakeElectron = {
    app, webContents:{getAllWebContents:()=>[view]}
  };
  const context = {
    process:{env:{CELIKOM_W33_RUNTIME_PROBE:"1",CELIKOM_W23_DEV_DIAG:"CI-only",
      ...(cdp ? {CELIKOM_W37_CDP_PROBE:"1",CELIKOM_W39_CORS_HEADERS:"1"} : {})}},
    require: name => {
      if(name==="node:fs")return fakeFs;
      if(name==="node:https")return fakeHttps;
      if(name==="electron")return fakeElectron;
      throw Error("Unexpected require");
    },
    setTimeout: (fn, ms) => { timeouts.push({fn,ms}); if (ms===750) queueMicrotask(fn); return timeouts.length; },
    setInterval: (fn, ms) => { intervals.push({fn,ms}); return intervals.length; },
    clearInterval: () => {},
    clearTimeout: () => {},
    Date, URL, Set, Map, Promise
  };
  vm.runInNewContext(source, context, {timeout:1000});
  app.emit("web-contents-created", {}, view);
  return {
    app, view, debuggerMock, events, intervals, timeouts,
    setReady(nextUrl="musicapplication://desktop/") { url=nextUrl;isLoading=false;view.emit("dom-ready"); },
    scan() { intervals[0].fn(); },
    executions:()=>executions
  };
}
async function flush() {
  await new Promise(resolve=>setImmediate(resolve));
  await new Promise(resolve=>setImmediate(resolve));
}
test("W36: waits for approved DOM-ready and records main-vs-renderer HTTP independently",async()=>{
  const h=harness();
  await flush();
  assert.equal(h.executions(),0);
  h.setReady();
  await flush();
  assert.equal(h.executions(),1);
  assert.ok(h.events.includes("W33_RT_BOOTSTRAP_ON"));
  assert.ok(h.events.includes("W33_RT_MAIN_HTTP_403"));
  assert.ok(h.events.includes("W33_RT_MAIN_ACAO_NATIVE"));
  assert.ok(h.events.includes("W33_RT_APPROVED_RENDERER_FOUND"));
  assert.ok(h.events.includes("W33_RT_NATIVE_HTTP_403_VISIBLE_CSP_NONE"));
  h.scan();await flush();
  assert.equal(h.executions(),1,"completed result is not repeated");
});
test("W36: poll fallback catches a renderer which was created before listeners",async()=>{
  const h=harness({initialUrl:"musicapplication://desktop/",loading:true});
  h.scan();
  assert.equal(h.executions(),0);
  h.setReady();
  await flush();
  assert.equal(h.executions(),1);
});
test("W36: unapproved remote origin never receives probe",async()=>{
  const h=harness();
  h.setReady("https://example.org/");
  h.scan();await flush();
  assert.equal(h.executions(),0);
  assert.ok(!h.events.includes("W33_RT_APPROVED_RENDERER_FOUND"));
});
test("W36: failed renderer evaluation retries without duplicate in-flight calls",async()=>{
  const h=harness({failOnce:true});
  h.setReady();await flush();
  assert.equal(h.executions(),1);
  assert.ok(h.events.includes("W33_RT_RENDERER_EXECUTION_FAILED"));
  h.scan();await flush();
  assert.equal(h.executions(),2);
  assert.ok(h.events.includes("W33_RT_NATIVE_HTTP_403_VISIBLE_CSP_NONE"));
  h.scan();await flush();
  assert.equal(h.executions(),2);
});
test("W39: passive Chromium CORS categories contain no raw headers, URLs, or failedParameter",async()=>{
  const h=harness({cdp:true});
  h.setReady();
  await flush(); await flush();
  assert.ok(h.events.includes("W33_RT_CDP_REQUEST_SEEN"));
  assert.ok(h.events.includes("W33_RT_CDP_REQUEST_ORIGIN_UNLISTED_HTTPS"));
  assert.ok(h.events.includes("W33_RT_CDP_WIRE_REQUEST_ORIGIN_NULL"));
  assert.ok(h.events.includes("W33_RT_CDP_WIRE_RESPONSE_ACAO_ABSENT"));
  assert.ok(h.events.includes("W33_RT_CDP_WIRE_STATUS_403"));
  assert.ok(h.events.includes("W33_RT_CDP_CORS_ENUM_MISSING_ALLOW_ORIGIN_HEADER"));
  assert.ok(!h.events.join("\\n").includes("UNSAFE_CREDENTIAL_VALUE_NEVER_EMIT"));
  assert.ok(!h.events.join("\\n").includes("unexpected.example"));
  assert.ok(!h.events.join("\\n").includes("hostingersite.com"));
});

test("W39: passive CDP logs only categorical request/response Origin and CORS reason", async()=>{
  const h=harness({cdp:true});
  h.setReady();
  await flush();
  const requestId="secret-request-123";
  const privateUrl="https://darkred-camel-588676.hostingersite.com/api/v1/audio/7?token="+"0".repeat(64)+"&expires=1800000180&sid=1";
  h.debuggerMock.emit("message",{}, "Network.requestWillBeSent", {
    requestId,
    request:{url:privateUrl, method:"GET", headers:{Origin:"null","Authorization":"secret-private"}}
  });
  h.debuggerMock.emit("message",{},"Network.responseReceivedExtraInfo",{
    requestId,statusCode:403,headers:{"Access-Control-Allow-Origin":"https://music.yandex.ru","Set-Cookie":"secret-private"}
  });
  h.debuggerMock.emit("message",{},"Network.loadingFailed",{
    requestId,corsErrorStatus:{corsError:"MissingAllowOriginHeader", failedParameter:"secret-private"}
  });
  assert.ok(h.events.includes("W33_RT_CDP_REQUEST_SEEN"));
  assert.ok(h.events.includes("W33_RT_CDP_REQUEST_ORIGIN_NULL"));
  assert.ok(h.events.includes("W33_RT_CDP_WIRE_STATUS_403"));
  assert.ok(h.events.includes("W33_RT_CDP_WIRE_RESPONSE_ACAO_MUSIC_WEB"));
  assert.ok(h.events.includes("W33_RT_CDP_CORS_ENUM_MISSING_ALLOW_ORIGIN_HEADER"));
  assert.equal(h.events.some(e=>e.includes("secret-private")||e.includes("token=")),false);
  h.timeouts.filter(t=>t.ms===750).forEach(t=>t.fn());
  await flush();
});
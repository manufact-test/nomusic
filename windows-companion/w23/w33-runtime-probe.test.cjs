"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const EventEmitter = require("node:events");
const source = fs.readFileSync(path.join(__dirname, "w33-runtime-probe.cjs"), "utf8");

function harness({ initialUrl = "", loading = true, failOnce = false } = {}) {
  const events = [];
  const intervals = [];
  const timeouts = [];
  const app = new EventEmitter();
  let url = initialUrl, isLoading = loading, executions = 0;
  const view = Object.assign(new EventEmitter(), {
    id: 42,
    isDestroyed: () => false,
    getURL: () => url,
    isLoadingMainFrame: () => isLoading,
    executeJavaScript: async () => {
      executions++;
      if (failOnce && executions === 1) throw new Error("navigation");
      return {type:"NATIVE", outcome:"HTTP_403_VISIBLE", csp:"NONE"};
    }
  });
  const request = new EventEmitter();
  request.destroy = () => {};
  const fakeHttps = {
    get: (_url, opts, callback) => {
      assert.equal(opts.headers.Range, "bytes=0-31");
      assert.match(_url, /token=0{64}/);
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
    process:{env:{CELIKOM_W33_RUNTIME_PROBE:"1",CELIKOM_W23_DEV_DIAG:"CI-only"}},
    require: name => {
      if(name==="node:fs")return fakeFs;
      if(name==="node:https")return fakeHttps;
      if(name==="electron")return fakeElectron;
      throw Error("Unexpected require");
    },
    setTimeout: (fn, ms) => { timeouts.push({fn,ms}); return timeouts.length; },
    setInterval: (fn, ms) => { intervals.push({fn,ms}); return intervals.length; },
    clearInterval: () => {},
    clearTimeout: () => {},
    Date, URL, Set, Map, Promise
  };
  vm.runInNewContext(source, context, {timeout:1000});
  return {
    app, view, events, intervals, timeouts,
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
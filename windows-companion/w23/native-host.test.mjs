import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { EventEmitter } from "node:events";

const source = fs.readFileSync(new URL("./host.cjs", import.meta.url), "utf8");

async function runHost(url, { queue = [], token = "a".repeat(64) } = {}) {
  const diagnostics = [], evaluated = [], network = [];
  let drained = false;
  const view = {
    isDestroyed: () => false,
    getURL: () => url,
    on: () => {},
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
            : {enabled:false,signedIn:false,apiOrigin:""};
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
  return {diagnostics,evaluated,network};
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
    assert.ok(evaluated.every(js=>!js.includes("a".repeat(64))),"token never leaked to renderer");
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
  assert.ok(evaluated.every(s=>!s.includes("a".repeat(64))),"bridge capability never injected");
});
test("foreign track ID cannot trigger a localhost resolve request",async()=>{
  const {network}=await runHost("musicapplication://desktop/",{
    queue:[{requestId:"1",trackId:"123/../../admin"}]
  });
  assert.equal(network.filter(r=>r.path.startsWith("/v1/resolve")).length,0);
});

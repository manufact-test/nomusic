import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(new URL("./host.cjs", import.meta.url), "utf8");

async function runHost(url) {
  const diagnostics = [];
  const evaluated = [];
  const view = {
    isDestroyed:() => false, getURL:() => url,
    executeJavaScript:async script => {evaluated.push(script);}
  };
  const fakeFs = {
    readFileSync:filename=>filename.includes("renderer.js")
      ? "window.__celikomBridgeSetToken=()=>{};"
      : "a".repeat(64),
    appendFileSync:(_filename,line)=>diagnostics.push(line.trim())
  };
  const fakeElectron = {
    app:{getAppPath:()=>"/virtual",on:()=>{}},
    webContents:{getAllWebContents:()=>[view]}
  };
  const context = {
    require:name=>name==="electron"?fakeElectron:name==="node:fs"?fakeFs:requireNodePath(),
    process:{env:{LOCALAPPDATA:"C:\\Users\\test",CELIKOM_W23_DEV_DIAG:"diagnostics.log"}},
    URL,WeakMap,Set,JSON,console,
    setInterval:fn=>{fn();return{unref(){}}}
  };
  // The legitimate host's Node JS source is unchanged: only the Electron
  // app and filesystem are replaced with narrow fake dependencies.
  vm.runInNewContext(source, context, {timeout:1200});
  await new Promise(resolve=>setImmediate(resolve));
  return {diagnostics,evaluated};
}
function requireNodePath() {
  return {
    join:(...items)=>items.join("\\"),
    resolve:filename=>filename
  };
}
test("case-preserved native musicapplication origin allows automatic bridge",async()=>{
  for(const address of ["musicapplication://desktop/","musicapplication://Desktop/","MUSICAPPLICATION://DESKTOP/"]){
    const {diagnostics,evaluated}=await runHost(address);
    assert.ok(diagnostics.includes("APPROVED_VIEW"),address);
    assert.ok(diagnostics.includes("RENDERER_INJECTED"),address);
    assert.equal(evaluated.length,1,address);
    assert.ok(evaluated[0].includes("__celikomBridgeSetToken"),address);
  }
});
test("does not inject into foreign renderer protocols or hosts",async()=>{
  for(const address of ["https://unrelated.example/","musicapplication://evil/","file:///C:/index.html"]){
    const {diagnostics,evaluated}=await runHost(address);
    assert.equal(evaluated.length,0,address);
    assert.ok(diagnostics.includes("VIEW_NOT_APPROVED")||diagnostics.includes("VIEW_UNKNOWN_URL"));
  }
});

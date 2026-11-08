/**
 * W7 external, fixture-only CDP sidecar (Node 22).
 * Only Runtime.enable and Runtime.evaluate are implemented. No Network,
 * cookies, DOMStorage, user profiles, arbitrary hosts or installed Yandex.
 */
import { classifyDebugTarget, productionDecision } from "./session-policy.mjs";

const [portArg, origin, nonce] = process.argv.slice(2);
const port = Number(portArg);
const reject = reason => { throw Error("W7_"+reason); };
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const abortAfter=ms=>AbortSignal.timeout(ms);

function connect(wsUrl) {
  return new Promise((resolve,reject) => {
    const socket=new WebSocket(wsUrl);
    const timeout=setTimeout(()=>reject(Error("W7_WEBSOCKET_TIMEOUT")),8000);
    socket.addEventListener("open",()=>{clearTimeout(timeout);resolve(socket);},{once:true});
    socket.addEventListener("error",()=>{clearTimeout(timeout);reject(Error("W7_WEBSOCKET_FAILED"));},{once:true});
  });
}

function protocol(socket) {
  let next=0;
  const pending=new Map();
  socket.addEventListener("message",ev=>{
    let msg;
    try{msg=JSON.parse(ev.data);}catch{return;}
    if(!pending.has(msg.id))return;
    const {resolve,reject,timer}=pending.get(msg.id);
    clearTimeout(timer);pending.delete(msg.id);
    if(msg.error)reject(Error("W7_PROTOCOL_REJECTED_"+(msg.error.code||"UNKNOWN")));
    else resolve(msg.result);
  });
  const call=(method,params={},timeoutMs=10000)=>{
    if(!["Runtime.enable","Runtime.evaluate"].includes(method))
      reject("UNAPPROVED_CDP_METHOD");
    return new Promise((resolve,reject)=>{
      const id=++next,timer=setTimeout(()=>{
        pending.delete(id);reject(Error("W7_CDP_TIMEOUT_"+method));
      },timeoutMs);
      pending.set(id,{resolve,reject,timer});
      socket.send(JSON.stringify({id,method,params}));
    });
  };
  const evaluate=async(expression,timeoutMs=20000)=>{
    const result=await call("Runtime.evaluate",{
      expression,returnByValue:true,awaitPromise:true,generatePreview:false,
      silent:true,includeCommandLineAPI:false
    },timeoutMs);
    if(result?.exceptionDetails || result?.result?.subtype==="error")
      reject("RENDERER_EXPRESSION_FAILED");
    return result?.result?.value;
  };
  return {call,evaluate};
}

async function run() {
  const deadline=Date.now()+15000;
  const endpoint="http://127.0.0.1:"+port+"/json/list";
  if(productionDecision().allowDebugPortOnUserYandex)
    reject("PRODUCTION_DEBUG_PERMISSION_MUST_BE_FALSE");
  let target;
  while(Date.now()<deadline){
    try {
      const response=await fetch(endpoint,{signal:abortAfter(2000),redirect:"error"});
      if(response.ok){
        const list=await response.json();
        target=Array.isArray(list)?list.find(item=>
          classifyDebugTarget({target:item,debuggerPort:port,fixtureOrigin:origin,nonce}).accepted):null;
      }
    }catch{}
    if(target)break;
    await sleep(150);
  }
  if(!target)reject("FIXTURE_TARGET_NOT_FOUND");
  const gate=classifyDebugTarget({target,debuggerPort:port,fixtureOrigin:origin,nonce});
  if(!gate.accepted)reject("FIXTURE_TARGET_REJECTED");
  const socket=await connect(target.webSocketDebuggerUrl);
  try{
    const cdp=protocol(socket);
    await cdp.call("Runtime.enable",{},5000);
    const check='(() => JSON.stringify({title:document.title,origin:location.origin,'+
      'nonceMatch:(new URL(location.href)).searchParams.get("nonce")==='+JSON.stringify(nonce)+','+
      'publicFactories:Boolean(window.__nativeFixture?.req)}))()';
    const observed=JSON.parse(await cdp.evaluate(check,10000));
    if(observed.title!=="CELIKOM W7 isolated attach"||observed.origin!==origin||
       observed.nonceMatch!==true||observed.publicFactories!==true)
      reject("RUNTIME_HANDSHAKE_MISMATCH");
    // This evaluation DOES run JS, but ONLY inside the non-authenticated
    // synthetic page that just passed strict title/origin/nonce guards.
    // Never use it on a user Yandex session, even with consent.
    const expr='import("/activation.mjs").then(m=>m.runW7('+JSON.stringify(nonce)+'))';
    const result=await cdp.evaluate(expr,90000);
    if(!result?.passed || result.scope!=="ISOLATED_FIXTURE_ONLY" ||
       result.officialAppTested!==false || result.assertions<20)
      reject("ATTACH_ASSERTIONS_FAILED");
    console.log(JSON.stringify({
      scope:"W7_LOCAL_DEBUG_FIXTURE_ONLY", result:"PASS",
      assertions:result.assertions,checks:result.checks,
      officialYandexTouched:false,
      debugPortSafeForRealClients:false
    }));
  }finally{socket.close();}
}

run().catch(error=>{
  // Only bounded error codes; do not print debugging URLs, session data or paths.
  console.error(String(error?.message||"W7_ATTACH_FAILED").slice(0,160));
  process.exitCode=1;
});

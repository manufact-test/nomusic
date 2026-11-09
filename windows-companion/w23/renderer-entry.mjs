import {createNativeResourceAdapter} from "../w22/native-resource-adapter.mjs";
(() => {
  "use strict";
  if (window.__celikomBridgeSetToken) return;
  const endpoint = "http://127.0.0.1:21471";
  const approved = new Set(["https://desktop.app.music.yandex.net", "https://music.yandex.ru", "https://next.music.yandex.ru", "https://music.yandex.com"]);
  if (!approved.has(window.location.origin) &&
      !(window.location.protocol.toLowerCase()==="musicapplication:"&&window.location.hostname.toLowerCase()==="desktop"))
    return;
  let token="", apiOrigin="", stopped=false, attached=false, polling=false, lastState="";
  const validToken = value => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
  const headers = () => ({ "X-Celikom-Bridge-Token": token, "X-Celikom-Native-Host": "1" });

  async function request(path, options={}) {
    if (!validToken(token)) throw new Error("CELIKOM_UNPAIRED");
    const response = await fetch(endpoint + path, {
      method:options.method||"GET",
      headers:{...headers(), ...(options.body ? {"Content-Type":"application/json"}:{})},
      body:options.body ? JSON.stringify(options.body):undefined,
      credentials:"omit",cache:"no-store",referrerPolicy:"no-referrer",
      signal:options.signal
    });
    if (!response.ok) throw new Error("CELIKOM_LOCAL_UNAVAILABLE");
    return await response.json();
  }
  function cleanOrigin(value) {
    try {
      const uri=new URL(value);
      if (uri.protocol==="https:" && uri.origin===value && !uri.username &&
          !uri.password && uri.pathname==="/" && !uri.search && !uri.hash) return value;
    } catch {}
    return "";
  }
  const adapter=createNativeResourceAdapter({
    allowedOrigin:()=>apiOrigin,
    resolve:async (id,signal)=>{
      const response=await request("/v1/resolve?track_id="+encodeURIComponent(id),{signal});
      return response.found===true ? response.grant??null : null;
    }
  });
  function attachResource() {
    if (attached||stopped) return attached;
    const chunks=window.webpackChunk_N_E;
    if (!Array.isArray(chunks)) return false;
    let requireFn;
    try {
      const marker=Symbol("celikom-source");
      chunks.push([[marker],{},r=>{requireFn=r;}]);chunks.pop();
    } catch {return false;}
    if (!requireFn?.m||typeof requireFn!=="function") return false;
    for (const id in requireFn.m) {
      const factory=requireFn.m[id];
      if (typeof factory!=="function") continue;
      let src;
      try{src=factory.toString();}catch{continue;}
      if (!src.includes('"get-file-info"')&&!src.includes('"resources/v2/file-info"'))continue;
      let mod;
      try{mod=requireFn(id);}catch{continue;}
      for (const k in mod) {
        const Type=mod[k];
        if (!Type||typeof Type!=="function"||!Type.prototype||
            typeof Type.prototype.getFileInfo!=="function") continue;
        try {
          adapter.attach(Type.prototype);
          attached=true;
          console.info("[CELIKOM] Native file-info source connector attached");
          return true;
        }catch{continue;}
      }
    }
    return false;
  }
  async function heartbeat() {
    if (!validToken(token)) return;
    let status="ORIGINAL";
    if (adapter.enabled&&attached)status=adapter.status==="SOURCE_MAPPING_RETURNED_NOT_AUDIO_VERIFIED"
      ?"NATIVE_MAPPING_ACCEPTED":"NATIVE_CONNECTED";
    if (status===lastState) return;
    lastState=status;
    try {await request("/v1/heartbeat",{method:"POST",body:{trackId:null,status}});}
    catch {lastState="";}
  }
  async function poll() {
    if (polling||stopped) return;
    polling=true;
    try {
      if(!validToken(token)){adapter.disable();return;}
      const state=await request("/v1/state");
      const origin=cleanOrigin(state.apiOrigin);
      if(origin!==apiOrigin){adapter.disable();apiOrigin=origin;}
      if(state.enabled===true&&state.signedIn===true&&origin&&attached)adapter.enable();
      else adapter.disable();
      await heartbeat();
    }catch{adapter.disable();lastState="";}
    finally{polling=false;}
  }
  window.__celikomBridgeSetToken=value=>{
    if(stopped||!validToken(value)){adapter.disable();return;}
    if(token!==value){token=value;adapter.disable();apiOrigin="";}
    void poll();
  };
  const finder=setInterval(()=>{if(attachResource()){clearInterval(finder);void poll();}},300);
  let attempts=0;
  const cap=setInterval(()=>{if(attached||++attempts>=35){clearInterval(cap);if(!attached)clearInterval(finder);}},1000);
  attachResource();
  const pollTimer=setInterval(()=>void poll(),2600);
  window.addEventListener("beforeunload",()=>{
    stopped=true;clearInterval(pollTimer);clearInterval(finder);clearInterval(cap);
    adapter.dispose();delete window.__celikomBridgeSetToken;
  },{once:true});
})();

"use strict";
const {app,webContents}=require("electron");
const fs=require("node:fs");
const path=require("node:path");
const approvedOrigins=new Set([
 "https://desktop.app.music.yandex.net",
 "https://music.yandex.ru",
 "https://next.music.yandex.ru",
 "https://music.yandex.com"
]);
const capability=path.join(process.env.LOCALAPPDATA||"","CELIKOM","Windows","native-bridge.key");
let js="";
try{js=fs.readFileSync(path.join(app.getAppPath(),"celikom","renderer.js"),"utf8");}catch{}
const seen=new WeakMap();
const diagnostic=process.env.CELIKOM_W23_DEV_DIAG||"";
function report(code){
  if(!diagnostic||!/^[A-Z_]{3,48}$/.test(code))return;
  try{fs.appendFileSync(diagnostic,code+"\n");}catch{}
}
report("HOST_LOADED");
const noted=new Set();
function note(code) {if (!noted.has(code)) {noted.add(code);report(code);} }
if (!js) note("BUNDLE_MISSING"); else note("BUNDLE_PRESENT");
function getToken(){
  try{
    const t=fs.readFileSync(capability,"utf8").trim();
    return /^[a-f0-9]{64}$/.test(t)?t:"";
  }catch{return "";}
}
function validView(view){
  try {
    if (view.isDestroyed()) return false;
    const url=new URL(view.getURL());
    const scheme=(url.protocol||"unknown").replace(/[^a-z]/gi,"").toUpperCase();
    note("ORIGIN_SCHEME_"+scheme.slice(0,28));
    const hostname=url.hostname.toUpperCase().replace(/[^A-Z0-9]/g,"_").slice(0,35);
    if (hostname) note("ORIGIN_HOST_"+hostname);
    if (approvedOrigins.has(url.origin) ||
        (url.protocol==="musicapplication:"&&url.hostname==="desktop")) {
      note("APPROVED_VIEW");return true;
    }
    note("VIEW_NOT_APPROVED");
  } catch {note("VIEW_UNKNOWN_URL");}
  return false;
}
async function update(view){
  if(!js||!validView(view))return;
  const secret=getToken();
  if(!secret){note("BOOTSTRAP_KEY_MISSING");return;}
  note("BOOTSTRAP_KEY_PRESENT");
  if(seen.get(view)===secret)return;
  const source=";(()=>{if(!window.__celikomBridgeSetToken){"+
    js+"\n}if(window.__celikomBridgeSetToken)window.__celikomBridgeSetToken("+
    JSON.stringify(secret)+");})()";
  try{await view.executeJavaScript(source);seen.set(view,secret);report("RENDERER_INJECTED");}
  catch{note("RENDERER_EVALUATION_FAILED");}
}
app.on("web-contents-created",(_event,view)=>{
  view.on("console-message",(event,_level,legacyMessage)=>{
    const message=typeof event?.message==="string"?event.message:legacyMessage;
    if(message==="[CELIKOM] Native file-info source connector attached")report("RESOURCE_ATTACHED");
  });
  view.on("dom-ready",()=>{seen.delete(view);void update(view);});
  view.on("did-finish-load",()=>{seen.delete(view);void update(view);});
});
const refresher=setInterval(()=>{
  const views=webContents.getAllWebContents();
  if(views.length>0)note("WEB_CONTENTS_PRESENT");
  else note("NO_WEB_CONTENTS_YET");
  for(const view of views)void update(view);
},2800);
if(refresher.unref)refresher.unref();

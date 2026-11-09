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
function getToken(){
  try{
    const t=fs.readFileSync(capability,"utf8").trim();
    return /^[a-f0-9]{64}$/.test(t)?t:"";
  }catch{return "";}
}
function validView(view){
  try{return !view.isDestroyed()&&approvedOrigins.has(new URL(view.getURL()).origin);}
  catch{return false;}
}
async function update(view){
  if(!js||!validView(view))return;
  const secret=getToken();
  if(!secret||seen.get(view)===secret)return;
  const source=";(()=>{if(!window.__celikomBridgeSetToken){"+
    js+"\n}if(window.__celikomBridgeSetToken)window.__celikomBridgeSetToken("+
    JSON.stringify(secret)+");})()";
  try{await view.executeJavaScript(source);seen.set(view,secret);report("RENDERER_INJECTED");}
  catch{}
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
  for(const view of webContents.getAllWebContents()) void update(view);
},2800);
if(refresher.unref)refresher.unref();

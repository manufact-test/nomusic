"use strict";
/* W12 disposable Electron fixture — NEVER launch the owner's Yandex EXE. */
const {app,BrowserWindow}=require("electron");
const {existsSync,readFileSync,lstatSync}=require("node:fs");
const {resolve,relative,sep}=require("node:path");
const {tmpdir}=require("node:os");
const root=process.env.CELIKOM_W12_ROOT;
const profile=process.env.CELIKOM_W12_PROFILE;
const nonce=process.env.CELIKOM_W12_NONCE;
function safe(){
  try{
    const rootPath=resolve(root),profilePath=resolve(profile);
    const rel=relative(rootPath,profilePath);
    return process.env.CELIKOM_W12_FIXTURE_ONLY==="YES" &&
      /^[a-f0-9]{32}$/.test(nonce||"") &&
      rootPath.startsWith(resolve(tmpdir())+sep) &&
      rootPath.split(/[\\/]/).at(-1).startsWith("celikom-w12-generated-only-") &&
      rel!=="" && rel!==".." && !rel.startsWith(".."+sep) &&
      !lstatSync(rootPath).isSymbolicLink() &&
      !lstatSync(profilePath).isSymbolicLink() &&
      readFileSync(resolve(rootPath,".w12-marker"),"utf8")==="CELIKOM-W12-GENERATED-ONLY\n";
  }catch{return false;}
}
if(!safe())app.exit(81);
else{
  app.setName("CELIKOM-W12-SYNTHETIC");
  app.setPath("userData",resolve(profile));
  const gotLock=app.requestSingleInstanceLock({syntheticOnly:true});
  if(!gotLock){
    process.stdout.write("W12_SECONDARY_DENIED=1\n");
    app.quit();
  }else{
    app.on("second-instance",()=>{
      process.stdout.write("W12_SECOND_INSTANCE_FORWARDED=1\n");
    });
    app.whenReady().then(async()=>{
      try{
        const win=new BrowserWindow({show:false,
          webPreferences:{sandbox:true,nodeIntegration:false,
            contextIsolation:true,webSecurity:true}});
        await win.loadURL("data:text/html,<title>CELIKOM-W12-SYNTHETIC</title>");
        process.stdout.write("W12_PRIMARY_READY=1\n");
      }catch{app.exit(82);}
    });
    app.on("before-quit",()=>app.releaseSingleInstanceLock());
  }
}

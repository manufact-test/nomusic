import { readStagedUpload, deleteStagedUpload } from "../upload/staging.js";
import { createUploadJournal } from "../upload/upload-journal.js";

export const UPLOAD_STATE_KEY = "celikom_background_upload_v1";
const journal = createUploadJournal(chrome.storage.local);
let active = null;
let stateWrites = Promise.resolve();
function update(task, phase, extras = {}) {
  const publicState = {
    id:task.id, trackId:task.trackId, phase,
    percent: Number.isInteger(extras.percent) ? extras.percent : 0,
    code: typeof extras.code === "string" ? extras.code.slice(0,40) : "",
    at: Date.now()
  };
  stateWrites = stateWrites.catch(() => {}).then(() =>
    chrome.storage.local.set({[UPLOAD_STATE_KEY]:publicState})).catch(() => {});
  return stateWrites;
}
async function execute(task) {
  let xhr = null, watchdog = null;
  let failure = "", sent = 0, firstByte = false, startAt = Date.now(), lastPercent = -1;
  let done = false;
  try {
    if (!/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(task.id) ||
        !/^[1-9]\d{0,23}$/.test(task.trackId) ||
        !/^[a-f0-9]{64}$/.test(task.token) ||
        !Number.isInteger(task.durationMs) || task.durationMs < 1000 || task.durationMs > 86400000) {
      throw new Error("invalid_upload_metadata");
    }
    const config = await (await fetch(chrome.runtime.getURL("api/config.json"))).json();
    if (!config.baseUrl || task.origin !== new URL(config.baseUrl).origin || !task.origin.startsWith("https://")) {
      throw new Error("upload_origin_invalid");
    }
    const file = await readStagedUpload(task.id);
    await update(task, "connecting");
    void journal.record(task.id, "connecting");
    const data = new FormData();
    data.append("service","yandex");
    data.append("track_id",task.trackId);
    data.append("duration_ms",String(task.durationMs));
    for (const key of ["artist","title","album"]) data.append(key,typeof task[key] === "string" ? task[key] : "");
    data.append("declaration","1");
    data.append("request_id",task.id);
    data.append("file",file,typeof task.filename === "string" ? task.filename.slice(0,200) : "audio.mp3");
    xhr = new XMLHttpRequest();
    active.xhr = xhr;
    xhr.open("POST",task.origin+"/api/v1/uploads");
    xhr.timeout=120000;
    xhr.setRequestHeader("Authorization","Bearer "+task.token);
    xhr.setRequestHeader("X-Celikom-Upload-Attempt",task.id);
    xhr.upload.addEventListener("progress",event=>{
      if (done) return;
      if (event.loaded > 0) firstByte = true;
      sent = event.loaded;
      const percent = event.lengthComputable && event.total ? Math.floor(event.loaded/event.total*100) : 0;
      if (Math.floor(percent/10) !== Math.floor(lastPercent/10)) {
        lastPercent = percent;
        void journal.record(task.id,"transferring",{sent,percent});
      }
      if (percent !== active.lastPercent) {
        active.lastPercent = percent;
        void update(task,"transferring",{percent});
      }
    });
    xhr.upload.addEventListener("load",()=>{
      firstByte=true;
      void journal.record(task.id,"server_wait");
      void update(task,"server_wait",{percent:100});
    });
    xhr.addEventListener("timeout",()=>{failure="timeout";});
    xhr.addEventListener("error",()=>{failure="network_error";});
    xhr.addEventListener("abort",()=>{failure=active?.cancelled?"cancelled":failure||"interrupted";});
    watchdog = setInterval(()=>{
      if (done || firstByte || !xhr) return;
      const elapsed = Date.now()-startAt;
      if (elapsed > 15000 && !active.waitNoted) {
        active.waitNoted=true;
        void journal.record(task.id,"waiting");
        void update(task,"waiting");
      }
      if (elapsed > 45000) {failure="stalled";xhr.abort();}
    },3000);
    await new Promise(resolve=>{
      xhr.addEventListener("loadend",resolve,{once:true});
      try {xhr.send(data);} catch {failure="network_error";resolve(null);}
    });
    done=true;
    let body = {};
    try {body=JSON.parse(xhr.responseText||"{}");}catch{}
    const code = typeof body.error === "string" && /^[a-z0-9_]{2,40}$/.test(body.error) ? body.error : "";
    const success = xhr.status===202 && body.status==="pending" && Number.isSafeInteger(body.replacement_id);
    const duplicate = ["track_pending","track_already_approved","already_approved"].includes(code);
    if (success || duplicate) {
      const phase=success?"completed":"duplicate";
      void journal.record(task.id,phase,{httpStatus:xhr.status,code:duplicate?code:"accepted"});
      await update(task,phase,{percent:100,code:duplicate?code:""});
    } else {
      const reason=failure||code||(xhr.status>=500?"server_unavailable":"http_error");
      void journal.record(task.id,"failed",{httpStatus:xhr.status,code:reason});
      await update(task,reason==="cancelled"?"cancelled":"failed",{percent:Math.max(0,lastPercent),code:reason});
    }
  } catch {
    void journal.record(task.id,"failed",{code:"upload_background_error"});
    await update(task,"failed",{code:"upload_background_error"});
  } finally {
    done=true;
    if(watchdog) clearInterval(watchdog);
    try {await deleteStagedUpload(task.id);}catch{}
    if(active?.id===task.id) active=null;
  }
}
chrome.runtime.onMessage.addListener((message,sender,respond)=>{
  if(sender?.id!==chrome.runtime.id || !message || typeof message!=="object") return false;
  if(message.type==="CELIKOM_UPLOAD_EXECUTE"){
    if(active){respond({ok:false,error:"upload_busy"});return false;}
    if(!message.task || typeof message.task.id!=="string"){respond({ok:false,error:"invalid_request"});return false;}
    active={id:message.task.id,xhr:null,cancelled:false,lastPercent:-1,waitNoted:false};
    void execute(message.task);
    respond({ok:true});
    return false;
  }
  if(message.type==="CELIKOM_UPLOAD_INTERRUPT"){
    if(!active || active.id!==message.id){respond({ok:false,error:"upload_not_active"});return false;}
    active.cancelled=true;
    active.xhr?.abort();
    respond({ok:true});
    return false;
  }
  return false;
});

import { readStagedUpload, deleteStagedUpload } from "../upload/staging.js";
// Offscreen documents have chrome.runtime but not chrome.storage. The service
// worker owns all status persistence and sanitizes reports from this document.
let active = null;
function update(task, phase, extras = {}) {
  return chrome.runtime.sendMessage({
    type:"CELIKOM_UPLOAD_STATUS",id:task.id,trackId:task.trackId,
    phase,percent:Number.isInteger(extras.percent)?extras.percent:0,
    code:typeof extras.code==="string"?extras.code.slice(0,40):"",
    sent:Number.isSafeInteger(extras.sent)?extras.sent:0,
    httpStatus:Number.isInteger(extras.httpStatus)?extras.httpStatus:0,
    retryAfterSeconds:Number.isInteger(extras.retryAfterSeconds)&&extras.retryAfterSeconds>0&&extras.retryAfterSeconds<=3600?extras.retryAfterSeconds:0
  }).catch(()=>{});
}
async function execute(task, operation) {
  let xhr = null, watchdog = null;
  let failure = "", sent = 0, firstByte = false, lastProgressAt = Date.now(), lastPercent = 0, bodySent = false;
  let done = false, terminal = null;
  const checkCancelled = () => { if(operation.cancelled)throw new Error("cancelled"); };
  const preparing = promise => Promise.race([promise,operation.cancellation.then(()=>{throw new Error("cancelled");})]).then(value=>{checkCancelled();return value;});
  try {
    if (!/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(task.id) ||
        !/^[1-9]\d{0,23}$/.test(task.trackId) ||
        !/^[a-f0-9]{64}$/.test(task.token) ||
        !Number.isInteger(task.durationMs) || task.durationMs < 1000 || task.durationMs > 86400000) {
      throw new Error("invalid_upload_metadata");
    }
    const response = await preparing(fetch(chrome.runtime.getURL("api/config.json")));
    const config = await preparing(response.json());
    if (!config.baseUrl || task.origin !== new URL(config.baseUrl).origin || !task.origin.startsWith("https://")) {
      throw new Error("upload_origin_invalid");
    }
    const file = await preparing(readStagedUpload(task.id));
    await preparing(update(task, "connecting"));
    const data = new FormData();
    data.append("service","yandex");
    data.append("track_id",task.trackId);
    data.append("duration_ms",String(task.durationMs));
    for (const key of ["artist","title","album"]) data.append(key,typeof task[key] === "string" ? task[key] : "");
    data.append("declaration","1");
    data.append("request_id",task.id);
    data.append("file",file,typeof task.filename === "string" ? task.filename.slice(0,200) : "audio.mp3");
    xhr = new XMLHttpRequest();
    operation.xhr = xhr;
    xhr.open("POST",task.origin+"/api/v1/uploads");
    xhr.timeout=120000;
    xhr.setRequestHeader("Authorization","Bearer "+task.token);
    xhr.setRequestHeader("X-Celikom-Upload-Attempt",task.id);
    xhr.upload.addEventListener("progress",event=>{
      if (done || operation.cancelled) return;
      if (event.loaded > sent) {lastProgressAt=Date.now();operation.waitNoted=false;}
      if (event.loaded > 0) firstByte = true;
      sent = event.loaded;
      const percent = event.lengthComputable && event.total ? Math.floor(event.loaded/event.total*100) : 0;
      if (percent !== lastPercent || !operation.progressNoted) {
        lastPercent = percent;operation.progressNoted=true;
        void update(task,"transferring",{percent,sent});
      }
    });
    xhr.upload.addEventListener("load",()=>{
      if(done || operation.cancelled)return;
      firstByte=true;bodySent=true;lastPercent=100;
      void update(task,"server_wait",{percent:100,sent});
    });
    xhr.addEventListener("timeout",()=>{failure="timeout";});
    xhr.addEventListener("error",()=>{failure="network_error";});
    xhr.addEventListener("abort",()=>{failure=operation.cancelled?"cancelled":failure||"interrupted";});
    watchdog = setInterval(()=>{
      if (done || bodySent || !xhr || operation.cancelled) return;
      const idle = Date.now()-lastProgressAt;
      if (idle > 15000 && !operation.waitNoted) {
        operation.waitNoted=true;
        void update(task,"waiting",{percent:lastPercent,sent,code:firstByte?"transfer_idle":""});
      }
      if (idle > (firstByte?30000:45000)) {failure="stalled";xhr.abort();}
    },3000);
    await new Promise(resolve=>{
      xhr.addEventListener("loadend",resolve,{once:true});
      try {checkCancelled();lastProgressAt=Date.now();xhr.send(data);} catch {failure="network_error";resolve(null);}
    });
    done=true;
    let body = {};
    try {body=JSON.parse(xhr.responseText||"{}");}catch{}
    const code = typeof body.error === "string" && /^[a-z0-9_]{2,40}$/.test(body.error) ? body.error : "";
    const success = xhr.status===202 && body.status==="pending" && Number.isSafeInteger(body.replacement_id);
    const duplicate = ["track_pending","track_already_approved","already_approved"].includes(code);
    if (success || duplicate) {
      const phase=success?"completed":"duplicate";
      terminal={phase,details:{percent:100,code:duplicate?code:"",httpStatus:xhr.status,sent}};
    } else {
      const reason=failure||code||(xhr.status>=500?"server_unavailable":"http_error");
      terminal={phase:reason==="cancelled"?"cancelled":"failed",details:{percent:Math.max(0,lastPercent),code:reason,httpStatus:xhr.status,retryAfterSeconds:body.retry_after_seconds,sent}};
    }
  } catch {
    terminal={phase:operation.cancelled?"cancelled":"failed",details:{code:operation.cancelled?"cancelled":"upload_background_error",percent:lastPercent,sent}};
  } finally {
    done=true;
    if(watchdog) clearInterval(watchdog);
    try {await deleteStagedUpload(task.id);}catch{}
    if(terminal)await update(task,terminal.phase,terminal.details);
    if(active===operation) active=null;
  }
}
chrome.runtime.onMessage.addListener((message,sender,respond)=>{
  const fromWorker = sender?.id===chrome.runtime.id && !sender?.tab &&
    (!sender?.url || sender.url===chrome.runtime.getURL("background/service-worker.js"));
  if(!fromWorker || !message || typeof message!=="object") return false;
  if(message.type==="CELIKOM_UPLOAD_EXECUTE"){
    if(!message.task || typeof message.task.id!=="string"){respond({ok:false,error:"invalid_request"});return false;}
    const begin=()=>{
      if(active){respond({ok:active.id===message.task.id&&!active.cancelled,error:active.id===message.task.id&&!active.cancelled?undefined:"upload_busy"});return;}
      const operation={id:message.task.id,xhr:null,cancelled:false,waitNoted:false,progressNoted:false,cancellation:null,cancel:null,finished:null};
      operation.cancellation=new Promise(resolve=>{operation.cancel=resolve;});
      active=operation;operation.finished=execute(message.task,operation);
      respond({ok:true});
    };
    if(active?.cancelled){void active.finished.then(begin);return true;}
    begin();return false;
  }
  if(message.type==="CELIKOM_UPLOAD_INTERRUPT"){
    if(!active || active.id!==message.id){respond({ok:false,error:"upload_not_active"});return false;}
    const operation=active;
    operation.cancelled=true;
    operation.cancel();
    operation.xhr?.abort();
    void operation.finished.then(()=>respond({ok:true}),()=>respond({ok:false,error:"upload_background_error"}));
    return true;
  }
  return false;
});

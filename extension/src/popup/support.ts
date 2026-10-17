import { buildSongReport, reportCategories } from "./song-report.js";
import { uploadTargetFromStatus } from "../upload/contract.js";
export function supportEmail(value: unknown): string {
  const email = typeof value === "string" ? value.trim() : "";
  return email.length <= 254 && /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,63}$/.test(email) ? email : "";
}

export function supportMessage(description: string, version: string, state: any): string {
  return description.trim().slice(0, 2000);
}

export async function initSupport(options: any = {}): Promise<void> {
  const doc = options.document || document;
  const panel = doc.querySelector("[data-support-panel]");
  const submit = doc.querySelector("[data-support-send]");
  const description = doc.querySelector("[data-support-description]");
  const note = doc.querySelector("[data-support-note]");
  if (!panel || !submit || !description || !note) return;
  const send = options.send;
  const kind=doc.querySelector("[data-support-kind]"), category=doc.querySelector("[data-support-category]");
  const fields=doc.querySelector("[data-support-song-fields]"), trackLabel=doc.querySelector("[data-support-track]"), label=doc.querySelector("[data-support-label]");
  let key = crypto.randomUUID(); let busy = false; let pendingMessage = "";
  let pendingPayload=null, pinned=null, generation=0;
  const song=()=>kind?.value==="song";
  const draftKey = "celikom-support-draft-v1";
  try {
    const draft = (await chrome.storage.session?.get(draftKey))?.[draftKey];
    if (draft && typeof draft.text === "string" && draft.text.length <= 2000 && /^[a-f0-9-]{36}$/.test(draft.key)) { description.value = draft.text; key = draft.key; pendingMessage = typeof draft.message === "string" && draft.message.length < 3000 ? draft.message : "";
      if(kind)kind.value=draft.kind==='song'?'song':'general';
      if(category&&Object.hasOwn(reportCategories,draft.category))category.value=draft.category;
      if(draft.payload?.kind==='song'&&draft.payload.report?.track?.id){pendingPayload=draft.payload;pinned=draft.payload.report.track;} }
  } catch (_) {}
  function saveDraft(){void chrome.storage.session?.set({[draftKey]:{text:description.value.slice(0,2000),key,kind:song()?'song':'general',category:category?.value,message:pendingMessage,payload:pendingPayload}});}
  const edited=()=>{key=crypto.randomUUID();pendingMessage="";pendingPayload=null;saveDraft();};
  description.addEventListener("input",edited);
  category?.addEventListener("change",edited);
  async function selectKind(){
    const current=++generation;fields&&(fields.hidden=!song());
    if(label)label.textContent=song()?"Комментарий (необязательно)":"Опишите проблему";
    if(!song()){submit.disabled=busy;return;}
    submit.disabled=true;
    if(trackLabel)trackLabel.textContent="Определяем песню…";
    try {
      const state=await send({type:"CELIKOM_STATUS_GET"});
      if(current!==generation||!song())return;
      pinned=uploadTargetFromStatus(state);
      if(trackLabel)trackLabel.textContent=pinned?[pinned.artist,pinned.title].filter(Boolean).join(" — "):"Сначала запустите песню в Яндекс Музыке.";
      submit.disabled=busy||!pinned;
    }catch(_){if(current===generation&&trackLabel)trackLabel.textContent="Не удалось определить песню. Повторите выбор после восстановления связи.";}
  }
  kind?.addEventListener("change",()=>{edited();void selectKind();});
  if(pendingPayload){if(fields)fields.hidden=false;if(label)label.textContent="Комментарий (необязательно)";if(trackLabel)trackLabel.textContent=[pinned.artist,pinned.title].filter(Boolean).join(" — ");}
  else void selectKind();
  const message = () => supportMessage(description.value || "", chrome.runtime.getManifest().version, options.getState?.());
  function feedback(text: string) { note.hidden = false; note.textContent = text; }
  const failure = (result: any) => feedback(result?.error === "rate_limited" ? "Слишком много обращений. Повторите позже." : result?.error === "invalid_session" ? "Войдите в аккаунт CELIKOM, чтобы отправить сообщение и получать ответы." : "Не удалось связаться с поддержкой. Текст сохранён в поле; повторите отправку.");
  submit.addEventListener("click", async () => {
    if (busy) return;
    if (!song() && description.value.trim().length < 3) { feedback("Опишите проблему перед отправкой."); return; }
    busy = true; submit.disabled = true; if(kind)kind.disabled=true;if(category)category.disabled=true;description.disabled=true; feedback("Отправляем…");
    try {
      if(!pendingPayload){
        if(song()){
          const state=await send({type:"CELIKOM_STATUS_GET"});
          if(!pinned||state.track?.id!==pinned.id){feedback("Трек изменился. Выберите вид обращения заново, чтобы сообщить о текущей песне.");return;}
          pendingPayload={kind:'song',message:message(),report:buildSongReport(state,category.value,chrome.runtime.getManifest().version)};
        }else {if(!pendingMessage)pendingMessage=message();pendingPayload={kind:'general',message:pendingMessage};}
      }
      await chrome.storage.session?.set({[draftKey]:{text:description.value.slice(0,2000),key,kind:pendingPayload.kind,category:category?.value,message:pendingMessage,payload:pendingPayload}});
      const result = await send({ type: "CELIKOM_AUTH", action: "support-send", ...pendingPayload, request_key: key });
      if (!result?.ok) { failure(result); return; }
      key = crypto.randomUUID(); pendingMessage = ""; pendingPayload=null; description.value = ""; await chrome.storage.session?.remove(draftKey); feedback(song()?"Сообщение о проблеме с песней отправлено":"Сообщение отправлено");
    } catch (_) { failure(null); } finally { busy = false; submit.disabled = song()&&!pinned; if(kind)kind.disabled=false;if(category)category.disabled=false;description.disabled=false; }
  });
}

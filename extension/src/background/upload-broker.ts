// Service worker only. Offscreen document persists while the action popup loses focus.
export function createUploadBroker(api) {
  const documentUrl = api.runtime.getURL("popup/upload-worker.html");
  let opening = null;
  async function ensureDocument() {
    if (!opening) opening = (async()=>{
      const existing = await api.runtime.getContexts({
        contextTypes:["OFFSCREEN_DOCUMENT"],documentUrls:[documentUrl]
      });
      if (!existing.length) {
        await api.offscreen.createDocument({
          url:"popup/upload-worker.html",reasons:["BLOBS"],
          justification:"Keep user-initiated audio transfer alive after closing CELIKOM popup."
        });
      }
    })().finally(()=>{opening=null;});
    return opening;
  }
  async function begin(task) {
    if(!api.offscreen?.createDocument || !api.runtime?.getContexts)
      return {ok:false,error:"upload_background_unavailable"};
    await ensureDocument();
    return api.runtime.sendMessage({type:"CELIKOM_UPLOAD_EXECUTE",task});
  }
  async function cancel(id) {
    if(!api.offscreen?.createDocument) return {ok:false,error:"upload_background_unavailable"};
    return api.runtime.sendMessage({type:"CELIKOM_UPLOAD_INTERRUPT",id});
  }
  return {begin,cancel};
}

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
    // The offscreen document may exist before its module installs the runtime
    // listener. Retry only message delivery, never the HTTP POST itself.
    for (let i=0;i<6;i++) {
      try {
        const reply = await api.runtime.sendMessage({type:"CELIKOM_UPLOAD_EXECUTE",task});
        if (reply?.ok || reply?.error) return reply;
      } catch { /* listener may still be initializing */ }
      await new Promise(resolve=>setTimeout(resolve,100));
    }
    return {ok:false,error:"upload_background_unavailable"};
  }
  async function cancel(id) {
    if(!api.offscreen?.createDocument) return {ok:false,error:"upload_background_unavailable"};
    return api.runtime.sendMessage({type:"CELIKOM_UPLOAD_INTERRUPT",id});
  }
  return {begin,cancel};
}

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
  let key = crypto.randomUUID(); let busy = false; let pendingMessage = "";
  const draftKey = "celikom-support-draft-v1";
  try {
    const draft = (await chrome.storage.session?.get(draftKey))?.[draftKey];
    if (draft && typeof draft.text === "string" && draft.text.length <= 2000 && /^[a-f0-9-]{36}$/.test(draft.key)) { description.value = draft.text; key = draft.key; pendingMessage = typeof draft.message === "string" && draft.message.length < 3000 ? draft.message : ""; }
  } catch (_) {}
  description.addEventListener("input", () => { key = crypto.randomUUID(); pendingMessage = ""; void chrome.storage.session?.set({ [draftKey]: { text: description.value.slice(0, 2000), key } }); });
  const message = () => supportMessage(description.value || "", chrome.runtime.getManifest().version, options.getState?.());
  function feedback(text: string) { note.hidden = false; note.textContent = text; }
  const failure = (result: any) => feedback(result?.error === "rate_limited" ? "Слишком много обращений. Повторите позже." : result?.error === "invalid_session" ? "Войдите в аккаунт CELIKOM, чтобы отправить сообщение и получать ответы." : "Не удалось связаться с поддержкой. Текст сохранён в поле; повторите отправку.");
  submit.addEventListener("click", async () => {
    if (busy) return;
    if (description.value.trim().length < 3) { feedback("Опишите проблему перед отправкой."); return; }
    busy = true; submit.disabled = true; feedback("Отправляем…");
    try {
      if (!pendingMessage) pendingMessage = message();
      await chrome.storage.session?.set({ [draftKey]: { text: description.value.slice(0, 2000), key, message: pendingMessage } });
      const result = await send({ type: "CELIKOM_AUTH", action: "support-send", message: pendingMessage, request_key: key });
      if (!result?.ok) { failure(result); return; }
      key = crypto.randomUUID(); pendingMessage = ""; description.value = ""; await chrome.storage.session?.remove(draftKey); feedback("Сообщение отправлено");
    } catch (_) { failure(null); } finally { busy = false; submit.disabled = false; }
  });
}

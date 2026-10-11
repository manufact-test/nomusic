export function supportEmail(value: unknown): string {
  const email = typeof value === "string" ? value.trim() : "";
  return email.length <= 254 && /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,63}$/.test(email) ? email : "";
}

export function supportMessage(description: string, version: string, state: any): string {
  const phase = typeof state?.phase === "string" && /^[A-Z_]{1,40}$/.test(state.phase) ? state.phase : "не получено";
  const trackId = typeof state?.track?.id === "string" && /^[1-9]\d{0,23}$/.test(state.track.id) ? state.track.id : "не определён";
  // Deliberate allowlist: never serialize diagnostics, session, account, URLs or tokens.
  return ["Обращение в техподдержку CELIKOM", "", description.trim().slice(0, 2000) || "Опишите проблему перед отправкой.", "",
    `Версия расширения: ${version}`, `Состояние: ${phase}`, `Track ID: ${trackId}`,
    `Связь с вкладкой: ${state?.connection?.controllerPresent === true && !state?.connection?.error ? "есть" : "не подтверждена"}`].join("\n");
}

export async function initSupport(options: any = {}): Promise<void> {
  const doc = options.document || document;
  const panel = doc.querySelector("[data-support-panel]");
  const copy = doc.querySelector("[data-support-copy]");
  const submit = doc.querySelector("[data-support-send]");
  const description = doc.querySelector("[data-support-description]");
  const note = doc.querySelector("[data-support-note]");
  const list = doc.querySelector("[data-support-tickets]");
  if (!panel || !copy || !submit || !description || !list) return;
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
  async function refresh(page = 1) {
    const result = await send({ type: "CELIKOM_AUTH", action: "support-list", page });
    list.replaceChildren();
    if (!result?.ok) {
      failure(result);
      const contact = doc.querySelector("[data-support-contact]");
      const address = supportEmail((await send({ type: "CELIKOM_AUTH", action: "support-contact" }))?.email);
      if (contact && address) { contact.replaceChildren(); contact.hidden = false; contact.append("Если не получается войти, напишите: "); const link = doc.createElement("a"); link.textContent = address; link.href = "mailto:" + address; contact.append(link); }
      return;
    }
    for (const ticket of result.tickets || []) {
      const button = doc.createElement("button"); button.type = "button"; button.className = "quiet wide";
      button.textContent = `Обращение №${ticket.id} — ${ticket.status === "answered" ? "есть ответ" : ticket.status === "closed" ? "закрыто" : "отправлено"}`;
      const showThread = async (page = 1) => {
        const thread = await send({ type: "CELIKOM_AUTH", action: "support-thread", ticket_id: ticket.id, message_page: page });
        if (!thread?.ok) { failure(thread); return; }
        const content = doc.createElement("div"); content.className = "support-thread";
        for (const m of thread.messages || []) {
          const p = doc.createElement("p"); p.style.whiteSpace = "pre-wrap"; p.style.overflowWrap = "anywhere";
          p.textContent = `${m.author === "support" ? "Поддержка" : "Вы"}: ${m.body}`; content.append(p);
        }
        if (thread.has_more) { const older = doc.createElement("button"); older.type = "button"; older.className = "quiet wide"; older.textContent = "Предыдущие сообщения"; older.addEventListener("click", () => void showThread(page + 1)); content.append(older); }
        if (page > 1) { const newer = doc.createElement("button"); newer.type = "button"; newer.className = "quiet wide"; newer.textContent = "Более новые сообщения"; newer.addEventListener("click", () => void showThread(page - 1)); content.append(newer); }
        list.querySelector(".support-thread")?.remove(); button.after(content);
      };
      button.addEventListener("click", () => void showThread()); list.append(button);
    }
    if (result.has_more) { const older = doc.createElement("button"); older.type = "button"; older.className = "quiet wide"; older.textContent = "Предыдущие обращения"; older.addEventListener("click", () => void refresh(page + 1)); list.append(older); }
    if (page > 1) { const newer = doc.createElement("button"); newer.type = "button"; newer.className = "quiet wide"; newer.textContent = "Более новые обращения"; newer.addEventListener("click", () => void refresh(page - 1)); list.append(newer); }
  }
  panel.addEventListener("toggle", () => { if (panel.open) void refresh(); });
  copy.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(message()); feedback("Обращение скопировано."); }
    catch (_) { feedback("Не удалось скопировать. Скопируйте описание вручную."); }
  });
  submit.addEventListener("click", async () => {
    if (busy) return;
    if (description.value.trim().length < 3) { feedback("Опишите проблему перед отправкой."); return; }
    busy = true; submit.disabled = true; feedback("Отправляем…");
    try {
      if (!pendingMessage) pendingMessage = message();
      await chrome.storage.session?.set({ [draftKey]: { text: description.value.slice(0, 2000), key, message: pendingMessage } });
      const result = await send({ type: "CELIKOM_AUTH", action: "support-send", message: pendingMessage, request_key: key });
      if (!result?.ok) { failure(result); return; }
      key = crypto.randomUUID(); pendingMessage = ""; description.value = ""; await chrome.storage.session?.remove(draftKey); await chrome.storage.session?.remove(draftKey); feedback(`Обращение №${result.ticket_id} отправлено. Ответ появится здесь и придёт на почту аккаунта.`);
      await refresh();
    } catch (_) { failure(null); } finally { busy = false; submit.disabled = false; }
  });
}

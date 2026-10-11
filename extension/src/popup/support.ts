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
  const copy = doc.querySelector("[data-support-copy]");
  const emailButton = doc.querySelector("[data-support-email]");
  const contact = doc.querySelector("[data-support-contact]");
  const description = doc.querySelector("[data-support-description]");
  const note = doc.querySelector("[data-support-note]");
  if (!copy || !emailButton || !description) return;
  let email = "";
  const message = () => supportMessage(description.value || "", chrome.runtime.getManifest().version, options.getState?.());
  function feedback(text: string) { if (note) { note.hidden = false; note.textContent = text; } }
  copy.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(message()); feedback("Обращение скопировано. Вставьте его в сообщение поддержке."); }
    catch (_) { feedback("Не удалось скопировать. Выделите описание проблемы и скопируйте его вручную."); }
  });
  emailButton.addEventListener("click", () => {
    if (!email) return;
    const url = `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent("CELIKOM — обращение в поддержку")}&body=${encodeURIComponent(message())}`;
    void chrome.tabs.create({ url }).catch(() => feedback("Не удалось открыть почту. Скопируйте обращение и отправьте его на " + email));
  });
  try {
    const response = await fetch(chrome.runtime.getURL("api/config.json"));
    if (!response.ok) return;
    email = supportEmail((await response.json()).supportEmail);
    if (email) { emailButton.disabled = false; if (contact) contact.textContent = email; }
  } catch (_) { /* Copy remains available offline and without a configured recipient. */ }
}

// Account screen only. Opening a panel never creates an invitation code.
export function initBenefitsPanel(send) {
  const root = document.querySelector("[data-benefits-panel]");
  if (!root) return { signed: () => {} };
  const q = (key) => root.querySelector("[data-benefits-" + key + "]");
  let generation = 0, code = null, signedIn = false, busy = false, loaded = false;
  const note = (text) => { q("note").textContent = text; q("note").hidden = !text; };
  function render(data) {
    root.hidden = !data.referrals_available;
    const ref = data.referrals;
    code = ref?.code || null;
    q("code").textContent = code || "";
    q("code").hidden = !code;
    q("create").hidden = !data.referrals_available || Boolean(code);
    q("copy").hidden = !code;
    q("share").hidden = !code || typeof globalThis.navigator?.share !== "function";
    q("progress").textContent = data.referrals_available
      ? "Зарегистрировались по коду: " + ref.registered_count + ". Бонусы за оплату пока недоступны."
      : "Подписка и приглашения пока недоступны.";
    note("");
  }
  async function load(create = false) {
    if (!signedIn || busy) return;
    const current = generation; busy = true;
    try {
      const result = await send({ type: "CELIKOM_AUTH", action: create ? "referral-code" : "benefits" });
      if (current !== generation || !signedIn) return;
      if (result?.ok) { loaded = true; render(result); }
      else note(result?.error === "invalid_session" ? "Войдите в аккаунт ещё раз." : "Не удалось получить данные. Повторите позже.");
    } catch (_) { if (current === generation && signedIn) note("Нет связи с сервером."); }
    finally { if (current === generation) busy = false; }
  }
  root.addEventListener("toggle", () => { if (root.open && !loaded) void load(); });
  q("create").addEventListener("click", () => void load(true));
  q("copy").addEventListener("click", async () => {
    if (!code || !signedIn) return;
    const current = generation;
    try { await navigator.clipboard.writeText(code); if (current === generation) note("Код скопирован."); }
    catch (_) { if (current === generation) note("Выделите и скопируйте код вручную."); }
  });
  q("share").addEventListener("click", async () => {
    if (!code || !signedIn) return;
    const current = generation;
    try { await navigator.share({ title: "CELIKOM", text: "Мой код приглашения в CELIKOM: " + code }); }
    catch (error) { if (current === generation && error?.name !== "AbortError") note("Можно скопировать код."); }
  });
  return { signed(value) {
    signedIn = value; generation++; busy = false; loaded = false; code = null;
    root.hidden = true; root.open = false;
    q("code").textContent = ""; q("code").hidden = true; note("");
    q("progress").textContent = value ? "Подписка и приглашения пока недоступны." : "";
    for (const key of ["create", "copy", "share"]) q(key).hidden = true;
    if (value) void load();
  } };
}

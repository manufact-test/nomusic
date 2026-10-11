// Account screen only. All dynamic values go through textContent.
export function initBenefitsPanel(send) {
  const root = document.querySelector("[data-benefits-panel]");
  if (!root) return { signed: () => {} };
  const q = (key) => root.querySelector("[data-benefits-" + key + "]");
  let generation = 0, code = null, signedIn = false, busy = false;
  const note = (text) => { q("note").textContent = text; };
  function render(data) {
    const access = data.entitlement;
    q("access").textContent = access?.allowed && access.valid_until
      ? (access.source === "subscription" ? "Подписка оплачена до " : "Пробный период до ") + new Date(access.valid_until).toLocaleString("ru-RU")
      : access?.reason === "trial_not_started" ? "3 дня пробного периода начнутся после «Старт»"
      : "Пробный период завершён";
    q("payment").textContent = "Оплата пока не подключена";
    const ref = data.referrals;
    code = ref?.code || null;
    q("code").textContent = code || "Код ещё не создан";
    q("create").hidden = !data.referrals_available || Boolean(code);
    q("copy").hidden = !code;
    q("share").hidden = !code || typeof globalThis.navigator?.share !== "function";
    q("progress").textContent = data.referrals_available
      ? "Зарегистрировались по коду: " + ref.registered_count + ". Подтверждение оплат пока не подключено."
      : "Приглашения пока готовятся";
    note("Скидки и награды пока не начисляются.");
  }
  async function load(create = false) {
    if (!signedIn || busy) return;
    const current = generation; busy = true; note("Загружаем…");
    try {
      const result = await send({ type: "CELIKOM_AUTH", action: create ? "referral-code" : "benefits" });
      if (current !== generation || !signedIn) return;
      if (result?.ok) render(result);
      else note(result?.error === "invalid_session" ? "Войдите в аккаунт ещё раз." : "Не удалось получить данные. Повторите позже.");
    } catch (_) { if (current === generation && signedIn) note("Нет связи с сервером."); }
    finally { if (current === generation) busy = false; }
  }
  root.addEventListener("toggle", () => { if (root.open) void load(); });
  q("refresh").addEventListener("click", () => void load());
  q("create").addEventListener("click", () => void load(true));
  q("copy").addEventListener("click", async () => {
    if (!code || !signedIn) return;
    try { await navigator.clipboard.writeText(code); note("Код скопирован."); }
    catch (_) { note("Выделите и скопируйте код вручную."); }
  });
  q("share").addEventListener("click", async () => {
    if (!code || !signedIn) return;
    try { await navigator.share({ title: "CELIKOM", text: "Мой код приглашения в CELIKOM: " + code }); }
    catch (error) { if (error?.name !== "AbortError") note("Не удалось открыть меню отправки. Можно скопировать код."); }
  });
  return { signed(value) {
    signedIn = value; generation++; busy = false; code = null;
    root.hidden = !value; root.open = false;
    for (const key of ["access", "payment", "code", "progress", "note"]) q(key).textContent = "";
    for (const key of ["create", "copy", "share"]) q(key).hidden = true;
  } };
}

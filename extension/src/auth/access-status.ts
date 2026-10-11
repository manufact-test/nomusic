import { readDisplay, writeDisplay, stableText } from "../popup/display-cache.js";
export function accessLabel(access) {
  if (!access) return "";
  if (access.allowed && access.source === "promo" && access.valid_until === null) return "Промокод · доступ навсегда";
  if (access.allowed && access.valid_until && Date.parse(access.valid_until) > Date.now()) {
    const prefix = access.source === "promo" ? "Промокод до " : access.source === "subscription" ? "Подписка до " : "Пробный период до ";
    return prefix + new Date(access.valid_until).toLocaleString("ru-RU", { timeZone: "Europe/Moscow", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }) + " (Москва)";
  }
  if (access.reason === "trial_not_started") return "3 дня пробного периода начнутся после «Старт»";
  if (access.reason === "email_unverified") return "Подтвердите почту, чтобы начать";
  if (access.reason === "service_incident") return "Сбой интеграции · время доступа будет компенсировано";
  if (access.reason === "account_disabled") return "Доступ к аккаунту отключён";
  return access.source === "subscription" ? "Подписка завершена" : "Пробный период завершён";
}

// Preview is presentation only. Start/audio still require a live server decision.
export function initAccessStatus(send) {
  const label = document.querySelector("[data-access-status]");
  const cached = readDisplay("access");
  const valid = (a) => typeof a?.allowed === "boolean" && typeof a.reason === "string"
    && typeof a.source === "string" && (a.valid_until === null || Number.isFinite(Date.parse(a.valid_until)));
  let confirmed = false, latest = valid(cached?.access) ? cached.access : null, busy = false, generation = 0;
  const text = (value) => { if (label?.dataset) delete label.dataset.kind; stableText(label, value); };
  stableText(label, latest ? accessLabel(latest) : cached?.signedOut ? "Войдите в аккаунт, чтобы начать" : "Загрузка доступа…", false);
  void send({ type: "CELIKOM_AUTH", action: "access-preview" }).then((result) => {
    if (!confirmed && result?.entitlement) { latest = result.entitlement; text(accessLabel(latest)); }
  }).catch(() => {});
  async function refreshAccess() {
    if (!label || busy) return;
    const current = generation; busy = true;
    if (latest) text(accessLabel(latest));
    try {
      const result = await send({ type: "CELIKOM_AUTH", action: "entitlement" });
      if (current !== generation) return;
      if (result?.ok && result.entitlement) {
        confirmed = true; latest = result.entitlement; writeDisplay("access", { access: latest }); text(accessLabel(latest)); label.title = "";
      } else if (result?.error === "invalid_session") {
        confirmed = true; latest = null; writeDisplay("access", { signedOut: true }); text("Войдите в аккаунт, чтобы начать");
      } else if (!latest) text("Нет связи. Оригинальная музыка доступна.");
      else label.title = "Нет связи. Показан последний полученный срок; доступ проверяется сервером.";
    } catch (_) { if (current === generation && !latest) text("Нет связи. Оригинальная музыка доступна."); }
    finally { if (current === generation) busy = false; }
  }
  document.addEventListener?.("celikom-account-logout", () => {
    generation++; busy = false; confirmed = true; latest = null;
    writeDisplay("access", { signedOut: true }); text("Войдите в аккаунт, чтобы начать");
  });
  document.addEventListener?.("celikom-promo-activated", () => { generation++; busy = false; void refreshAccess(); });
  document.addEventListener?.("celikom-account-login", () => { generation++; busy = false; void refreshAccess(); });
  return refreshAccess;
}

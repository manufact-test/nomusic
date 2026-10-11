export function accessLabel(access) {
  if (!access) return "";
  if (access.allowed && access.valid_until && Date.parse(access.valid_until) > Date.now()) {
    const prefix = access.source === "subscription" ? "Подписка до " : "Пробный период до ";
    return prefix + new Date(access.valid_until).toLocaleString("ru-RU", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" });
  }
  if (access.reason === "trial_not_started") return "3 дня пробного периода начнутся после «Старт»";
  if (access.reason === "email_unverified") return "Подтвердите почту, чтобы начать";
  if (access.reason === "account_disabled") return "Доступ к аккаунту отключён";
  return access.source === "subscription" ? "Подписка завершена" : "Пробный период завершён";
}

// Preview is presentation only. Start/audio still require a live server decision.
export function initAccessStatus(send) {
  const label = document.querySelector("[data-access-status]");
  let confirmed = false, latest = null, busy = false, generation = 0;
  const text = (value) => { if (label && label.textContent !== value) label.textContent = value; };
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
        confirmed = true; latest = result.entitlement; text(accessLabel(latest)); label.title = "";
      } else if (["invalid_session", "auth_disabled"].includes(result?.error)) {
        confirmed = true; latest = null; text("Войдите в аккаунт, чтобы начать");
      } else if (!latest) text("Нет связи. Оригинальная музыка доступна.");
      else label.title = "Нет связи. Показан последний полученный срок; доступ проверяется сервером.";
    } catch (_) { if (current === generation && !latest) text("Нет связи. Оригинальная музыка доступна."); }
    finally { if (current === generation) busy = false; }
  }
  document.addEventListener?.("celikom-account-logout", () => {
    generation++; busy = false; confirmed = true; latest = null;
    text("Войдите в аккаунт, чтобы начать");
  });
  document.addEventListener?.("celikom-account-login", () => { generation++; busy = false; void refreshAccess(); });
  return refreshAccess;
}

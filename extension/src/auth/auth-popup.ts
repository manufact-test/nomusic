// Isolated customer account UX. No changes to the playback controller or owner upload flow.
export function initAuthPanel(send) {
  const root = document.querySelector("[data-auth-panel]");
  const summary = document.querySelector("[data-auth-summary]");
  const form = document.querySelector("[data-auth-form]");
  const email = document.querySelector("[data-auth-email]");
  const password = document.querySelector("[data-auth-password]");
  const submit = document.querySelector("[data-auth-submit]");
  const note = document.querySelector("[data-auth-note]");
  const signed = document.querySelector("[data-auth-signed]");
  const identity = document.querySelector("[data-auth-identity]");
  const devices = document.querySelector("[data-auth-devices]");
  const modeButton = document.querySelector("[data-auth-mode]");
  let mode = "login";
  if (!root) return;
  const call = (action, props = {}) => send({ type: "CELIKOM_AUTH", action, ...props });
  const errors = {
    invalid_credentials: "Неверный email или пароль.",
    account_disabled: "Аккаунт ограничен. Обратитесь в поддержку.",
    account_unavailable: "Этот email уже используется.",
    weak_password: "Пароль должен содержать минимум 12 символов.",
    rate_limited: "Слишком много попыток. Повторите позже.",
    invalid_request: "Проверьте введённые данные.",
    invalid_session: "Сессия истекла. Войдите снова.",
    auth_unavailable: "Сервер недоступен. Попробуйте позже."
  };
  function message(value) { if (note) note.textContent = value || ""; }
  function render(value) {
    form.hidden = value.signedIn === true;
    signed.hidden = value.signedIn !== true;
    if (identity) identity.textContent = value.user?.email || "";
    if (summary) summary.textContent = value.signedIn ? "Аккаунт · подключён" : "Аккаунт";
    if (devices) devices.hidden = true;
    if (value.error) message(errors[value.error] || "Войдите в аккаунт.");
  }
  function renderMode() {
    if (submit) submit.textContent = mode === "login" ? "Войти" : "Зарегистрироваться";
    if (modeButton) modeButton.textContent = mode === "login" ? "Создать аккаунт" : "У меня уже есть аккаунт";
    if (password) password.autocomplete = mode === "login" ? "current-password" : "new-password";
    message("");
  }
  void call("status").then((value) => {
    if (!value?.available) return;
    root.hidden = false;
    render(value);
  }).catch(() => undefined);
  modeButton?.addEventListener("click", () => {
    mode = mode === "login" ? "register" : "login"; renderMode();
  });
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submit) submit.disabled = true;
    message("Проверяем…");
    try {
      const response = await call(mode, { email: email.value.trim(), password: password.value });
      password.value = "";
      if (response?.ok) {
        message("Готово");
        render({ signedIn: true, user: response.user });
      } else message(errors[response?.error] || "Не удалось войти.");
    } catch (_error) { message("Нет связи с сервером."); }
    finally { if (submit) submit.disabled = false; }
  });
  root.querySelector("[data-auth-logout]")?.addEventListener("click", async () => {
    message("Выходим…");
    const result = await call("logout").catch(() => ({ ok: false }));
    if (result?.ok) { render({ signedIn: false }); message("Вы вышли."); }
    else message("Не удалось завершить серверную сессию. Повторите выход.");
  });
  root.querySelector("[data-auth-list-devices]")?.addEventListener("click", async () => {
    message("Проверяем устройства…");
    const result = await call("sessions").catch(() => ({ ok: false }));
    if (!result?.ok || !Array.isArray(result.sessions)) { message("Не удалось получить устройства."); return; }
    if (devices) {
      devices.replaceChildren();
      for (const session of result.sessions) {
        const line = document.createElement("li");
        const text = document.createElement("span");
        text.textContent = session.current ? "Это устройство" : "Другое устройство";
        line.append(text);
        if (!session.current) {
          const button = document.createElement("button");
          button.textContent = "Отключить";
          button.type = "button";
          button.addEventListener("click", async () => {
            button.disabled = true;
            const res = await call("revoke", { session_id: session.id }).catch(() => ({ ok: false }));
            if (res?.ok) line.remove();
            else { button.disabled = false; message("Не удалось отключить устройство."); }
          });
          line.append(button);
        }
        devices.append(line);
      }
      devices.hidden = false;
    }
    message("");
  });
  renderMode();
}

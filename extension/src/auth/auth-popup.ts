// Customer auth popup: no device list; server keeps per-device sessions.
export function initAuthPanel(send) {
  const q = (name) => document.querySelector("[data-auth-" + name + "]");
  const root = q("panel"), note = q("note"), email = q("email"), pass = q("password");
  if (!root) return;
  const views = { login: q("form"), verify: q("verify-form"), recovery: q("recovery-form"),
    reset: q("new-password-form"), signed: q("signed") };
  const call = (action, more = {}) => send({ type: "CELIKOM_AUTH", action, ...more });
  let mode = "login", pendingEmail = "", pendingPassword = "", busy = false;
  // The Chrome popup closes when users switch to their mailbox. Keep ONLY the
  // pending email + purpose in extension storage; never persist a password/code.
  const pendingKey = "celikom-auth-pending-email";
  const rememberedKey = "celikom-auth-remembered-email";
  const suggestion = q("email-suggestion");
  let rememberedEmail = "";
  let userEditingEmail = false;
  const mailStore = globalThis.chrome?.storage?.local;
  async function savePending(purpose, address) {
    if (!mailStore || !goodEmail(address)) return;
    await mailStore.set({ [pendingKey]: { purpose, email: address } });
  }
  async function loadPending() {
    if (!mailStore) return null;
    const value = (await mailStore.get(pendingKey))[pendingKey];
    if (!value || !["verify", "reset"].includes(value.purpose) || !goodEmail(value.email))
      return null;
    return value;
  }
  async function clearPending() {
    if (mailStore) await mailStore.remove(pendingKey);
  }
  async function remember(address) {
    if (!goodEmail(address)) return;
    rememberedEmail = address;
    if (mailStore) await mailStore.set({ [rememberedKey]: address });
    updateEmailSuggestion();
  }
  function updateEmailSuggestion() {
    if (!suggestion) return;
    const typed = email.value.trim().toLowerCase();
    const match = rememberedEmail && (!typed || rememberedEmail.toLowerCase().startsWith(typed))
      && typed !== rememberedEmail.toLowerCase();
    suggestion.hidden = !match;
    if (match) suggestion.textContent = rememberedEmail;
  }
  function chooseRememberedEmail() {
    if (!rememberedEmail) return;
    email.value = rememberedEmail;
    userEditingEmail = true;
    if (suggestion) suggestion.hidden = true;
    // Browser field owns focus and paste/autofill; no synthetic keyboard event.
    email.focus();
  }
  suggestion?.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    chooseRememberedEmail();
  });
  suggestion?.addEventListener("click", chooseRememberedEmail);
  email.addEventListener("input", () => {
    userEditingEmail = true;
    updateEmailSuggestion();
  });
  email.addEventListener("focus", updateEmailSuggestion);
  email.addEventListener("keydown", (event) => {
    if (suggestion?.hidden === false && ["ArrowDown", "Enter"].includes(event.key)) {
      event.preventDefault();
      chooseRememberedEmail();
    }
    if (event.key === "Escape" && suggestion) suggestion.hidden = true;
  });
  email.addEventListener("blur", () => {
    if (suggestion) suggestion.hidden = true;
  });
  const errors = {
    invalid_credentials: "Не удалось войти. Проверьте email и пароль или создайте аккаунт.",
    account_unavailable: "Этот email уже используется. Попробуйте войти.",
    account_disabled: "Аккаунт ограничен.",
    email_unavailable: "Отправка писем пока недоступна. Повторите позже.",
    weak_password: "Пароль должен содержать минимум 12 символов.",
    invalid_code: "Неверный или просроченный код.",
    rate_limited: "Слишком много попыток. Подождите и повторите.",
    invalid_session: "Сессия истекла. Войдите снова.",
    invalid_request: "Проверьте введённые данные.",
    auth_unavailable: "Сервер недоступен. Повторите позже."
  };
  const show = (value = "", kind = "info") => {
    note.textContent = value;
    note.hidden = !value;
    note.dataset.kind = kind;
  };
  function view(next, user) {
    const previous = mode;
    mode = next;
    root.dataset.authScreen = next;
    for (const [key, el] of Object.entries(views)) el.hidden =
      key === "login" ? !["login", "register"].includes(next) : key !== next;
    q("summary").textContent = next === "signed" ? "Аккаунт · подключён" : "Аккаунт";
    q("identity").textContent = user?.email || "";
    q("submit").textContent = next === "register" ? "Зарегистрироваться" : "Войти";
    q("mode").textContent = next === "register" ? "У меня уже есть аккаунт" : "Создать аккаунт";
    pass.autocomplete = next === "register" ? "new-password" : "current-password";
    // Form switching must not resize/jump the popup or erase a native autofill.
    if (previous !== next) {
      const content = root.querySelector?.(".account-content");
      if (content) content.scrollTop = 0;
    }
    if (next !== "login" && next !== "register" && suggestion) suggestion.hidden = true;
    show();
  }
  const goodEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/u.test(v) && v.length <= 254;
  const goodPass = (v) => [...v].length >= 12 && [...v].length <= 128;
  async function act(action, data, done) {
    if (busy) return;
    busy = true;
    show("Проверяем…", "loading");
    try {
      const result = await call(action, data);
      if (result?.ok) await done(result);
      else show(errors[result?.error] || "Не удалось выполнить действие.", "error");
    } catch (_) { show("Нет связи с сервером.", "error"); }
    finally { busy = false; }
  }
  function eye(input, control) {
    control?.addEventListener("click", () => {
      const visible = input.type === "password";
      input.type = visible ? "text" : "password";
      control.setAttribute("aria-pressed", String(visible));
      control.setAttribute("aria-label", visible ? "Скрыть пароль" : "Показать пароль");
      input.focus();
    });
  }
  eye(pass, q("eye")); eye(q("reset-password"), q("reset-eye"));
  void Promise.all([call("status"), loadPending(),
    mailStore ? mailStore.get(rememberedKey) : Promise.resolve({})]).then(([state, pending, known]) => {
    rememberedEmail = goodEmail(known?.[rememberedKey]) ? known[rememberedKey] : "";
    if (!state?.available) return;
    root.hidden = false;
    if (state.signedIn) {
      void clearPending();
      void remember(state.user?.email);
      view("signed", state.user);
    } else if (state.localSession) {
      view("signed", state.user);
      q("summary").textContent = "Аккаунт · нет связи";
      show("Нет соединения. Вход на этом устройстве сохранён.", "loading");
    } else if (pending) {
      // After switching to the mailbox, reopen the confirmation panel automatically.
      root.open = true;
      pendingEmail = pending.email;
      email.value = pending.email;
      if (pending.purpose === "reset") {
        q("recovery-email").value = pending.email;
        view("reset");
        show("Введите код из письма. Можно закрыть окно и вернуться позже.");
      } else {
        view("verify");
        show("Введите код из письма. Для повторной отправки войдите с паролем.");
      }
    } else {
      view("login");
      if (!userEditingEmail) updateEmailSuggestion();
    }
  }).catch(() => {});
  q("mode").addEventListener("click", () => view(mode === "login" ? "register" : "login"));
  views.login.addEventListener("submit", (e) => {
    e.preventDefault();
    const address = email.value.trim(), password = pass.value;
    if (!goodEmail(address)) return show("Введите корректный email.", "error");
    if (!password || (mode === "register" && !goodPass(password))) {
      return show(mode === "register" ? "Пароль: минимум 12 символов." : "Введите пароль.", "error");
    }
    void act(mode, { email: address, password }, async (result) => {
      await remember(address);
      if (result.verification_required) {
        pendingEmail = address; pendingPassword = password;
        await savePending("verify", address);
        pass.value = ""; view("verify"); show("Код отправлен на почту.");
      } else {
        await clearPending();
        pendingPassword = ""; pass.value = ""; view("signed", result.user);
      }
    });
  });
  views.verify.addEventListener("submit", (e) => {
    e.preventDefault();
    const code = q("code").value.trim();
    if (!/^\d{6}$/.test(code)) return show("Введите шестизначный код.", "error");
    void act("verify-email", { email: pendingEmail, code }, async (result) => {
      await clearPending();
      await remember(result.user?.email);
      pendingPassword = ""; q("code").value = "";
      view("signed", result.user);
    });
  });
  q("resend").addEventListener("click", () => {
    if (!pendingPassword) { view("login"); return show("Войдите с паролем, чтобы повторно получить код."); }
    void act("resend-verification", { email: pendingEmail, password: pendingPassword }, () => show("Код отправлен повторно."));
  });
  q("back").addEventListener("click", () => { pendingPassword = ""; email.value = pendingEmail; view("login"); });
  q("forgot").addEventListener("click", () => { q("recovery-email").value = email.value.trim(); view("recovery"); });
  q("recovery-back").addEventListener("click", () => view("login"));
  views.recovery.addEventListener("submit", (e) => {
    e.preventDefault();
    const address = q("recovery-email").value.trim();
    if (!goodEmail(address)) return show("Введите корректный email.", "error");
    void act("request-reset", { email: address }, async () => {
      pendingEmail = address;
      await savePending("reset", address);
      view("reset");
      show("Если почта зарегистрирована, код отправлен.");
    });
  });
  views.reset.addEventListener("submit", (e) => {
    e.preventDefault();
    const code = q("reset-code").value.trim(), password = q("reset-password").value;
    if (!/^\d{6}$/.test(code)) return show("Введите шестизначный код.", "error");
    if (!goodPass(password)) return show("Новый пароль: минимум 12 символов.", "error");
    void act("reset-password", { email: pendingEmail, code, new_password: password }, async () => {
      await clearPending();
      q("reset-password").value = ""; email.value = pendingEmail;
      view("login"); show("Пароль изменён. Войдите с новым паролем.");
    });
  });
  q("reset-back").addEventListener("click", () => view("login"));
  q("logout").addEventListener("click", () => {
    void act("logout", {}, async () => {
      await clearPending();
      view("login"); show("Вы вышли.");
    });
  });
  view("login");
}

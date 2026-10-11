export function initPromoPanel(send) {
  const root = document.querySelector("[data-auth-promo-panel]");
  if (!root) return { signed() {} };
  const form = root.querySelector("form"), code = root.querySelector("input"), button = root.querySelector("button"), note = root.querySelector("[data-promo-note]");
  let generation = 0, busy = false, signedIn = false;
  const errors = { invalid_promo: "Проверьте код: от 8 до 64 латинских букв, цифр, дефисов или подчёркиваний.", promo_unavailable: "Промокод недоступен или закончился лимит активаций.", promo_payment_pending: "Эта скидка станет доступна после подключения оплаты.", promo_lifetime_active: "У вас уже есть бессрочный доступ.", rate_limited: "Слишком много попыток. Повторите через 15 минут.", invalid_session: "Войдите в аккаунт ещё раз." };
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || !signedIn) return;
    const current = generation; busy = true; button.disabled = true; note.textContent = "Проверяем промокод…";
    try {
      const result = await send({ type: "CELIKOM_AUTH", action: "promo-redeem", code: code.value.trim() });
      if (current !== generation) return;
      if (result?.ok) {
        note.textContent = result.revoked ? "Эта активация отозвана. Повторно использовать код нельзя." : result.already_activated ? "Вы уже активировали этот промокод." : "Промокод активирован.";
        code.value = "";
        document.dispatchEvent(new Event("celikom-promo-activated"));
      } else note.textContent = errors[result?.error] || "Нет связи. Повторите попытку позже.";
    } catch (_) { if (current === generation) note.textContent = "Нет связи. Повторите попытку позже."; }
    finally { if (current === generation) { busy = false; button.disabled = false; } }
  });
  return { signed(value) { generation++; signedIn = value; busy = false; root.hidden = !value; button.disabled = false; code.value = ""; note.textContent = ""; } };
}

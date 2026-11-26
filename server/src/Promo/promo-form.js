"use strict";
for (const form of document.querySelectorAll("[data-promo-create]")) {
  const field = name => form.elements.namedItem(name);
  const forever = field("forever"), percent = field("discount_percent");
  const days = field("duration_days"), windowChoice = field("activation_window"), deadline = field("activation_deadline");
  const sync = () => {
    forever.disabled = Number(percent.value) !== 100;
    if (forever.disabled) forever.checked = false;
    days.disabled = forever.checked;
    days.required = !forever.checked;
    form.querySelector("[data-promo-days]").hidden = forever.checked;
    const fixed = windowChoice.value === "fixed";
    form.querySelector("[data-promo-deadline]").hidden = !fixed;
    deadline.disabled = !fixed;
    deadline.required = fixed;
  };
  form.addEventListener("change", sync);
  percent.addEventListener("input", sync);
  sync();
}

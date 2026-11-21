(() => {
  'use strict';
  const root = document.querySelector('[data-bulk-select]');
  if (!root) return;
  const boxes = [...document.querySelectorAll('[data-bulk-candidate]')];
  const count = root.querySelector('[data-bulk-count]');
  const all = root.querySelector('[data-bulk-all]');
  const none = root.querySelector('[data-bulk-none]');
  const submit = [...root.querySelectorAll('button[data-bulk-action]')];
  function sync() {
    const n = boxes.filter((box) => box.checked).length;
    count.textContent = 'Выбрано ' + n + ' из ' + boxes.length;
    submit.forEach((button) => { button.disabled = !n; });
    all.disabled = n === boxes.length;
    none.disabled = n === 0;
  }
  all.addEventListener('click', () => { boxes.forEach((box) => { box.checked = true; }); sync(); });
  none.addEventListener('click', () => { boxes.forEach((box) => { box.checked = false; }); sync(); });
  boxes.forEach((box) => box.addEventListener('change', sync));
  sync();
})();

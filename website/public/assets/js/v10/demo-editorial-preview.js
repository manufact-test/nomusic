/* Stage 4 local editor preview: only output text; never rewrite approved v10 JS.
   Original event handlers execute first and continue to own ARIA/data-mode state. */
(() => {
  const panel = document.getElementById('sound-panel');
  const result = document.getElementById('sound-result');
  const service = document.getElementById('mode-service');
  const restored = document.getElementById('mode-restored');
  if (!panel || !result || !service || !restored ||
      !panel.hasAttribute('data-editorial-service') ||
      !panel.hasAttribute('data-editorial-restored')) return;
  const labels = {
    service: panel.getAttribute('data-editorial-service'),
    restored: panel.getAttribute('data-editorial-restored')
  };
  function sync() {
    if (panel.dataset.mode === 'service' || panel.dataset.mode === 'restored') {
      result.textContent = labels[panel.dataset.mode];
    }
  }
  service.addEventListener('click', sync);
  restored.addEventListener('click', sync);
  sync();
})();

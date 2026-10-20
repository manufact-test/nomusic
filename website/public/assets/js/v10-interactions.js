/*
 * Behavior extracted from owner-approved CELIKOM_SITE_CLEAN_v10.html.
 * Keep accessible button states and original text; no fabricated audio.
 */
(() => {
 const board=document.getElementById('sound-panel');
 const result=document.getElementById('sound-result');
 const buttons={service:document.getElementById('mode-service'),restored:document.getElementById('mode-restored')};
 if(!board || !result || !buttons.service || !buttons.restored) return;
 for(const [mode,button] of Object.entries(buttons)) {
  button.addEventListener('click',() => {
   board.dataset.mode=mode;
   for(const [name,control] of Object.entries(buttons)) control.setAttribute('aria-pressed',String(name===mode));
   result.textContent=mode==='restored'?'Играет знакомая версия — если\u00a0она доступна':'Звучит версия из\u00a0плеера';
  });
 }
})();

(() => {
  const root = document.getElementById('faq');
  if (!root) return;
  const items = [...root.querySelectorAll('.faq-item')];
  const buttons = [...root.querySelectorAll('.faq-filter')];
  const empty = root.querySelector('#faq-empty');
  function apply(category) {
    let shown=0;
    for(const item of items){
      const visible=category==='all'||item.dataset.category===category;
      item.hidden=!visible;
      if (!visible) item.open=false;
      if(visible) shown++;
    }
    for(const button of buttons) button.setAttribute('aria-pressed',String(button.dataset.filter===category));
    if(empty) empty.hidden=shown>0;
  }
  for(const button of buttons) button.addEventListener('click',()=>apply(button.dataset.filter));
  const hash = decodeURIComponent(location.hash.slice(1));
  const target=hash?document.getElementById(hash):null;
  if(target && target.classList.contains('faq-item')){apply(target.dataset.category);target.open=true;}
  else apply('all');
})();

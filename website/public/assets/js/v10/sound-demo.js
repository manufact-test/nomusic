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

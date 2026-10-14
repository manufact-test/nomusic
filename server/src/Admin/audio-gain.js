function createGainChain(context, audio, db) {
  const source=context.createMediaElementSource(audio),gain=context.createGain();
  const limiter=context.createDynamicsCompressor(),compensation=context.createGain(),ceiling=context.createWaveShaper();
  limiter.threshold.value=-1;limiter.knee.value=0;limiter.ratio.value=20;limiter.attack.value=0.001;limiter.release.value=0.1;
  // Web Audio fixed makeup gain: cancel it so the slider controls the actual quiet-signal gain.
  // https://webaudio.github.io/web-audio-api/#computing-the-makeup-gain
  compensation.gain.value=Math.pow(10,limiter.threshold.value*(1-1/limiter.ratio.value)*0.6/20);
  const curve=new Float32Array(4097);for(let i=0;i<curve.length;i++)curve[i]=Math.max(-0.98,Math.min(0.98,i*2/(curve.length-1)-1));
  ceiling.curve=curve;ceiling.oversample="none";
  source.connect(gain);limiter.connect(compensation);compensation.connect(ceiling);ceiling.connect(context.destination);
  let positive=null;
  const set=(value)=>{
    if(!Number.isFinite(value)||value< -12||value>12)throw new Error("invalid_audio_gain");
    const next=value>0;
    if(next!==positive){gain.disconnect();gain.connect(next?limiter:context.destination);positive=next;}
    gain.gain.setTargetAtTime(Math.pow(10,value/20),context.currentTime,0.01);
  };
  set(db);
  return {set,destroy(){for(const node of [source,gain,limiter,compensation,ceiling]){try{node.disconnect();}catch{}}}};
}

(()=>{
 "use strict";
 const contexts=new Map();
 function controller(audio,db){
  let context,chain;
  return {
   async set(value){
    if(!context){const Type=window.AudioContext||window.webkitAudioContext;if(!Type)throw Error("unsupported");context=new Type();chain=createGainChain(context,audio,db);contexts.set(audio,context);}
    chain.set(value);await context.resume();if(context.state!=="running")throw Error("blocked");
   }
  };
 }
 for(const audio of document.querySelectorAll('[data-gain-audio]')){
  const stored=Number(audio.dataset.gainDb||0),control=controller(audio,stored);
  const form=[...document.querySelectorAll('[data-audio-gain]')].find(f=>f.dataset.audioId===audio.closest('.player-wrap').id);
  let wanted=stored;const slider=form?.querySelector('[name=gain_db]'),note=form?.querySelector('[data-gain-note]'),output=form?.querySelector('[data-gain-value]');
  const failure=()=>{audio.pause();if(note)note.textContent='Не удалось включить прослушивание громкости. Попробуйте в Chrome и нажмите воспроизведение ещё раз.';};
  audio.addEventListener('play',()=>{void control.set(wanted).catch(failure);});
  if(!form)continue;
  const update=()=>{wanted=Number(slider.value);output.textContent=(wanted>0?'+':'')+wanted.toLocaleString('ru-RU')+' дБ';void control.set(wanted).catch(failure);};
  slider.addEventListener('input',update);
  form.querySelector('[data-gain-reset]').addEventListener('click',()=>{slider.value='0';update();});
 }
 window.addEventListener('pagehide',event=>{if(event.persisted)return;for(const context of contexts.values())void context.close().catch(()=>{});contexts.clear();});
})();

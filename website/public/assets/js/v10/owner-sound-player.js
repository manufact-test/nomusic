/* CELIKOM v10 audio A/B: isolated 11-second excerpt, no extension-media changes. */
(()=>{
'use strict';
const board=document.getElementById('sound-panel');
const toggle=document.getElementById('celikom-demo-play');
const seek=document.getElementById('celikom-demo-seek');
const time=document.getElementById('celikom-demo-time');
const status=document.getElementById('sound-result');
const modes={service:document.getElementById('mode-service'),restored:document.getElementById('mode-restored')};
const sounds={service:document.getElementById('celikom-demo-service'),restored:document.getElementById('celikom-demo-restored')};
if(!board||!toggle||!seek||!time||!status||Object.values(sounds).some(x=>!x))return;
const length=11;
let mode='service',token=0,frame=null;
const visibleSeconds=n=>'0:'+String(Math.max(0,Math.min(length,Math.floor(n)))).padStart(2,'0');
const current=()=>sounds[mode];
const display=(at=current().currentTime||0)=>{
 const position=Math.max(0,Math.min(length,at));
 seek.value=String(position);
 seek.style.setProperty('--progress',(position/length*100).toFixed(3)+'%');
 time.textContent=visibleSeconds(position)+' / 0:11';
};
const fail=()=>{
 token++;
 for(const sound of Object.values(sounds)){sound.pause();sound.volume=1}
 status.hidden=false;
 status.textContent='Не удалось загрузить аудиофрагмент. Попробуй позже.';
 toggle.setAttribute('aria-label','Воспроизвести фрагмент');
 toggle.setAttribute('aria-pressed','false');
 board.dataset.playing='false'
};
const updateButton=()=>{
 const playing=!current().paused&&!current().ended;
 board.dataset.playing=playing?'true':'false';
 toggle.setAttribute('aria-pressed',String(playing));
 toggle.setAttribute('aria-label',playing?'Пауза':'Воспроизвести фрагмент');
 toggle.textContent=playing?'❚❚':'▶';
 if(playing){if(frame===null)frame=requestAnimationFrame(tick)}
 else if(frame!==null){cancelAnimationFrame(frame);frame=null}
};
function tick(){frame=null;display();if(!current().paused)frame=requestAnimationFrame(tick)}
const fade=(audio,from,to,ms,stamp,done)=>{
 const start=performance.now();
 function next(now){
  if(token!==stamp)return;
  const t=Math.min(1,(now-start)/ms);
  audio.volume=from+(to-from)*t;
  if(t<1)requestAnimationFrame(next);
  else if(done)done()
 }
 requestAnimationFrame(next)
};
const sourceReady=()=>{
 if(board.dataset.demoReady!=='true'){
  status.hidden=false;
  status.textContent='Аудиофрагменты пока недоступны.';
  return false
 }
 return true
};
async function play(){
 if(!sourceReady())return;
 const stamp=++token,sound=current();
 if(sound.currentTime>=length-.05)sound.currentTime=0;
 status.hidden=true;
 try{
  sound.volume=1;
  await sound.play();
  if(stamp!==token){sound.pause();return}
  updateButton()
 }catch{if(stamp===token)fail()}
}
toggle.addEventListener('click',()=>{
 if(!sourceReady())return;
 if(current().paused)play();
 else{token++;current().pause();updateButton()}
});
for(const [name,button] of Object.entries(modes)){
 if(!button)continue;
 button.addEventListener('click',()=>{
  if(name===mode)return;
  const former=current(),wasPlaying=!former.paused&&!former.ended;
  const position=Math.min(length-.03,Math.max(0,former.currentTime||0));
  const stamp=++token;
  former.pause();former.volume=1;
  mode=name;board.dataset.mode=name;
  for(const [key,element] of Object.entries(modes)){
   if(element)element.setAttribute('aria-pressed',String(key===name))
  }
  const replacement=current();
  try{replacement.currentTime=position}catch{}
  display(position);updateButton();
  if(!wasPlaying||!sourceReady())return;
  replacement.volume=0;
  replacement.play().then(()=>{
   if(token!==stamp){replacement.pause();return}
   fade(replacement,0,1,115,stamp,()=>{replacement.volume=1});
   updateButton()
  }).catch(()=>{if(token===stamp)fail()})
 })
}
seek.addEventListener('input',()=>{
 if(!sourceReady())return;
 const position=Number(seek.value),stamp=++token;
 for(const audio of Object.values(sounds)){
  try{audio.currentTime=position}catch{}
  audio.volume=1
 }
 if(!current().paused){
  const playing=current();
  playing.play().then(()=>{if(stamp===token)updateButton()})
                .catch(()=>{if(stamp===token)fail()});
 }
 display(position)
});
for(const sound of Object.values(sounds)){
 sound.addEventListener('timeupdate',()=>{if(sound===current())display()});
 sound.addEventListener('error',()=>{if(sound===current()&&board.dataset.demoReady==='true')fail()});
 sound.addEventListener('ended',()=>{
  if(sound!==current())return;
  token++;sound.pause();try{sound.currentTime=0}catch{}
  display(0);updateButton()
 })
}
if(!sourceReady())toggle.disabled=true;
display(0);updateButton()
})();

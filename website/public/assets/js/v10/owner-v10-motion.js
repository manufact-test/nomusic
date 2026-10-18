/* Owner-approved interaction-only layer. No visual v10 markup changes. */
(()=>{
'use strict';
const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
const smooth=()=>!reduced.matches;
let activateFaqHash=()=>{};
document.addEventListener('click',event=>{
 const link=event.target.closest('a[href^="#"]');
 if(!link||event.defaultPrevented||event.button!==0||event.metaKey||
 event.ctrlKey||event.shiftKey||event.altKey)return;
 const hash=link.getAttribute('href');
 if(!hash||hash==='#')return;
 let id;
 try{id=decodeURIComponent(hash.slice(1))}catch{return}
 const target=document.getElementById(id);
 if(!target)return;
 event.preventDefault();
 const top=target.getBoundingClientRect().top+window.scrollY-24;
 window.scrollTo({top:Math.max(0,top),behavior:smooth()?'smooth':'instant'});
 if(location.hash!==hash)history.pushState(null,'',hash);
 else history.replaceState(null,'',hash);
 if(target.matches('#faq details.faq-item'))activateFaqHash(target);
});
if(smooth()&&'IntersectionObserver'in window){
 const selectors=['.hero-copy','.hero .visual','.benefit','.process > .eyebrow',
 '.process > h2','.step','.demo-copy','.demo-board','.familiar > div',
 '.community-header','.community-card','.trust-copy','.trust-callout',
 '.faq-heading-row','.faq-nav','.faq-content','.reward-copy',
 '.reward-illustration','.install-text','.install-card','.closing'];
 const targets=[...new Set(document.querySelectorAll(selectors.join(',')))];
 const observer=new IntersectionObserver(entries=>{
  for(const entry of entries){
   if(!entry.isIntersecting)continue;
   entry.target.classList.add('celikom-visible');
   observer.unobserve(entry.target)
  }
 },{rootMargin:'0px 0px -35px 0px',threshold:.06});
 for(const element of targets){
  if(element.getBoundingClientRect().top<innerHeight*.83)continue;
  element.classList.add('celikom-reveal');
  observer.observe(element)
 }
}
// FAQ v5.10: globally coordinated accordion. Height is measured as a
// BORDER-BOX (the approved v10 CSS uses * {box-sizing:border-box}).
// Previously subtracting padding from scrollHeight caused a 23/19px jump.
const faqRoot=document.getElementById('faq');
if(faqRoot){
 const records=new Map();
 const items=[...faqRoot.querySelectorAll('details.faq-item')];
 for(const detail of items){
  const summary=detail.querySelector('summary');
  const answer=detail.querySelector('.answer');
  if(!summary||!answer)continue;
  records.set(detail,{detail,answer,desired:detail.open,animation:null});
 }
 let opened=[...records.keys()].find(detail=>detail.open&&!detail.hidden)||null;
 let queued=null;
 const canAnimate=state=>smooth()&&typeof state.answer.animate==='function';
 const tidy=state=>{
  state.answer.classList.remove('celikom-answer-animating');
  for(const prop of ['height','padding-bottom','overflow','opacity']){
   state.answer.style.removeProperty(prop)
  }
 };
 const interrupt=state=>{
  if(!state.animation)return null;
  const cs=getComputedStyle(state.answer);
  const frame={
   height:state.answer.getBoundingClientRect().height,
   padding:parseFloat(cs.paddingBottom)||0,
   opacity:parseFloat(cs.opacity)||0
  };
  const animation=state.animation;
  state.animation=null;
  animation.onfinish=null;
  animation.oncancel=null;
  animation.cancel();
  return frame
 };
 const naturalSize=state=>{
  const style=state.answer.style;
  const height=style.getPropertyValue('height');
  const padding=style.getPropertyValue('padding-bottom');
  // Read the natural border-box WITH bottom padding, not content height.
  style.removeProperty('height');
  style.removeProperty('padding-bottom');
  const box=state.answer.getBoundingClientRect().height;
  const bottom=parseFloat(getComputedStyle(state.answer).paddingBottom)||0;
  if(height)style.setProperty('height',height);
  if(padding)style.setProperty('padding-bottom',padding);
  return {height:box,padding:bottom,opacity:1}
 };
 function afterClose(){
  if(!queued)return;
  const next=queued;
  queued=null;
  if(next.hidden||!records.has(next))return;
  opened=next;
  transition(records.get(next),true)
 }
 function transition(state,wantOpen){
  if(state.desired===wantOpen &&
      (state.animation || state.detail.open===wantOpen))return;
  const detail=state.detail,answer=state.answer;
  const start=interrupt(state)|| (detail.open ? {
   height:answer.getBoundingClientRect().height,
   padding:parseFloat(getComputedStyle(answer).paddingBottom)||0,
   opacity:parseFloat(getComputedStyle(answer).opacity)||1
  } : {height:0,padding:0,opacity:0});
  state.desired=wantOpen;
  if(wantOpen)detail.open=true;
  if(!canAnimate(state)){
   detail.open=wantOpen;
   tidy(state);
   if(!wantOpen){
    if(opened===detail)opened=null;
    afterClose()
   }
   return
  }
  const end=wantOpen?naturalSize(state):{height:0,padding:0,opacity:0};
  answer.classList.add('celikom-answer-animating');
  answer.style.height=start.height+'px';
  answer.style.paddingBottom=start.padding+'px';
  answer.style.opacity=String(start.opacity);
  answer.style.overflow='hidden';
  const animation=answer.animate([
   {height:start.height+'px',paddingBottom:start.padding+'px',opacity:start.opacity},
   {height:end.height+'px',paddingBottom:end.padding+'px',opacity:end.opacity}
  ],{duration:wantOpen?290:260,easing:'cubic-bezier(.4,0,.2,1)',fill:'forwards'});
  state.animation=animation;
  animation.onfinish=()=>{
   if(state.animation!==animation)return;
   state.animation=null;
   animation.onfinish=null;
   animation.oncancel=null;
   animation.cancel();
   if(!state.desired)detail.open=false;
   tidy(state);
   if(!state.desired){
    if(opened===detail)opened=null;
    afterClose()
   }
  }
 }
 function requestOpen(detail){
  if(!records.has(detail)||detail.hidden)return;
  if(opened===detail){
   queued=null;
   transition(records.get(detail),true);
  }else if(opened){
   queued=detail;
   transition(records.get(opened),false)
  }else{
   opened=detail;
   queued=null;
   transition(records.get(detail),true)
  }
 }
 function requestToggle(detail){
  if(opened===detail){
   queued=null;
   transition(records.get(detail),!records.get(detail).desired)
  }else if(queued===detail){
   queued=null
  }else requestOpen(detail)
 }
 function forceClose(detail){
  const state=records.get(detail);
  if(!state)return;
  interrupt(state);
  state.desired=false;
  detail.open=false;
  tidy(state);
  if(opened===detail)opened=null;
  if(queued===detail)queued=null
 }
 // The source v10 filter hides other categories immediately. Stop any
 // effects before the filter's original click handler changes open/hidden.
 faqRoot.addEventListener('click',event=>{
  const filter=event.target.closest('.faq-filter');
  if(!filter||!faqRoot.contains(filter))return;
  const category=filter.dataset.filter;
  if(opened&&category!=='all'&&opened.dataset.category!==category)forceClose(opened);
  if(queued&&category!=='all'&&queued.dataset.category!==category)queued=null
 },true);
 for(const [detail,state] of records){
  detail.querySelector('summary').addEventListener('click',event=>{
   event.preventDefault();
   requestToggle(detail)
  });
  // The original filter and initial hash can alter details.open natively.
  detail.addEventListener('toggle',()=>{
   if(detail.open){
    if(state.animation)return;
    if(opened&&opened!==detail)forceClose(detail);
    else{opened=detail;state.desired=true}
   }else{
    interrupt(state);
    state.desired=false;
    tidy(state);
    if(opened===detail){opened=null;afterClose()}
   }
  })
 }
 activateFaqHash=target=>{
  if(!records.has(target))return;
  if(target.hidden){
   const filter=[...faqRoot.querySelectorAll('.faq-filter')]
    .find(button=>button.dataset.filter===target.dataset.category);
   if(filter)filter.click()
  }
  requestOpen(target)
 };
 window.addEventListener('hashchange',()=>{
  let id;
  try{id=decodeURIComponent(location.hash.slice(1))}catch{return}
  const item=document.getElementById(id);
  if(item)activateFaqHash(item)
 });
 // Protect against a restored page unexpectedly containing multiple opens.
 for(const detail of records.keys()){
  if(detail!==opened&&detail.open)forceClose(detail)
 }
}
})();

/* Owner-approved interaction-only layer. No visual v10 markup changes. */
(()=>{
'use strict';
const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
const smooth=()=>!reduced.matches;
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
// Closing animation modifies the answer's content HEIGHT and BOTTOM PADDING
// at the same time. Native details is collapsed only after both reach zero.
// The previous whole-card clipping made the answer disappear first, leaving
// an apparently separate closing step.
for(const detail of document.querySelectorAll('#faq details.faq-item')){
 const summary=detail.querySelector('summary');
 const answer=detail.querySelector('.answer');
 if(!summary||!answer)continue;
 let active=null;
 let desiredOpen=detail.open;
 let naturalContent=0;
 let naturalPadding=0;
 const cleanup=()=>{
  answer.classList.remove('celikom-answer-animating');
  for(const property of ['height','padding-bottom','overflow','opacity']){
   answer.style.removeProperty(property)
  }
 };
 summary.addEventListener('click',event=>{
  if(!smooth()||typeof answer.animate!=='function')return;
  event.preventDefault();
  // Read the current interpolated values for rapid repeated clicks.
  let fromHeight=0,fromPadding=0,fromOpacity=0;
  if(active){
   const cs=getComputedStyle(answer);
   fromHeight=parseFloat(cs.height)||0;
   fromPadding=parseFloat(cs.paddingBottom)||0;
   fromOpacity=parseFloat(cs.opacity)||0;
   const was=active;
   active=null;
   was.onfinish=null;
   was.oncancel=null;
   was.cancel();
   answer.style.height=fromHeight+'px';
   answer.style.paddingBottom=fromPadding+'px';
   answer.style.opacity=String(fromOpacity)
  }else if(detail.open){
   const cs=getComputedStyle(answer);
   fromHeight=parseFloat(cs.height)||0;
   fromPadding=parseFloat(cs.paddingBottom)||0;
   fromOpacity=1
  }
  const opening=!desiredOpen;
  desiredOpen=opening;
  if(opening && !detail.open){
   detail.open=true;
   // Detect full natural dimensions before setting an explicit height.
   const cs=getComputedStyle(answer);
   naturalPadding=parseFloat(cs.paddingBottom)||0;
   naturalContent=Math.max(0,answer.scrollHeight-naturalPadding)
  }else if(!naturalContent){
   const cs=getComputedStyle(answer);
   naturalPadding=parseFloat(cs.paddingBottom)||0;
   naturalContent=Math.max(0,answer.scrollHeight-naturalPadding)
  }
  const toHeight=opening?naturalContent:0;
  const toPadding=opening?naturalPadding:0;
  const toOpacity=opening?1:0;
  answer.classList.add('celikom-answer-animating');
  answer.style.height=fromHeight+'px';
  answer.style.paddingBottom=fromPadding+'px';
  answer.style.opacity=String(fromOpacity);
  answer.style.overflow='hidden';
  const current=answer.animate([
   {height:fromHeight+'px',paddingBottom:fromPadding+'px',opacity:fromOpacity},
   {height:toHeight+'px',paddingBottom:toPadding+'px',opacity:toOpacity}
  ],{duration:opening?290:260,easing:'cubic-bezier(.4,0,.2,1)',fill:'forwards'});
  active=current;
  current.onfinish=()=>{
   if(active!==current)return;
   active=null;
   current.oncancel=null;
   current.cancel();
   if(!desiredOpen)detail.open=false;
   cleanup()
  };
  current.oncancel=()=>{
   if(active!==current)return;
   active=null;
   cleanup()
  }
 });
}
})();
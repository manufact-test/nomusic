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
for(const detail of document.querySelectorAll('#faq details.faq-item')){
 const summary=detail.querySelector('summary');
 if(!summary)continue;
 let animation=null;
 let desiredOpen=detail.open;
 const reset=()=>{
  detail.classList.remove('celikom-faq-animating');
  detail.style.removeProperty('height');
  detail.style.removeProperty('overflow');
 };
 summary.addEventListener('click',event=>{
  if(!smooth()||typeof detail.animate!=='function')return;
  event.preventDefault();
  // A fast second click reverses the current animation smoothly.
  // Measure the rendered intermediate height BEFORE cancelling WAAPI.
  const from=detail.getBoundingClientRect().height;
  const opening=!desiredOpen;
  desiredOpen=opening;
  if(animation){
   animation.onfinish=null;
   animation.cancel();
   animation=null;
  }
  if(opening)detail.open=true;
  const computed=getComputedStyle(detail);
  const border=(parseFloat(computed.borderTopWidth)||0)
              +(parseFloat(computed.borderBottomWidth)||0);
  const closedHeight=summary.getBoundingClientRect().height+border;
  const expandedHeight=detail.scrollHeight+border;
  const to=opening?expandedHeight:closedHeight;
  if(Math.abs(to-from)<.5){
   detail.open=opening;
   reset();
   return;
  }
  detail.classList.add('celikom-faq-animating');
  detail.style.height=from+'px';
  detail.style.overflow='hidden';
  const current=detail.animate(
   [{height:from+'px'},{height:to+'px'}],
   {duration:opening?270:260,easing:'cubic-bezier(.22,.7,.22,1)',fill:'forwards'}
  );
  animation=current;
  current.onfinish=()=>{
   if(animation!==current)return;
   // Close only after the whole card, including its padding, has collapsed.
   detail.open=desiredOpen;
   current.cancel();
   animation=null;
   reset();
  };
  current.oncancel=()=>{
   if(animation===current){animation=null;reset()}
  };
 })
}
})();
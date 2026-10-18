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
 const answer=detail.querySelector('.answer');
 if(!summary||!answer)continue;
 let active=null;
 summary.addEventListener('click',event=>{
  if(!smooth()||typeof answer.animate!=='function')return;
  event.preventDefault();
  if(active){active.finish();active=null}
  const opening=!detail.open;
  if(opening)detail.open=true;
  const height=answer.scrollHeight;
  const start=opening?0:height;
  const end=opening?height:0;
  const animation=answer.animate([
   {height:start+'px',opacity:opening?0:1},
   {height:end+'px',opacity:opening?1:0}
  ],{duration:opening?240:180,easing:'cubic-bezier(.22,.7,.22,1)'});
  active=animation;
  animation.onfinish=()=>{
   if(active!==animation)return;
   if(!opening)detail.open=false;
   active=null
  };
  animation.oncancel=()=>{if(active===animation)active=null}
 })
}
})();
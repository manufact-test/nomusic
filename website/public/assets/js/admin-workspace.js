/* CELIKOM CMS owner workspace: accessible single-area navigation, no server state changes. */
(()=>{
 'use strict';
 const shell=document.querySelector('.cms-shell');
 if(!shell)return;
 const pages=[...shell.querySelectorAll('[data-cms-view]')];
 const links=[...shell.querySelectorAll('[data-cms-link]')];
 const groups=[...shell.querySelectorAll('#text-editor details.section-editor')];
 const groupButtons=[...shell.querySelectorAll('[data-cms-group-select]')];
 const faqEntries=[...shell.querySelectorAll('#faq-editor details.faq-entry')];
 const faqTabs=[...shell.querySelectorAll('[data-faq-filter]')];
 const faqSearch=document.getElementById('cms-faq-search');
 const faqCounter=document.getElementById('cms-faq-count');
 const title=document.getElementById('cms-active-title');
 const names={'overview':'Обзор сайта','text-editor':'Тексты и разделы',
  'faq-editor':'Вопросы и ответы','media-editor':'Медиатека',
  'revision-editor':'Публикации'};
 const recognized=new Set(Object.keys(names));
 const areaFromHash=()=>{
  const id=location.hash.slice(1);
  return recognized.has(id)?id:null;
 };
 const groupFromParams=new URLSearchParams(location.search).get('group');
 let rememberedGroup=null;
 try{rememberedGroup=sessionStorage.getItem('celikom_cms_editor_group')}catch{}

 const show=(target,updateHash)=>{
  if(!recognized.has(target))target='overview';
  document.body.classList.add('cms-ui-ready');
  for(const page of pages){
   const active=page.dataset.cmsView===target;
   page.classList.toggle('is-active',active);
   page.hidden=!active;
  }
  for(const link of links){
   const active=link.dataset.cmsLink===target;
   link.classList.toggle('is-active',active);
   if(active)link.setAttribute('aria-current','page');
   else link.removeAttribute('aria-current');
  }
  if(title)title.textContent=names[target];
  if(updateHash){
   if(location.hash!=='#'+target)history.pushState(null,'','#'+target);
   window.scrollTo({top:0,behavior:'instant'});
  }
 };
 const chooseGroup=(index)=>{
  if(index<0||index>=groups.length)return;
  for(let i=0;i<groups.length;i++){
   const selected=index===i;
   groups[i].hidden=!selected;
   groups[i].open=selected;
  }
  try{sessionStorage.setItem('celikom_cms_editor_group',groups[index].dataset.cmsGroup)}catch{}
  for(const button of groupButtons){
   const on=button.dataset.cmsGroupSelect===groups[index].dataset.cmsGroup;
   button.classList.toggle('is-active',on);
   button.setAttribute('aria-pressed',String(on));
  }
 };
 for(const link of links){
  link.addEventListener('click',event=>{
   if(event.ctrlKey||event.metaKey||event.altKey||event.shiftKey)return;
   event.preventDefault();
   show(link.dataset.cmsLink,true)
  })
 }
 for(const button of groupButtons){
  button.addEventListener('click',()=>{
   const index=groups.findIndex(x=>x.dataset.cmsGroup===button.dataset.cmsGroupSelect);
   if(index>=0)chooseGroup(index)
  })
 }
 for(const group of groups){
  group.querySelector('summary')?.addEventListener('click',event=>{
   // Keep one predictable open group, never a 14-section accordion.
   event.preventDefault()
  })
 }
 const filterFaq=()=>{
  const tab=faqTabs.find(b=>b.getAttribute('aria-pressed')==='true');
  const category=tab?.dataset.faqFilter||'all';
  const search=(faqSearch?.value||'').trim().toLocaleLowerCase('ru');
  let count=0;
  for(const entry of faqEntries){
   const same=category==='all'||entry.dataset.faqCategory===category;
   const matches=!search||entry.querySelector('summary')?.textContent.toLocaleLowerCase('ru').includes(search);
   const visible=same&&matches;
   entry.hidden=!visible;
   if(!visible)entry.open=false;
   if(visible)count++;
  }
  if(faqCounter)faqCounter.textContent='Показано вопросов: '+count;
 };
 for(const tab of faqTabs)tab.addEventListener('click',()=>{
  for(const b of faqTabs)b.setAttribute('aria-pressed',String(b===tab));
  filterFaq()
 });
 faqSearch?.addEventListener('input',filterFaq);
 let initial=areaFromHash();
 if(!initial){
  const saved=new URLSearchParams(location.search).get('saved')||'';
  initial=(saved==='1')?'text-editor':
   (saved==='faq')?'faq-editor':
   (saved==='media'||saved==='media-choice')?'media-editor':
   (saved==='published'||saved==='restored')?'revision-editor':'overview';
 }
 const preferred=groups.findIndex(group=>group.dataset.cmsGroup===(groupFromParams||rememberedGroup));
 chooseGroup(preferred>=0?preferred:0);
 filterFaq();
 show(initial,false);
 // After saving an individual FAQ, return the owner to the exact question
 // rather than collapsing the whole editor back to an anonymous list.
 const focusId=new URLSearchParams(location.search).get('focus');
 if(initial==='faq-editor' && focusId && /^faq-question-[0-9]{2,4}$/.test(focusId)){
  const entry=faqEntries.find(item=>item.querySelector('input[name="faq_id"]')?.value===focusId);
  if(entry){
   for(const tab of faqTabs)tab.setAttribute('aria-pressed',String(tab.dataset.faqFilter==='all'));
   if(faqSearch)faqSearch.value='';
   filterFaq();
   entry.open=true;
   requestAnimationFrame(()=>entry.scrollIntoView({block:'center',behavior:'instant'}));
  }
 }

 window.addEventListener('hashchange',()=>{
  const section=areaFromHash();
  if(section)show(section,false)
 });
})();

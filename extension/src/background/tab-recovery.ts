import { isSupportedPage } from "./controller-bootstrap.js";

// Bounded event-driven retries fit within an ordinary MV3 wake; no permanent
// worker, polling, alarm permission, forced reload or tab focus change.
export function registerTabRecovery(api, bootstrap, readEnabled, clock = {}) {
  const jobs=new Map();
  const schedule=clock.schedule||((fn,ms)=>{const timer=setTimeout(fn,ms);timer?.unref?.();return timer;});
  const cancel=clock.cancel||clearTimeout;
  const delays=[500,1500,4000];
  const retryable=result=>result?.retryable===true||["controller-start-timeout","bridge-connect-timeout"].includes(result?.error);
  const valid=job=>jobs.get(job.tabId)===job;
  function forget(tabId){const job=jobs.get(tabId);if(job?.timer!=null)cancel(job.timer);jobs.delete(tabId);bootstrap.forget(tabId);}
  async function recover(job) {
    if(!valid(job))return;
    job.timer=null;
    try {
      if(!await readEnabled()||!valid(job)){if(valid(job))jobs.delete(job.tabId);return;}
      let tab;try{tab=await api.tabs.get(job.tabId);}catch{if(valid(job))jobs.delete(job.tabId);return;}
      if(!valid(job))return;
      if(!isSupportedPage(tab.url)||tab.discarded||tab.status==="loading"){if(valid(job))jobs.delete(job.tabId);return;}
      if(!await readEnabled()||!valid(job)){if(valid(job))jobs.delete(job.tabId);return;}
      const result=await bootstrap.ensure(job.tabId);
      if(!valid(job))return;
      if(retryable(result)&&job.attempt<delays.length&&await readEnabled()&&valid(job)){
        job.timer=schedule(()=>{void recover(job);},delays[job.attempt++]);return;
      }
    }catch{/* Local tab lifecycle failures are retried by the next browser event. */}
    if(valid(job))jobs.delete(job.tabId);
  }
  const attempt=tabId=>{if(!Number.isInteger(tabId)||jobs.has(tabId))return;const job={tabId,attempt:0,timer:null};jobs.set(tabId,job);void recover(job);};
  api.tabs.onUpdated?.addListener((tabId,change)=>{
    if(change.status==="loading"||change.url||change.discarded===true)forget(tabId);
    if(change.status==="complete"||change.discarded===false)attempt(tabId);
  });
  api.tabs.onCreated?.addListener(tab=>{if(isSupportedPage(tab.url))attempt(tab.id);});
  api.tabs.onActivated?.addListener(info=>attempt(info.tabId));
  api.tabs.onReplaced?.addListener((added,removed)=>{forget(removed);attempt(added);});
  api.tabs.onRemoved?.addListener(forget);
}

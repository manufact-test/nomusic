import {readDisplay,writeDisplay,clearDisplay} from "./display-cache.js";
// The remembered hint controls layout only; export always rechecks the background authority.
export function initDiagnosticsButton(send) {
 const node=document.querySelector("[data-action='diagnostics']");if(!node)return;
 let generation=0,allowed=false;
 node.hidden=readDisplay("diagnostics-hint")?.show!==true;node.disabled=true;
 async function refresh(){const own=++generation;allowed=false;node.disabled=true;
  try {const result=await send({type:"CELIKOM_AUTH",action:"diagnostics-access"});if(own!==generation)return;
   allowed=result?.ok===true&&result.allowed===true;if(!allowed&&result?.verified===false)return;node.hidden=!allowed;node.disabled=!allowed;
   if(allowed)writeDisplay("diagnostics-hint",{show:true});else clearDisplay("diagnostics-hint");
  }catch{if(own===generation){allowed=false;node.disabled=true;}}
 }
 document.addEventListener?.("celikom-account-logout",()=>{generation++;allowed=false;node.disabled=true;node.hidden=true;clearDisplay("diagnostics-hint");});
 document.addEventListener?.("celikom-account-login",()=>{void refresh();});
 node.addEventListener("click",async()=>{if(!allowed)return;
  const own=generation;const result=await send({type:"CELIKOM_DIAGNOSTICS_GET"});
  if(own!==generation)return;if(!result?.ok||!result.state){allowed=false;node.hidden=true;node.disabled=true;clearDisplay("diagnostics-hint");return;}
  await navigator.clipboard.writeText(JSON.stringify(result.state,null,2));node.textContent="Скопировано";
 });
 void refresh();return {refresh};
}

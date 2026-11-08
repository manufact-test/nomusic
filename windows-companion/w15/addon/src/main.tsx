import {defineAddon} from "@pulsesync/addon-sdk";
import addonConfig from "../addon.config.mjs";
import {createCelikomSourceController} from "../../source-controller.mjs";
import {createCompanionBridge} from "../../bridge-client.mjs";

// Runtime is permitted only in a user's intentionally installed PulseSync host.
// This file never patches, launches or debugs Yandex Music.
export default defineAddon({
  id: addonConfig.id,
  name: addonConfig.name,
  start: async api => {
    const local = createCompanionBridge({net:api.net, storage:api.storage});
    let trustedApiOrigin = "";
    const controller = createCelikomSourceController({
      api, resolve:(id, signal)=>local.resolve(id, signal),
      // Only a paired companion can supply an API origin and signed grant.
      allowedOrigin: () => trustedApiOrigin
    });
    let stopped=false, asked=false, timer;
    const stop=()=>{
      if(stopped)return;
      stopped=true;
      if(timer)clearInterval(timer);
      api.signal.removeEventListener("abort",stop);
      void controller.dispose();
    };
    const ask=async()=>{
      if(asked||stopped)return;
      asked=true;
      try {
        const values = await api.modals.form({
          title:"Подключить CELIKOM Companion",
          message:"Откройте CELIKOM на Windows и введите шестизначный код из приложения.",
          confirmLabel:"Подключить", cancelLabel:"Позже",
          fields:[{name:"code", label:"Код CELIKOM",type:"text",
            value:"", placeholder:"000000", minLength:6,maxLength:6,required:true}]
        });
        if(stopped||!values||typeof values.code!=="string")return;
        const ok=await local.pair(values.code.trim());
        if(ok)await check();
        else void api.toasts.show("CELIKOM: неверный или просроченный код.");
      } catch { /* No modal support or user cancelled: remain off */ }
    };
    const check=async()=>{
      if(stopped)return;
      const online=await local.health();
      if(!online){controller.disable();return;}
      if(!local.pairedLocally) {controller.disable();void ask();return;}
      const status=await local.state();
      if(stopped)return;
      if(!status.paired) {controller.disable();return;}
      let canonicalOrigin="";
      try {
        const parsed=new URL(status.apiOrigin || "");
        if(parsed.protocol === "https:" && parsed.origin === status.apiOrigin &&
           parsed.pathname === "/" && !parsed.username && !parsed.password)
          canonicalOrigin=parsed.origin;
      } catch {}
      if(canonicalOrigin !== trustedApiOrigin) {
        controller.disable();
        trustedApiOrigin=canonicalOrigin;
      }
      if(status.enabled && status.signedIn && trustedApiOrigin)controller.enable();
      else controller.disable();
      await local.heartbeat(controller.trackId,controller.status);
    };
    try {
      await controller.start();
      await local.initialize();
      api.signal.addEventListener("abort",stop,{once:true});
      // A user can launch CELIKOM before OR after Yandex. The bridge is
      // rechecked in the background; a failure leaves original audio.
      timer=setInterval(()=>{void check().catch(()=>controller.disable())},2600);
      void check().catch(()=>controller.disable());
      return stop;
    } catch (error) {stop();throw error;}
  }
});

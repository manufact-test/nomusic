/**
 * W7 CDP-activated fixture payload. Never bundled or injected into Yandex Music.
 * CDP only imports this module after confirming a nonce-bound LOCAL test page.
 */
import { createWindowsSourceBridge } from "/bridge.mjs";
import { createNativeOriginalRecovery } from "/recovery.mjs";

export async function runW7(nonce) {
  const checks=[], blobs=[];
  let bridge, audio, recovery;
  const check=(value,label)=>{if(!value)throw Error("W7_ASSERT_"+label);checks.push(label);};
  const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const match=new URL(location.href);
  if (match.hostname!=="127.0.0.1" || match.searchParams.get("nonce")!==nonce ||
      document.title!=="CELIKOM W7 isolated attach") throw Error("W7_NOT_ISOLATED_FIXTURE");
  const req=window.__nativeFixture?.req;
  check(typeof req==="function","pinned actual public Yandex Webpack factories loaded");
  const Source=req(window.__nativeFixture.sourceModule).__testNativeSource;
  check(typeof Source==="function","genuine Yandex native source getter available in test");
  const resources=[];
  for(const [moduleId, factory] of Object.entries(req.m)){
    const text=Function.prototype.toString.call(factory);
    if(!text.includes("getFileInfoBatch") ||
       (!text.includes('"get-file-info"') && !text.includes('"resources/v2/file-info"'))) continue;
    try {
      for(const C of Object.values(req(moduleId)))
        if(typeof C==="function" && C.prototype?.getFileInfo && C.prototype?.getFileInfoBatch &&
           !resources.includes(C))resources.push(C);
    }catch{}
  }
  check(resources.length===2,"two genuine Yandex resource classes v1/v2 loaded");
  const register=async trackId=>{
    const response=await fetch(trackId==="1001"?"/media/alt1001.mp3":"/media/alt2002.mp3");
    check(response.ok && response.headers.get("content-type")==="audio/mpeg",
      "synthetic alternate audio fetched and validated");
    const bytes=await response.arrayBuffer();
    check(bytes.byteLength>10000,"whole synthetic MP3 byte buffer available");
    const url=URL.createObjectURL(new Blob([bytes],{type:"audio/mpeg"}));
    blobs.push(url);
    return url;
  };
  try {
    bridge=createWindowsSourceBridge({origin:location.origin});
    for(const C of resources)bridge.install(C.prototype);
    check(bridge.diagnostics().installed===2,"W4 source gate dynamically installed from external CDP activation");
    bridge.setEnabled(true);bridge.setTrack("1001");
    const first=await register("1001"), second=await register("2002");
    for(const [trackId,url]of [["1001",first],["2002",second]])
      bridge.registerPreparedAsset({trackId,url,expiresAt:Date.now()+110000,
        bitrate:128,approved:true,entitled:true,durationMatched:true,audioValidated:true});
    const original=id=>{
      const source=id==="2002"?"/media/orig2002.mp3":"/media/orig1001.mp3";
      return {trackId:id,realId:id,codec:"mp3",transport:"raw",bitrate:128,
        quality:"nq",urls:[location.origin+source],url:location.origin+source};
    };
    const instances=resources.map(C=>{
      const kind=C.prototype.getByteRange?"v1":"v2";
      const obj=Object.create(C.prototype);
      obj.createHttpOptions=x=>x;
      obj.httpClient={get:async(path,params)=>({url:location.origin+"/file-info",
        timings:{response:1},json:async()=>{
          const ids=String(params?.params?.trackIds||params?.params?.trackId||"").split(",");
          if(path.includes("batch"))return {[kind==="v1"?"downloadInfos":"fileInfos"]:ids.map(original)};
          return kind==="v1"?{downloadInfo:original(ids[0])}:original(ids[0]);
        }})};
      return {kind,obj};
    });
    const single=async(obj,id)=>{
      const response=await obj.getFileInfo({trackId:id,quality:"nq",
        codecs:["mp3"],transports:["raw"]});
      return response?.downloadInfo||response?.fileInfo;
    };
    for(const {kind,obj}of instances){
      check((await single(obj,"1001")).url===first,kind+" exact-ID replacement descriptor");
      const resp=await obj.getFileInfoBatch({trackIds:"9999,1001,2002",
        quality:"nq",codecs:["mp3"],transports:["raw"]});
      const arr=resp?.downloadInfos||resp?.fileInfos;
      check(arr.length===3&&arr[0].url===original("9999").url&&arr[1].url===first&&
        arr[2].url===original("2002").url,kind+" untouched mixed batch");
    }
    audio=document.createElement("audio");audio.muted=true;audio.preload="auto";
    document.body.append(audio);
    check(document.querySelectorAll("audio,video").length===1,"only one playing media element");

    const load=async data=>{
      const native=new Source({data,loadingTime:performance.now()});
      native.vsid="w7-test";native.sourceIndex=0;native.positionSec=0;
      const raw=native.src;
      let src=raw;
      // Scope normalization to only two exactly owned, ephemeral fixture Blobs.
      for(const owned of blobs)if(raw.startsWith(owned+"?")){
        src=owned+(raw.includes("#")?raw.slice(raw.indexOf("#")):"");break;
      }
      const loaded=new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>{cleanup();reject(Error("W7_LOAD_TIMEOUT"));},10000);
        const yes=()=>{cleanup();resolve();};
        const no=()=>{cleanup();reject(Error("W7_MEDIA_ERROR_"+(audio.error?.code||0)));};
        function cleanup(){clearTimeout(timer);audio.removeEventListener("loadeddata",yes);
          audio.removeEventListener("error",no);}
        audio.addEventListener("loadeddata",yes);audio.addEventListener("error",no);
      });
      audio.pause();audio.src=src;audio.load();await loaded;
      return {raw,src};
    };
    const seek=async sec=>{
      const reached=new Promise((resolve,reject)=>{
        const timer=setTimeout(()=>{audio.removeEventListener("seeked",on);reject(Error("W7_SEEK_TIMEOUT"));},9000);
        const on=()=>{clearTimeout(timer);resolve();};
        audio.addEventListener("seeked",on,{once:true});
      });
      audio.currentTime=sec;await reached;
    };
    const firstDescriptor=await single(instances[0].obj,"1001");
    const firstSource=await load(firstDescriptor);
    check(firstSource.src.startsWith(first)&&firstSource.raw.includes("?vsid="),
      "actual Yandex getter passes alternate source to native Electron decoder");
    check(audio.duration>9&&audio.duration<11,"native first track duration matches 10s");
    await audio.play();await sleep(200);
    check(!audio.paused&&audio.currentTime>0,"native audio playback starts");
    audio.pause();const time=audio.currentTime;await sleep(150);
    check(audio.paused&&Math.abs(audio.currentTime-time)<0.03,"native Pause holds same clock");
    await seek(7);check(Math.abs(audio.currentTime-7)<0.2,"native Seek works");

    // W8: intentionally corrupt the currently selected synthetic alternate,
    // let Electron deliver a REAL media error, then automatically reacquire
    // and restore the original through the SAME media element.
    recovery=createNativeOriginalRecovery({
      sourceGate:bridge,
      reacquireOriginal:async id=>single(instances[0].obj,id),
      applyToSameDecoder:async({original:descriptor,snapshot,isCurrent})=>{
        if(!isCurrent())return false;
        await load(descriptor); // never constructs another decoder
        if(!isCurrent())return false;
        if(snapshot.positionSec>0){
          const position=Math.min(snapshot.positionSec,Math.max(0,audio.duration-0.3));
          await seek(position);
        }
        if(!isCurrent())return false;
        if(snapshot.wasPlaying)await audio.play();
        return true;
      }
    });
    recovery.setTrack("1001");
    await audio.play();
    const playbackSnapshot={positionSec:audio.currentTime,wasPlaying:!audio.paused};
    const corrupt=URL.createObjectURL(new Blob([new Uint8Array(1024)],{type:"audio/mpeg"}));
    blobs.push(corrupt);
    const failureEvent=new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{audio.removeEventListener("error",on);reject(Error("W8_MEDIA_ERROR_NOT_TRIGGERED"));},12000);
      const on=()=>{clearTimeout(timer);resolve(audio.error?.code||0);};
      audio.addEventListener("error",on,{once:true});
    });
    audio.src=corrupt;audio.load();
    const mediaFault=await failureEvent;
    check(mediaFault===4,"real Electron decoder reports unsupported/corrupt synthetic MP3");
    const recovered=await recovery.onNativeDecodeError("1001",playbackSnapshot);
    check(recovered.status==="RESTORED_ORIGINAL","W8 automatically reacquires and plays original on decoder error");
    check(audio.currentSrc.startsWith(location.origin+"/media/orig1001.mp3")&&
      !audio.paused&&Math.abs(audio.currentTime-playbackSnapshot.positionSec)<0.6,
      "W8 original restored at same position and play state in ONE media element");
    check((await recovery.onNativeDecodeError("1001",playbackSnapshot)).status==="ALREADY_ATTEMPTED",
      "W8 duplicate decoder error cannot trigger recovery loop");
    check(document.querySelectorAll("audio,video").length===1,
      "W8 fallback did not create a second decoder");
    recovery.setTrack("2002");
    bridge.setTrack("2002");
    const next=await single(instances[1].obj,"2002");
    check(next.url===second,"Next chooses exact second track");
    await load(next);
    check(audio.duration>29&&audio.duration<31,"longer second track decoded");
    await seek(25);await audio.play();
    check(!audio.paused&&audio.currentTime>=24.8,"native late Seek after Next works");
    check(document.querySelectorAll("audio,video").length===1,
      "Next did not create overlay player");

    let release;
    const waitFor=new Promise(resolve=>{release=resolve;});
    const delayed=instances[0].obj,origGet=delayed.httpClient.get;
    delayed.httpClient.get=async(...args)=>{await waitFor;return origGet(...args);};
    bridge.setTrack("1001");const pending=single(delayed,"1001");
    bridge.setTrack("2002");release();
    const stale=await pending;
    check(stale.url===original("1001").url,"delayed old result retains original without stale rewrite");
    delayed.httpClient.get=origGet;

    bridge.original();
    const old=await single(instances[1].obj,"2002");
    check(old.url===original("2002").url,"Original reacquisition returns untouched descriptor");
    const restored=await load(old);
    check(restored.src.startsWith(location.origin+"/media/orig2002.mp3"),
      "original synthetic URL consumed by same native decoder");
    await audio.play();await sleep(150);
    check(!audio.paused,"original synthetic MP3 plays normally");
    bridge.stop();
    check((await single(instances[1].obj,"2002")).url===original("2002").url,
      "Stop prevents future replacement");
    check(document.querySelectorAll("audio,video").length===1,
      "no second player is constructed");
    return {passed:true,assertions:checks.length,checks,scope:"ISOLATED_FIXTURE_ONLY",
      officialAppTested:false};
  }finally{
    audio?.pause();audio?.removeAttribute("src");audio?.load();audio?.remove();
    recovery?.dispose();bridge?.dispose();for(const url of blobs)URL.revokeObjectURL(url);
  }
}

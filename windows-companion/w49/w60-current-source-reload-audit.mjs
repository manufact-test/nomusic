/**
 * W60: READ-ONLY audit of a pinned, signed original Yandex 5.126.1 ASAR.
 * Do not call player actions, patch source, inspect accounts or print URLs.
 * Goal: determine if there is an already-supported safe in-place source refresh
 * for CELIKOM Start/Stop that preserves track, queue, position and pause.
 */
import fs from "node:fs";
import crypto from "node:crypto";
import {inspectAsar} from "../w23/asar-images.mjs";
const input=process.argv[2];
if(!input)throw Error("W60_VENDOR_ASAR_MISSING");
const bytes=fs.readFileSync(input);
const actual=crypto.createHash("sha256").update(bytes).digest("hex");
if(actual!=="5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215")
  throw Error("W60_UNTRUSTED_ASAR");
const chunks=[
  "app/_next/static/chunks/9091-cdf5e7f5a0e6a5b5.js",
  "app/_next/static/chunks/app/(product)/layout-4afaa928fcc37741.js"
];
function safe(s){return s.replace(/https?:\/\/[^\s'"<>]+/g,"[URL]").replace(/\b[a-f0-9]{40,}\b/gi,"[HASH]").replace(/\s+/g," ").slice(0,1150)}
for(const chunk of chunks) {
  const src=inspectAsar(bytes,chunk).toString("utf8");
  const isPlayer=chunk.includes("9091-");
  const tokens=isPlayer
    ? ["class Z{","restartContext(","setIndex(","setProgress(","playContext(","playCurrent(","restartTrack(","resume()","getCurrentEntity(","this.player.play(","this.player.playback","changeCurrentIndex","reloadEntity(","reload(e)","reloadMediaSource(","mediaController.reload(","currentMediaPlayer.play(","playbackState.queueState.index","getCurrentEntity(","currentContextEntityPair","disableCache","QUALITY_CHANGE","qualityChange","reloadEntity(C.QUALITY_CHANGE)","beforeEntityReloadProcessStart"]
    : ["getMediaSource(","getFileInfo(","getCurrentTrack(","restartContext(","setIndex(","playContext(","reloadCurrent(","invalidateMediaSource(","reloadEntity(","reload(e)","getPreloadedFileInfo(","disableCache","mediaSourceData=null","QUALITY_CHANGE","qualityChange"];
  const found={};
  for(const token of tokens){
    let idx=-1,offset=0; const hits=[];
    while((idx=src.indexOf(token,offset))>=0 && hits.length<12) {
      offset=idx+token.length;
      hits.push(idx);
    }
    if(hits.length)found[token]=hits.length;
    for(const idx of hits.slice(0,isPlayer?4:2)) {
      const raw=src.slice(Math.max(0,idx-90),Math.min(src.length,idx+1000));
      console.log("W60_STATIC_PLAYER_CONTEXT "+JSON.stringify({chunk:isPlayer?"player":"provider",token,index:idx,context:safe(raw)}));
    }
  }
  console.log("W60_STATIC_PLAYER_COUNTS "+JSON.stringify({chunk:isPlayer?"player":"provider",length:src.length,found}));
}
console.log("W60_READONLY_DONE_NO_RUNTIME_CHANGE");

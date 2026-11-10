/**
 * W49b: bounded, READ-ONLY semantic review of pinned vendor ASAR.
 * Reads only known static chunks. Never starts renderer, executes source,
 * accesses Yandex account, or changes files; clips source excerpts.
 */
import fs from "node:fs";
import crypto from "node:crypto";
import {inspectAsar} from "../w23/asar-images.mjs";

const file=process.argv[2];if(!file)throw Error("W49B_ARG");
const bytes=fs.readFileSync(file);
if(crypto.createHash("sha256").update(bytes).digest("hex")!==
  "5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215")
  throw Error("W49B_INVALID_VENDOR_HASH");
const files=[
  "app/_next/static/chunks/6820-4385b9c887bedd61.js",
  "app/_next/static/chunks/app/(product)/layout-4afaa928fcc37741.js",
  "app/_next/static/chunks/9091-cdf5e7f5a0e6a5b5.js"
];
const needles=[
  "getFileInfoFromResourceRequest",
  "getFileInfoFrom",
  "isResourcesFileInfoEnabled",
  "getFileInfoBatch",
  "downloadInfo",
  "fileInfo:e.fileInfo",
  "transports:",
  "encraw",
  "aac-mp4",
  "key:",
  ".key",
  "decryptKey",
  "url:",
  "urls:",
  "codec:",
  "gain:",
  "responseTime",
  "TRACK_DECRYPT_KEY_RECEIVED",
  "PLAYER_ERROR",
  "MEDIA_ELEMENT_ERROR",
  "AudioContext",
  "MediaSourcePreload"
];
let shown=0;
for(const fileName of files){
  const s=inspectAsar(bytes,fileName).toString("utf8");
  const tally={};
  for(const needle of needles){
    const positions=[];let p=0;
    while((p=s.indexOf(needle,p))>=0){positions.push(p);p+=needle.length||1;if(positions.length>1000)break;}
    if(positions.length===0)continue;
    tally[needle]=positions.length;
    // Prefer response/shaping cases before player-library internals.
    const cap=/FileInfoFrom|fileInfo:e|encraw|transports:|downloadInfo|decryptKey/.test(needle)?3:1;
    for(const pos of positions.slice(0,cap)){
      if(shown>=65)break;
      const raw=s.slice(Math.max(0,pos-230),Math.min(s.length,pos+needle.length+330));
      const safe=raw.replace(/https?:\/\/[^\s'"<>]+/g,"[URL]")
        .replace(/\b[a-f0-9]{40,}\b/gi,"[HASH]")
        .replace(/[\u0000-\u001f\u007f-\u009f]+/g," ")
        .replace(/\s+/g," ").slice(0,610);
      console.log("W49B_SEMANTIC_CONTEXT "+JSON.stringify({script:fileName.split("/").at(-1),needle,pos,context:safe}));
      shown++;
    }
  }
  console.log("W49B_SEMANTIC_COUNTS "+JSON.stringify({file:fileName,bytes:s.length,tally}));
}
console.log("W49B_READONLY_VERIFIED_ORIGINAL");

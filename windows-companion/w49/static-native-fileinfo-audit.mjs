/**
 * W49: static-only analysis of the vendor-signed original Windows Yandex ASAR
 * in a disposable Windows runner. Does not modify ASAR, account, or player.
 * Read bounded source excerpts only for explicit API/decoder tokens.
 * NEVER upload original ASAR, installable Yandex binaries, or arbitrary data.
 */
import fs from "node:fs";
import crypto from "node:crypto";

const file = process.argv[2];
if (!file) throw Error("W49_INPUT_MISSING");
const bytes=fs.readFileSync(file);
const sha=crypto.createHash("sha256").update(bytes).digest("hex");
if (sha!=="5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215")
  throw Error("W49_OFFICIAL_ASAR_SHA_UNEXPECTED");
if(bytes.readUInt32LE(0)!==4) throw Error("W49_ASAR_BAD_HEADER");
const jsonLen=bytes.readUInt32LE(12);
const dataStart=16+((jsonLen+3)&~3);
const tree=JSON.parse(bytes.subarray(16,16+jsonLen).toString("utf8"));
if (!tree.files || dataStart>=bytes.length) throw Error("W49_ASAR_NO_FILES");

let found=0, scripts=0;
const targets=[
  ["API_FILEINFO","get-file-info"],
  ["API_FILEINFO_V2","resources/v2/file-info"],
  ["FN_GET_FILEINFO","getFileInfo("],
  ["FN_GET_FILEINFO_BATCH","getFileInfoBatch("],
  ["CODEC_AAC_MP4","aac-mp4"],
  ["CODEC_AUDIO_MP4","audio/mp4"],
  ["CODEC_AUDIO_MPEG","audio/mpeg"],
  ["TRANSPORT_RAW","transport:\"raw\""],
  ["DECRYPT","decrypt"],
  ["ENC_RAW","encraw"],
  ["ENUM_ENC_RAW","ENCRAW"],
  ["TRANSPORT_PROPERTY",".transport"],
  ["MEDIA_SOURCE_FACTORY","createMediaSource("],
  ["GET_MEDIA_SOURCE","getMediaSource("],
  ["MEDIA_ERROR_CODE","E_GET_MEDIA_SRC"],
  ["ERROR_PLAYER","playerErrorsRaised"],
  ["WEB_AUDIO","AudioContext"],
  ["HTML_MEDIA_SOURCE","MediaSource"],
];
const totals=Object.fromEntries(targets.map(([name])=>[name,0]));
let shown=0;
function preview(s) {
  return s.replace(/[\u0000-\u001f\u007f-\u009f]+/g," ")
    .replace(/https?:\/\/[^\s'"<>]+/gi,"[URL]")
    .replace(/\b[a-f0-9]{40,}\b/gi,"[HASH]")
    .replace(/\s+/g," ").slice(0,300);
}
function walk(entries,prefix="") {
  for(const [name,node] of Object.entries(entries)) {
    const path=prefix?prefix+"/"+name:name;
    if(node.files){walk(node.files,path);continue;}
    if(node.unpacked||!/\.(?:js|mjs|cjs|html)$/.test(path)) continue;
    if(!path.startsWith("app/_next/static/chunks/"))continue;
    if(!Number.isSafeInteger(node.size)||!/^\d+$/.test(node.offset))continue;
    scripts++;
    const offset=dataStart+Number(node.offset);
    if(node.size<=0||offset+node.size>bytes.length)continue;
    const src=bytes.subarray(offset,offset+node.size).toString("utf8");
    let matched=false;
    for(const [label,needle] of targets) {
      const index=src.indexOf(needle);
      if(index<0)continue;
      totals[label]++;
      matched=true;
      if(shown>=65)continue;
      // Small semantic context only, never copy any full proprietary bundle.
      const context=preview(src.slice(Math.max(0,index-130),Math.min(src.length,index+needle.length+170)));
      console.log("W49_STATIC_CONTEXT "+JSON.stringify({label,file:path.slice(0,190),bytes:node.size,context}));
      shown++;
    }
    if(matched) found++;
  }
}
walk(tree.files);
console.log("W49_SIGNED_ORIGINAL_STATIC_SUMMARY "+JSON.stringify({shaVerified:true,scripts,matches:found,totals}));
console.log("W49_ONLY_READ_ORIGINAL_ASAR_NO_ACCOUNT_NO_PLAYER");

/**
 * W52: READ-ONLY bounded source-flow check of the exact vendor-signed Yandex ASAR.
 * No account, binary patch, private URL or network call. Outputs positions and
 * tiny sanitized contexts, never vendor bundles or raw media grants.
 */
import fs from "node:fs";
import crypto from "node:crypto";
import {inspectAsar} from "../w23/asar-images.mjs";
const file=process.argv[2]; if(!file)throw Error("W52_MISSING_VENDOR_INPUT");
const bytes=fs.readFileSync(file);
const hash=crypto.createHash("sha256").update(bytes).digest("hex");
if(hash!=="5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215")
  throw Error("W52_VENDOR_NOT_PINNED");
const paths=[
  "app/_next/static/chunks/app/(product)/layout-4afaa928fcc37741.js",
  "app/_next/static/chunks/9091-cdf5e7f5a0e6a5b5.js"
];
const needles=[
  "new tL({data:t","class tL","tL=class","tL=void","tL=",
  "downloadInfoSource","getMediaSource(", "corePlay(", "createMediaSource(",
  ".urls[0]","split(\"?\")","new URL(","URLSearchParams","searchParams"
];
function compact(s){return s.replace(/https?:\/\/[^\s'"<>]+/g,"[URL]")
  .replace(/\b[a-f0-9]{40,}\b/gi,"[HASH]")
  .replace(/[\u0000-\u001f\u007f-\u009f]+/g," ")
  .replace(/\s+/g," ").slice(0,700);}
let result={};
for(const name of paths){
  const s=inspectAsar(bytes,name).toString("utf8");
  if(name.includes("layout-")){
    // W55: an MP3 source can still receive VSID/sourceIndex later, even if
    // not passed to the original constructor. Inspect all actual writers.
    const setters=[".vsid=",".sourceIndex=",".vsid =",".sourceIndex =",
      "sourceIndex:","vsid:","getQueryParamsString()"];
    for(const needle of setters){
      const positions=[];let pos=-1;
      while((pos=s.indexOf(needle,pos+1))>=0&&positions.length<50)
        positions.push(pos);
      const points=positions.slice(0,8).map(at=>({
        pos:at,
        context:compact(s.slice(Math.max(0,at-175),Math.min(s.length,at+needle.length+220)))
      }));
      console.log("W55_VENDOR_SOURCE_FIELD_WRITERS "+JSON.stringify({
        needle,count:positions.length,points
      }));
    }
    const at=s.indexOf("class tL{");
    if(at<0)throw Error("W52_VENDOR_DOWNLOAD_INFO_SOURCE_MISSING");
    const full=s.slice(at,at+2450);
    const safe=full.replace(/https?:\/\/[^\s'"<>]+/g,"[URL]")
      .replace(/\b[a-f0-9]{40,}\b/gi,"[HASH]")
      .replace(/[\u0000-\u001f\u007f-\u009f]+/g," ")
      .replace(/\s+/g," ").slice(0,2400);
    console.log("W52_VENDOR_SOURCE_BUILDER "+JSON.stringify({pos:at,context:safe}));
  }
  const found={};
  for(const needle of needles){
    let at=-1,count=0,examples=[];
    while((at=s.indexOf(needle,at+1))>=0){
      count++;
      if(examples.length<2){
        const from=Math.max(0,at-240),to=Math.min(s.length,at+needle.length+360);
        examples.push({pos:at,context:compact(s.slice(from,to))});
      }
      if(count>=3000)break;
    }
    found[needle]=count;
    if(examples.length&&
       ["new tL({data:t","class tL","tL=class","tL=void","tL=",
        "downloadInfoSource",".urls[0]","split(\"?\")","searchParams"].includes(needle))
       console.log("W52_VENDOR_URL_FLOW "+JSON.stringify({chunk:name.split("/").at(-1),needle,examples}));
  }
  result[name.split("/").at(-1)]={bytes:s.length,found};
}
console.log("W52_VENDOR_URL_FLOW_SUMMARY "+JSON.stringify(result));
console.log("W52_STATIC_ORIGINAL_READONLY_PASS");

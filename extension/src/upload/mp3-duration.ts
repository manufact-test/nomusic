import { stripMp3MetadataTail } from "./mp3-metadata.js";
/* Bounded lossless MP3 normalization. Never searches past broken audio. */
export function inspectMp3(buffer) {
  const data = new Uint8Array(buffer), size = data.length;
  if (size < 1024 || size > 31457280) return null;
  const view = new DataView(data.buffer, data.byteOffset, size);
  const marker = (p, text) => p >= 0 && p + text.length <= size && [...text].every((c,i)=>data[p+i]===c.charCodeAt(0));
  let position=0, tags=0, metadataBytes=0;
  const skipTags=()=>{
    while(marker(position,"ID3")) {
      if(position+10>size || ++tags>4)return false;
      const version=data[position+3], flags=data[position+5];
      if(![2,3,4].includes(version)||data[position+4]===255||
          (flags&(version===2?0x3f:version===3?0x1f:0x0f))||data.subarray(position+6,position+10).some(x=>x&128))return false;
      const length=10+(data[position+6]<<21)+(data[position+7]<<14)+(data[position+8]<<7)+data[position+9]+(version===4&&(flags&16)?10:0);
      if(position+length>size|| (metadataBytes+=length)>8388608)return false;
      if(version===4&&(flags&16)&&!marker(position+length-10,"3DI"))return false;
      position+=length;
    }
    return true;
  };
  // A few downloaders omit the last padding-slot byte. Accept only a single
  // missing byte in an unprotected MPEG-1 padded final frame whose side info
  // proves all coded audio bits are already present. Never invent audio bits.
  const ancillaryByteMissing=(p,h,bytes)=>{
    if(p+bytes!==size+1 || ((h>>>19)&3)!==3 || !((h>>>16)&1) || !((h>>>9)&1))return false;
    const channels=((h>>>6)&3)===3?1:2, side=channels===1?17:32;
    if(p+4+side>size)return false;
    let bit=0;
    const read=n=>{let value=0;for(let i=0;i<n;i++,bit++)value=(value<<1)|((data[p+4+(bit>>>3)]>>>(7-(bit&7)))&1);return value;};
    const back=read(9);bit+=(channels===1?5:3)+channels*4;
    let codedBits=0;
    for(let i=0;i<channels*2;i++){codedBits+=read(12);bit+=47;}
    return codedBits>0 && codedBits <= (back+size-p-4-side)*8;
  };
  let repairedAncillaryByte=false;
  const frameAt=(p,allowFinalRepair=false)=>{
    if(p+4>size)return null;
    const h=view.getUint32(p), version=(h>>>19)&3, index=(h>>>12)&15, rateIndex=(h>>>10)&3;
    if(h>>>21!==2047||version===1||((h>>>17)&3)!==1||index<1||index>14||rateIndex===3)return null;
    const rate=[44100,48000,32000][rateIndex]/(version===3?1:version===2?2:4);
    const bitrate=(version===3?[0,32,40,48,56,64,80,96,112,128,160,192,224,256,320]:[0,8,16,24,32,40,48,56,64,80,96,112,128,144])[index];
    const bytes=Math.floor((version===3?144:72)*bitrate*1000/rate)+((h>>>9)&1);
    if(bytes<24||bytes>1441)return null;
    const repair=p+bytes>size;
    if(repair&&(!allowFinalRepair||!ancillaryByteMissing(p,h,bytes)))return null;
    const crc=(h>>>16)&1?0:2, mono=((h>>>6)&3)===3;
    const side=version===3?(mono?17:32):(mono?9:17), info=p+4+crc+side;
    const metadata=(marker(info,"Info")||marker(info,"Xing"))&&info+8<=p+bytes&&
      data.subarray(p+4+crc,info).every(x=>x===0);
    return {bytes:repair?bytes-1:bytes,repair,rate,version,samples:version===3?1152:576,metadata};
  };
  if(!skipTags())return null;
  let firstInfo=null, headerCount=0, signature=null;
  while(true){
    const f=frameAt(position);
    if(!f||!f.metadata)break;
    if(++headerCount>4)return null;
    if(signature&&(signature.rate!==f.rate||signature.version!==f.version))return null;
    signature=f;
    if(firstInfo===null)firstInfo=data.subarray(position,position+f.bytes);
    position+=f.bytes;
    if(!skipTags())return null;
  }
  const start=position;
  let frames=0, samples=firstInfo?signature.samples:0, rate=signature?.rate||0, version=signature?.version;
  while(position+4<=size){
    const f=frameAt(position,frames>=2);if(!f)break;
    if(f.metadata||(rate&&(rate!==f.rate||version!==f.version)))return null;
    rate=f.rate;version=f.version;position+=f.bytes;samples+=f.samples;
    repairedAncillaryByte ||= f.repair;
    if(++frames>500000||samples/rate>86400)return null;
  }
  const audioEnd=position;
  const tail=stripMp3MetadataTail(data,audioEnd);
  if(!tail)return null;
  position=tail.position;let end=tail.end;
  // Some tagged downloads leave an orphaned XMP property/closing-tag tail
  // after complete MPEG frames and zero padding. Match the ENTIRE bounded
  // ASCII fragment, not arbitrary bytes containing an XML-looking substring.
  // No XML is parsed/executed, and no search past a damaged audio frame occurs.
  let removedXmpTail=false;
  if(end-position<=4096 && end>position){
    let textAt=position;while(textAt<end&&data[textAt]===0)textAt++;
    if(textAt-position>=32 && textAt<end){
      const tail=data.subarray(textAt,end);
      if(tail.every(x=>x===9||x===10||x===13||(x>=32&&x<=126))){
        let text=new TextDecoder("utf-8",{fatal:true}).decode(tail).trim().replace(/[ \t\r\n]+/g," ");
        for(const closing of ['<?xpacket end="r"?>','<?xpacket end="w"?>']){
          if(text.endsWith(closing))text=text.slice(0,-closing.length).trim();
        }
        const closing=/<\/rdf:Description> ?<\/rdf:RDF> ?<\/x:xmpmeta>$/;
        const suffix=closing.exec(text);
        if(suffix){
          const head=text.slice(0,suffix.index).trim();
          const properties=head.replace(/\/?>$/,"").trim().split(" ");
          const id='(?:xmp\\.did:)?[A-Fa-f0-9-]{8,64}';
          const property=new RegExp('^stRef:(?:instanceID|documentID|originalDocumentID)="'+id+'"$');
          const fragment=new RegExp('^'+id+'"$');
          if(/\/?>$/.test(head)&&properties.length<=4
              &&(fragment.test(properties[0])||property.test(properties[0]))
              &&properties.slice(1).every(value=>property.test(value))
              &&properties.some(value=>property.test(value))){removedXmpTail=true;position=end;}
        }
      }
    }
  }
  if(end<position||end-position>4096||!data.subarray(position,end).every(x=>x===0)||frames<2||!rate)return null;
  const durationMs=Math.round(1000*samples/rate);
  if(durationMs<1000||durationMs>86400000)return null;
  const bytes=new Uint8Array((firstInfo?.length||0)+audioEnd-start+(repairedAncillaryByte?1:0));
  if(firstInfo)bytes.set(firstInfo);bytes.set(data.subarray(start,audioEnd),firstInfo?.length||0);
  return {durationMs,bytes,changed:bytes.length!==size||repairedAncillaryByte,repairedAncillaryByte,removedXmpTail,metadataKinds:tail.kinds};
}
export function mp3DurationMs(buffer): number | null { return inspectMp3(buffer)?.durationMs??null; }

export function durationNotice(originalMs, audioMs) {
  if (!Number.isFinite(originalMs) || !Number.isFinite(audioMs)) return { blocked: true, kind: "error", text: "Не удалось прочитать аудиофайл и проверить его длительность. Проверьте, что это настоящий MP3 или M4A (AAC), либо выберите другой файл. Непроверенный файл не отправляется." };
  const delta = audioMs - originalMs, difference = Math.abs(delta);
  const time = ms => { const seconds=Math.floor(ms/1000);return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`; };
  const description = `Оригинал: ${time(originalMs)} · файл: ${time(audioMs)}.`;
  if (difference <= 1500) return { kind: "ok", text: description + " Длительность подходит для подмены." };
  const mismatch = ` Файл ${delta > 0 ? "длиннее" : "короче"} на ${Math.round(difference / 1000)} с.`;
  return { blocked: true, kind: "error", text: description + mismatch + (difference > 5000 ? " Разница больше 5 секунд: выберите подходящую версию." : "") + " Допуск подмены — 1,5 с; с этим файлом подмена не запустится. Выберите файл подходящей длительности." };
}

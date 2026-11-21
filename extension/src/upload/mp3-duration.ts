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
  const frameAt=p=>{
    if(p+4>size)return null;
    const h=view.getUint32(p), version=(h>>>19)&3, index=(h>>>12)&15, rateIndex=(h>>>10)&3;
    if(h>>>21!==2047||version===1||((h>>>17)&3)!==1||index<1||index>14||rateIndex===3)return null;
    const rate=[44100,48000,32000][rateIndex]/(version===3?1:version===2?2:4);
    const bitrate=(version===3?[0,32,40,48,56,64,80,96,112,128,160,192,224,256,320]:[0,8,16,24,32,40,48,56,64,80,96,112,128,144])[index];
    const bytes=Math.floor((version===3?144:72)*bitrate*1000/rate)+((h>>>9)&1);
    if(bytes<24||bytes>1441||p+bytes>size)return null;
    const crc=(h>>>16)&1?0:2, mono=((h>>>6)&3)===3;
    const side=version===3?(mono?17:32):(mono?9:17), info=p+4+crc+side;
    const metadata=(marker(info,"Info")||marker(info,"Xing"))&&info+8<=p+bytes&&
      data.subarray(p+4+crc,info).every(x=>x===0);
    return {bytes,rate,version,samples:version===3?1152:576,metadata};
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
    const f=frameAt(position);if(!f)break;
    if(f.metadata||(rate&&(rate!==f.rate||version!==f.version)))return null;
    rate=f.rate;version=f.version;position+=f.bytes;samples+=f.samples;
    if(++frames>500000||samples/rate>86400)return null;
  }
  const audioEnd=position;
  let end=size;
  if(end-position>=128&&marker(end-128,"TAG"))end-=128;
  if(end-position>=32&&marker(end-32,"APETAGEX")){
    const at=end-32, av=view.getUint32(at+8,true), bytes=view.getUint32(at+12,true);
    if(av!==2000||bytes<32||bytes>1048576||view.getUint32(at+16,true)>128||bytes>end-position)return null;
    end-=bytes;
    if(end-position>=32&&marker(end-32,"APETAGEX")){
      if(view.getUint32(end-24,true)!==av||view.getUint32(end-20,true)!==bytes)return null;
      end-=32;
    }
  }
  if(end-position>=128&&marker(end-128,"TAG"))end-=128;
  if(end-position>=128&&marker(position,"TAG")){
    const length=end-position;
    if(length===128||data.subarray(position+128,end).every(x=>x===0))position=end;
    else {
      /* Some downloaders count UTF-8 characters instead of ID3v1 bytes. */
      if(length>512)return null;
      let text;try{text=new TextDecoder("utf-8",{fatal:true}).decode(data.subarray(position+3,end-1));}catch{return null;}
      if([...text].length!==124||/[\x01-\x1f\x7f]/u.test(text))return null;
      position=end;
    }
  }
  if(end<position||end-position>4096||!data.subarray(position,end).every(x=>x===0)||frames<2||!rate)return null;
  const durationMs=Math.round(1000*samples/rate);
  if(durationMs<1000||durationMs>86400000)return null;
  const bytes=new Uint8Array((firstInfo?.length||0)+audioEnd-start);
  if(firstInfo)bytes.set(firstInfo);bytes.set(data.subarray(start,audioEnd),firstInfo?.length||0);
  return {durationMs,bytes,changed:bytes.length!==size};
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

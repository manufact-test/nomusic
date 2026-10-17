// Bounded M4A metadata preflight. The server independently verifies sample tables.
export function inspectM4a(buffer) {
  const v=new DataView(buffer),size=v.byteLength;
  if(size<1024||size>31457280)throw Error("invalid_m4a");
  let count=0;
  const text=(p,n)=>String.fromCharCode(...new Uint8Array(buffer,p,n));
  function boxes(start,end){
    const result=[];
    for(let p=start;p<end;){
      if(++count>8192||end-p<8)throw Error("invalid_m4a");
      let n=v.getUint32(p),head=8;const type=text(p+4,4);
      if(n===1){if(end-p<16||v.getUint32(p+8)!==0)throw Error("invalid_m4a");n=v.getUint32(p+12);head=16;}
      if(n===0)n=end-p;
      if(n<head||n>end-p)throw Error("invalid_m4a");
      result.push({type,start:p+head,end:p+n});p+=n;
    }
    return result;
  }
  const one=(list,type)=>{const found=list.filter(b=>b.type===type);if(found.length!==1)throw Error("invalid_m4a");return found[0];};
  const children=b=>boxes(b.start,b.end);
  const top=boxes(0,size);if(top[0]?.type!=="ftyp"||top.some(b=>b.type==='moof'))throw Error("invalid_m4a");
  const moov=one(top,'moov'),mdat=one(top,'mdat');if(mdat.end-mdat.start<512)throw Error("invalid_m4a");
  const tracks=children(moov).filter(b=>b.type==='trak');if(tracks.length!==1)throw Error("unsupported_m4a");
  const mdia=one(children(tracks[0]),'mdia'),mdiaBoxes=children(mdia),hdlr=one(mdiaBoxes,'hdlr'),mdhd=one(mdiaBoxes,'mdhd');
  if(hdlr.end-hdlr.start<12||text(hdlr.start+8,4)!=='soun')throw Error("unsupported_m4a");
  const version=v.getUint8(mdhd.start);let rate,duration;
  if(version===0&&mdhd.end-mdhd.start>=24){rate=v.getUint32(mdhd.start+12);duration=v.getUint32(mdhd.start+16);}
  else if(version===1&&mdhd.end-mdhd.start>=36&&v.getUint32(mdhd.start+24)===0){rate=v.getUint32(mdhd.start+20);duration=v.getUint32(mdhd.start+28);}
  else throw Error("invalid_m4a");
  if(!rate||!duration)throw Error("invalid_m4a");
  const seconds=duration/rate;
  if(seconds<1||seconds>86400)throw Error("m4a_duration_limit");
  const stbl=one(children(one(mdiaBoxes,'minf')),'stbl'),tables=children(stbl),stsd=one(tables,'stsd'),stsz=one(tables,'stsz'),stts=one(tables,'stts');
  if(stsd.end-stsd.start<8||v.getUint32(stsd.start+4)!==1)throw Error("unsupported_m4a");
  const entry=one(boxes(stsd.start+8,stsd.end),'mp4a');
  if(entry.end-entry.start<28||v.getUint16(entry.start+8)!==0)throw Error("unsupported_m4a");
  const channels=v.getUint16(entry.start+16),sampleRate=v.getUint32(entry.start+24)>>>16;
  if(channels<1||channels>2||sampleRate<8000||sampleRate>48000)throw Error("unsupported_m4a");
  const extras=boxes(entry.start+28,entry.end);if(extras.some(b=>['sinf','schm'].includes(b.type))||!extras.some(b=>b.type==='esds'))throw Error("unsupported_m4a");
  if(stsz.end-stsz.start<12||stts.end-stts.start<8)throw Error("invalid_m4a");
  const samples=v.getUint32(stsz.start+8),entries=v.getUint32(stts.start+4);
  if(!samples||samples>500000||entries>samples||stts.end-stts.start!==8+entries*8)throw Error("invalid_m4a");
  let sampleCount=0,totalTime=0;
  for(let i=0;i<entries;i++){const n=v.getUint32(stts.start+8+i*8),delta=v.getUint32(stts.start+12+i*8);if(!n||!delta)throw Error("invalid_m4a");sampleCount+=n;totalTime+=n*delta;}
  if(sampleCount!==samples||Math.abs(totalTime-duration)>rate/10)throw Error("invalid_m4a");
  return {durationMs:Math.round(seconds*1000),channels,sampleRate};
}

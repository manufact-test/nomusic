// Standard metadata only, outside the already validated MPEG frame interval.
// No filename rules, XML execution, frame resynchronization or decoder bypass.
export function stripMp3MetadataTail(data, audioEnd) {
  const size=data.length, view=new DataView(data.buffer,data.byteOffset,size);
  const marker=(p,s)=>p>=audioEnd&&p+s.length<=size&&[...s].every((c,i)=>data[p+i]===c.charCodeAt(0));
  const digits=(p,n)=>{if(p<audioEnd||p+n>size)return null;let value=0;for(let i=0;i<n;i++){const c=data[p+i];if(c<48||c>57)return null;value=value*10+c-48;}return value;};
  let position=audioEnd,end=size,padding=0,metadataBytes=0;const kinds=[];
  const consume=(next,kind)=>{metadataBytes+=end-next;if(next<position||metadataBytes>8388608||kinds.length>=16)return false;end=next;kinds.push(kind);return true;};
  while(end>position){
    if(end-position>=128&&marker(end-128,'TAG')){if(!consume(end-128,'id3v1'))return null;continue;}
    if(end-position>=227&&marker(end-227,'TAG+')){if(!consume(end-227,'id3v1-enhanced'))return null;continue;}
    if(end-position>=32&&marker(end-32,'APETAGEX')){
      const at=end-32,v=view.getUint32(at+8,true),bytes=view.getUint32(at+12,true),items=view.getUint32(at+16,true);
      if(![1000,2000].includes(v)||bytes<32||bytes>1048576||items>128||bytes>end-position)return null;
      let start=end-bytes;
      if(start-position>=32&&marker(start-32,'APETAGEX')){
        if(v!==2000||view.getUint32(start-24,true)!==v||view.getUint32(start-20,true)!==bytes)return null;
        start-=32;
      }
      if(!consume(start,v===1000?'apev1':'apev2'))return null;continue;
    }
    if(end-position>=15&&marker(end-9,'LYRICS200')){
      const bytes=digits(end-15,6),start=bytes===null?-1:end-15-bytes;
      if(bytes===null||bytes<19||start<position||!marker(start,'LYRICSBEGIN'))return null;
      let cursor=start+11,fields=0;
      while(cursor<end-15){
        if(cursor+8>end-15||![0,1,2].every(i=>data[cursor+i]>=65&&data[cursor+i]<=90))return null;
        const length=digits(cursor+3,5);if(length===null||cursor+8+length>end-15||++fields>128)return null;
        cursor+=8+length;
      }
      if(cursor!==end-15||fields===0||!consume(start,'lyrics3v2'))return null;continue;
    }
    if(end-position>=20&&marker(end-9,'LYRICSEND')){
      let start=-1;
      for(let p=Math.max(position,end-5120);p<=end-20;p++){
        if(marker(p,'LYRICSBEGIN')&&!data.subarray(p+11,end-9).some(c=>c===0||c===255||(c<32&&![9,10,13].includes(c)))){start=p;break;}
      }
      if(start<0)return null;
      if(!consume(start,'lyrics3v1'))return null;continue;
    }
    // Retain compatibility with known UTF-8-inflated ID3v1 writers.
    if(marker(position,'TAG')&&end-position>=128&&end-position<=512){
      const length=end-position;
      let valid=length===128||data.subarray(position+128,end).every(c=>c===0);
      if(!valid){try{const text=new TextDecoder('utf-8',{fatal:true}).decode(data.subarray(position+3,end-1));valid=[...text].length===124&&!/[\x01-\x1f\x7f]/u.test(text);}catch{}}
      if(valid){if(!consume(position,'id3v1-legacy'))return null;continue;}
    }
    // Tail ID3v2 uses the same bounded header rules as a leading tag.
    if(marker(position,'ID3')&&position+10<=end){
      const version=data[position+3],flags=data[position+5],reserved=version===2?0x3f:version===3?0x1f:0x0f;
      if(![2,3,4].includes(version)||data[position+4]===255||(flags&reserved)||data.subarray(position+6,position+10).some(c=>c&128))return null;
      const length=10+(data[position+6]<<21)+(data[position+7]<<14)+(data[position+8]<<7)+data[position+9]+(version===4&&(flags&16)?10:0);
      if(position+length>end||length>8388608||(version===4&&(flags&16)&&!marker(position+length-10,'3DI')))return null;
      metadataBytes+=length;if(metadataBytes>8388608||kinds.length>=16)return null;
      position+=length;kinds.push('id3v2-tail');continue;
    }
    // Check every endpoint before dropping zero padding, so a genre/reserved
    // zero inside ID3/APE is never mistaken for padding after that tag.
    if(data[end-1]===0){if(++padding>4096)return null;end--;continue;}
    break;
  }
  return {position,end,kinds,padding};
}

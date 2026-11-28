import test from 'node:test';
import assert from 'node:assert/strict';
import {mp3DurationMs,durationNotice,inspectMp3} from '../dist/unpacked/upload/mp3-duration.js';
function mp3(version=3,count=60,vbr=false){
 const frames=[];const rate=version===3?44100:version===2?22050:11025;
 for(let i=0;i<count;i++){
  const index=vbr&&i%2?8:9,bitrate=(version===3?[0,32,40,48,56,64,80,96,112,128]:[0,8,16,24,32,40,48,56,64,80])[index];
  const frame=new Uint8Array(Math.floor((version===3?144:72)*bitrate*1000/rate));
  new DataView(frame.buffer).setUint32(0,(0xffe00000|(version<<19)|(1<<17)|(1<<16)|(index<<12))>>>0);frames.push(frame);
 }
 const data=new Uint8Array(frames.reduce((n,f)=>n+f.length,0));let offset=0;for(const f of frames){data.set(f,offset);offset+=f.length;}return data;
}
test('MP3 frame duration supports variable bitrate and all supported MPEG versions',()=>{
 for(const version of [3,2,0])for(const vbr of [false,true]){
  const rate=version===3?44100:version===2?22050:11025;
  assert.equal(mp3DurationMs(mp3(version,60,vbr)),Math.round(60000*(version===3?1152:576)/rate));
 }
});
test('MP3 duration accepts ID3 tags and silence padding, rejects truncation and wrong audio',()=>{
 const data=mp3();const tagged=new Uint8Array(data.length+10+128+100);tagged.set([73,68,51,4,0,0,0,0,0,0]);tagged.set(data,10);tagged.set([84,65,71],data.length+10);
 assert.equal(mp3DurationMs(tagged),mp3DurationMs(data));
 assert.equal(mp3DurationMs(data.slice(0,-20)),null);
 assert.equal(mp3DurationMs(new Uint8Array(2000)),null);
 tagged[tagged.length-1]=1;assert.equal(mp3DurationMs(tagged),null);
});
test('duration warnings honor 1500 ms compatibility and greater-than-five-second threshold in both directions',()=>{
 for(const sign of [-1,1]){
  assert.equal(durationNotice(180000,180000+sign*1500).kind,'ok');
  assert.match(durationNotice(180000,180000+sign*1501).text,/подмена не запустится/);
  assert.doesNotMatch(durationNotice(180000,180000+sign*5000).text,/Разница больше 5/);
  assert.match(durationNotice(180000,180000+sign*5001).text,/Разница больше 5/);
  assert.equal(durationNotice(180000,180000+sign*5001).blocked,true);
  assert.equal(durationNotice(180000,180000+sign*1501).blocked,true);
  assert.equal(durationNotice(180000,180000+sign*5000).blocked,true);
  assert.doesNotMatch(durationNotice(183720,180872).text,/3:03,|3:00,|2,848/);
  assert.match(durationNotice(183720,180872).text,/3:03.*3:00.*на 3 с/);
  assert.doesNotMatch(durationNotice(180000,180000+sign*5001).text,/Перед публикацией/);
 }
 assert.doesNotMatch(durationNotice(180000,null).text,/подходит/);
});

function withApeTail(data, invalid=false) {
  const item = new Uint8Array([4,0,0,0, 0,0,0,0, 84,105,116,108,101,0, 84,101,115,116]);
  const footer = new Uint8Array(32);
  footer.set(new TextEncoder().encode("APETAGEX"),0);
  const view = new DataView(footer.buffer);
  view.setUint32(8,invalid?1234:2000,true);
  view.setUint32(12,32+item.length,true);
  view.setUint32(16,1,true);
  const tagged = new Uint8Array(data.length+item.length+footer.length);
  tagged.set(data);tagged.set(item,data.length);tagged.set(footer,data.length+item.length);
  return tagged;
}
test('real-world bounded APEv2 metadata is accepted but malformed trailers remain blocked',()=>{
 const original=mp3(3,100,true);
 assert.equal(mp3DurationMs(withApeTail(original)),mp3DurationMs(original));
 assert.equal(mp3DurationMs(withApeTail(original,true)),null);
 const evil=new Uint8Array(original.length+32);evil.set(original);
 evil.set(new TextEncoder().encode("APETAGEX"),original.length);
 assert.equal(mp3DurationMs(evil),null);
});
test('unreadable duration is a blocking, user-readable preflight, never server-guess warning',()=>{
 const issue=durationNotice(277900,null);
 assert.equal(issue.blocked,true);
 assert.equal(issue.kind,'error');
 assert.match(issue.text,/Не удалось прочитать аудиофайл/);
 assert.doesNotMatch(issue.text,/Файл дополнительно проверит сервер/);
});


function id3v24(body) {
  const tag = new Uint8Array(10 + body.length);
  tag.set([73,68,51,4,0,0,(body.length>>>21)&127,(body.length>>>14)&127,
    (body.length>>>7)&127,body.length&127]);
  tag.set(body,10);
  return tag;
}
function concatenate(...chunks) {
  const all=new Uint8Array(chunks.reduce((length,chunk)=>length+chunk.length,0));
  let p=0; for(const chunk of chunks){all.set(chunk,p);p+=chunk.length;}return all;
}
test("double ID3v2.4 headers before MPEG frames remain a valid MP3",()=>{
  const audio=mp3(3,100,true);
  const first=id3v24(new Uint8Array(35).fill(0x41));
  const second=id3v24(new Uint8Array(34).fill(0x42));
  const tagged=concatenate(first,second,audio);
  assert.equal(mp3DurationMs(tagged),mp3DurationMs(audio));
  assert.equal(durationNotice(277900,277969).kind,"ok");
});
test("malformed or excessive consecutive ID3 headers cannot bypass frame validation",()=>{
  const audio=mp3(3,100);
  const first=id3v24(new Uint8Array(35));
  const second=id3v24(new Uint8Array(34));
  const malformed=concatenate(first,second,audio);
  malformed[first.length+6]=0xff; // synchsafe sizes cannot set high bits
  assert.equal(mp3DurationMs(malformed),null);
  const truncated=concatenate(first,second.slice(0,7),audio);
  assert.equal(mp3DurationMs(truncated),null);
  const excessive=concatenate(...Array.from({length:5},()=>first),audio);
  assert.equal(mp3DurationMs(excessive),null);
  const fake=concatenate(first,second,new Uint8Array(2000).fill(0x40));
  assert.equal(mp3DurationMs(fake),null);
});

function infoFrame(){const f=mp3(3,1);f.set(new TextEncoder().encode('Info'),36);return f;}
test('lossless cleanup preserves first Info header and every audio frame, removes interleaved duplicate metadata',()=>{
 const audio=mp3(3,100,true),info=infoFrame(),tag=id3v24(new Uint8Array(30));
 const original=concatenate(tag,info,tag,info,audio,new TextEncoder().encode('TAG'),new Uint8Array(125));
 const result=inspectMp3(original);
 assert.deepEqual(result.bytes,concatenate(info,audio));
 assert.deepEqual(inspectMp3(result.bytes).bytes,result.bytes);
 assert.equal(result.durationMs,mp3DurationMs(concatenate(info,audio)));
 assert.equal(inspectMp3(concatenate(info,audio.subarray(0,417),tag,audio)),null);
 assert.equal(inspectMp3(concatenate(info,audio,info)),null);
});
test('UTF-8 inflated ID3v1 trailer is bounded by character count, arbitrary suffixes stay rejected',()=>{
 const audio=mp3(3,100),body='Ж'.repeat(27)+'x'.repeat(97);
 const tail=concatenate(new TextEncoder().encode('TAG'+body),new Uint8Array([7]));
 assert.equal(tail.length,155);
 assert.deepEqual(inspectMp3(concatenate(audio,tail)).bytes,audio);
 assert.equal(inspectMp3(concatenate(audio,tail,new Uint8Array([1]))),null);
});

function finalPaddedFrame(lengths=[1024,0,0,0]) {
 const frame=new Uint8Array(1045).fill(0xaa);frame.fill(0,0,36);
 frame.set([0xff,0xfb,0xe2,0x64]);
 const put=(offset,count,value)=>{for(let i=0;i<count;i++){const bit=offset+i,at=4+(bit>>>3);frame[at]|=((value>>>(count-1-i))&1)<<(7-(bit&7));}};
 for(let i=0;i<4;i++)put(20+i*59,12,lengths[i]);
 return frame;
}
test('one missing final ancillary byte is reconstructed without removing any existing audio byte',()=>{
 const audio=mp3(),last=finalPaddedFrame(),original=concatenate(audio,last.subarray(0,-1));
 const result=inspectMp3(original);
 assert.equal(result.repairedAncillaryByte,true);assert.equal(result.bytes.length,original.length+1);
 assert.deepEqual(result.bytes.subarray(0,-1),original);assert.equal(result.bytes.at(-1),0);
 assert.equal(result.durationMs,mp3DurationMs(concatenate(audio,last)));
 assert.equal(inspectMp3(result.bytes).changed,false);
});
test('EOF repair rejects missing coded bits, longer truncation, unpadded frames and protected CRC frames',()=>{
 const audio=mp3();
 assert.equal(inspectMp3(concatenate(audio,finalPaddedFrame([3000,3000,2072,0]).subarray(0,-1))),null);
 assert.equal(inspectMp3(concatenate(audio,finalPaddedFrame().subarray(0,-2))),null);
 const unpadded=finalPaddedFrame();unpadded[2]&=0xfd;
 assert.equal(inspectMp3(concatenate(audio,unpadded.subarray(0,-2))),null);
 const protectedFrame=finalPaddedFrame();protectedFrame[1]&=0xfe;
 assert.equal(inspectMp3(concatenate(audio,protectedFrame.subarray(0,-1))),null);
 assert.equal(inspectMp3(concatenate(finalPaddedFrame().subarray(0,-1))),null);
});
test('ancillary repair cannot skip internal damage or change MPEG format',()=>{
 const audio=mp3(),last=finalPaddedFrame();
 assert.equal(inspectMp3(concatenate(audio,new Uint8Array([1]),last.subarray(0,-1))),null);
 last[2]|=4;
 assert.equal(inspectMp3(concatenate(audio,last.subarray(0,-1))),null);
});

const xmpOrphan='ABCDEF0123456"\n stRef:documentID="xmp.did:0123456789ABCDEF0123456789ABCDEF01"\n stRef:originalDocumentID="xmp.did:0123456789ABCDEF0123456789ABCDEF01"/>\n </rdf:Description>\n </rdf:RDF>\n</x:xmpmeta>\n';
test('orphaned XMP property tail after zero padding is removed without changing any MPEG frame',()=>{
 const audio=mp3(),tag=id3v24(new Uint8Array(300)),id3v1=concatenate(new TextEncoder().encode('TAG'),new Uint8Array(125));
 const source=concatenate(tag,audio,new Uint8Array(1804),new TextEncoder().encode(xmpOrphan+' '.repeat(1100)),id3v1);
 const clean=inspectMp3(source);assert.equal(clean.removedXmpTail,true);assert.deepEqual(clean.bytes,audio);
 assert.equal(clean.durationMs,mp3DurationMs(audio));assert.equal(inspectMp3(clean.bytes).changed,false);
});
test('XMP cleanup rejects arbitrary trailers, broken frame headers, binary/control data and over-limit tails',()=>{
 const audio=mp3(),encode=s=>new TextEncoder().encode(s),padding=new Uint8Array(64);
 for(const bad of [xmpOrphan+'garbage',xmpOrphan.replace('stRef:', 'st\0Ref:'),xmpOrphan+'\x01','random '+xmpOrphan,xmpOrphan.replace('</rdf:RDF>',''),xmpOrphan.replace('xmp.did:','file:///secret'),xmpOrphan+'<script/>']){
  assert.equal(inspectMp3(concatenate(audio,padding,encode(bad))),null);
 }
 assert.equal(inspectMp3(concatenate(audio,encode(xmpOrphan))),null,'no cleanup without the explicit zero-padding boundary');
 assert.equal(inspectMp3(concatenate(audio,new Uint8Array(4096),encode(xmpOrphan))),null);
 const broken=audio.slice();broken[417]=0;
 assert.equal(inspectMp3(concatenate(broken,padding,encode(xmpOrphan))),null,'cannot search past a broken frame');
});

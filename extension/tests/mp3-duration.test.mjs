import test from 'node:test';
import assert from 'node:assert/strict';
import {mp3DurationMs,durationNotice} from '../dist/unpacked/upload/mp3-duration.js';
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
 }
 assert.doesNotMatch(durationNotice(180000,null).text,/подходит/);
});

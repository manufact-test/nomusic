import test from 'node:test';
import assert from 'node:assert/strict';
import { createMusicTabs } from '../dist/unpacked/background/music-tabs.js';
test('background Yandex playback supplies popup status and original command from another website', async () => {
  let active={id:99,url:'https://example.org/'};
  const music=[{id:1,url:'https://music.yandex.ru/'},{id:2,url:'https://music.yandex.ru/album/2'}];
  const sent=[];
  const api={tabs:{query:async q=>q.active?[active]:music,sendMessage:async(id,m)=>{sent.push({id,m});return {ok:true}}}};
  const bootstrap={ensure:async id=>({error:null,status:{track:{id:String(id)},bridge:{healthy:true},player:{paused:id===1},phase:id===2?'REPLACEMENT_ACTIVE':'READY'}})};
  const tabs=createMusicTabs(api,bootstrap);
  assert.equal((await tabs.connection()).tabId,2);
  await tabs.send({type:'CELIKOM_RESTORE_ORIGINAL'});
  assert.equal(sent[0].id,2);
  active=music[0];assert.equal((await tabs.connection()).tabId,1);
  music.splice(0);assert.equal((await tabs.connection()).error,'no-music-tab');
  assert.equal(await tabs.send({type:'anything'}),null);
});
test('an unhealthy remembered tab cannot mask a healthy paused music tab',async()=>{
 const api={tabs:{query:async q=>q.active?[{id:99}]:[{id:1,url:'https://music.yandex.ru/'},{id:2,url:'https://music.yandex.ru/'}]}};
 const tabs=createMusicTabs(api,{ensure:async id=>({error:id===1?'timeout':null,status:{bridge:{healthy:id===2},player:{paused:true}}})});
 assert.equal((await tabs.connection()).tabId,2);
});

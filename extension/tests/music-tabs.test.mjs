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

test('explicit mismatch recovery reloads only the discovered music tab with the same fresh incident',async()=>{
 const reloads=[],mismatch={trackId:'48592143',since:10000};let current=mismatch,url='https://music.yandex.ru/';
 const api={tabs:{query:async q=>q.active?[{id:99}]:[{id:1,url:'https://music.yandex.ru/'}],
  get:async id=>({id,url}),reload:async id=>reloads.push(id)}};
 const tabs=createMusicTabs(api,{ensure:async()=>({status:{bridge:{healthy:true},player:{paused:false},track:{playbackMismatch:current}}})});
 assert.equal((await tabs.reloadMismatchedPlayer({trackId:'42',since:10000})).ok,false);
 assert.equal((await tabs.reloadMismatchedPlayer({...mismatch,since:1})).ok,false);
 current=null;assert.equal((await tabs.reloadMismatchedPlayer(mismatch)).ok,false);
 current=mismatch;url='https://example.org/';assert.equal((await tabs.reloadMismatchedPlayer(mismatch)).ok,false);
 assert.deepEqual(reloads,[]);
 url='https://music.yandex.ru/';assert.equal((await tabs.reloadMismatchedPlayer(mismatch)).ok,true);assert.deepEqual(reloads,[1]);
});
test('double recovery click cannot reload a page twice concurrently',async()=>{
 let finish;const reloads=[],mismatch={trackId:'42',since:10000};
 const api={tabs:{query:async()=>[{id:1,url:'https://music.yandex.ru/'}],get:async()=>({url:'https://music.yandex.ru/'}),reload:id=>{reloads.push(id);return new Promise(r=>finish=r)}}};
 const tabs=createMusicTabs(api,{ensure:async()=>({status:{bridge:{healthy:true},player:{paused:false},track:{playbackMismatch:mismatch}}})});
 const pending=tabs.reloadMismatchedPlayer(mismatch);
 for(let i=0;i<10;i++)await Promise.resolve();
 assert.equal((await tabs.reloadMismatchedPlayer(mismatch)).error,'reload_pending');
 finish();assert.equal((await pending).ok,true);assert.deepEqual(reloads,[1]);
});

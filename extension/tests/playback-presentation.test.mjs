import test from 'node:test';import assert from 'node:assert/strict';
import {playbackPresentation} from '../dist/unpacked/popup/playback-presentation.js';
test('Enabled original is explicit; a stalled preparation exposes manual retry',()=>{
 assert.equal(playbackPresentation({enabled:true,phase:'READY'}).label,'Включён · играет оригинал');
 assert.equal(playbackPresentation({enabled:true,phase:'PREPARING',preparation:{stage:'loading',elapsedMs:9999}}).startDisabled,true);
 const stalled=playbackPresentation({enabled:true,phase:'PREPARING',preparation:{stage:'loading',elapsedMs:10000}});
 assert.equal(stalled.startDisabled,false);assert.equal(stalled.startLabel,'Повторить');assert.equal(stalled.label,'Загружаем аудио…');
 assert.equal(playbackPresentation({enabled:true,phase:'READY',suspended:true}).startDisabled,false);
 assert.equal(playbackPresentation({enabled:true,phase:'REPLACEMENT_ACTIVE'}).startDisabled,true);
});

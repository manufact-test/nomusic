import assert from 'node:assert/strict';
import test from 'node:test';
import {validAudioSelection} from '../dist/unpacked/upload/contract.js';
import {ApiClient} from '../dist/unpacked/api/api-client.js';
test('Audio picker accepts MP3 and M4A with the existing size bound',()=>{
 for(const name of ['song.mp3','song.M4A'])assert.equal(validAudioSelection({name,size:2048}),true);
 for(const file of [null,{name:'a.m4a.exe',size:2048},{name:'a.m4a',size:31457281},{name:'a.m4a',size:0}])assert.equal(validAudioSelection(file),false);
});
test('Resolver negotiates M4A and validates MIME, while older MP3 responses still work',async()=>{
 const now=1791478000000;let mime='audio/mp4';
 const config={api_version:1,minimum_extension_version:'0.4.0',maintenance:false,features:{replacements:true}};
 const client=new ApiClient('https://private.example',{now:()=>now,fetch:async url=>{
  if(!url.endsWith('/config'))assert.equal(new URL(url).searchParams.get('audio_formats'),'mp3,m4a');
  return new Response(JSON.stringify(url.endsWith('/config')?config:{found:true,replacement_id:7,version:1,duration_ms:3000,expires_at:now/1000+600,audio_url:`/api/v1/audio/7?token=${'a'.repeat(64)}&expires=${now/1000+600}`,...(mime?{mime_type:mime}:{})}),{headers:{'content-type':'application/json'}});
 }});
 assert.equal((await client.resolveUncached('yandex','7')).mimeType,'audio/mp4');
 mime=undefined;assert.equal((await client.resolveUncached('yandex','7')).mimeType,'audio/mpeg');
 mime='video/mp4';await assert.rejects(client.resolveUncached('yandex','7'),/invalid_api_response/);
});

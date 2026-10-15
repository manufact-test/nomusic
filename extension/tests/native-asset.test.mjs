import test from 'node:test';
import assert from 'node:assert/strict';
await import('../dist/unpacked/player/replacement-player.js');
const {ReplacementPlayer}=globalThis.__CELIKOM_REPLACEMENT_PLAYER_V1__;
function fixture({size=2500000}={}){
 let active=0,peak=0,calls=0,tag='"'+'a'.repeat(64)+'-1"',status=206,oversize=false;
 const bytes=Uint8Array.from({length:size},(_,i)=>i%251);
 const asset={url:'https://private.example/api/v1/audio/27?token=current',replacementId:27,version:1,mimeType:'audio/mp4'};
 const env={document:{createElement:()=>({dataset:{},addEventListener(){}})},setTimeout,clearTimeout,AbortController,fetch:async(url,options)=>{
  calls++;active++;peak=Math.max(peak,active);await new Promise(r=>setTimeout(r,2));active--;
  if(options.signal.aborted)throw new Error('Replacement cancelled');
  assert.equal(options.cache,'no-store');assert.equal(options.credentials,'omit');
  if(status!==206)return new Response('{}',{status,headers:{'content-type':'application/json'}});
  const [,a,b]=/^bytes=(\d+)-(\d+)$/.exec(options.headers.Range),from=Number(a),last=Math.min(Number(b),size-1);
  return new Response(oversize?new Uint8Array(last-from+2):bytes.slice(from,last+1),{status:206,headers:{'content-type':'audio/mp4','content-range':`bytes ${from}-${last}/${size}`,'etag':tag}});
 }};
 const player=()=>{const p=new ReplacementPlayer(env,()=>{});p.fetchAbort=new AbortController();return p};
 return {asset,bytes,player,get calls(){return calls},get peak(){return peak},setTag:v=>tag=v,setStatus:v=>status=v,overflow:()=>oversize=true};
}
test('native M4A parallel ranges preserve bytes and cache still makes an authorized signed request',async()=>{
 const f=fixture(),p=f.player(),blob=await p.fetchNativeAsset(f.asset);
 assert.deepEqual(new Uint8Array(await blob.arrayBuffer()),f.bytes);assert.equal(f.calls,5);assert.equal(f.peak,4);
 const before=f.calls;const cached=await f.player().fetchNativeAsset({...f.asset,url:f.asset.url.replace('current','rotated')});
 assert.equal(cached,blob);assert.equal(f.calls,before+1,'cache reuse requires a fresh signed range');
 f.setStatus(403);await assert.rejects(f.player().fetchNativeAsset(f.asset),/remote-stream-http/);
 f.setStatus(206);f.setTag('"'+'b'.repeat(64)+'-2"');const changed=await f.player().fetchNativeAsset({...f.asset,version:2});
 assert.notEqual(changed,blob);assert.equal(f.calls,before+7,'changed version downloads all bytes again');
});
test('native download rejects oversized range bodies and cancelled work cannot populate cache',async()=>{
 const f=fixture();f.overflow();await assert.rejects(f.player().fetchNativeAsset(f.asset),/remote-stream-range/);
 const g=fixture(),p=g.player();const task=p.fetchNativeAsset({...g.asset,version:99});p.destroyed=true;p.fetchAbort.abort();await assert.rejects(task,/cancelled/);
 const before=g.calls;await g.player().fetchNativeAsset({...g.asset,version:99});assert.equal(g.calls,before+5);
});

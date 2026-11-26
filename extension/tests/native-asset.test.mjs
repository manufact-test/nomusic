import test from 'node:test';
import assert from 'node:assert/strict';
await import('../dist/unpacked/player/replacement-player.js');
const {ReplacementPlayer}=globalThis.__CELIKOM_REPLACEMENT_PLAYER_V1__;
function fixture({size=2500000,mimeType="audio/mp4"}={}){
 let active=0,peak=0,calls=0,tag='"'+'a'.repeat(64)+'-1"',status=206,oversize=false,failures=new Map();const offsets=[];
 const bytes=Uint8Array.from({length:size},(_,i)=>i%251);
 const asset={url:'https://private.example/api/v1/audio/27?token=current',replacementId:27,version:1,mimeType};
 const env={document:{createElement:()=>({dataset:{},addEventListener(){}})},setTimeout:(fn,ms)=>setTimeout(fn,[500,1000].includes(ms)?1:ms),clearTimeout,AbortController,fetch:async(url,options)=>{
  calls++;active++;peak=Math.max(peak,active);await new Promise(r=>setTimeout(r,2));active--;
  if(options.signal.aborted)throw new Error('Replacement cancelled');
  assert.equal(options.cache,'no-store');assert.equal(options.credentials,'omit');

  const [,a,b]=/^bytes=(\d+)-(\d+)$/.exec(options.headers.Range),from=Number(a),last=Math.min(Number(b),size-1);
  offsets.push(from);const result=failures.get(from)?.shift()??status;
  if(result!==206)return new Response('{}',{status:result,headers:{'content-type':'application/json'}});
  return new Response(oversize?new Uint8Array(last-from+2):bytes.slice(from,last+1),{status:206,headers:{'content-type':mimeType,'content-range':`bytes ${from}-${last}/${size}`,'etag':tag}});
 }};
 const player=()=>{const p=new ReplacementPlayer(env,()=>{});p.fetchAbort=new AbortController();return p};
 return {asset,bytes,player,get calls(){return calls},get peak(){return peak},setTag:v=>tag=v,setStatus:v=>status=v,offsets,fail:(offset,sequence)=>failures.set(offset,sequence),overflow:()=>oversize=true};
}
test('native M4A uses one bounded cold response without concurrent bursts and preserves bytes and cache still makes an authorized signed request',async()=>{
 const f=fixture(),p=f.player(),blob=await p.fetchNativeAsset(f.asset);
 assert.deepEqual(new Uint8Array(await blob.arrayBuffer()),f.bytes);assert.equal(f.calls,1);assert.equal(f.peak,1);
 const before=f.calls;const cached=await f.player().fetchNativeAsset({...f.asset,url:f.asset.url.replace('current','rotated')});
 assert.equal(cached,blob);assert.equal(f.calls,before+1,'cache reuse requires a fresh signed range');
 f.setStatus(403);await assert.rejects(f.player().fetchNativeAsset(f.asset),/remote-stream-http/);
 f.setStatus(206);f.setTag('"'+'b'.repeat(64)+'-2"');const changed=await f.player().fetchNativeAsset({...f.asset,version:2});
 assert.notEqual(changed,blob);assert.equal(f.calls,before+3,'changed version downloads all bytes again');
});
test('native download rejects oversized range bodies and cancelled work cannot populate cache',async()=>{
 const f=fixture();f.overflow();await assert.rejects(f.player().fetchNativeAsset(f.asset),/remote-stream-range/);
 const g=fixture(),p=g.player();const task=p.fetchNativeAsset({...g.asset,version:99});p.destroyed=true;p.fetchAbort.abort();await assert.rejects(task,/cancelled/);
 const before=g.calls;await g.player().fetchNativeAsset({...g.asset,version:99});assert.equal(g.calls,before+1);
});

test('cold native file retries temporary HTTP503 without parallel readers',async()=>{
 const f=fixture();f.fail(0,[503,503,206]);const p=f.player();
 const blob=await p.fetchNativeAsset({...f.asset,version:200});
 assert.deepEqual(new Uint8Array(await blob.arrayBuffer()),f.bytes);
 assert.deepEqual(f.offsets,[0,0,0]);assert.equal(f.peak,1);assert.equal(p.streamState.receivedBytes,f.bytes.length);
});
test('M4A retries remain bounded and never retry a revoked signed response',async()=>{
 const f=fixture();f.setStatus(503);const p=f.player();
 await assert.rejects(p.fetchNativeAsset(f.asset),error=>error.message==='remote-stream-http'&&error.streamDetail.httpStatus===503&&error.streamDetail.attempt===3);
 assert.equal(f.calls,3);
 f.setStatus(403);const before=f.calls;await assert.rejects(f.player().fetchNativeAsset(f.asset),/remote-stream-http/);assert.equal(f.calls,before+1);
});

test('approved complete MP3 is byte-preserving, bounded, sequential and still enforces signed access',async()=>{
 const f=fixture({mimeType:'audio/mpeg'}),p=f.player(),blob=await p.fetchNativeAsset(f.asset);
 assert.equal(blob.type,'audio/mpeg');assert.deepEqual(new Uint8Array(await blob.arrayBuffer()),f.bytes);
 assert.deepEqual(f.offsets,[0]);assert.equal(f.peak,1);
 f.setStatus(403);await assert.rejects(f.player().fetchNativeAsset(f.asset),/remote-stream-http/);
});

test('buffered audio renewal needs a fresh signed Range and exact content/version/gain; it never trusts an offline cache',async()=>{
 const f=fixture(),p=f.player();f.setTag('"'+'a'.repeat(64)+'-301"');await p.fetchNativeAsset({...f.asset,version:301});
 assert.equal(p.canRevalidateAuthorization(),true);
 const grant={...f.asset,version:301,url:f.asset.url.replace('current','new-grant')},before=f.calls;
 assert.equal(await p.revalidateAuthorization(grant),true);assert.equal(f.calls,before+1);
 assert.equal(await p.revalidateAuthorization({...grant,gainDb:1}),false,'gain changes cannot reuse the old audio graph');
 assert.equal(await p.revalidateAuthorization({...grant,version:302}),false);
 f.setTag('"'+'b'.repeat(64)+'-301"');assert.equal(await p.revalidateAuthorization(grant),false);
 f.setStatus(403);await assert.rejects(p.revalidateAuthorization(grant),error=>error.streamDetail.httpStatus===403);
});
test('an aborted signed renewal cannot approve a destroyed player',async()=>{
 const f=fixture(),p=f.player();f.setTag('"'+'a'.repeat(64)+'-303"');await p.fetchNativeAsset({...f.asset,version:303});
 const pending=p.revalidateAuthorization({...f.asset,version:303});p.destroyed=true;p.authorizationAbort.abort();
 await assert.rejects(pending,/cancelled/);assert.equal(p.authorizationAbort,null);
});

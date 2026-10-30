import test from 'node:test';
import assert from 'node:assert/strict';
import {probe,monitor} from '../scripts/celikom-api-monitor.mjs';
const good=url=>new Response(url.includes('/resolve?')?'':JSON.stringify(url.endsWith('/health')?{status:'ok',service:'celikom-api'}:{features:{replacements:true,analytics:false}}),{status:url.includes('/resolve?')?401:200,headers:{'content-type':'application/json'}});
test('public monitor checks health, feature contract and denied anonymous resolve without credentials',async()=>{
 const calls=[];const result=await monitor(async(url,opts)=>{calls.push({url,opts});return good(url)},async()=>assert.fail('healthy checks need no retry'));
 assert.equal(result.ok,true);assert.equal(calls.length,3);assert.ok(calls.every(c=>!c.opts.headers&&c.opts.redirect==='error'));
});
test('persistent empty HTTP 500 fails both rounds and never prints a response body',async()=>{
 const result=await monitor(async()=>new Response('private-token-must-not-leak',{status:500}),async()=>{});
 assert.equal(result.ok,false);assert.equal(result.samples.length,2);assert.ok(result.samples.every(s=>s.checks.every(c=>c.status===500&&!c.ok)));
 assert.ok(!JSON.stringify(result).includes('private-token'));
});
test('monitor records recovery and rejects captive pages, oversized JSON and missing feature contracts',async()=>{
 let calls=0;const result=await monitor(async url=>++calls<=3?new Response('',{status:500}):good(url),async()=>{});
 assert.equal(result.ok,true);assert.equal(result.recovered,true);
 for(const make of [()=>new Response('<html>'),()=>new Response(' '.repeat(20000),{headers:{'content-type':'application/json'}}),()=>new Response('{}',{headers:{'content-type':'application/json'}})]) {
  const result=await probe(async()=>make());assert.ok(result.some(c=>!c.ok));
 }
});

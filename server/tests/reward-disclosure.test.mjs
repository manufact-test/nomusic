import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';

const source = await readFile(new URL('../src/Reward/reward-disclosure.js', import.meta.url), 'utf8');
const tick = () => new Promise(resolve => setImmediate(resolve));
function fixture(fetch) {
  const listeners = {}, attributes = {};
  const content = { children: [], setAttribute(k,v) {attributes[k]=v}, removeAttribute(k) {delete attributes[k]},
    replaceChildren(...nodes) {this.children=nodes}, addEventListener(k,fn) {listeners[k]=fn} };
  const summary = { textContent: 'Песни и бонусы', addEventListener(k,fn) {listeners['summary-'+k]=fn} };
  content.getBoundingClientRect=()=>({height:700});
  const tail={style:{},setAttribute(){}};
  const window={scrollY:900,innerHeight:600,addEventListener(k,fn){listeners['window-'+k]=fn},scrollTo({top}){this.scrollY=top}};
  const card = { open:false, dataset:{rewardAccount:'2',rewardUrl:'/admin?tab=rewards&page=1&account=2'},
    querySelector: selector => selector === 'summary' ? summary : content,
    addEventListener(k,fn) {listeners[k]=fn} };
  const document = {body:{appendChild(){}},documentElement:{scrollHeight:1500}, querySelectorAll: () => [card], createElement: name => name==='div'?tail:({textContent:''}), importNode: node => ({...node}) };
  const context = { document, window, location: { href:'https://example.test/admin?tab=rewards',origin:'https://example.test'},
    URL,AbortSignal,fetch, DOMParser:class { parseFromString(html) {return {querySelector:()=>html==='own history'?{childNodes:[{song:'own'}]}:null}}} };
  runInNewContext(source,context);
  return {card,content,summary,listeners,context,tail,window};
}
const response = html => ({ok:true,headers:{get:()=> 'text/html; charset=utf-8'},text:async()=>html});

test('opening loads only account history; closing and reopening never navigate or refetch',async()=>{
  const requests=[];
  const fx=fixture(async(url,options)=>{requests.push({url,options});return response('own history')});
  fx.card.open=true;fx.listeners.toggle();await tick();
  assert.equal(fx.summary.textContent,'Свернуть');assert.equal(fx.content.children[0].song,'own');
  assert.equal(requests.length,1);assert.equal(new URL(requests[0].url).searchParams.get('account'),'2');
  assert.equal(requests[0].options.credentials,'same-origin');
  fx.card.open=false;fx.listeners.toggle();assert.equal(fx.summary.textContent,'Песни и бонусы');
  fx.card.open=true;fx.listeners.toggle();await tick();
  assert.equal(requests.length,1);assert.equal(fx.context.location.href,'https://example.test/admin?tab=rewards');
});
test('a late history response cannot reopen a collapsed account',async()=>{
  let finish;const fx=fixture(()=>new Promise(resolve=>finish=resolve));
  fx.card.open=true;fx.listeners.toggle();fx.card.open=false;fx.listeners.toggle();
  finish(response('own history'));await tick();
  assert.equal(fx.card.open,false);assert.equal(fx.summary.textContent,'Песни и бонусы');
  assert.equal(fx.content.children[0].song,'own');
});
test('session failure stays inside the card and a later open retries',async()=>{
  let calls=0;const fx=fixture(async()=>response(++calls===1?'login page':'own history'));
  fx.card.open=true;fx.listeners.toggle();await tick();
  assert.match(fx.content.children[0].textContent,/Не удалось/);assert.equal(fx.card.dataset.rewardLoaded,undefined);
  fx.card.open=false;fx.listeners.toggle();fx.card.open=true;fx.listeners.toggle();await tick();
  assert.equal(calls,2);assert.equal(fx.content.children[0].song,'own');
});
test('song pagination updates the same card; foreign links cannot request another origin',async()=>{
  const urls=[];const fx=fixture(async url=>{urls.push(url);return response('own history')});
  let prevented=0;
  const click=href=>fx.listeners.click({button:0,target:{closest:()=>({href})},preventDefault(){prevented++}});
  click('https://example.test/admin?tab=rewards&page=1&account=2&song_page=2');await tick();
  assert.equal(prevented,1);assert.equal(new URL(urls[0]).searchParams.get('song_page'),'2');
  click('https://foreign.test/admin?tab=rewards&account=2');await tick();
  assert.equal(urls.length,1);assert.equal(fx.context.location.href,'https://example.test/admin?tab=rewards');
});

 test('collapse near page bottom reserves only missing height and releases it after scrolling up',()=>{
  const fx=fixture(async()=>response('own history'));fx.card.open=true;
  let prevented=false;fx.listeners['summary-click']({preventDefault(){prevented=true}});
  assert.equal(prevented,true);assert.equal(fx.card.open,false);
  assert.equal(fx.window.scrollY,900);assert.equal(fx.tail.style.height,'700px');
  fx.window.scrollY=100;fx.listeners['window-scroll']();
  assert.equal(fx.tail.style.height,'0px');
 });

import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const elements = new Map();
function el(selector, values = {}) {
  const handlers = new Map();
  const node = { value: "", textContent: "", disabled: false, hidden: false, dataset: {},
    files: [], checked: false, title: "", style: {}, ...values,
    setAttribute(name, value) { this[name] = value; },
    addEventListener(name, fn) { handlers.set(name, fn); },
    async fire(name) { return handlers.get(name)?.({ preventDefault() {} }); } };
  elements.set(selector, node);
  return node;
}
for (const selector of ["[data-access-status]", "[data-version-status]", "[data-status]", "[data-action='start']", "[data-action='stop']",
  "[data-action='restore']", "[data-action='diagnostics']", "[data-track]", "[data-test-track]",
  "[data-upload-panel]", "[data-upload-track]", "[data-upload-file]", "[data-upload-key]",
  "[data-upload-cancel]", "[data-upload-confirm]", "[data-upload-continue]", "[data-upload-stop]",
  "[data-upload-rights]", "[data-upload-progress]", "[data-upload-status]", "[data-upload-submit]",
  "[data-upload-duration]", "[data-upload-result]", "[data-upload-result-title]", "[data-upload-result-note]",
  "[data-file-picker]", "[data-file-title]", "[data-file-name]",
  "[data-action='add']", "[data-upload-form]", "[data-action='suggest']", "[data-suggest-panel]", "[data-suggest-submit]", "[data-suggest-note]", "[data-suggest-track]", "[data-suggest-result]", "[data-suggest-result-title]", "[data-suggest-result-note]"]) el(selector);
const find = (selector) => elements.get(selector);
find("[data-upload-panel]").hidden = true;
find("[data-suggest-panel]").hidden = true;
find("[data-upload-form]").hidden = true;
find("[data-upload-result]").hidden = true;
find("[data-upload-progress]").hidden = true;
find("[data-upload-confirm]").hidden = true;
find("[data-upload-cancel]").hidden = true;

const selected = { track: { id: "144530503", confidence: 200, ambiguous: false,
  metadata: { durationMs: 180872, title: "Owner fixture", artist: "CI" } } };
let current = selected, offline = false;
let version = "none";
const intervals = [];
const pendingTracks = new Set();
const requests = [];
const statusCalls = [];
const suggestionPosts=[];let suggestionRace=null;
globalThis.document = { activeElement: null, querySelector: find };
globalThis.window = { setInterval(fn) { intervals.push(fn); return 1; } };
globalThis.chrome = {
  runtime: {
    getURL: (p) => "chrome-extension://ci-test/" + p,
    async sendMessage(message) {
      if (offline) throw new Error("simulated extension disconnect");
      if (message.type === "CELIKOM_AUTH" && message.action === "track-status") return {ok:true,status:version};
      if (message.type === "CELIKOM_AUTH" && message.action === "contribution-access") return {ok:true,access_token:"c".repeat(64)};
      if (message.type === "CELIKOM_STATUS_GET") return { ...current, phase: "READY", enabled: true };
      return { ok: true };
    }
  }
};
globalThis.fetch = async (url,options={}) => {
  if(String(url).includes("/api/v1/track-requests")){suggestionPosts.push(options);return {status:suggestionRace?409:202,json:async()=>suggestionRace?{error:suggestionRace}:{status:"pending",request_id:123}};}
  if (String(url).includes("/api/v1/tracks/upload-status")) {
    statusCalls.push(String(url));
    const currentTrackId = new URL(String(url)).searchParams.get("track_id");
    return { ok: true, async json() { return { status: pendingTracks.has(currentTrackId) ? "pending" : "none" }; } };
  }
  return { ok: true, async json() { return { baseUrl: "https://isolated-owner-test.example/" }; } };
};
class FakeXHR {
  static throwOnSend = false;
  static hold = false;
  constructor() {
    this.status = 202;
    this.responseText = JSON.stringify({ status: "pending", replacement_id: 71, duplicate: false });
    this.listeners = new Map();
    this.upload = { addEventListener() {} };
  }
  open(method, url) { this.method = method; this.url = url; }
  setRequestHeader(name, value) { this.headers ||= new Map(); this.headers.set(name, value); }
  addEventListener(name, cb) { this.listeners.set(name, cb); }
  send(body) {
    requests.push({ method: this.method, url: this.url, headers: this.headers, body });
    if (FakeXHR.throwOnSend) throw new Error("network startup denied");
    if (FakeXHR.hold) return;
    queueMicrotask(() => {
      pendingTracks.add(String(body.get("track_id")));
      this.listeners.get("loadend")?.();
    });
  }
  abort() {
    this.status = 0;
    this.listeners.get("abort")?.();
    this.listeners.get("loadend")?.();
  }
}
globalThis.XMLHttpRequest = FakeXHR;
globalThis.document.querySelectorAll = () => [];
await import("../dist/unpacked/popup/popup.js");
await new Promise((resolve) => setImmediate(resolve));

function selection() {
  const file = new Blob([new Uint8Array(2500)], { type: "audio/mpeg" });
  Object.defineProperty(file, "name", { value: "owner.mp3" });
  find("[data-upload-file]").files = [file];
  find("[data-upload-rights]").checked = true;
  find("[data-upload-key]").value = "a-private-session-only-owner-token";
}
function form() { return find("[data-upload-form]"); }
function result() { return find("[data-upload-result]"); }

test("Stage 7 Add version pins exact Track ID, checks server, then shows form", async () => {
  const html = await readFile(new URL("../popup/popup.html", import.meta.url), "utf8");
  assert.match(html, /data-upload-track[^>]*readonly/);
  assert.match(html, /data-upload-result[^>]*hidden/);
  await find("[data-action='add']").fire("click");
  assert.equal(find("[data-upload-panel]").hidden, false);
  assert.equal(find("[data-upload-track]").value, "144530503");
  assert.equal(find("[data-action='add']").textContent, "Загрузить версию");
  assert.equal(find("[data-action='add']").disabled, false);
  assert.equal(find("[data-action='add']").dataset.loading, "false");
  assert.equal(form().hidden, false);
  assert.equal(find("[data-upload-submit]").disabled, false);
  assert.ok(statusCalls.at(-1).includes("track_id=144530503"));
});

test("Stage 7 pending check does not reveal an incomplete panel while the network is waiting", async () => {
  await find("[data-action='add']").fire("click"); // closes current form
  const originalFetch = globalThis.fetch;
  let complete;
  globalThis.fetch = async (url, ...args) => {
    if (String(url).includes("/api/v1/tracks/upload-status")) {
      await new Promise((resolve) => { complete = resolve; });
    }
    return originalFetch(url, ...args);
  };
  try {
    const pending = find("[data-action='add']").fire("click");
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(find("[data-upload-panel]").hidden, true, "no unfinished form while checking");
    assert.equal(form().hidden, true);
    assert.equal(find("[data-action='add']").dataset.loading, "true");
    assert.equal(find("[data-action='add']").disabled, true);
    complete();
    await pending;
    assert.equal(find("[data-upload-panel]").hidden, false);
    assert.equal(form().hidden, false);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("Stage 7 changed track during preparation never sends audio", async () => {
  selection();
  current = { track: { ...selected.track, id: "144530504" } };
  await form().fire("submit");
  assert.equal(requests.length, 0);
  assert.match(find("[data-upload-status]").textContent, /Трек изменился/);
});

test("Stage 7 extension status disconnect never sends audio", async () => {
  current = selected;
  offline = true;
  await form().fire("submit");
  assert.equal(requests.length, 0);
  assert.match(find("[data-upload-status]").textContent, /Не удалось связаться/);
  offline = false;
});

test("Stage 7 synchronous network error does not strand disabled submit", async () => {
  FakeXHR.throwOnSend = true;
  await form().fire("submit");
  assert.equal(requests.length, 1);
  assert.equal(find("[data-upload-submit]").disabled, false);
  assert.match(find("[data-upload-status]").textContent, /Не удалось связаться/);
  FakeXHR.throwOnSend = false;
});

test("Stage 7 accepted upload displays unmistakable confirmation and locks controls", async () => {
  await form().fire("submit");
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(requests.length, 2);
  assert.equal(requests.at(-1).method, "POST");
  assert.equal(requests.at(-1).url, "https://isolated-owner-test.example/api/v1/uploads");
  assert.equal(requests.at(-1).headers.get("Authorization"), "Bearer " + "c".repeat(64));
  assert.equal(requests.at(-1).body.get("track_id"), "144530503");
  assert.equal(requests.at(-1).body.get("duration_ms"), "180872");
  assert.equal(requests.at(-1).body.get("declaration"), "1");
  assert.equal(requests.at(-1).body.get("service"), "yandex");
  assert.ok(/^[a-f0-9-]{36}$/.test(requests.at(-1).body.get("request_id")));
  assert.equal(form().hidden, true);
  assert.equal(result().hidden, false);
  assert.match(find("[data-upload-result-title]").textContent, /Отправлено на проверку/);
  assert.equal(find("[data-upload-submit]").disabled, true);
  assert.equal(elements.get("[data-upload-key]")?.value, "a-private-session-only-owner-token", "unused historical input is never read by user upload");
  await form().fire("submit");
  assert.equal(requests.length, 2, "click again cannot upload");
});

test("Stage 7 reopening popup-equivalent panel sees server pending without bearer", async () => {
  await find("[data-action='add']").fire("click"); // close
  await find("[data-action='add']").fire("click"); // open, query server again
  assert.equal(form().hidden, true);
  assert.equal(result().hidden, false);
  assert.match(find("[data-upload-result-title]").textContent, /Трек уже добавлен/);
  assert.match(find("[data-upload-result-note]").textContent, /ожидает проверки/);
  assert.equal(requests.length, 2);
});

test("Stage 7 on another Track ID remains eligible and rejects unconfirmed rights", async () => {
  current = { track: { ...selected.track, id: "144530505" } };
  await find("[data-action='add']").fire("click");
  await find("[data-action='add']").fire("click");
  assert.equal(find("[data-upload-track]").value, "144530505");
  assert.equal(form().hidden, false);
  find("[data-upload-rights]").checked = false;
  await form().fire("submit");
  assert.equal(requests.length, 2);
});

 test("popup separates detected track from available, pending and missing version", async () => {
  current = selected;
  for (const value of ["none", "pending", "approved"]) {
    version = value;
    // A new exact track forces a fresh presence check without waiting for polling.
    current = {track: {...selected.track, id: selected.track.id + String(value.length)}};
    intervals[0]();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(find("[data-status]").textContent, "Включён · играет оригинал");
    const text = find("[data-version-status]").textContent;
    assert.match(text, value === "none" ? /ещё не загружена/ : value === "pending" ? /на проверке/ : /доступна/);
  }
  current = {track: null}; intervals[0]();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(find("[data-version-status]").hidden, true, "no empty status row without a track");
  assert.equal(find("[data-version-status]").textContent, "");
});

test('two consecutive songs upload without reloading or Start/Stop and with separate request IDs',async()=>{
 current={track:{...selected.track,id:'944530501'}};
 intervals[0]();await new Promise(resolve=>setImmediate(resolve));
 await find("[data-action='add']").fire('click');
 assert.equal(form().hidden,false);
 selection();await form().fire('submit');await new Promise(resolve=>setImmediate(resolve));
 const first=requests.at(-1);
 assert.equal(first.body.get('track_id'),'944530501');
 assert.equal(result().hidden,false);
 current={track:{...selected.track,id:'944530502'}};
 intervals[0]();await new Promise(resolve=>setImmediate(resolve));
 assert.equal(find('[data-upload-panel]').hidden,true,'old song result closes on track change');
 assert.equal(find('[data-upload-rights]').checked,false);
 assert.equal(find('[data-upload-file]').value,'');
 await find("[data-action='add']").fire('click');
 assert.equal(form().hidden,false,'one click opens the new song');
 assert.equal(find('[data-upload-track]').value,'944530502');
 selection();await form().fire('submit');await new Promise(resolve=>setImmediate(resolve));
 const second=requests.at(-1);
 assert.equal(second.body.get('track_id'),'944530502');
 assert.notEqual(second.body.get('request_id'),first.body.get('request_id'));
 assert.equal(result().hidden,false);
});

test('switching songs and clicking upload before polling opens the new form in one click',async()=>{
 current={track:{...selected.track,id:'944530503'}};
 await find("[data-action='add']").fire('click');
 assert.equal(find('[data-upload-track]').value,'944530503');
 assert.equal(form().hidden,false);
 assert.equal(result().hidden,true);
 assert.equal(find('[data-upload-rights]').checked,false);
});

test('search-selected song recovers a temporary status failure without reload or duplicate audio',async()=>{
 current={track:{...selected.track,id:'944530504'}};
 const originalFetch=globalThis.fetch;let calls=0;const before=requests.length;
 globalThis.fetch=async(url,...args)=>{
  if(String(url).includes('/tracks/upload-status') && ++calls===1) return {ok:false,status:503,json:async()=>({error:'temporarily_unavailable'})};
  return originalFetch(url,...args);
 };
 try{
  await find("[data-action='add']").fire('click');
  assert.equal(calls,2);assert.equal(form().hidden,false);
  assert.equal(find('[data-upload-track]').value,'944530504');
  assert.equal(requests.length,before,'presence recovery never sends audio');
 }finally{globalThis.fetch=originalFetch;}
});

test('failed opening is retried in one click rather than merely closing the error panel',async()=>{
 current={track:{...selected.track,id:'944530505'}};
 offline=true;await find("[data-action='add']").fire('click');offline=false;
 assert.equal(form().hidden,true);
 await find("[data-action='add']").fire('click');
 assert.equal(form().hidden,false);
 assert.equal(find('[data-upload-track]').value,'944530505');
});

test('song changes while checking do not display the previous song form',async()=>{
 current={track:{...selected.track,id:'944530506'}};
 const originalFetch=globalThis.fetch;
 globalThis.fetch=async(url,...args)=>{
  if(String(url).includes('/tracks/upload-status')) current={track:{...selected.track,id:'944530507'}};
  return originalFetch(url,...args);
 };
 try{
  await find("[data-action='add']").fire('click');
  assert.equal(form().hidden,true);assert.match(find('[data-upload-status]').textContent,/Песня сменилась/);
 }finally{globalThis.fetch=originalFetch;}
 await find("[data-action='add']").fire('click');
 assert.equal(form().hidden,false);assert.equal(find('[data-upload-track]').value,'944530507');
});

test('active replacement label is stable across polls even when original audio is paused',async()=>{
 const send=chrome.runtime.sendMessage;
 const node=find('[data-version-status]');let writes=[];let text=node.textContent;
 Object.defineProperty(node,'textContent',{configurable:true,get:()=>text,set:value=>{writes.push(value);text=value;}});
 chrome.runtime.sendMessage=async(message)=>message.type==='CELIKOM_STATUS_GET'
  ?{...current,enabled:true,phase:'REPLACEMENT_ACTIVE',player:{paused:true}}:send(message);
 try {
  for(let i=0;i<4;i++) {intervals[0]();await new Promise(resolve=>setImmediate(resolve));}
  assert.equal(node.textContent,'Подмена активна · версия CELIKOM');
  assert.deepEqual(writes,['Подмена активна · версия CELIKOM'],'no intermediate availability or pause label on repeated polls');
  chrome.runtime.sendMessage=send;
  intervals[0]();await new Promise(resolve=>setImmediate(resolve));
  assert.match(node.textContent,/доступна для подмены/);
 } finally {
  chrome.runtime.sendMessage=send;
  Object.defineProperty(node,'textContent',{configurable:true,writable:true,value:text});
 }
});


test('suggesting available or pending audio shows the green result and never posts a request',async()=>{
 current=selected;offline=false;
 for(const status of ['approved','pending']){
  version=status;find('[data-suggest-panel]').hidden=true;
  const count=suggestionPosts.length;const opening=find("[data-action='suggest']").fire('click');
  assert.equal(find("[data-action='suggest']").disabled,true);assert.equal(find("[data-action='suggest']").textContent,'Проверяем…');await opening;
  assert.equal(find("[data-action='suggest']").disabled,false);
  assert.equal(find('[data-suggest-result]').hidden,false);assert.equal(find('[data-suggest-submit]').hidden,true);
  assert.match(find('[data-suggest-result-title]').textContent,status==='approved'?/доступна/:/проверке/);assert.equal(suggestionPosts.length,count);
 }
 version='none';
});
test('a catalog race on suggestion submit is handled as already available, not an error or repeated post',async()=>{
 current=selected;version='none';find('[data-suggest-panel]').hidden=true;
 await find("[data-action='suggest']").fire('click');assert.equal(find('[data-suggest-submit]').disabled,false);
 suggestionRace='track_already_approved';await find('[data-suggest-submit]').fire('click');
 assert.equal(find('[data-suggest-result]').hidden,false);assert.match(find('[data-suggest-result-title]').textContent,/доступна/);
 assert.equal(find('[data-suggest-note]').hidden,true);suggestionRace=null;
});
test('local MP3 duration warning is visible before any file upload',async()=>{
 const {mp3DurationMs}=await import('../dist/unpacked/upload/mp3-duration.js');
 const bytes=await readFile(new URL('../assets/test-audio.mp3',import.meta.url));
 const duration=mp3DurationMs(bytes);assert.ok(duration>1000);
 current={...selected,track:{...selected.track,id:'144530599',metadata:{...selected.track.metadata,durationMs:duration+5001}}};
 find('[data-upload-panel]').hidden=true;version='none';await find("[data-action='add']").fire('click');
 const file=new Blob([bytes],{type:'audio/mpeg'});Object.defineProperty(file,'name',{value:'local.mp3'});find('[data-upload-file]').files=[file];
 const count=requests.length;await find('[data-upload-file]').fire('change');await new Promise(resolve=>setTimeout(resolve,10));
 assert.equal(find('[data-upload-duration]').hidden,false);assert.match(find('[data-upload-duration]').textContent,/Разница больше 5 секунд/);assert.equal(requests.length,count);
});

test('duration mismatch blocks submit even if called directly and selecting a compatible file unlocks',async()=>{
 const bytes=await readFile(new URL('../assets/test-audio.mp3',import.meta.url));
 const {mp3DurationMs}=await import('../dist/unpacked/upload/mp3-duration.js');
 const duration=mp3DurationMs(bytes);
 const input=find('[data-upload-file]'),button=find('[data-upload-submit]');
 assert.equal(button.disabled,true);
 find('[data-upload-rights]').checked=true;
 const count=requests.length;await find('[data-upload-form]').fire('submit',{preventDefault(){}});
 assert.equal(requests.length,count);assert.equal(button.disabled,true);
 current={...selected,track:{...selected.track,id:'144530598',metadata:{...selected.track.metadata,durationMs:duration}}};
 find('[data-upload-panel]').hidden=true;await find("[data-action='add']").fire('click');
 const file=new Blob([bytes],{type:'audio/mpeg'});Object.defineProperty(file,'name',{value:'fits.mp3'});input.files=[file];
 await input.fire('change');await new Promise(resolve=>setTimeout(resolve,10));
 assert.equal(button.disabled,false);assert.equal(find('[data-upload-duration]').dataset.kind,'ok');
});

test('cancelled empty picker does not send a file or lock another song form',async()=>{
 current={track:{...selected.track,id:'944530520'}};find('[data-upload-panel]').hidden=true;
 await find("[data-action='add']").fire('click');
 const before=requests.length,input=find('[data-upload-file]');input.files=[];
 await input.fire('cancel');assert.equal(input.disabled,false);assert.equal(requests.length,before);
 current={track:{...selected.track,id:'944530521'}};
 await find("[data-action='add']").fire('click');assert.equal(find('[data-upload-track]').value,'944530521');assert.equal(form().hidden,false);
});

test('Stop interrupts a pending Start and its late response cannot disable a fresh retry',async()=>{
 const original=chrome.runtime.sendMessage;let complete;
 chrome.runtime.sendMessage=message=>message.type==='CELIKOM_ENABLED_SET'&&message.enabled?new Promise(r=>complete=r):message.type==='CELIKOM_ENABLED_SET'?Promise.resolve({...current,phase:'STOPPED',enabled:false}):original(message);
 try {
  const start=find("[data-action='start']"),stop=find("[data-action='stop']");
  const pending=start.fire('click');await Promise.resolve();assert.equal(stop.disabled,false);
  await stop.fire('click');assert.equal(start.disabled,false);
  complete({...current,enabled:true,phase:'READY'});await pending;
  assert.equal(start.disabled,false,'old Start response cannot overwrite Stop');
 }finally{chrome.runtime.sendMessage=original;}
});

test('a Start message that never returns releases the button after its deadline',async(t)=>{
 t.mock.timers.enable({apis:['setTimeout','Date']});
 const original=chrome.runtime.sendMessage;
 chrome.runtime.sendMessage=m=>m.type==='CELIKOM_ENABLED_SET'?new Promise(()=>{}):original(m);
 try {
  const start=find("[data-action='start']"),pending=start.fire('click');assert.equal(start.disabled,true);
  t.mock.timers.tick(60000);await pending;
  assert.equal(start.disabled,false);assert.match(find('[data-access-status]').textContent,/Проверка не завершена/);
 }finally{chrome.runtime.sendMessage=original;}
});

test("Explicit cancel uses CELIKOM's own dialog and records no silent interruption", async () => {
  version = "none";
  current = { track: {...selected.track, id: "944530599"} };
  find("[data-upload-panel]").hidden = true;
  await find("[data-action='add']").fire("click");
  selection();
  FakeXHR.hold = true;
  try {
    await form().fire("submit");
    assert.equal(find("[data-upload-cancel]").hidden, false);
    await find("[data-upload-cancel]").fire("click");
    assert.equal(find("[data-upload-confirm]").hidden, false);
    await find("[data-upload-continue]").fire("click");
    assert.equal(find("[data-upload-confirm]").hidden, true);
    await find("[data-upload-cancel]").fire("click");
    await find("[data-upload-stop]").fire("click");
    assert.equal(find("[data-upload-cancel]").hidden, true);
    assert.match(find("[data-upload-status]").textContent, /отменена/);
    assert.equal(find("[data-upload-submit]").disabled, false);
  } finally { FakeXHR.hold = false; }
});

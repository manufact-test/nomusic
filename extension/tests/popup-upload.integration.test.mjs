import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const elements = new Map();
function el(selector, values = {}) {
  const handlers = new Map();
  const node = { value: "", textContent: "", disabled: false, hidden: false, dataset: {},
    files: [], checked: false, title: "", style: {}, ...values,
    setAttribute(name, value) { this[name] = value; },
    focus() { this.focused = true; },
    addEventListener(name, fn) { handlers.set(name, fn); },
    async fire(name) { return handlers.get(name)?.({ preventDefault() {} }); } };
  elements.set(selector, node);
  return node;
}
for (const selector of ["[data-access-status]", "[data-version-status]", "[data-status]", "[data-action='start']", "[data-action='stop']",
  "[data-action='restore']", "[data-action='diagnostics']", "[data-track]", "[data-test-track]",
  "[data-upload-panel]", "[data-upload-track]", "[data-upload-file]", "[data-upload-key]",
  "[data-upload-transfer-slot]", "[data-upload-confirm]", "[data-upload-continue]", "[data-upload-stop]",
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
find("[data-upload-transfer-slot]").hidden = true;

const selected = { track: { id: "144530503", confidence: 200, ambiguous: false,
  metadata: { durationMs: 180872, title: "Owner fixture", artist: "CI" } } };
let current = selected, offline = false;
let version = "none";
const intervals = [];
const pendingTracks = new Set();
const requests = [];
const statusCalls = [];
let trackStatusResponder = null;
const suggestionPosts=[];let suggestionRace=null;
globalThis.document = { activeElement: null, querySelector: find };
globalThis.window = { setInterval(fn) { intervals.push(fn); return 1; } };
const localValues = {};
globalThis.chrome = {
  storage: {local: {
    async get(key) { return {[key]:localValues[key]}; },
    async set(values) { Object.assign(localValues,values); }
  }},
  runtime: {
    getURL: (p) => "chrome-extension://ci-test/" + p,
    async sendMessage(message) {
      if (offline) throw new Error("simulated extension disconnect");
      if (message.type === "CELIKOM_AUTH" && message.action === "track-status") {
        statusCalls.push(message.track_id);
        if (trackStatusResponder) return trackStatusResponder(message.track_id);
        return {ok:true,status:pendingTracks.has(message.track_id) ? "pending" : version};
      }
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

// Full-length synthetic 128 kbps MPEG-1 Layer III, never a copyrighted file.
// Prior all-zero "MP3" fixture bypassed content checks and masked validation.
const fixtureFrames = 6924;
const fixtureAudio = new Uint8Array(fixtureFrames * 417);
for (let offset = 0; offset < fixtureAudio.length; offset += 417)
  fixtureAudio.set([0xff, 0xfb, 0x90, 0x64], offset);
function selection() {
  const file = new Blob([fixtureAudio], { type: "audio/mpeg" });
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
  assert.ok(statusCalls.includes("144530503"));
});

test("Panel opens immediately in neutral state and never flashes stale form/pending", async () => {
  await find("[data-action='add']").fire("click");
  let release;
  trackStatusResponder=()=>new Promise(resolve=>{release=resolve;});
  try {
    const action=find("[data-action='add']");
    const pending=action.fire("click");
    await new Promise(resolve=>setImmediate(resolve));
    assert.equal(find("[data-upload-panel]").hidden,false);
    assert.equal(form().hidden,true);
    assert.equal(result().hidden,true);
    assert.equal(action.dataset.loading,"false");
    assert.equal(action.disabled,false);
    assert.match(find("[data-upload-status]").textContent,/Проверяем возможность загрузки/);
    release({ok:true,status:"none"});
    await pending;
    assert.equal(form().hidden,false);
    assert.equal(find("[data-upload-status]").hidden,true);
  } finally {trackStatusResponder=null;}
});

test("Closing during presence check never reopens after late response",async()=>{
 const action=find("[data-action='add']");
 await action.fire("click");
 let release;trackStatusResponder=()=>new Promise(resolve=>{release=resolve;});
 try {
  const pending=action.fire("click");
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(find("[data-upload-panel]").hidden,false);
  await action.fire("click");
  assert.equal(find("[data-upload-panel]").hidden,true);
  release({ok:true,status:"pending"});
  await pending;
  assert.equal(find("[data-upload-panel]").hidden,true);
  assert.equal(result().hidden,true);
 }finally{trackStatusResponder=null;}
 // The following tests use the original track form.
 await action.fire("click");
 assert.equal(form().hidden,false);
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
  version="none";
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

test('a temporary auth status failure retries once without sending an upload',async()=>{
 current={track:{...selected.track,id:'944530504'}};
 let calls=0;const before=requests.length;
 trackStatusResponder=async()=>++calls===1?{ok:false,error:"auth_unavailable"}:{ok:true,status:"none"};
 try{
  await find("[data-action='add']").fire('click');
  assert.equal(calls,2);assert.equal(form().hidden,false);
  assert.equal(find('[data-upload-track]').value,'944530504');
  assert.equal(requests.length,before,'status recovery must not POST audio');
 }finally{trackStatusResponder=null;}
});

test('failed opening is retried in one click rather than merely closing the error panel',async()=>{
 current={track:{...selected.track,id:'944530505'}};
 offline=true;await find("[data-action='add']").fire('click');offline=false;
 assert.equal(form().hidden,true);
 await find("[data-action='add']").fire('click');
 assert.equal(form().hidden,false);
 assert.equal(find('[data-upload-track]').value,'944530505');
});

test('song changes after presence read never reveal previous song form',async()=>{
 current={track:{...selected.track,id:'944530506'}};
 const original=chrome.runtime.sendMessage;
 let statusReads=0;
 chrome.runtime.sendMessage=async message=>{
  if(message.type==="CELIKOM_STATUS_GET" && ++statusReads===3)
    current={track:{...selected.track,id:'944530507'}};
  return original(message);
 };
 try {
  await find("[data-action='add']").fire('click');
  assert.equal(form().hidden,true);
  assert.match(find('[data-upload-status]').textContent,/Песня сменилась/);
 } finally {chrome.runtime.sendMessage=original;}
 await find("[data-action='add']").fire('click');
 assert.equal(form().hidden,false);
 assert.equal(find('[data-upload-track]').value,'944530507');
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
 pendingTracks.delete(selected.track.id); // tests must not borrow a previous synthetic submission
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

test("full-width green Submit becomes red Cancel; explicit confirmation restores the primary action", async () => {
  version = "none";
  current = { track: {...selected.track, id: "944530599"} };
  find("[data-upload-panel]").hidden = true;
  await find("[data-action='add']").fire("click");
  selection();
  FakeXHR.hold = true;
  try {
    await form().fire("submit");
    const action = find("[data-upload-submit]");
    assert.equal(action.dataset.uploadMode, "cancel");
    assert.equal(action.type, "button");
    assert.equal(action.textContent, "Отменить загрузку");
    assert.equal(find("[data-upload-transfer-slot]").hidden, false);
    await action.fire("click");
    assert.equal(find("[data-upload-confirm]").hidden, false);
    await find("[data-upload-continue]").fire("click");
    assert.equal(find("[data-upload-confirm]").hidden, true);
    await action.fire("click");
    await find("[data-upload-stop]").fire("click");
    assert.equal(find("[data-upload-transfer-slot]").hidden, true);
    assert.match(find("[data-upload-status]").textContent, /отменена/);
    assert.equal(action.dataset.uploadMode, "retry");
    assert.equal(action.disabled, false);
  } finally { FakeXHR.hold = false; }
});

test("upload form displays CELIKOM-styled required-field feedback", async () => {
  const markup = await readFile(new URL("../popup/popup.html", import.meta.url), "utf8");
  assert.match(markup, /<form data-upload-form hidden novalidate>/);
  assert.match(markup, /data-upload-confirm/);
  current = {track: {...selected.track, id: "944530598"}};
  find("[data-upload-panel]").hidden = true;
  await find("[data-action='add']").fire("click");
  const baseline = requests.length;
  find("[data-upload-file]").files = [];
  find("[data-upload-rights]").checked = true;
  await form().fire("submit");
  assert.match(find("[data-upload-status]").textContent, /Выберите MP3 или M4A/);
  assert.equal(find("[data-upload-status]").dataset.kind, "error");
  assert.equal(requests.length, baseline);
  selection();
  find("[data-upload-rights]").checked = false;
  await form().fire("submit");
  assert.match(find("[data-upload-status]").textContent, /Подтвердите/);
  assert.equal(requests.length, baseline);
});

test("background uploader keeps the form stable and never forces popup scroll", async()=>{
 const source=await readFile(new URL("../src/popup/popup.ts",import.meta.url),"utf8");
 const html=await readFile(new URL("../popup/popup.html",import.meta.url),"utf8");
 const css=await readFile(new URL("../popup/popup.css",import.meta.url),"utf8");
 assert.doesNotMatch(source,/scrollIntoView\s*\(/,"No involuntary scroll during preflight or upload");
 assert.match(source,/if\(uploadForm\) uploadForm\.hidden = false;/,
   "Popup form stays rendered when checking background status");
 assert.doesNotMatch(source,/uploadForm\.hidden\s*=\s*active/,
   "Background transfer must not collapse the form");
 assert.match(html,/class="upload-transfer-slot"/);
 assert.match(html,/data-upload-progress/);
 assert.doesNotMatch(html,/data-upload-cancel/);
 assert.match(css,/data-upload-mode="cancel"/);
 assert.match(css,/\.upload-transfer-slot\[hidden\]/);
 assert.doesNotMatch(css,/height:\s*82px/);
 assert.equal((html.match(/data-upload-status/g)||[]).length,1);
});

test("upload panel respects explicit Close despite repeated background status polls", async () => {
  const id="944530597", key="celikom_background_upload_v1", action=find("[data-action='add']");
  current={track:{...selected.track,id}};
  version="none";
  find("[data-upload-panel]").hidden=true;
  await action.fire("click");
  assert.equal(find("[data-upload-panel]").hidden,false);
  localValues[key]={id:"123e4567-e89b-42d3-a456-426614174000",trackId:id,phase:"transferring",percent:65,at:Date.now()};
  await intervals[0]();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(find("[data-upload-submit]").dataset.uploadMode,"cancel");
  assert.equal(find("[data-upload-progress]").value,65);
  await action.fire("click");
  assert.equal(find("[data-upload-panel]").hidden,true);
  assert.equal(action["aria-expanded"],"false");
  for(let n=0;n<4;n++){await intervals[0]();await new Promise(resolve=>setImmediate(resolve));}
  assert.equal(find("[data-upload-panel]").hidden,true,"closed must stay closed");
  await action.fire("click");
  assert.equal(find("[data-upload-panel]").hidden,false,"open returns to same upload");
  assert.equal(find("[data-upload-submit]").dataset.uploadMode,"cancel");
  localValues[key]={...localValues[key],phase:"completed",percent:100,at:Date.now()};
  await intervals[0]();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(find("[data-upload-submit]").dataset.uploadMode,"complete");
  assert.equal(find("[data-upload-transfer-slot]").hidden,true);
  assert.match(find("[data-upload-status]").textContent,/отправлена на модерацию/);
  await action.fire("click");
  assert.equal(find("[data-upload-panel]").hidden,true);
  for(let n=0;n<3;n++){await intervals[0]();await new Promise(resolve=>setImmediate(resolve));}
  assert.equal(find("[data-upload-panel]").hidden,true,"completed poll cannot resurrect the form");
  pendingTracks.add(id);
  await action.fire("click");
  assert.equal(result().hidden,false);
  assert.equal(form().hidden,true,"completed song must not offer a fresh form");
  assert.match(find("[data-upload-result-title]").textContent,/Трек уже добавлен/);
  delete localValues[key];
});

test("progress bar is between checkbox and the green/red primary action",async()=>{
 const html=await readFile(new URL("../popup/popup.html",import.meta.url),"utf8");
 const rights=html.indexOf("data-upload-rights"),progress=html.indexOf("data-upload-transfer-slot"),button=html.indexOf("data-upload-submit");
 assert.ok(rights>=0&&rights<progress&&progress<button,"progress must be under the checkbox and above button");
 const between=html.slice(rights,button);
 assert.match(between,/data-upload-progress/);
 assert.match(between,/data-upload-transfer-slot hidden/);
});

test("stale local completed attempt cannot replace fresh server result with a false pending claim",async()=>{
 const action=find("[data-action='add']"),id="944530611",key="celikom_background_upload_v1";
 current={track:{...selected.track,id}};
 version="none";pendingTracks.delete(id);
 find("[data-upload-panel]").hidden=true;
 localValues[key]={id:"123e4567-e89b-42d3-a456-426614174000",trackId:id,phase:"completed",percent:100,at:Date.now()};
 await intervals[0]();await new Promise(resolve=>setImmediate(resolve));
 assert.equal(find("[data-upload-panel]").hidden,true,"historical local completed must not auto-open");
 await action.fire("click");
 assert.equal(find("[data-upload-panel]").hidden,false);
 assert.equal(result().hidden,true,"no false already-uploaded result from old storage");
 assert.equal(form().hidden,false,"live server none authorizes fresh form");
 delete localValues[key];
});

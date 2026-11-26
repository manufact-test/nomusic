import test from "node:test";
import assert from "node:assert/strict";
import {createUploadBroker} from "../dist/unpacked/background/upload-broker.js";
import {readFile} from "node:fs/promises";

test("no tabs are created; only one hidden worker is bootstrapped for concurrent requests",async()=>{
 const events=[],url="chrome-extension://ci/popup/upload-worker.html";
 let contexts=[];
 const api={runtime:{
   getURL:path=>"chrome-extension://ci/"+path,
   getContexts:async args=>{assert.deepEqual(args.contextTypes,["OFFSCREEN_DOCUMENT"]);return contexts;},
   sendMessage:async message=>{events.push(message.type);return {ok:true}}
 },offscreen:{async createDocument(config){
   assert.equal(config.url,"popup/upload-worker.html");
   assert.deepEqual(config.reasons,["BLOBS"]);
   events.push("create");contexts=[{documentUrl:url}];
 }}};
 const broker=createUploadBroker(api);
 const [a,b]=await Promise.all([broker.begin({id:"a"}),broker.begin({id:"b"})]);
 assert.equal(a.ok,true);assert.equal(b.ok,true);
 assert.equal(events.filter(x=>x==="create").length,1);
 assert.equal(events.filter(x=>x==="CELIKOM_UPLOAD_EXECUTE").length,2);
 await broker.cancel("a");
 assert.equal(events.at(-1),"CELIKOM_UPLOAD_INTERRUPT");
});
test("the installed package has no dedicated upload tab and uses a hidden worker",async()=>{
 const popup=await readFile(new URL("../dist/unpacked/popup/popup.js",import.meta.url),"utf8");
 const html=await readFile(new URL("../dist/unpacked/popup/popup.html",import.meta.url),"utf8");
 const manifest=JSON.parse(await readFile(new URL("../dist/unpacked/manifest.json",import.meta.url),"utf8"));
 assert.equal(popup.includes('tabs.create({url: chrome.runtime.getURL("popup/popup.html#upload")}'),false);
 assert.equal(popup.includes('popup/popup.html#upload'),false);
 assert.ok(popup.includes("stageUploadFile"));
 assert.ok(popup.includes("CELIKOM_UPLOAD_BEGIN"));
 assert.equal(html.includes("в отдельной вкладке"),false);
 assert.deepEqual(manifest.permissions.includes("offscreen"),true);
 assert.equal(manifest.action.default_popup,"popup/popup.html");
 const workerHtml=await readFile(new URL("../dist/unpacked/popup/upload-worker.html",import.meta.url),"utf8");
 assert.match(workerHtml,/offscreen\/upload-worker\.js/);
});

import { test } from "node:test";
import assert from "node:assert/strict";
import { classifyDebugTarget, productionDecision } from "./session-policy.mjs";
const port = 35791, nonce="a".repeat(32), fixtureOrigin="http://127.0.0.1:42715";
const target={type:"page",title:"CELIKOM W7 isolated attach",url:fixtureOrigin+"/?nonce="+nonce,
webSocketDebuggerUrl:"ws://127.0.0.1:"+port+"/devtools/page/0123456789ABCDEF"};
test("W7 exact isolated fixture may attach without official-client rights",()=>{
 const result=classifyDebugTarget({target,debuggerPort:port,fixtureOrigin,nonce});
 assert.equal(result.accepted,true);assert.equal(result.mayTouchOfficialYandex,false);
});
test("W7 all other targets are rejected, even a legitimate Yandex Music tab",()=>{
 const bad=[
 {target:{...target,url:"https://music.yandex.ru/?nonce="+nonce}},
 {target:{...target,url:fixtureOrigin+"/?nonce="+("b".repeat(32))}},
 {target:{...target,title:"Яндекс Музыка"}},
 {target:{...target,type:"iframe"}},
 {target:{...target,webSocketDebuggerUrl:"ws://0.0.0.0:"+port+"/devtools/page/1"}},
 {target:{...target,webSocketDebuggerUrl:"ws://evil.example:"+port+"/devtools/page/1"}},
 {target:{...target,webSocketDebuggerUrl:"ws://127.0.0.1:1000/devtools/page/1"}},
 {target:{...target,webSocketDebuggerUrl:"ws://127.0.0.1:"+port+"/devtools/browser/1"}},
 {target:{...target,webSocketDebuggerUrl:"ws://127.0.0.1:"+port+"/devtools/page/1?secret=x"}},
 {target:{...target,url:fixtureOrigin+"/?nonce="+nonce+"&token=bad"}},
 {fixtureOrigin:"https://music.yandex.ru"},
 {fixtureOrigin:"http://localhost:42715"},
 {debuggerPort:0}, {nonce:"not-hex"}
 ];
 for(const change of bad) assert.equal(classifyDebugTarget(
 {target,debuggerPort:port,fixtureOrigin,nonce,...change}).accepted,false,
 "Expected safe rejection: "+JSON.stringify(change));
});
test("W7 never authorizes debugging, patching or claims of official compatibility",()=>{
 const p=productionDecision();
 assert.equal(p.allowDebugPortOnUserYandex,false);
 assert.equal(p.allowYandexFileChanges,false);
 assert.equal(p.supportedLiveAttachment,false);
});

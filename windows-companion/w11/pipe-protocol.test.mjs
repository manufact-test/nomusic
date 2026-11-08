import { test } from "node:test";
import assert from "node:assert/strict";
import { PassThrough } from "node:stream";
import { createPipeTransport, exactFixtureTarget } from "./pipe-protocol.mjs";
const nonce="a".repeat(32), origin="http://127.0.0.1:43121";
const target={type:"page",title:"CELIKOM W7 isolated attach",url:origin+"/?nonce="+nonce};
test("W11 accepts one exact test-only frame target",()=>{
  assert.equal(exactFixtureTarget(target,origin,nonce),true);
  for(const wrong of [
    {...target,url:"https://music.yandex.ru/?nonce="+nonce},
    {...target,url:origin+"/?nonce="+nonce+"&token=private"},
    {...target,title:"Яндекс Музыка"},
    {...target,type:"service_worker"},
    {...target,url:origin+"/?nonce="+("b".repeat(32))}
  ]) assert.equal(exactFixtureTarget(wrong,origin,nonce),false);
  assert.equal(exactFixtureTarget(target,"http://0.0.0.0:43121",nonce),false);
});
test("W11 JSON-NUL framing tolerates split responses and unrelated CDP events",async()=>{
  const writes=new PassThrough(),reads=new PassThrough();
  const c=createPipeTransport(writes,reads);
  const pending=c.send("Browser.getVersion");
  const chunk=await new Promise(resolve=>writes.once("data",resolve));
  assert.equal(chunk.at(-1),0);
  const request=JSON.parse(chunk.subarray(0,-1).toString());
  assert.equal(request.method,"Browser.getVersion");
  const response=Buffer.from(JSON.stringify({id:request.id,result:{product:"Electron/44"}})+"\0");
  reads.write('{"method":"Target.targetInfoChanged","params":{}}\0');
  reads.write(response.subarray(0,6));
  reads.write(response.subarray(6));
  const result=await pending;
  assert.equal(result.product,"Electron/44");
  assert.equal(c.stats().inflight,0);
  c.close();
});
test("W11 rejects CDP commands outside narrow fixture allowlist",()=>{
  const c=createPipeTransport(new PassThrough(),new PassThrough());
  for(const method of ["Network.enable","Storage.getCookies","Browser.setDownloadBehavior",
    "Runtime.callFunctionOn","Fetch.enable","Debugger.enable"])
    assert.throws(()=>c.send(method),/W11_NOT_ALLOWED_CDP_METHOD/);
  c.close();
});
test("W11 session ID mismatch fails closed",async()=>{
  const write=new PassThrough(),read=new PassThrough();
  const c=createPipeTransport(write,read);
  const p=c.send("Runtime.enable",{}, {sessionId:"session_A"});
  const frame=JSON.parse((await new Promise(resolve=>write.once("data",resolve))).toString("utf8").split("\0")[0]);
  read.write(JSON.stringify({id:frame.id,sessionId:"session_B",result:{}})+"\0");
  await assert.rejects(p,/W11_SESSION_ID_MISMATCH/);
});
test("W11 close rejects pending commands and clears state",async()=>{
  const c=createPipeTransport(new PassThrough(),new PassThrough());
  const p=c.send("Target.getTargets");
  c.close();
  await assert.rejects(p,/W11_PIPE_CLOSED/);
  assert.equal(c.stats().inflight,0);
});
test("W11 malformed JSON-NUL frame fails closed",async()=>{
  const writer=new PassThrough(), reader=new PassThrough();
  const c=createPipeTransport(writer,reader);
  const pending=c.send("Browser.getVersion");
  reader.write(Buffer.concat([Buffer.from("{malformed-frame"), Buffer.from([0])]));
  await assert.rejects(pending,/W11_INVALID_CDP_FRAME/);
  assert.equal(c.stats().closed,true);
});

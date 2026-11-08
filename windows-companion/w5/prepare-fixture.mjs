import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import vm from "node:vm";
import path from "node:path";
import { setDefaultResultOrder } from "node:dns";
import { setDefaultAutoSelectFamilyAttemptTimeout } from "node:net";

setDefaultResultOrder("ipv4first");
setDefaultAutoSelectFamilyAttemptTimeout(3000);

const output = path.resolve(process.argv[2] || "windows-companion/w5/out");
await mkdir(output, { recursive: true });
const get = async url => {
  let last;
  for (let attempt = 0; attempt < 4; attempt++) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(30000) });
      if (!response.ok) throw Error("Fixture download HTTP " + response.status);
      return await response.text();
    } catch (error) {
      last = error;
      if (attempt < 3) await new Promise(resolve => setTimeout(resolve, (attempt + 1) * 500));
    }
  }
  throw last;
};
const manifest = JSON.parse(await readFile(new URL("asset-manifest.json", import.meta.url), "utf8"));
let html, urls;
if (process.env.CELIKOM_RESEARCH_ASSET_CACHE) {
  html = "cached public homepage";
  urls = JSON.parse(await readFile(path.join(process.env.CELIKOM_RESEARCH_ASSET_CACHE, "script-urls.json"), "utf8"));
} else if (process.env.CELIKOM_NATIVE_LIVE_ASSETS === "1") {
  html = await get("https://music.yandex.ru/");
  urls = [...new Set([...html.matchAll(/<script[^>]+src="([^"]+)/g)].map(m => m[1]))];
} else {
  html = "pinned public frontend " + manifest.frontend;
  urls = manifest.assets.map(asset => asset.url);
}
const factories = {}, context = { self: { webpackChunk_N_E: [] } }, provenance = [];
context.self.webpackChunk_N_E.push = chunk => Object.assign(factories, chunk[1]);
vm.createContext(context);
for (let offset = 0; offset < urls.length; offset += 8) {
  const batch = await Promise.all(urls.slice(offset, offset + 8).map(async (url, j) => {
    if (!url.includes("/_next/static/chunks/")) return null;
    const source = process.env.CELIKOM_RESEARCH_ASSET_CACHE
      ? await readFile(path.join(process.env.CELIKOM_RESEARCH_ASSET_CACHE, "web-assets", (offset + j) + ".js"), "utf8")
      : await get(new URL(url, "https://music.yandex.ru/").href);
    if (!source.startsWith("(self.webpackChunk_N_E") && !source.startsWith('"use strict";(self.webpackChunk_N_E')) return null;
    const expected = manifest.assets.find(asset => asset.url === url)?.sha256;
    if (expected && createHash("sha256").update(source).digest("hex") !== expected) throw Error("Public fixture asset hash mismatch");
    return { source, url };
  }));
  for (const item of batch.filter(Boolean)) {
    vm.runInContext(item.source, context, { timeout: 2000 });
    provenance.push({ url: item.url, sha256: createHash("sha256").update(item.source).digest("hex") });
  }
}
const sourceFactory = Object.entries(factories).find(([, f]) => f.toString().includes('"downloadInfoSource"') && f.toString().includes("getQueryParamsString"));
if (!sourceFactory) throw Error("Current Yandex source class not found");
const [sourceModule, sourceFn] = sourceFactory, sourceText = sourceFn.toString();
const sourceName = sourceText.match(/class ([\w$]+)\{get src\(\)\{[\s\S]*?get mirrorUrls\(\)/)?.[1];
const args = sourceText.match(/^\(([^)]+)\)=>/)?.[1].split(",");
if (!sourceName || !args || args.length !== 3) throw Error("Unsupported source factory shape");
/* Test-only export exposes an otherwise private class. Its class body is unchanged.
   Downloaded third-party code is a transient fixture, never checked into git. */
const exportBody = sourceText.slice(0, -1) + `;Object.defineProperty(${args[1]},"__testNativeSource",{value:${sourceName},enumerable:true});}`;
const entries = Object.entries(factories).map(([id, f]) => JSON.stringify(id) + ":" + (id === sourceModule ? exportBody : f.toString()));
const loader = `
const factories={${entries.join(",\n")}},cache={};
function req(id){if(cache[id])return cache[id].exports;if(!factories[id])throw Error('missing fixture module '+id);const m=cache[id]={exports:{}};try{factories[id](m,m.exports,req)}catch(e){delete cache[id];throw e}return m.exports}
req.d=(e,d)=>{for(const k in d)if(!Object.hasOwn(e,k))Object.defineProperty(e,k,{enumerable:true,get:d[k]})};
req.r=e=>Object.defineProperty(e,'__esModule',{value:true});req.o=(o,k)=>Object.hasOwn(o,k);req.n=m=>{const g=m&&m.__esModule?()=>m.default:()=>m;req.d(g,{a:g});return g};req.g=globalThis;req.m=factories;req.nmd=m=>m;
req.t=(v,mode)=>{if(mode&1)v=req(v);if(mode&8)return v;if(v&&typeof v==='object'&&(mode&4)&&v.__esModule)return v;const ns=Object.create(null);req.r(ns);Object.defineProperty(ns,'default',{enumerable:true,value:v});if(mode&2&&typeof v!=='string')for(const k in v)Object.defineProperty(ns,k,{enumerable:true,get:()=>v[k]});return ns};
const chunks=[];chunks.push=chunk=>{Object.assign(factories,chunk[1]);if(chunk[0]?.some(id=>typeof id==='symbol'))chunk[2]?.(req);return chunks.length};
globalThis.webpackChunk_N_E=chunks;
globalThis.__nativeFixture={req,sourceModule:${JSON.stringify(sourceModule)}};
`;
await writeFile(path.join(output, "webpack-fixture.js"), loader + "\n");
await writeFile(path.join(output, "provenance.json"), JSON.stringify({ fetchedAt: new Date().toISOString(), modules: Object.keys(factories).length, privateClassExportForTestOnly: true, assets: provenance }, null, 2) + "\n");
console.log("W5 prepared pinned public Yandex resource/source classes (test-only)", Object.keys(factories).length, "modules");

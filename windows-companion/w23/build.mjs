import {build} from "esbuild";
import path from "node:path";
import fs from "node:fs/promises";
const root=path.resolve(import.meta.dirname);
const outdir=path.join(root,"dist");
await fs.mkdir(outdir,{recursive:true});
await build({
  entryPoints:[path.join(root,"renderer-entry.mjs")],
  bundle:true,format:"iife",platform:"browser",target:"chrome120",
  minify:true,legalComments:"none",
  outfile:path.join(outdir,"renderer.js")
});
await fs.copyFile(path.join(root,"host.cjs"),path.join(outdir,"host.cjs"));
const content=await fs.readFile(path.join(outdir,"renderer.js"),"utf8");
if(!content.includes("__celikomBridgeNativeDrain")||
   !content.includes("get-file-info")||content.length<3500)
  throw Error("W23_INVALID_RENDERER_BUNDLE");
console.log("W23_RENDERER_BUNDLE_PASS",content.length);

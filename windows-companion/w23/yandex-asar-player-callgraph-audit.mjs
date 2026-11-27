import { parse } from "acorn";
import fs from "node:fs";
import crypto from "node:crypto";

const [asarPath, reportPath] = process.argv.slice(2);
if (!asarPath || !reportPath) throw new Error("W188_USAGE");
const bytes = fs.readFileSync(asarPath);
if (bytes.length < 16 || bytes.readUInt32LE(0) !== 4) throw new Error("W188_ASAR_INVALID");
const headerLength = bytes.readUInt32LE(12);
if (!headerLength || headerLength > 30 * 1024 * 1024) throw new Error("W188_ASAR_HEADER_INVALID");
const dataStart = 16 + ((headerLength + 3) & ~3);
if (dataStart > bytes.length) throw new Error("W188_ASAR_DATA_START_INVALID");
const header = JSON.parse(bytes.subarray(16, 16 + headerLength).toString("utf8"));
if (!header?.files || typeof header.files !== "object") throw new Error("W188_ASAR_TREE_INVALID");
const sha256 = value => crypto.createHash("sha256").update(value).digest("hex");


const TARGET_MODULES = new Set(["7123","7695","92632","96820","72882"]);
function astWalk(node, visit, parent = null) {
  if (!node || typeof node !== "object" || typeof node.type !== "string") return;
  visit(node, parent);
  for (const [key, value] of Object.entries(node)) {
    if (key === "start" || key === "end" || key === "loc" || key === "range") continue;
    if (Array.isArray(value)) {
      for (const item of value) astWalk(item, visit, node);
    } else if (value && typeof value === "object" && typeof value.type === "string") {
      astWalk(value, visit, node);
    }
  }
}
function astName(node) {
  if (!node) return "";
  if (node.type === "Identifier") return node.name;
  if (node.type === "ThisExpression") return "this";
  if (node.type === "Super") return "super";
  if (node.type === "MemberExpression") {
    const left = astName(node.object);
    const right = node.computed ? (node.property?.value ?? "?") : node.property?.name;
    return left && right ? left + "." + right : left;
  }
  if (node.type === "CallExpression") return astName(node.callee);
  return node.type;
}
function astAnalyzeFactory(fn, id, path, source) {
  const requireName = fn.params?.[2]?.type === "Identifier" ? fn.params[2].name : "";
  const deps = new Set(), imports = [], calls = [], classes = [], assignments = [], constructions = [];
  astWalk(fn.body, node => {
    if (node.type === "CallExpression" && requireName &&
        node.callee?.type === "Identifier" && node.callee.name === requireName) {
      const arg = node.arguments?.[0];
      if (arg?.type === "Literal" && /^\d+$/.test(String(arg.value)))
        deps.add(String(arg.value));
    }
    if (node.type === "VariableDeclarator" && node.id?.type === "Identifier" &&
        node.init?.type === "CallExpression" && requireName &&
        node.init.callee?.type === "Identifier" && node.init.callee.name === requireName) {
      const arg = node.init.arguments?.[0];
      if (arg?.type === "Literal" && /^\d+$/.test(String(arg.value)))
        imports.push({local:node.id.name,moduleId:String(arg.value)});
    }
    if (node.type === "CallExpression" && node.callee?.type === "MemberExpression") {
      const method = node.callee.computed ? node.callee.property?.value : node.callee.property?.name;
      if (["getFileInfo","getFileInfoBatch","getMediaSource","reloadEntity"].includes(method))
        calls.push({method,receiver:astName(node.callee.object)});
    }
    if (node.type === "NewExpression")
      constructions.push(astName(node.callee));
    if (node.type === "ClassDeclaration" || node.type === "ClassExpression") {
      const methods = (node.body?.body || []).filter(x => x.type === "MethodDefinition")
        .map(x => ({name:x.key?.name ?? x.key?.value ?? "",kind:x.kind,static:x.static === true}));
      classes.push({name:node.id?.name || "",base:astName(node.superClass),methods});
    }
    if (node.type === "AssignmentExpression" && node.left?.type === "MemberExpression" &&
        node.left.object?.type === "ThisExpression") {
      assignments.push({property:node.left.property?.name ?? node.left.property?.value ?? "",
        valueType:node.right?.type || "", valueName:astName(node.right)});
    }
  });
  const bodyText = source.slice(fn.start, fn.end);
  const hasResourceMethod = /getFileInfo|getFileInfoBatch|getMediaSource|reloadEntity/.test(bodyText);
  const related = TARGET_MODULES.has(id) || [...deps].some(x=>TARGET_MODULES.has(x)) ||
    calls.length > 0 || hasResourceMethod;
  if (!related) return null;
  return {
    path,moduleId:id,requireParameter:requireName,dependencies:[...deps].slice(0,160),
    imports:imports.slice(0,80),exports:exportKeys(bodyText),
    classes:classes.slice(0,40),thisAssignments:assignments.slice(0,100),
    constructions:constructions.slice(0,80),calls:calls.slice(0,160)
  };
}
function astAuditFile(source, path) {
  if (!/(?:7123|7695|92632|96820|72882)/.test(source)) return [];
  let ast;
  try { ast = parse(source,{ecmaVersion:"latest",sourceType:"script",allowReturnOutsideFunction:true,allowHashBang:true}); }
  catch { return []; }
  const found = [];
  astWalk(ast, node => {
    if (node.type !== "Property" || node.computed || !node.value ||
        !["FunctionExpression","ArrowFunctionExpression"].includes(node.value.type)) return;
    const raw = node.key?.type === "Literal" ? node.key.value :
      node.key?.type === "Identifier" ? node.key.name : "";
    const id = String(raw);
    if (!/^\d{1,6}$/.test(id)) return;
    const item = astAnalyzeFactory(node.value,id,path,source);
    if (item) found.push(item);
  });
  return found;
}

function moduleFactories(source) {
  const pattern = /(?:^|[,{])\s*["']?([0-9]{1,6})["']?\s*:\s*(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)/g;
  return [...source.matchAll(pattern)].map(match => ({
    id: match[1], start: match.index, end: pattern.lastIndex
  }));
}
function moduleForIndex(source, factories, index) {
  let selected = null, next = null;
  for (const item of factories) {
    if (item.start <= index) selected = item;
    else { next = item; break; }
  }
  if (!selected) return { id: null, source };
  return { id: selected.id, source: source.slice(selected.start, next ? next.start : source.length) };
}
function methodShapes(source, name) {
  const patterns = [
    new RegExp(name+"\\s*\\(([^)]*)\\)\\s*\\{", "g"),
    new RegExp(name+"\\s*:\\s*(?:async\\s*)?function\\s*\\(([^)]*)\\)", "g"),
    new RegExp(name+"\\s*:\\s*(?:async\\s*)?\\(([^)]*)\\)\\s*=>", "g"),
    new RegExp(name+"\\s*=\\s*(?:async\\s*)?\\(([^)]*)\\)\\s*=>", "g")
  ];
  const result = [];
  for (const pattern of patterns) for (const match of source.matchAll(pattern)) {
    const params = match[1].split(",").map(x => x.trim()).filter(Boolean);
    const body = source.slice(match.index + match[0].length, match.index + match[0].length + 3000);
    result.push({
      parameterCount: params.length,
      readsId: /\.id\b/.test(body),
      readsTrackId: /\.trackId\b/.test(body),
      readsEntity: /\.entity\b/.test(body),
      callsGetFileInfo: /\.getFileInfo\s*\(/.test(body),
      callsGetMediaSource: /\.getMediaSource\s*\(/.test(body),
      returnsFileInfo: /\.fileInfo\b/.test(body),
      returnsDownloadInfo: /\.downloadInfo\b/.test(body)
    });
    if (result.length >= 5) return result;
  }
  return result;
}
function exportKeys(source) {
  const keys = new Set();
  for (const match of source.matchAll(/[A-Za-z_$][\w$]*\.d\(\s*[A-Za-z_$][\w$]*\s*,\s*\{([^}]{0,4000})\}\s*\)/g)) {
    for (const item of match[1].matchAll(/(?:^|,)\s*([A-Za-z_$][\w$]*)\s*:/g)) keys.add(item[1]);
  }
  for (const match of source.matchAll(/\bexports\.([A-Za-z_$][\w$]*)\s*=/g)) keys.add(match[1]);
  return [...keys].slice(0, 40);
}
function moduleDependencies(source) {
  const header = source.slice(0, 240).match(/(?:^|[,{])\s*["']?[0-9]{1,6}["']?\s*:\s*(?:function\s*\(([^)]*)\)|\(([^)]*)\)\s*=>|([A-Za-z_$][\w$]*)\s*=>)/);
  const args = (header?.[1] || header?.[2] || header?.[3] || "")
    .split(",").map(x => x.trim()).filter(Boolean);
  const requireName = args[2] || "";
  if (!requireName || !/^[A-Za-z_$][\w$]*$/.test(requireName)) return [];
  const pattern = new RegExp("\\b" + requireName + "\\s*\\(\\s*([0-9]{1,6})\\s*\\)", "g");
  return [...new Set([...source.matchAll(pattern)].map(x => x[1]))].slice(0, 100);
}
function callReceivers(source, name) {
  const pattern = new RegExp("([A-Za-z_$][\\w$]*(?:\\.[A-Za-z_$][\\w$]*)*)\\." + name + "\\s*\\(", "g");
  return [...new Set([...source.matchAll(pattern)].map(x => x[1]))].slice(0, 30);
}
function factoryArgs(source) {
  const header = source.slice(0, 500).match(/(?:^|[,{])\s*["']?[0-9]{1,6}["']?\s*:\s*(?:function\s*\(([^)]*)\)|\(([^)]*)\)\s*=>|([A-Za-z_$][\w$]*)\s*=>)/);
  return (header?.[1] || header?.[2] || header?.[3] || "")
    .split(",").map(x => x.trim()).filter(Boolean);
}
function classDeclarations(source) {
  return [...source.matchAll(/\bclass\s+([A-Za-z_$][\w$]*)(?:\s+extends\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*))?/g)]
    .slice(0, 40).map(x => ({name:x[1], base:x[2] || ""}));
}
function prototypeAssignments(source) {
  return [...source.matchAll(/([A-Za-z_$][\w$]*)\.prototype\.([A-Za-z_$][\w$]*)\s*=/g)]
    .slice(0, 80).map(x => ({owner:x[1], method:x[2]}));
}
function constructorPropertyAssignments(source) {
  return [...source.matchAll(/this\.([A-Za-z_$][\w$]*)\s*=\s*(?:new\s+)?([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)/g)]
    .slice(0, 80).map(x => ({property:x[1], valueType:x[2]}));
}
function summarizeModule(path, id, source) {
  const has = name => source.includes(name);
  return {
    path, moduleId: id, factoryArgs: factoryArgs(source),
    exportKeys: exportKeys(source),
    webpackDependencies: moduleDependencies(source),
    classDeclarations: classDeclarations(source),
    prototypeAssignments: prototypeAssignments(source),
    constructorPropertyAssignments: constructorPropertyAssignments(source),
    getFileInfoCallReceivers: callReceivers(source, "getFileInfo"),
    getFileInfoBatchCallReceivers: callReceivers(source, "getFileInfoBatch"),
    getMediaSourceCallReceivers: callReceivers(source, "getMediaSource"),
    reloadEntityCallReceivers: callReceivers(source, "reloadEntity"),
    methodCounts: {
      getFileInfo: (source.match(/getFileInfo/g) || []).length,
      getFileInfoBatch: (source.match(/getFileInfoBatch/g) || []).length,
      getMediaSource: (source.match(/getMediaSource/g) || []).length,
      reloadEntity: (source.match(/reloadEntity/g) || []).length
    },
    hasStateGetter: /get\s+state\s*\(/.test(source),
    hasReloadEntity: has("reloadEntity"),
    hasGetFileInfo: has("getFileInfo"),
    hasGetMediaSource: has("getMediaSource"),
    getFileInfoShapes: methodShapes(source, "getFileInfo"),
    getMediaSourceShapes: methodShapes(source, "getMediaSource"),
    reloadEntityShapes: methodShapes(source, "reloadEntity")
  };
}

const relevant = [];
const astRelevant = [];
const pinned = [];
let scanned = 0;
function walk(files, prefix = "") {
  for (const [name, node] of Object.entries(files)) {
    const path = prefix ? prefix + "/" + name : name;
    if (!node || typeof node !== "object") continue;
    if (node.files && typeof node.files === "object") { walk(node.files, path); continue; }
    if (node.unpacked || !/\.(?:js|cjs|mjs)$/i.test(path)) continue;
    const size = Number(node.size), offset = Number(node.offset);
    if (!Number.isSafeInteger(size) || size < 0 || size > 32*1024*1024 ||
        !Number.isSafeInteger(offset) || offset < 0 || dataStart+offset+size > bytes.length) continue;
    const source = bytes.subarray(dataStart+offset, dataStart+offset+size).toString("utf8");
    scanned++;
    astRelevant.push(...astAuditFile(source,path));
    const factories = moduleFactories(source);
    for (let i=0;i<factories.length;i++) {
      const current=factories[i], next=factories[i+1];
      const body=source.slice(current.start,next?next.start:source.length);
      const hasFile=body.includes("getFileInfo");
      const hasMedia=body.includes("getMediaSource");
      const hasReload=body.includes("reloadEntity");
      if (current.id==="7123") pinned.push(summarizeModule(path,current.id,body));
      if (hasFile || hasMedia || hasReload) {
        relevant.push(summarizeModule(path,current.id,body));
      }
    }
  }
}
walk(header.files);
relevant.sort((a,b)=>
  Number(b.hasGetFileInfo)-Number(a.hasGetFileInfo) ||
  Number(b.hasGetMediaSource)-Number(a.hasGetMediaSource) ||
  Number(b.hasReloadEntity)-Number(a.hasReloadEntity) ||
  a.path.localeCompare(b.path) || a.moduleId.localeCompare(b.moduleId));
const report = {
  schema: 1,
  purpose: "read-only module identity and call-shape audit of signed official Yandex 5.129.0 app.asar",
  archiveBytes: bytes.length,
  archiveSha256: sha256(bytes),
  scannedJsFiles: scanned,
  pinnedModule7123: pinned,
  playerMethodModules: relevant.slice(0,100),
  astModuleGraph: astRelevant.slice(0,250)
};
fs.writeFileSync(reportPath,JSON.stringify(report,null,2),{flag:"w"});
const output = {
  archiveBytes: report.archiveBytes, archiveSha256: report.archiveSha256,
  scannedJsFiles: scanned, pinnedModule7123: pinned,
  playerMethodModules: relevant.slice(0,60),
  astModuleGraph: astRelevant.slice(0,250)
};
console.log("W188_YANDEX_51280_PLAYER_CALLGRAPH_AUDIT",JSON.stringify(output));
if (!relevant.some(x=>x.hasGetFileInfo) || !relevant.some(x=>x.hasGetMediaSource))
  throw new Error("W188_PLAYER_METHOD_MODULES_NOT_FOUND");

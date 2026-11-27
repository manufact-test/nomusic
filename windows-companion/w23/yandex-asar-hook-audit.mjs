import fs from "node:fs";
import crypto from "node:crypto";

const asarPath = process.argv[2];
const reportPath = process.argv[3];
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
const terms = [
  ["endpoint_get_file_info", '"get-file-info"'],
  ["endpoint_file_info_path", '"resources/v2/file-info"'],
  ["method_getFileInfo", "getFileInfo"],
  ["method_getFileInfoBatch", "getFileInfoBatch"],
  ["method_reloadEntity", "reloadEntity"],
  ["method_getMediaSource", "getMediaSource"],
  ["webpack_runtime", "webpackChunk_N_E"]
];
const hits = [];
let scanned = 0;
function moduleFactories(source) {
  const pattern = /(?:^|[,{])\s*["']?([0-9]{1,6})["']?\s*:\s*(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)/g;
  return [...source.matchAll(pattern)].map(match => ({
    id: match[1],
    start: match.index,
    end: pattern.lastIndex
  }));
}
function moduleForIndex(source, index) {
  const factories = moduleFactories(source);
  let selected = null, next = null;
  for (const item of factories) {
    if (item.start <= index) selected = item;
    else { next = item; break; }
  }
  if (!selected) return { id: null, source };
  return {
    id: selected.id,
    source: source.slice(selected.start, next ? next.start : source.length)
  };
}
function methodShapes(source, name) {
  const patterns = [
    new RegExp(name+"\\s*\\(([^)]*)\\)\\s*\\{", "g"),
    new RegExp(name+"\\s*:\\s*(?:async\\s*)?function\\s*\\(([^)]*)\\)", "g"),
    new RegExp(name+"\\s*:\\s*(?:async\\s*)?\\(([^)]*)\\)\\s*=>", "g"),
    new RegExp(name+"\\s*=\\s*(?:async\\s*)?\\(([^)]*)\\)\\s*=>", "g")
  ];
  const shapes = [];
  for (const pattern of patterns) {
    for (const match of source.matchAll(pattern)) {
      const parameters = match[1].split(",").map(x => x.trim()).filter(Boolean);
      const body = source.slice(match.index + match[0].length, match.index + match[0].length + 2400);
      shapes.push({
        parameterCount: parameters.length,
        parameterNames: parameters.filter(x => /^[A-Za-z_$][\w$]*$/.test(x)),
        readsTrackId: /\.trackId\b/.test(body),
        readsTrackIds: /\.trackIds\b/.test(body),
        readsId: /\.id\b/.test(body),
        readsIds: /\.ids\b/.test(body),
        readsTrack_id: /\.track_id\b/.test(body),
        returnsFileInfo: /\.fileInfo\b/.test(body),
        returnsDownloadInfo: /\.downloadInfo\b/.test(body)
      });
      if (shapes.length >= 4) return shapes;
    }
  }
  return shapes;
}
function callShapes(source, name) {
  const pattern = new RegExp(
    "([A-Za-z_$][\\w$]*(?:\\.[A-Za-z_$][\\w$]*)*)\\."+name+"\\s*\\(", "g");
  const shapes = [];
  for (const match of source.matchAll(pattern)) {
    const start = match.index + match[0].length;
    let depth = 1, end = start;
    while (end < source.length && depth > 0) {
      const ch = source[end++];
      if (ch === "(") depth++;
      else if (ch === ")") depth--;
    }
    const args = source.slice(start, Math.max(start, end - 1));
    const first = args.split(",")[0].trim();
    const keys = [...first.matchAll(/([A-Za-z_$][\w$]*)\s*:/g)].map(x => x[1]);
    shapes.push({
      receiver: match[1],
      firstArgumentKind: first.startsWith("{") ? "object" :
        /^[A-Za-z_$][\w$]*\./.test(first) ? "property-access" :
        /^[A-Za-z_$][\w$]*$/.test(first) ? "identifier" : "other",
      firstArgumentPropertyKeys: [...new Set(keys)]
    });
    if (shapes.length >= 8) break;
  }
  return shapes;
}
function walk(files, prefix = "") {
  for (const [name, node] of Object.entries(files)) {
    const path = prefix ? prefix + "/" + name : name;
    if (!node || typeof node !== "object") continue;
    if (node.files && typeof node.files === "object") {
      walk(node.files, path);
      continue;
    }
    if (node.unpacked || !/\.(?:js|cjs|mjs)$/i.test(path)) continue;
    const size = Number(node.size);
    const offset = Number(node.offset);
    if (!Number.isSafeInteger(size) || size < 0 || size > 32 * 1024 * 1024 ||
        !Number.isSafeInteger(offset) || offset < 0 ||
        dataStart + offset + size > bytes.length) continue;
    const source = bytes.subarray(dataStart + offset, dataStart + offset + size).toString("utf8");
    scanned++;
    const counts = {};
    for (const [key, needle] of terms) {
      let count = 0, at = -1, first = -1;
      while ((at = source.indexOf(needle, at + 1)) !== -1) {
        if (first < 0) first = at;
        count++;
      }
      if (count) counts[key] = count;
      if (key.startsWith("endpoint_") && first >= 0) {
        const module = moduleForIndex(source, first);
        counts.endpointModuleId = module.id;
        counts.getFileInfoShapes = methodShapes(module.source, "getFileInfo");
        counts.getFileInfoBatchShapes = methodShapes(module.source, "getFileInfoBatch");
      }
    }
    if (counts.method_getFileInfo) {
      counts.getFileInfoShapes = methodShapes(source, "getFileInfo");
      counts.getFileInfoCalls = callShapes(source, "getFileInfo");
    }
    if (counts.method_getFileInfoBatch) {
      counts.getFileInfoBatchShapes = methodShapes(source, "getFileInfoBatch");
      counts.getFileInfoBatchCalls = callShapes(source, "getFileInfoBatch");
    }
    if (counts.method_reloadEntity) counts.reloadEntityShapes = methodShapes(source, "reloadEntity");
    if (counts.method_getMediaSource) counts.getMediaSourceShapes = methodShapes(source, "getMediaSource");
    if (Object.keys(counts).length) hits.push({ path, size, counts });
  }
}
walk(header.files);
hits.sort((a, b) =>
  (Number(!!b.counts.endpoint_get_file_info) + Number(!!b.counts.endpoint_file_info_path)) -
  (Number(!!a.counts.endpoint_get_file_info) + Number(!!a.counts.endpoint_file_info_path)) ||
  (Number(!!b.counts.method_getFileInfo) - Number(!!a.counts.method_getFileInfo)) ||
  a.path.localeCompare(b.path));
const endpointFiles = hits.filter(item =>
  item.counts.endpoint_get_file_info || item.counts.endpoint_file_info_path);
const methodFiles = hits.filter(item =>
  item.counts.method_getFileInfo || item.counts.method_getFileInfoBatch);
const report = {
  schema: 1,
  purpose: "read-only static audit of official signed Yandex 5.129.0 app.asar",
  archiveBytes: bytes.length,
  archiveSha256: sha256(bytes),
  scannedJsFiles: scanned,
  endpointFiles: endpointFiles.length,
  methodFiles: methodFiles.length,
  endpointCandidates: endpointFiles,
  methodCandidates: methodFiles
};
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), { flag: "w" });
console.log("W188_YANDEX_51280_ASAR_AUDIT", JSON.stringify({
  archiveBytes: report.archiveBytes,
  archiveSha256: report.archiveSha256,
  scannedJsFiles: report.scannedJsFiles,
  endpointFiles: report.endpointFiles,
  methodFiles: report.methodFiles,
  endpointCandidates: report.endpointCandidates.slice(0, 20),
  methodCandidates: report.methodCandidates.slice(0, 20)
}));
if (endpointFiles.length === 0 || methodFiles.length === 0) {
  throw new Error("W188_RESOURCE_API_CANDIDATES_NOT_FOUND");
}

import fs from "node:fs";
import crypto from "node:crypto";

const asarPath = process.argv[2];
const reportPath = process.argv[3];
if (!asarPath || !reportPath) throw new Error("W181_USAGE");
const bytes = fs.readFileSync(asarPath);
if (bytes.length < 16 || bytes.readUInt32LE(0) !== 4) throw new Error("W181_ASAR_INVALID");
const headerLength = bytes.readUInt32LE(12);
if (!headerLength || headerLength > 30 * 1024 * 1024) throw new Error("W181_ASAR_HEADER_INVALID");
const dataStart = 16 + ((headerLength + 3) & ~3);
if (dataStart > bytes.length) throw new Error("W181_ASAR_DATA_START_INVALID");
const header = JSON.parse(bytes.subarray(16, 16 + headerLength).toString("utf8"));
if (!header?.files || typeof header.files !== "object") throw new Error("W181_ASAR_TREE_INVALID");
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
function moduleIdsNear(text, index) {
  const before = text.slice(Math.max(0, index - 24000), index);
  const matches = [...before.matchAll(/(?:^|[,{])\s*([0-9]{1,6})\s*:\s*function\b/g)];
  return [...new Set(matches.slice(-3).map(match => match[1]))];
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
        counts.moduleIdsNearEndpoint = moduleIdsNear(source, first);
      }
    }
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
  purpose: "read-only static audit of official signed Yandex 5.128.0 app.asar",
  archiveBytes: bytes.length,
  archiveSha256: sha256(bytes),
  scannedJsFiles: scanned,
  endpointFiles: endpointFiles.length,
  methodFiles: methodFiles.length,
  endpointCandidates: endpointFiles,
  methodCandidates: methodFiles
};
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), { flag: "w" });
console.log("W181_YANDEX_51280_ASAR_AUDIT", JSON.stringify({
  archiveBytes: report.archiveBytes,
  archiveSha256: report.archiveSha256,
  scannedJsFiles: report.scannedJsFiles,
  endpointFiles: report.endpointFiles,
  methodFiles: report.methodFiles,
  endpointCandidates: report.endpointCandidates.slice(0, 20),
  methodCandidates: report.methodCandidates.slice(0, 20)
}));
if (endpointFiles.length === 0 || methodFiles.length === 0) {
  throw new Error("W181_RESOURCE_API_CANDIDATES_NOT_FOUND");
}

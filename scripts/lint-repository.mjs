import { readFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ignoredDirectories = new Set([".git", "dist", "node_modules", "vendor"]);
const textExtensions = new Set([".cjs", ".css", ".html", ".js", ".json", ".md", ".mjs", ".php", ".ts", ".yaml", ".yml"]);
const secretPatterns = [
  /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/,
  /\bghp_[A-Za-z0-9]{30,}\b/,
  /\bgithub_pat_[A-Za-z0-9_]{40,}\b/,
  /\bAKIA[0-9A-Z]{16}\b/,
  /\bsk-[A-Za-z0-9]{32,}\b/
];

async function walk(directory) {
  const files = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await walk(absolute));
    else files.push(absolute);
  }
  return files;
}

const failures = [];
const files = await walk(root);
for (const file of files) {
  const info = await stat(file);
  if (info.size > 5 * 1024 * 1024) failures.push(`${path.relative(root, file)} exceeds 5 MiB`);
  if (!textExtensions.has(path.extname(file))) continue;

  const relative = path.relative(root, file);
  const source = await readFile(file, "utf8");
  if (source.includes("\r\n")) failures.push(`${relative} uses CRLF`);
  if (source.length > 0 && !source.endsWith("\n")) failures.push(`${relative} has no final newline`);
  if (source.includes("\0")) failures.push(`${relative} contains a NUL byte`);
  for (const pattern of secretPatterns) {
    if (pattern.test(source)) failures.push(`${relative} matches a forbidden credential pattern`);
  }
  if (file.endsWith(".json")) {
    try {
      JSON.parse(source);
    } catch (error) {
      failures.push(`${relative} is invalid JSON: ${error.message}`);
    }
  }
}

const forbiddenFiles = [".env", "id_rsa", "id_ed25519"];
for (const name of forbiddenFiles) {
  const info = await stat(path.join(root, name)).catch(() => null);
  if (info) failures.push(`${name} must not be committed`);
}

if (failures.length) {
  throw new Error(`Repository lint failed:\n- ${failures.join("\n- ")}`);
}

console.log(`Repository lint passed for ${files.length} files.`);

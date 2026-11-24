import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const TABLE_NAME = /^[a-z][a-z0-9_]{0,63}$/;
const REQUIRED_TABLES = [
  "schema_migrations",
  "tracks",
  "audio_assets",
  "track_replacements"
];

export function parseSnapshotTableCountsJson(source) {
  let value;
  try {
    value = JSON.parse(source);
  } catch {
    throw new Error("W5_RESTORE_COUNTS_JSON_INVALID");
  }
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("W5_RESTORE_COUNTS_SHAPE_INVALID");

  const entries = Object.entries(value);
  if (entries.length < REQUIRED_TABLES.length || entries.length > 100)
    throw new Error("W5_RESTORE_COUNTS_SIZE_INVALID");

  for (const table of REQUIRED_TABLES) {
    if (!Object.hasOwn(value, table))
      throw new Error("W5_RESTORE_COUNTS_REQUIRED_TABLE_MISSING");
  }
  for (const [table, count] of entries) {
    if (!TABLE_NAME.test(table) || !Number.isSafeInteger(count) || count < 0)
      throw new Error("W5_RESTORE_COUNTS_ENTRY_INVALID");
  }

  return entries
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([table, count]) => table + "\t" + String(count))
    .join("\n") + "\n";
}

if (process.argv[1] &&
    import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    if (process.argv.length !== 3) throw new Error("W5_RESTORE_COUNTS_ARGUMENTS_INVALID");
    process.stdout.write(parseSnapshotTableCountsJson(
      fs.readFileSync(process.argv[2], "utf8")
    ));
  } catch {
    process.stderr.write("W5_RESTORE_COUNTS_INVALID\n");
    process.exitCode = 2;
  }
}

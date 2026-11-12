/** Cross-language compatibility test using the ACTUAL unchanged PHP ByteRange. 
 * No network, account, backend configuration, Yandex binary or mock decoder.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve as resolvePath } from "node:path";
import { buildByteRangeHeaders, validateRangeResponse } from "./source-contract.mjs";

const base = dirname(fileURLToPath(import.meta.url));
const phpByteRange = resolvePath(base, "../../server/src/Http/ByteRange.php");
const actualPhp = [
  'require $argv[1];',
  'try {',
  '  [$start,$end] = \\Celikom\\Http\\ByteRange::parse($argv[2], (int)$argv[3]);',
  '  echo json_encode(["status"=>206,"start"=>$start,"end"=>$end], JSON_THROW_ON_ERROR);',
  '} catch (\\InvalidArgumentException $e) {',
  '  echo json_encode(["status"=>416], JSON_THROW_ON_ERROR);',
  '}'
].join("\n");

function invokeRealPhp(range, length) {
  const raw = execFileSync("php", ["-r", actualPhp, phpByteRange, range, String(length)],
    { encoding: "utf8", timeout: 5000, maxBuffer: 4096 });
  return JSON.parse(raw);
}

function realPhpRange(start, end, length) {
  return invokeRealPhp(buildByteRangeHeaders(start, end).Range, length);
}

function actualPhpResponse(start, end, size, etag) {
  const php = realPhpRange(start, end, size);
  if (php.status === 416) return {
    status: 416, headers: { "content-range": `bytes */${size}` }
  };
  return { status: 206, headers: {
    "content-range": `bytes ${php.start}-${php.end}/${size}`,
    "content-length": String(php.end - php.start + 1),
    etag
  }};
}

test("real unchanged PHP ByteRange exact interval and EOF clipping match Android contract", () => {
  const size = 16384;
  const witness = {size, etag: '"sha256-v3"'};
  const scenarios = [
    [0, 0], [0, 1023], [1024, 2047], [8192, 12287],
    [16000, 20000], [16383, null], [10000, null]
  ];
  for (const [start, end] of scenarios) {
    const response = actualPhpResponse(start, end, size, witness.etag);
    const verified = validateRangeResponse(response, start, end, witness);
    assert.equal(verified.ok, true, `PHP/JS incompatible at bytes=${start}-${end ?? ""}`);
    assert.equal(verified.start, start);
    assert.equal(verified.end, Math.min(end ?? size - 1, size - 1));
    assert.equal(verified.total, size);
  }
  const invalid = actualPhpResponse(16384, null, size, witness.etag);
  assert.equal(invalid.status, 416);
  assert.equal(validateRangeResponse(invalid, 16384, null, witness).code,
    "RANGE_UNSATISFIABLE");
  assert.throws(() => buildByteRangeHeaders(2048, 1024), /INVALID_BYTE_RANGE/);
  assert.equal(invokeRealPhp("bytes=2048-1024", size).status, 416);
});

test("real PHP metadata boundary catches a short-but-plausible 206 intermediary", () => {
  const witness = {size: 16384, etag: '"sha256-v3"'};
  const good = actualPhpResponse(1024, 8191, witness.size, witness.etag);
  assert.equal(validateRangeResponse(good, 1024, 8191, witness).ok, true);
  const shortBodyClaim = { ...good, headers: {
    "content-range": "bytes 1024-4095/16384",
    "content-length": "3072",
    "etag": witness.etag
  }};
  assert.equal(validateRangeResponse(shortBodyClaim, 1024, 8191, witness).code,
    "RANGE_MISMATCH");
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectMp3} from '../dist/unpacked/upload/mp3-duration.js';
import {metadataCases} from './fixtures/mp3-metadata-fixtures.mjs';

for (const {name,source,expected} of metadataCases()) {
  test('MP3 metadata matrix: '+name,()=>{
    const prepared=inspectMp3(source);
    if(expected===null){assert.equal(prepared,null);return;}
    assert.ok(prepared,'recognized metadata must preserve usable frames');
    assert.deepEqual(Buffer.from(prepared.bytes),expected);
    assert.deepEqual(inspectMp3(prepared.bytes).bytes,prepared.bytes,'normalization is idempotent');
  });
}

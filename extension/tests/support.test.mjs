import test from 'node:test';
import assert from 'node:assert/strict';
import { supportEmail, supportMessage } from '../dist/unpacked/popup/support.js';
test('support recipient rejects URI injection and report excludes account/session credentials', () => {
  assert.equal(supportEmail('team@example.org'), 'team@example.org');
  for (const email of ['team@example.org?bcc=other@example.org', 'team@example.org\r\nBcc:other@example.org', 'javascript:alert(1)', null]) assert.equal(supportEmail(email), '');
  const report = supportMessage('Не работает', '0.4.29', {phase:'ERROR',track:{id:'36116709'},account:{email:'private@example.org'},token:'secret',session:{refresh:'secret'},connection:{detail:'secret'}});
  assert.equal(report, "Не работает"); assert.match(report, /Не работает/); assert.doesNotMatch(report, /secret|private@example/);
  assert.ok(supportMessage('a'.repeat(4000), '0.4.29', null).length < 2400);
});

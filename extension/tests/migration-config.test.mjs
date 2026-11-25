import test from 'node:test';
import assert from 'node:assert/strict';
import {apiBuildConfig} from '../scripts/api-build-config.mjs';
import {startAccessError,startAccessMessage} from '../dist/unpacked/auth/start-access.js';
test('production builds default to the migrated API and refuse old hosting without removing loopback fixtures',()=>{
 assert.deepEqual(apiBuildConfig(),{baseUrl:'https://api.celikom.com'});
 assert.deepEqual(apiBuildConfig(''),{baseUrl:'https://api.celikom.com'});
 for(const host of ['darkred-camel-588676.hostingersite.com','lemonchiffon-narwhal-791953.hostingersite.com'])assert.throws(()=>apiBuildConfig('https://'+host),/retired/);
 assert.equal(apiBuildConfig('http://127.0.0.1:8080').baseUrl,'http://127.0.0.1:8080');
 assert.equal(apiBuildConfig('https://fixture.example').baseUrl,'https://fixture.example');
});
test('access denial and expired trial are not reported as a server outage; private details never become text',()=>{
 assert.match(startAccessMessage('trial_inactive'),/Пробный период завершён/);
 assert.match(startAccessMessage('email_unverified'),/Подтвердите почту/);
 assert.match(startAccessMessage('auth_timeout'),/не ответил вовремя/);
 assert.equal(startAccessError('invalid_session'),'sign_in_required');
 for(const code of ['password=secret','__proto__','constructor',null]){
  assert.equal(startAccessError(code),'auth_unavailable');assert.doesNotMatch(startAccessMessage(code),/secret|__proto__/);
 }
});

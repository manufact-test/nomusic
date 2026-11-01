import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

test('Promo form groups lifetime and conditionally enables Moscow deadline', () => {
  const controls = Object.fromEntries(['forever','discount_percent','duration_days','activation_window','activation_deadline'].map(name => [name,{value:'',checked:false,addEventListener(type,fn){this[type]=fn;}}]));
  controls.discount_percent.value='100';
  const days={},deadline={};
  const form={elements:{namedItem:name=>controls[name]},querySelector:s=>s==='[data-promo-days]'?days:deadline,addEventListener(type,fn){this[type]=fn;}};
  vm.runInNewContext(readFileSync(new URL('../src/Promo/promo-form.js',import.meta.url),'utf8'),{document:{querySelectorAll:()=>[form]}});
  assert.equal(deadline.hidden,true);assert.equal(controls.activation_deadline.disabled,true);
  controls.activation_window.value='fixed';form.change();
  assert.equal(deadline.hidden,false);assert.equal(controls.activation_deadline.required,true);assert.equal(controls.activation_deadline.disabled,false);
  controls.activation_window.value='unlimited';form.change();assert.equal(deadline.hidden,true);assert.equal(controls.activation_deadline.disabled,true);
  controls.forever.checked=true;form.change();assert.equal(days.hidden,true);assert.equal(controls.duration_days.disabled,true);
  controls.discount_percent.value='20';controls.discount_percent.input();assert.equal(controls.forever.checked,false);assert.equal(controls.forever.disabled,true);assert.equal(days.hidden,false);assert.equal(controls.duration_days.required,true);
});

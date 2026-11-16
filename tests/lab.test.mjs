import test from 'node:test';
import assert from 'node:assert/strict';
import {step, signature, growth, classify, patterns, toSet} from '../lab/life.mjs';

test('canonical still life, oscillator and glider on an unbounded plane', () => {
  const block = toSet(patterns.block), blinker = toSet(patterns.blinker), glider = toSet(patterns.glider);
  assert.equal(signature(step(block)), signature(block));
  assert.equal(signature(step(step(blinker))), signature(blinker));
  let next = glider;
  for (let i=0;i<4;i++) next=step(next);
  assert.equal(signature(next), signature(toSet(patterns.glider.map(([x,y])=>[x+1,y+1]))));
  assert.equal(step(new Set()).size, 0);
});

test('growth and exact repeated-state detection distinguish moving patterns', () => {
  assert.equal(growth(0, 4), null);
  assert.equal(growth(4, 6), .5);
  assert.equal(growth(4, 0), -1);
  const block = toSet(patterns.block), blink = toSet(patterns.blinker), phase = step(blink);
  assert.equal(classify(new Set(), block, 1, new Map()), 'Extinct');
  assert.equal(classify(block, block, 1, new Map([[signature(block), 0]])), 'Still life');
  assert.equal(classify(blink, phase, 2, new Map([[signature(blink), 0]])), 'Exact cycle · period 2');
  assert.equal(classify(blink, phase, 4, new Map([[signature(blink), 2]])), 'Exact cycle · period 2');
  let glider = toSet(patterns.glider), moving = glider;
  for (let i=0;i<4;i++) moving=step(moving);
  assert.equal(classify(moving, step(step(step(glider))), 4, new Map([[signature(glider), 0]])), 'Evolving');
});

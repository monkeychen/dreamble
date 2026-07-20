import { test } from 'node:test';
import assert from 'node:assert/strict';
import { postSlug, projectSlug, isListed, sortByDateDesc } from '../src/lib/helpers.mjs';

test('postSlug 去掉日期前缀', () => {
  assert.equal(postSlug('2026-07-16-hello-world'), 'hello-world');
});

test('postSlug 兼容带 /index 的 id', () => {
  assert.equal(postSlug('2026-07-16-hello-world/index'), 'hello-world');
});

test('projectSlug 取目录名', () => {
  assert.equal(projectSlug('sample-tool/index'), 'sample-tool');
  assert.equal(projectSlug('sample-tool'), 'sample-tool');
});

test('isListed：public 且非 draft 才列出', () => {
  assert.equal(isListed({ visibility: 'public', draft: false }), true);
  assert.equal(isListed({ visibility: 'unlisted', draft: false }), false);
  assert.equal(isListed({ visibility: 'public', draft: true }), false);
});

test('sortByDateDesc 新文章在前', () => {
  const a = { data: { date: new Date('2026-01-01') } };
  const b = { data: { date: new Date('2026-06-01') } };
  assert.deepEqual([a, b].sort(sortByDateDesc), [b, a]);
});

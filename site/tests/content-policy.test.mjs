import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  frontmatterDate,
  validatePostRecords,
  validateProjectNames,
} from '../scripts/lib/content-policy.mjs';

test('frontmatterDate 读取严格 YYYY-MM-DD 日期', () => {
  assert.equal(frontmatterDate('---\ntitle: T\ndate: 2026-07-20\n---\n正文'), '2026-07-20');
  assert.equal(frontmatterDate('---\ndate: "2026-07-20"\n---\n'), '2026-07-20');
  assert.equal(frontmatterDate('没有 frontmatter'), null);
});

test('文章目录、日期和 slug 全部合规时通过', () => {
  assert.deepEqual(
    validatePostRecords([
      { name: '2026-07-19-first-post', date: '2026-07-19' },
      { name: '2026-07-20-second-post', date: '2026-07-20' },
    ]),
    []
  );
});

test('拒绝非法文章目录和目录日期不一致', () => {
  const errors = validatePostRecords([
    { name: 'bad-directory', date: '2026-07-20' },
    { name: '2026-07-20-valid-slug', date: '2026-07-19' },
  ]);
  assert.match(errors.join('\n'), /bad-directory 不合规/);
  assert.match(errors.join('\n'), /目录日期 2026-07-20.*date 2026-07-19/);
});

test('拒绝会生成同一路由的重复文章 slug', () => {
  const errors = validatePostRecords([
    { name: '2026-07-19-same-slug', date: '2026-07-19' },
    { name: '2026-07-20-same-slug', date: '2026-07-20' },
  ]);
  assert.match(errors.join('\n'), /slug 重复/);
  assert.match(errors.join('\n'), /\/posts\/same-slug\//);
});

test('作品目录只接受规范 slug', () => {
  assert.deepEqual(validateProjectNames(['wx-kit', 'tool2']), []);
  assert.match(validateProjectNames(['Bad_Project'])[0], /不合规/);
});

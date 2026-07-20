import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { commitPostImport, hasPostIndex } from '../scripts/lib/import-storage.mjs';

async function fixture() {
  const root = await mkdtemp(path.join(os.tmpdir(), 'dreamble-import-test-'));
  return {
    root,
    postsRoot: path.join(root, 'posts'),
    stagingRoot: path.join(root, 'staging'),
  };
}

test('commitPostImport 完整写入后原子落到正式目录', async (t) => {
  const paths = await fixture();
  t.after(() => rm(paths.root, { recursive: true, force: true }));

  const result = await commitPostImport({
    ...paths,
    title: '测试文章',
    date: '2026-07-20',
    slug: 'atomic-post',
    populate: async (staging) => {
      await writeFile(path.join(staging, 'image.png'), 'image');
      return { markdown: '正文', imgSummary: '图片 1 张' };
    },
  });

  assert.equal(result.dir, path.join(paths.postsRoot, '2026-07-20-atomic-post'));
  assert.match(await readFile(path.join(result.dir, 'index.md'), 'utf8'), /title: "测试文章"/);
  assert.equal(await readFile(path.join(result.dir, 'image.png'), 'utf8'), 'image');
  assert.equal(await hasPostIndex(paths.postsRoot, '2026-07-20-atomic-post'), true);
});

test('commitPostImport 失败时不留下正式目录或暂存半成品', async (t) => {
  const paths = await fixture();
  t.after(() => rm(paths.root, { recursive: true, force: true }));

  await assert.rejects(
    commitPostImport({
      ...paths,
      title: '失败文章',
      date: '2026-07-20',
      slug: 'failed-post',
      populate: async (staging) => {
        await writeFile(path.join(staging, 'partial.png'), 'partial');
        throw new Error('模拟复制失败');
      },
    }),
    /模拟复制失败/
  );

  assert.deepEqual(await readdir(paths.postsRoot), []);
  assert.deepEqual(await readdir(paths.stagingRoot), []);
});

test('hasPostIndex 不把缺少 index.md 的目录判断为完整文章', async (t) => {
  const paths = await fixture();
  t.after(() => rm(paths.root, { recursive: true, force: true }));
  assert.equal(await hasPostIndex(paths.postsRoot, 'missing-post'), false);
});

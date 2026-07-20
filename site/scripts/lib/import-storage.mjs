import { mkdir, mkdtemp, readFile, rename, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buildIndexMd } from './wechat.mjs';

export async function hasPostIndex(postsRoot, directory) {
  try {
    await readFile(path.join(postsRoot, directory, 'index.md'));
    return true;
  } catch (error) {
    if (error.code === 'ENOENT') return false;
    throw error;
  }
}

/** 所有文件先写入 content 外的同盘暂存目录，完整后再原子移动到正式目录。 */
export async function commitPostImport({ postsRoot, stagingRoot, title, date, slug, populate }) {
  await mkdir(postsRoot, { recursive: true });
  await mkdir(stagingRoot, { recursive: true });
  const staging = await mkdtemp(path.join(stagingRoot, `${slug}-`));
  let committed = false;
  try {
    const { markdown, imgSummary } = await populate(staging);
    await writeFile(path.join(staging, 'index.md'), buildIndexMd({ title, date, markdown }));
    const target = path.join(postsRoot, `${date}-${slug}`);
    await rename(staging, target);
    committed = true;
    return { dir: target, imgSummary };
  } finally {
    if (!committed) await rm(staging, { recursive: true, force: true });
  }
}

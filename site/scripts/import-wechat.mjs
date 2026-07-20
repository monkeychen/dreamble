#!/usr/bin/env node
import { copyFile, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import {
  extractArticle,
  htmlToMarkdown,
  collectImages,
  imageFilename,
  localizeImages,
  formatDateCN,
  fromWxkit,
  parseBatchFile,
  findPostDir,
} from './lib/wechat.mjs';
import { commitPostImport, hasPostIndex } from './lib/import-storage.mjs';
import { IMPORT_STAGING_ROOT, POSTS_ROOT } from './lib/project-paths.mjs';

function usage() {
  console.error('用法: npm run import -- <公众号文章URL> <英文slug>');
  console.error('批量: npm run import -- --file <清单文件>   # 每行: <URL> <slug>，支持 # 注释');
  console.error('slug 只能包含小写字母、数字、连字符，例如: my-first-post');
  process.exit(1);
}

const hasWxkit = spawnSync('wx-kit', ['--version'], { encoding: 'utf8' }).status === 0;

async function existingPost(slug) {
  const directories = await readdir(POSTS_ROOT).catch((error) => {
    if (error.code === 'ENOENT') return [];
    throw error;
  });
  return findPostDir(directories, slug);
}

// 通道一（优先）：本机 wx-kit CLI。走真实客户端通道，不受微信反爬影响，
// 图片由 wx-kit 本地化。不可用或失败时返回 null，由调用方回落到通道二。
async function importViaWxkit(url, slug) {
  if (!hasWxkit) return null;
  const tmp = await mkdtemp(path.join(os.tmpdir(), 'wx-kit-import-'));
  try {
    const r = spawnSync(
      'wx-kit',
      ['download', '-u', url, '--formats', 'md,meta', '-o', tmp],
      { encoding: 'utf8' }
    );
    const jsonLine = (r.stdout ?? '').trim().split('\n').filter((l) => l.startsWith('{')).pop();
    if (r.status !== 0 || !jsonLine) {
      console.warn('⚠️  wx-kit 下载失败，回落到内置抓取');
      return null;
    }
    const item = JSON.parse(jsonLine).items?.[0];
    if (!item?.ok || !item.dir) {
      console.warn('⚠️  wx-kit 未成功下载该文章，回落到内置抓取');
      return null;
    }

    const { title, date, body } = fromWxkit(await readFile(path.join(item.dir, 'content.md'), 'utf8'));
    if (!title || !date) {
      console.warn('⚠️  wx-kit 产物缺少标题或日期，回落到内置抓取');
      return null;
    }

    const result = await commitPostImport({
      postsRoot: POSTS_ROOT,
      stagingRoot: IMPORT_STAGING_ROOT,
      title,
      date,
      slug,
      populate: async (staging) => {
        const imagesDirectory = path.join(item.dir, 'images');
        let imageFiles;
        try {
          imageFiles = await readdir(imagesDirectory);
        } catch (error) {
          if (error.code !== 'ENOENT') throw error;
          imageFiles = [];
        }
        for (const file of imageFiles) {
          await copyFile(path.join(imagesDirectory, file), path.join(staging, file));
        }
        return {
          markdown: body,
          imgSummary: `图片 ${imageFiles.length} 张（wx-kit 已本地化）`,
        };
      },
    });
    return { ...result, channel: 'wx-kit' };
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}

// 通道二（回落）：内置抓取。微信对非浏览器请求可能返回反爬页，失败时抛错。
async function importViaFetch(url, slug) {
  let html;
  try {
    const res = await fetch(url, { headers: { 'user-agent': 'Mozilla/5.0' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}。检查链接是否可在浏览器打开`);
    html = await res.text();
  } catch (err) {
    throw new Error(`抓取失败: ${err.cause?.code ?? err.message}`);
  }

  const { title, date, contentHtml } = extractArticle(html);
  if (!contentHtml.trim()) {
    throw new Error(
      '未找到正文（#js_content）——很可能被微信反爬拦截。建议安装 wx-kit（https://github.com/monkeychen/wx-kit），本命令会自动优先使用它'
    );
  }

  const originalMarkdown = htmlToMarkdown(contentHtml);
  const formattedDate = formatDateCN(date);
  const result = await commitPostImport({
    postsRoot: POSTS_ROOT,
    stagingRoot: IMPORT_STAGING_ROOT,
    title,
    date: formattedDate,
    slug,
    populate: async (staging) => {
      const urls = collectImages(originalMarkdown);
      const mapping = [];
      for (const [i, imgUrl] of urls.entries()) {
        const filename = imageFilename(imgUrl, i);
        try {
          const imgRes = await fetch(imgUrl, { headers: { referer: 'https://mp.weixin.qq.com/' } });
          if (!imgRes.ok) {
            console.warn(`⚠️  图片下载失败(HTTP ${imgRes.status})，保留原链接: ${imgUrl}`);
            continue;
          }
          await writeFile(path.join(staging, filename), Buffer.from(await imgRes.arrayBuffer()));
          mapping.push([imgUrl, filename]);
        } catch (err) {
          console.warn(`⚠️  图片下载失败(${err.cause?.code ?? err.message})，保留原链接: ${imgUrl}`);
        }
      }
      return {
        markdown: localizeImages(originalMarkdown, mapping),
        imgSummary: `下载图片 ${mapping.length}/${urls.length} 张`,
      };
    },
  });
  return { ...result, channel: '内置抓取' };
}

/** 导入单篇。失败抛错，由调用方决定中断（单篇模式）或继续（批量模式）。 */
async function importOne(url, slug) {
  const existed = await existingPost(slug);
  if (existed) throw new Error(`slug 已存在：${existed}。请更换 slug，或先人工处理已有内容`);
  return (await importViaWxkit(url, slug)) ?? (await importViaFetch(url, slug));
}

async function runBatch(file) {
  let text;
  try {
    text = await readFile(file, 'utf8');
  } catch {
    console.error(`清单文件不存在或不可读: ${file}`);
    process.exit(1);
  }
  const entries = parseBatchFile(text);
  if (entries.length === 0) {
    console.error('清单为空（没有有效的 "<URL> <slug>" 行）');
    process.exit(1);
  }

  const existingDirs = await readdir(POSTS_ROOT).catch(() => []);
  const ok = [];
  const skipped = [];
  const failed = [];

  for (const [i, entry] of entries.entries()) {
    const label = `[${i + 1}/${entries.length}]`;
    if (entry.error) {
      console.warn(`${label} ✗ ${entry.error}`);
      failed.push({ ...entry, reason: entry.error });
      continue;
    }
    const existed = findPostDir(existingDirs, entry.slug);
    if (existed) {
      if (await hasPostIndex(POSTS_ROOT, existed)) {
        console.log(`${label} ⏭  已存在，跳过: ${existed}`);
        skipped.push(entry);
      } else {
        const reason = `检测到不完整目录 ${existed}（缺少 index.md），请人工检查后重跑`;
        console.warn(`${label} ✗ ${reason}`);
        failed.push({ ...entry, reason });
      }
      continue;
    }
    try {
      const r = await importOne(entry.url, entry.slug);
      console.log(`${label} ✅ ${r.dir}（通道: ${r.channel}，${r.imgSummary}）`);
      ok.push(entry);
      existingDirs.push(path.basename(r.dir));
    } catch (err) {
      console.warn(`${label} ✗ ${entry.slug}: ${err.message}`);
      failed.push({ ...entry, reason: err.message });
    }
  }

  console.log(`\n==> 批量导入完成：成功 ${ok.length}，跳过 ${skipped.length}（已存在），失败 ${failed.length}`);
  if (failed.length > 0) {
    console.log('失败清单（修正后可重跑同一文件，已成功的会自动跳过）:');
    for (const f of failed) console.log(`  - ${f.url ?? f.line}  ${f.slug ?? ''}  ← ${f.reason}`);
  }
  console.log('下一步: npm run dev 预览检查，确认后 npm run publish 发布');
  process.exit(failed.length > 0 ? 1 : 0);
}

const args = process.argv.slice(2);
if (args[0] === '--file' || args[0] === '-f') {
  if (!args[1]) usage();
  await runBatch(args[1]);
} else {
  const [url, slug] = args;
  if (!url || !slug || !/^[a-z0-9-]+$/.test(slug)) usage();
  try {
    const r = await importOne(url, slug);
    console.log(`✅ 已导入: ${r.dir}（通道: ${r.channel}，${r.imgSummary}）`);
    console.log('下一步: npm run dev 预览检查，确认后 npm run publish 发布');
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}

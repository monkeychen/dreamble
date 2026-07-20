import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  extractArticle,
  htmlToMarkdown,
  collectImages,
  imageFilename,
  localizeImages,
  buildIndexMd,
  formatDateCN,
  fromWxkit,
  parseBatchFile,
  findPostDir,
} from '../scripts/lib/wechat.mjs';

const html = await readFile(new URL('./fixtures/wechat-article.html', import.meta.url), 'utf8');

test('extractArticle 取出标题、日期、正文', () => {
  const { title, date, contentHtml } = extractArticle(html);
  assert.equal(title, '测试文章标题');
  assert.equal(date.toISOString().slice(0, 10), '2025-07-16');
  assert.match(contentHtml, /第一段内容/);
  assert.match(contentHtml, /src="https:\/\/mmbiz\.qpic\.cn\/mmbiz_png/);
});

test('htmlToMarkdown 转出图片与段落', () => {
  const { contentHtml } = extractArticle(html);
  const md = htmlToMarkdown(contentHtml);
  assert.match(md, /第一段内容。/);
  assert.match(md, /!\[\]\(https:\/\/mmbiz\.qpic\.cn/);
});

test('collectImages 去重收集图片 URL', () => {
  const md = '![](https://a.com/1?wx_fmt=png) text ![](https://a.com/1?wx_fmt=png) ![](https://a.com/2?wx_fmt=jpeg)';
  assert.deepEqual(collectImages(md), ['https://a.com/1?wx_fmt=png', 'https://a.com/2?wx_fmt=jpeg']);
});

test('imageFilename 依 wx_fmt 决定扩展名', () => {
  assert.equal(imageFilename('https://a.com/1?wx_fmt=png', 0), 'img-01.png');
  assert.equal(imageFilename('https://a.com/2?wx_fmt=jpeg', 1), 'img-02.jpg');
  assert.equal(imageFilename('https://a.com/3', 2), 'img-03.jpg');
});

test('localizeImages 改写为相对路径', () => {
  const md = '![](https://a.com/1?wx_fmt=png)';
  const out = localizeImages(md, [['https://a.com/1?wx_fmt=png', 'img-01.png']]);
  assert.equal(out, '![](./img-01.png)');
});

test('buildIndexMd 生成合规 frontmatter', () => {
  const out = buildIndexMd({ title: '标题：带冒号', date: new Date('2025-07-16'), markdown: '正文' });
  assert.match(out, /^---\n/);
  assert.match(out, /title: "标题：带冒号"/);
  assert.match(out, /date: 2025-07-16/);
  assert.match(out, /source: wechat/);
  assert.match(out, /正文\n$/);
});

test('formatDateCN 按东八区格式化，UTC 前一日晚间应为次日', () => {
  // 2025-07-16T18:00:00Z = 北京时间 2025-07-17 02:00
  assert.equal(formatDateCN(new Date('2025-07-16T18:00:00Z')), '2025-07-17');
  assert.equal(formatDateCN(new Date('2025-07-16T00:00:00Z')), '2025-07-16');
});

test('fromWxkit 解析 wx-kit 产物：标题/日期/正文/图片路径', () => {
  const md = `---
title: "测试标题"
account: "聊哉梦呓"
author: "安哥"
publishTime: "2026-06-17 09:15"
source: "https://mp.weixin.qq.com/s/xxx"
---
# 测试标题

正文第一段。

![](images/img-1.png)
`;
  const { title, date, body } = fromWxkit(md);
  assert.equal(title, '测试标题');
  assert.equal(date, '2026-06-17');
  assert.match(body, /^正文第一段。/);
  assert.match(body, /!\[\]\(\.\/img-1\.png\)/);
  assert.doesNotMatch(body, /# 测试标题/);
});

test('fromWxkit 对缺失 frontmatter 的输入返回空标题', () => {
  const { title, date } = fromWxkit('没有 frontmatter 的内容');
  assert.equal(title, '');
  assert.equal(date, null);
});

test('buildIndexMd 接受 YYYY-MM-DD 字符串日期', () => {
  const out = buildIndexMd({ title: 'T', date: '2026-06-17', markdown: '正文' });
  assert.match(out, /date: 2026-06-17/);
});

test('parseBatchFile 解析清单：URL+slug、注释、空行、非法行', () => {
  const text = `# 我的备份清单
https://mp.weixin.qq.com/s/aaa first-post

https://mp.weixin.qq.com/s/bbb second-post
https://mp.weixin.qq.com/s/ccc Bad_Slug
只有一列
`;
  const entries = parseBatchFile(text);
  assert.equal(entries.length, 4);
  assert.deepEqual(entries[0], { url: 'https://mp.weixin.qq.com/s/aaa', slug: 'first-post' });
  assert.deepEqual(entries[1], { url: 'https://mp.weixin.qq.com/s/bbb', slug: 'second-post' });
  assert.match(entries[2].error, /slug/);
  assert.match(entries[3].error, /格式/);
});

test('findPostDir 按 slug 匹配已存在的文章目录', () => {
  const dirs = ['2026-06-17-wx-kit-intro', '2026-07-01-other-post'];
  assert.equal(findPostDir(dirs, 'wx-kit-intro'), '2026-06-17-wx-kit-intro');
  assert.equal(findPostDir(dirs, 'intro'), null);
  assert.equal(findPostDir(dirs, 'new-post'), null);
});

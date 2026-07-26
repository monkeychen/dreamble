import assert from 'node:assert/strict';
import test from 'node:test';
import {
  ARTICLE_THEMES,
  CODE_THEMES,
  applyTextAction,
  buildExportDocument,
  convertExternalLinksToFootnotes,
  countDocument,
  documentTitle,
  formatMarkdown,
  normalizeSettings,
  preprocessMarkdown,
  safeExportFilename,
} from '../src/lib/md2wechat.mjs';

test('md2wechat 注册 12 套完整正文主题和 7 套代码主题', () => {
  assert.equal(ARTICLE_THEMES.length, 12);
  assert.equal(CODE_THEMES.length, 7);
  assert.equal(new Set(ARTICLE_THEMES.map((theme) => theme.id)).size, 12);
  assert.equal(new Set(CODE_THEMES.map((theme) => theme.id)).size, 7);
  assert.ok(new Set(ARTICLE_THEMES.map((theme) => theme.variant)).size >= 10);
});

test('normalizeSettings 拒绝未知主题并约束可调参数', () => {
  const settings = normalizeSettings({
    theme: 'unknown',
    codeTheme: 'github',
    accent: '#12abEF',
    fontSize: 99,
    lineHeight: 0,
    paragraphSpacing: 1.26,
    fontFamily: 'comic',
    codeWrap: false,
    syncScroll: false,
    viewMode: 'preview',
  });

  assert.equal(settings.theme, 'magazine');
  assert.equal(settings.codeTheme, 'github');
  assert.equal(settings.accent, '#12abEF');
  assert.equal(settings.fontSize, 20);
  assert.equal(settings.lineHeight, 1.5);
  assert.equal(settings.paragraphSpacing, 1.3);
  assert.equal(settings.fontFamily, 'theme');
  assert.equal(settings.codeWrap, false);
  assert.equal(settings.syncScroll, false);
  assert.equal(settings.viewMode, 'preview');
});

test('applyTextAction 包裹选区并插入结构模板', () => {
  assert.deepEqual(applyTextAction('内容', 0, 2, 'bold'), {
    value: '**内容**',
    selectionStart: 2,
    selectionEnd: 4,
  });

  const table = applyTextAction('开头', 2, 2, 'table');
  assert.match(table.value, /\| 项目 \| 说明 \|/);
  assert.match(table.value, /开头\n\n\|/);

  const list = applyTextAction('第一行\n第二行', 0, 7, 'unordered-list');
  assert.equal(list.value, '- 第一行\n- 第二行');
});

test('applyTextAction 覆盖完整格式工具栏动作', () => {
  const actions = [
    'heading',
    'bold',
    'italic',
    'strike',
    'quote',
    'unordered-list',
    'ordered-list',
    'inline-code',
    'code-block',
    'link',
    'image',
    'table',
    'divider',
    'toc',
    'math',
    'ruby',
  ];

  actions.forEach((action) => {
    const result = applyTextAction('文字', 0, 2, action);
    assert.notEqual(result.value, '文字', `${action} 应修改 Markdown`);
    assert.ok(result.selectionStart >= 0);
    assert.ok(result.selectionEnd >= result.selectionStart);
  });
});

test('formatMarkdown 统一换行、清理行尾空格和多余空行', () => {
  assert.equal(formatMarkdown('标题  \r\n\r\n\r\n正文\t\r\n'), '标题\n\n正文\n');
});

test('convertExternalLinksToFootnotes 保留公众号链接并去重外链', () => {
  const source = [
    '[外链](https://example.com/a)',
    '[同一外链](https://example.com/a)',
    '[公众号](https://mp.weixin.qq.com/s/abc)',
    '![图片](https://example.com/a.png)',
  ].join('\n');
  const result = convertExternalLinksToFootnotes(source);

  assert.match(result, /外链\[\^ext-1\]/);
  assert.match(result, /同一外链\[\^ext-1\]/);
  assert.match(result, /\[\^ext-1\]: https:\/\/example\.com\/a/);
  assert.match(result, /\[公众号\]\(https:\/\/mp\.weixin\.qq\.com\/s\/abc\)/);
  assert.match(result, /!\[图片\]\(https:\/\/example\.com\/a\.png\)/);
  assert.equal((result.match(/\[\^ext-1\]:/g) ?? []).length, 1);
});

test('preprocessMarkdown 生成目录、注音和文末参考资料', () => {
  const result = preprocessMarkdown(`# 标题

[TOC]

## 第一节

文字{工具|gōng jù}[^note]

[^note]: 参考说明`);

  assert.match(result, /> \*\*目录\*\*/);
  assert.match(result, /- 第一节/);
  assert.match(result, /<ruby>工具<rt>gōng jù<\/rt><\/ruby>/);
  assert.match(result, /<sup data-footnote-ref="1">\[1\]<\/sup>/);
  assert.match(result, /### 参考资料/);
  assert.match(result, /1\. 参考说明/);
});

test('文档统计、标题和导出文件名保持可用', () => {
  assert.deepEqual(countDocument('一 二\n三'), { characters: 3, lines: 2 });
  assert.equal(documentTitle('# 我的 / 文章\n正文'), '我的 / 文章');
  assert.equal(safeExportFilename('我的 / 文章', '.html'), '我的-文章.html');
  const html = buildExportDocument('标题 <测试>', '<section><h1>标题</h1></section>');
  assert.match(html, /<title>标题 &lt;测试&gt;<\/title>/);
  assert.match(html, /<section><h1>标题<\/h1><\/section>/);
});

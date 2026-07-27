export const ARTICLE_THEMES = [
  {
    id: 'magazine',
    name: '旧杂志',
    description: '人文、随笔、深度长文',
    variant: 'editorial',
    accent: '#9c4526',
    text: '#3a3226',
    muted: '#756750',
    border: '#e2d7c0',
    soft: '#f6f0e3',
    paper: '#fffdf8',
    font: 'serif',
  },
  {
    id: 'classic',
    name: '经典蓝',
    description: '通用、知识、方法论',
    variant: 'classic',
    accent: '#2f5d8a',
    text: '#243447',
    muted: '#68798c',
    border: '#cddceb',
    soft: '#edf4fa',
    paper: '#ffffff',
    font: 'sans',
  },
  {
    id: 'memo',
    name: '便签',
    description: '经验、清单、轻阅读',
    variant: 'memo',
    accent: '#8a6534',
    text: '#43392c',
    muted: '#7c6f5d',
    border: '#dfcfaa',
    soft: '#fff7d8',
    paper: '#fffdf3',
    font: 'sans',
  },
  {
    id: 'lake',
    name: '雁栖湖',
    description: '旅行、生活、叙事',
    variant: 'lake',
    accent: '#397b83',
    text: '#29464a',
    muted: '#6b8588',
    border: '#bfdbdc',
    soft: '#ecf7f6',
    paper: '#fbfefd',
    font: 'serif',
  },
  {
    id: 'brief',
    name: '商务简报',
    description: '商业、汇报、分析',
    variant: 'brief',
    accent: '#1f3a5f',
    text: '#202b3a',
    muted: '#667386',
    border: '#c9d2df',
    soft: '#eef2f7',
    paper: '#ffffff',
    font: 'sans',
  },
  {
    id: 'minimal',
    name: '极简黑',
    description: '技术、观点、极简',
    variant: 'minimal',
    accent: '#1f2933',
    text: '#202124',
    muted: '#73777d',
    border: '#d9dce1',
    soft: '#f4f5f6',
    paper: '#ffffff',
    font: 'sans',
  },
  {
    id: 'yellow',
    name: '山吹',
    description: '灵感、创意、活力',
    variant: 'marker',
    accent: '#b77900',
    text: '#3f3423',
    muted: '#7a6a50',
    border: '#ead59a',
    soft: '#fff4c7',
    paper: '#fffdf7',
    font: 'sans',
  },
  {
    id: 'red',
    name: '红绯',
    description: '热点、评论、醒目',
    variant: 'banner',
    accent: '#b23a3a',
    text: '#3d2929',
    muted: '#826767',
    border: '#e7c3c3',
    soft: '#fff0f0',
    paper: '#fffdfd',
    font: 'serif',
  },
  {
    id: 'green',
    name: '绿意',
    description: '成长、健康、自然',
    variant: 'leaf',
    accent: '#27745b',
    text: '#263c34',
    muted: '#668075',
    border: '#c5dfd4',
    soft: '#edf7f2',
    paper: '#fbfefc',
    font: 'serif',
  },
  {
    id: 'cyan',
    name: '嫩青',
    description: '教程、产品、清爽',
    variant: 'dotted',
    accent: '#16869a',
    text: '#263f44',
    muted: '#66838a',
    border: '#bde0e5',
    soft: '#ecf9fb',
    paper: '#fbfeff',
    font: 'sans',
  },
  {
    id: 'purple',
    name: '姹紫',
    description: '文化、审美、品牌',
    variant: 'card',
    accent: '#7b4d9d',
    text: '#3b3042',
    muted: '#786b80',
    border: '#ddcbe8',
    soft: '#f7f0fb',
    paper: '#fffdfd',
    font: 'serif',
  },
  {
    id: 'orange',
    name: '橙心',
    description: '活动、运营、分享',
    variant: 'underline',
    accent: '#d0642b',
    text: '#463329',
    muted: '#806e64',
    border: '#efcfbd',
    soft: '#fff3eb',
    paper: '#fffdfb',
    font: 'sans',
  },
];

export const CODE_THEMES = [
  {
    id: 'atom-dark',
    name: 'Atom Dark',
    background: '#282c34',
    text: '#abb2bf',
    keyword: '#c678dd',
    string: '#98c379',
    comment: '#7f848e',
    number: '#d19a66',
    title: '#61afef',
    meta: '#56b6c2',
    addition: '#98c379',
    deletion: '#e06c75',
    border: '#3b4048',
  },
  {
    id: 'atom-light',
    name: 'Atom Light',
    background: '#fafafa',
    text: '#383a42',
    keyword: '#a626a4',
    string: '#50a14f',
    comment: '#a0a1a7',
    number: '#986801',
    title: '#4078f2',
    meta: '#0184bc',
    addition: '#50a14f',
    deletion: '#e45649',
    border: '#d7d7d7',
  },
  {
    id: 'monokai',
    name: 'Monokai',
    background: '#272822',
    text: '#f8f8f2',
    keyword: '#f92672',
    string: '#e6db74',
    comment: '#88846f',
    number: '#ae81ff',
    title: '#a6e22e',
    meta: '#66d9ef',
    addition: '#a6e22e',
    deletion: '#f92672',
    border: '#3d3e38',
  },
  {
    id: 'github',
    name: 'GitHub',
    background: '#f6f8fa',
    text: '#24292f',
    keyword: '#cf222e',
    string: '#0a3069',
    comment: '#6e7781',
    number: '#0550ae',
    title: '#8250df',
    meta: '#953800',
    addition: '#116329',
    deletion: '#82071e',
    border: '#d0d7de',
  },
  {
    id: 'vs2015',
    name: 'VS 2015',
    background: '#1e1e1e',
    text: '#dcdcdc',
    keyword: '#569cd6',
    string: '#ce9178',
    comment: '#6a9955',
    number: '#b5cea8',
    title: '#dcdcaa',
    meta: '#4ec9b0',
    addition: '#b5cea8',
    deletion: '#f44747',
    border: '#333333',
  },
  {
    id: 'xcode',
    name: 'Xcode',
    background: '#ffffff',
    text: '#262626',
    keyword: '#ad3da4',
    string: '#d12f1b',
    comment: '#5d6c79',
    number: '#272ad8',
    title: '#3e8087',
    meta: '#78492a',
    addition: '#227d51',
    deletion: '#b31d28',
    border: '#d8d8d8',
  },
  {
    id: 'mac',
    name: 'Mac 窗口',
    background: '#172033',
    text: '#e5edf6',
    keyword: '#ff7ab2',
    string: '#ffcc66',
    comment: '#7f8fa6',
    number: '#b392f0',
    title: '#7dcfff',
    meta: '#5de4c7',
    addition: '#5de4c7',
    deletion: '#ff6b81',
    border: '#2d3b52',
  },
];

export const DEFAULT_SETTINGS = {
  theme: 'magazine',
  codeTheme: 'atom-dark',
  accent: '',
  fontSize: 16,
  lineHeight: 1.8,
  paragraphSpacing: 1,
  fontFamily: 'theme',
  codeWrap: true,
  syncScroll: true,
  viewMode: 'split',
};

const ARTICLE_THEME_IDS = new Set(ARTICLE_THEMES.map((theme) => theme.id));
const CODE_THEME_IDS = new Set(CODE_THEMES.map((theme) => theme.id));
const FONT_FAMILIES = new Set(['theme', 'serif', 'sans']);
const VIEW_MODES = new Set(['split', 'editor', 'preview']);

function clampNumber(value, fallback, min, max, step = 0.1) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  const clamped = Math.min(max, Math.max(min, number));
  return Math.round(clamped / step) * step;
}

export function normalizeSettings(input = {}) {
  return {
    theme: ARTICLE_THEME_IDS.has(input.theme) ? input.theme : DEFAULT_SETTINGS.theme,
    codeTheme: CODE_THEME_IDS.has(input.codeTheme) ? input.codeTheme : DEFAULT_SETTINGS.codeTheme,
    accent: /^#[0-9a-f]{6}$/i.test(input.accent ?? '') ? input.accent : '',
    fontSize: clampNumber(input.fontSize, DEFAULT_SETTINGS.fontSize, 14, 20, 1),
    lineHeight: clampNumber(input.lineHeight, DEFAULT_SETTINGS.lineHeight, 1.5, 2.2),
    paragraphSpacing: clampNumber(input.paragraphSpacing, DEFAULT_SETTINGS.paragraphSpacing, 0.5, 1.8),
    fontFamily: FONT_FAMILIES.has(input.fontFamily) ? input.fontFamily : DEFAULT_SETTINGS.fontFamily,
    codeWrap: typeof input.codeWrap === 'boolean' ? input.codeWrap : DEFAULT_SETTINGS.codeWrap,
    syncScroll: typeof input.syncScroll === 'boolean' ? input.syncScroll : DEFAULT_SETTINGS.syncScroll,
    viewMode: VIEW_MODES.has(input.viewMode) ? input.viewMode : DEFAULT_SETTINGS.viewMode,
  };
}

export function getArticleTheme(id) {
  return ARTICLE_THEMES.find((theme) => theme.id === id) ?? ARTICLE_THEMES[0];
}

export function getCodeTheme(id) {
  return CODE_THEMES.find((theme) => theme.id === id) ?? CODE_THEMES[0];
}

export function countDocument(markdown) {
  return {
    characters: markdown.replace(/\s/g, '').length,
    lines: markdown.length === 0 ? 0 : markdown.split('\n').length,
  };
}

function selectionResult(value, start, end) {
  return { value, selectionStart: start, selectionEnd: end };
}

function wrapSelection(value, start, end, before, after, placeholder) {
  const selected = value.slice(start, end);
  const content = selected || placeholder;
  const replacement = `${before}${content}${after}`;
  const next = `${value.slice(0, start)}${replacement}${value.slice(end)}`;
  const contentStart = start + before.length;
  return selectionResult(next, contentStart, contentStart + content.length);
}

function prefixLines(value, start, end, prefix) {
  const lineStart = value.lastIndexOf('\n', Math.max(0, start - 1)) + 1;
  const nextBreak = value.indexOf('\n', end);
  const lineEnd = nextBreak === -1 ? value.length : nextBreak;
  const block = value.slice(lineStart, lineEnd);
  const replacement = block
    .split('\n')
    .map((line) => `${prefix}${line}`)
    .join('\n');
  const next = `${value.slice(0, lineStart)}${replacement}${value.slice(lineEnd)}`;
  return selectionResult(next, lineStart, lineStart + replacement.length);
}

function insertBlock(value, start, end, block) {
  const before = value.slice(0, start);
  const after = value.slice(end);
  const leading = before.length > 0 && !before.endsWith('\n\n') ? (before.endsWith('\n') ? '\n' : '\n\n') : '';
  const trailing = after.length > 0 && !after.startsWith('\n\n') ? (after.startsWith('\n') ? '\n' : '\n\n') : '';
  const replacement = `${leading}${block}${trailing}`;
  const next = `${before}${replacement}${after}`;
  const cursor = start + replacement.length - trailing.length;
  return selectionResult(next, cursor, cursor);
}

export function applyTextAction(value, start, end, action) {
  switch (action) {
    case 'bold':
      return wrapSelection(value, start, end, '**', '**', '加粗文字');
    case 'italic':
      return wrapSelection(value, start, end, '*', '*', '强调文字');
    case 'strike':
      return wrapSelection(value, start, end, '~~', '~~', '删除文字');
    case 'inline-code':
      return wrapSelection(value, start, end, '`', '`', 'code');
    case 'code-block':
      return wrapSelection(value, start, end, '```text\n', '\n```', '在这里输入代码');
    case 'link':
      return wrapSelection(value, start, end, '[', '](https://)', '链接文字');
    case 'image':
      return wrapSelection(value, start, end, '![', '](https://)', '图片描述');
    case 'heading':
      return prefixLines(value, start, end, '## ');
    case 'quote':
      return prefixLines(value, start, end, '> ');
    case 'unordered-list':
      return prefixLines(value, start, end, '- ');
    case 'ordered-list':
      return prefixLines(value, start, end, '1. ');
    case 'table':
      return insertBlock(value, start, end, '| 项目 | 说明 |\\n| --- | --- |\\n| 示例 | 内容 |');
    case 'divider':
      return insertBlock(value, start, end, '---');
    case 'toc':
      return insertBlock(value, start, end, '[TOC]');
    case 'math':
      return wrapSelection(value, start, end, '$', '$', 'E = mc^2');
    case 'ruby':
      return wrapSelection(value, start, end, '{', '|pīn yīn}', '注音文字');
    default:
      return selectionResult(value, start, end);
  }
}

export function formatMarkdown(markdown) {
  const normalized = markdown
    .replace(/\r\n?/g, '\n')
    .split('\n')
    .map((line) => line.replace(/[ \t]+$/g, ''))
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  return normalized ? `${normalized}\n` : '';
}

export function stripChatGptContentReferences(markdown) {
  const lines = markdown.replace(/\r\n?/g, '\n').split('\n');
  let fence = null;

  return lines
    .filter((line) => {
      const fenceMatch = line.match(/^\s*(`{3,}|~{3,})/);
      if (fenceMatch) {
        const marker = fenceMatch[1][0];
        const length = fenceMatch[1].length;
        if (fence === null) fence = { marker, length };
        else if (fence.marker === marker && length >= fence.length) fence = null;
        return true;
      }

      if (fence !== null) return true;
      return !/^\s*::chatgpt-content-reference\{[^}\r\n]*\}\s*$/.test(line);
    })
    .join('\n');
}

export function convertExternalLinksToFootnotes(markdown) {
  const footnotes = [];
  const converted = markdown.replace(
    /(?<!!)\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)(?:\s+"[^"]*")?\)/g,
    (match, label, url) => {
      try {
        if (new URL(url).hostname === 'mp.weixin.qq.com') return match;
      } catch {
        return match;
      }
      const existing = footnotes.find((item) => item.url === url);
      const index = existing ? existing.index : footnotes.length + 1;
      if (!existing) footnotes.push({ index, label, url });
      return `${label}[^ext-${index}]`;
    },
  );

  if (footnotes.length === 0) return markdown;
  const definitions = footnotes.map((item) => `[^ext-${item.index}]: ${item.url}`).join('\n');
  return `${converted.trimEnd()}\n\n${definitions}\n`;
}

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

export function preprocessMarkdown(markdown) {
  const lines = stripChatGptContentReferences(markdown).split('\n');
  const definitions = new Map();
  const bodyLines = [];

  for (const line of lines) {
    const match = line.match(/^\[\^([^\]]+)\]:\s*(.+)$/);
    if (match) definitions.set(match[1], match[2]);
    else bodyLines.push(line);
  }

  const referenceOrder = [];
  let body = bodyLines.join('\n').replace(/\[\^([^\]]+)\]/g, (match, id) => {
    if (!definitions.has(id)) return match;
    let index = referenceOrder.indexOf(id);
    if (index === -1) {
      referenceOrder.push(id);
      index = referenceOrder.length - 1;
    }
    return `<sup data-footnote-ref="${index + 1}">[${index + 1}]</sup>`;
  });

  body = body.replace(/\{([^{}\n|]+)\|([^{}\n]+)\}/g, (_match, word, pronunciation) => (
    `<ruby>${escapeHtml(word)}<rt>${escapeHtml(pronunciation)}</rt></ruby>`
  ));

  if (body.includes('[TOC]')) {
    const items = bodyLines
      .map((line) => line.match(/^(#{2,3})\s+(.+)$/))
      .filter(Boolean)
      .map((match) => `${match[1].length === 3 ? '  ' : ''}- ${match[2].replace(/[*_`~]/g, '')}`);
    body = body.replaceAll('[TOC]', items.length > 0 ? `> **目录**\n>\n${items.join('\n')}` : '> **目录**');
  }

  if (referenceOrder.length > 0) {
    const references = referenceOrder
      .map((id, index) => `${index + 1}. ${definitions.get(id)}`)
      .join('\n');
    body = `${body.trimEnd()}\n\n---\n\n### 参考资料\n\n${references}\n`;
  }

  return body;
}

export function documentTitle(markdown) {
  const match = markdown.match(/^#\s+(.+)$/m);
  return (match?.[1] ?? '公众号文章').replace(/[*_`~[\]]/g, '').trim() || '公众号文章';
}

export function safeExportFilename(title, extension) {
  const safe = title
    .normalize('NFKC')
    .replace(/[\\/:*?"<>|]/g, '-')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 64);
  const ext = extension.replace(/^\./, '');
  return `${safe || '公众号文章'}.${ext}`;
}

export function buildExportDocument(title, articleHtml) {
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)}</title>
</head>
<body style="margin:0;padding:24px;background:#f5f5f5;">
  <main style="max-width:680px;margin:0 auto;padding:28px;background:#fff;">${articleHtml}</main>
</body>
</html>
`;
}

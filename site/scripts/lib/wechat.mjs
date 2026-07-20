import * as cheerio from 'cheerio';
import TurndownService from 'turndown';

/** 按东八区（文章的实际时区）格式化日期为 YYYY-MM-DD。 */
export function formatDateCN(date) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai' }).format(date);
}

/** 从公众号文章 HTML 提取标题、发表日期、正文 HTML（img 的 data-src 已还原为 src）。 */
export function extractArticle(html) {
  const $ = cheerio.load(html);
  const title = ($('meta[property="og:title"]').attr('content') || $('#activity-name').text()).trim();
  const m = html.match(/var\s+ct\s*=\s*"(\d+)"/);
  if (!m) console.warn('⚠️  未在页面中找到发表时间（var ct），使用当前日期');
  const date = m ? new Date(Number(m[1]) * 1000) : new Date();
  const content = $('#js_content');
  content.find('img').each((_, el) => {
    const src = $(el).attr('data-src') || $(el).attr('src');
    if (src) $(el).attr('src', src);
  });
  return { title, date, contentHtml: content.html() ?? '' };
}

const turndown = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced' });

export function htmlToMarkdown(html) {
  return turndown.turndown(html);
}

/** 收集 markdown 中的远程图片 URL（去重、保持出现顺序）。 */
export function collectImages(markdown) {
  const urls = [...markdown.matchAll(/!\[[^\]]*\]\((https?:\/\/[^)\s]+)\)/g)].map((m) => m[1]);
  return [...new Set(urls)];
}

export function imageFilename(url, index) {
  const fmt = new URL(url).searchParams.get('wx_fmt');
  const ext = (fmt || 'jpg').replace('jpeg', 'jpg');
  return `img-${String(index + 1).padStart(2, '0')}.${ext}`;
}

/** mapping: Array<[远程URL, 本地文件名]> */
export function localizeImages(markdown, mapping) {
  let out = markdown;
  for (const [url, filename] of mapping) out = out.replaceAll(url, `./${filename}`);
  return out;
}

/** date 可为 Date 或 'YYYY-MM-DD' 字符串（wx-kit 产物给的就是东八区日期字符串）。 */
export function buildIndexMd({ title, date, markdown }) {
  const d = typeof date === 'string' ? date : formatDateCN(date);
  return `---\ntitle: ${JSON.stringify(title)}\ndate: ${d}\nsource: wechat\n---\n\n${markdown}\n`;
}

/**
 * 解析 wx-kit CLI 下载产物的 content.md：
 * 取 frontmatter 中的 title 与 publishTime（东八区），正文去掉 frontmatter 与
 * 重复的首个 H1，图片引用从 images/ 子目录改写为同目录相对路径（本站约定）。
 */
/**
 * 解析批量导入清单：每行 `<URL> <slug>`（空白分隔），支持 # 注释与空行。
 * 非法行不中断解析，返回带 error 字段的条目由调用方汇报。
 */
export function parseBatchFile(text) {
  const entries = [];
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const parts = line.split(/\s+/);
    if (parts.length !== 2) {
      entries.push({ line, error: `行格式应为 "<URL> <slug>"（空白分隔两列）: ${line}` });
      continue;
    }
    const [url, slug] = parts;
    if (!/^[a-z0-9-]+$/.test(slug)) {
      entries.push({ url, slug, error: `slug 只能包含小写字母、数字、连字符: ${slug}` });
      continue;
    }
    entries.push({ url, slug });
  }
  return entries;
}

/** 在文章目录名列表中查找 slug 对应的已有目录（YYYY-MM-DD-<slug>），无则返回 null。 */
export function findPostDir(dirNames, slug) {
  const re = new RegExp(`^\\d{4}-\\d{2}-\\d{2}-${slug}$`);
  return dirNames.find((d) => re.test(d)) ?? null;
}

export function fromWxkit(contentMd) {
  const m = contentMd.match(/^---\n([\s\S]*?)\n---\n/);
  if (!m) return { title: '', date: null, body: contentMd.trim() + '\n' };
  const fm = m[1];
  const title = (fm.match(/^title:\s*"?(.*?)"?\s*$/m)?.[1] ?? '').trim();
  const date = fm.match(/^publishTime:\s*"?(\d{4}-\d{2}-\d{2})/m)?.[1] ?? null;
  let body = contentMd.slice(m[0].length);
  body = body.replace(/^\s*# .*\n+/, '');
  body = body.replace(/\]\(images\//g, '](./');
  return { title, date, body: body.trim() + '\n' };
}

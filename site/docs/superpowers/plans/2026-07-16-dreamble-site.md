# 聊哉梦呓个人站（dreamble-site）Implementation Plan

> [!WARNING]
> 历史快照：本计划记录 `site/` 仍是独立 `dreamble-site` 仓库时的实施过程。绝对路径、命令、依赖版本、测试数量和代码片段不再作为当前操作依据；当前规则见 `site/AGENTS.md`，操作见 `site/README.md`。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建并上线一个纯静态个人站（simiam.com）：markdown 放入约定目录即发表文章/上架作品，一条命令发布到自有服务器。

**Architecture:** Astro 5 静态站点，Content Collections 对 frontmatter 做构建时 schema 校验；内容真源在本地 git 仓库；`npm run publish` 构建后 rsync（失败 fallback git bare 仓库 + hook）同步 `dist/` 到服务器，nginx 直接伺服。无数据库、无后台、无应用进程。

**Tech Stack:** Astro 5、@astrojs/rss、turndown + cheerio（公众号导入脚本）、node:test（单元测试）、bash（发布/服务器脚本）、nginx + certbot（服务器侧）。

## Global Constraints

- 站点域名：`https://simiam.com`（astro.config `site` 字段，RSS/sitemap/canonical 均用它）
- **服务器 IP、用户名、密码一律不写入任何被 git 跟踪的文件**；地址与账号只存 `.deploy.env`（已 gitignore），密码不落任何文件（SSH 密钥已配好，免密登录可用）
- 内容约定：一篇文章 = 一个目录 `content/posts/YYYY-MM-DD-<slug>/index.md`；一个作品 = 一个目录 `content/projects/<slug>/index.md`；图片与 index.md 同目录、相对路径引用
- 文章 frontmatter：`title`、`date` 必填；`summary`/`tags`/`source: wechat`/`visibility: public|unlisted`/`draft` 可选
- 作品 frontmatter：`name`、`tagline` 必填，`links` 至少一项；`cover`/`status`/`order` 可选；正文为空则不生成详情页
- unlisted 三重隔离：不进列表页、不进 RSS/sitemap、页面加 `<meta name="robots" content="noindex">`；draft 完全不构建
- 页脚备案信息：`闽ICP备18023112号`（链接 beian.miit.gov.cn）+ `闽公网安备 35012102500070号`（链接 beian.gov.cn 备案详情页，附图标）
- 站点界面中文（`lang="zh-CN"`），暗色模式跟随系统（`prefers-color-scheme`），默认零客户端 JS
- commit message 用英文；git push 由站主手动执行，本计划任何步骤不得执行 `git push`（发布脚本里推往**部署服务器** bare 仓库的 push 除外，那是部署通道不是代码托管）
- 本地环境已确认：Node 24、npm 11、macOS openrsync（协议 29，支持 `-az --delete`）
- 每个任务结束必须 `npm run build` 与 `npm test`（存在时）通过后才 commit

---

### Task 1: Astro 脚手架 + 项目 CLAUDE.md

**Files:**
- Create: `package.json`、`astro.config.mjs`、`tsconfig.json`、`src/pages/index.astro`（占位，Task 6 重写）、`CLAUDE.md`
- Modify: `.gitignore`（追加 Astro 生成目录）

**Interfaces:**
- Produces: `npm run dev/build/preview` 可用；`astro.config.mjs` 导出 `site: 'https://simiam.com'`（后续 RSS/sitemap 依赖 `context.site`）

- [ ] **Step 1: 初始化 package.json 并安装依赖**

```bash
cd /Users/chenzhian/workspace/ai/dreamble-site
npm init -y
npm install astro @astrojs/rss
npm install -D turndown cheerio
```

- [ ] **Step 2: 覆写 package.json 的关键字段**

将 `package.json` 改为（保留 npm 生成的依赖版本号）：

```json
{
  "name": "dreamble-site",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "test": "node --test tests/",
    "import": "node scripts/import-wechat.mjs",
    "publish": "bash scripts/publish.sh"
  }
}
```

注意：`npm run publish` 走的是 scripts 命名空间，不会触发 npm 自身的 publish 命令。

- [ ] **Step 3: 创建 astro.config.mjs 与 tsconfig.json**

`astro.config.mjs`：

```js
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://simiam.com',
});
```

`tsconfig.json`：

```json
{
  "extends": "astro/tsconfigs/strict",
  "include": [".astro/types.d.ts", "**/*"],
  "exclude": ["dist"]
}
```

- [ ] **Step 4: 创建占位首页**

`src/pages/index.astro`：

```astro
---
---
<html lang="zh-CN">
  <head><meta charset="utf-8" /><title>聊哉梦呓</title></head>
  <body><h1>聊哉梦呓</h1></body>
</html>
```

- [ ] **Step 5: 追加 .gitignore**

在现有 `.gitignore` 末尾追加：

```
# astro
.astro/
```

- [ ] **Step 6: 验证构建**

Run: `npm run build`
Expected: 构建成功，`dist/index.html` 存在且包含「聊哉梦呓」：

```bash
grep 聊哉梦呓 dist/index.html
```

- [ ] **Step 7: 写项目 CLAUDE.md（约束先行）**

`CLAUDE.md`：

```markdown
# dreamble-site 项目规范

个人站「聊哉梦呓」（simiam.com）：公众号文章备份 + 独立发表 + 工具作品展示。
纯静态：Astro 构建，服务器上只有 nginx + 静态文件。设计文档见 docs/superpowers/specs/。

## 目录约定
- 文章：content/posts/YYYY-MM-DD-<slug>/index.md（一文一目录，图片同目录相对引用）
- 作品：content/projects/<slug>/index.md（正文为空则无详情页）
- frontmatter 字段以 src/content.config.ts 的 schema 为准（构建时强制校验，填错会报错指明文件与字段）

## 常用命令
- npm run dev — 本地预览
- npm run build — 构建（含 schema 校验）
- npm test — 单元测试
- npm run import -- <公众号文章URL> <英文slug> — 导入公众号文章（图片本地化）
- npm run publish — 构建并发布到服务器（rsync 优先，失败自动走 git 通道）

## 部署
- 服务器信息在 .deploy.env（gitignored）：服务器地址、账号一律不进 git，密码不落任何文件（SSH 密钥认证）
- 首次部署与 HTTPS 步骤见 docs/deploy.md

## 规范
- commit message 用英文；git push 由站主手动执行，不要自动 push
- 改动后必须 npm run build && npm test 通过再 commit
```

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: scaffold Astro project with site config and project conventions"
```

---

### Task 2: 内容 schema + 辅助函数 + 示例内容

**Files:**
- Create: `src/content.config.ts`、`src/lib/helpers.mjs`、`tests/helpers.test.mjs`
- Create: `content/posts/2026-07-16-hello-world/index.md`、`content/posts/2026-07-16-hello-world/cover.png`
- Create: `content/posts/2026-07-16-unlisted-sample/index.md`、`content/posts/2026-07-16-draft-sample/index.md`
- Create: `content/projects/sample-tool/index.md`、`content/projects/sample-tool/screenshot.png`、`content/projects/bare-tool/index.md`
- Create: `content/about.md`

**Interfaces:**
- Produces: collections `posts`、`projects`（`getCollection('posts')` 等）；`postSlug(id: string): string`、`projectSlug(id: string): string`、`isListed(data): boolean`（`!draft && visibility === 'public'`）、`sortByDateDesc(a, b): number`。后续所有页面任务只通过这些接口取内容。

- [ ] **Step 1: 写失败的单元测试**

`tests/helpers.test.mjs`：

```js
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm test`
Expected: FAIL，`Cannot find module .../src/lib/helpers.mjs`

- [ ] **Step 3: 实现 helpers.mjs**

`src/lib/helpers.mjs`：

```js
/** 内容集合 id → URL slug。id 可能是 "2026-07-16-foo" 或 "2026-07-16-foo/index"。 */
export function postSlug(id) {
  const dir = id.split('/')[0];
  const m = dir.match(/^\d{4}-\d{2}-\d{2}-(.+)$/);
  return m ? m[1] : dir;
}

export function projectSlug(id) {
  return id.split('/')[0];
}

/** 是否进入列表页 / RSS / sitemap */
export function isListed(data) {
  return !data.draft && data.visibility === 'public';
}

export function sortByDateDesc(a, b) {
  return b.data.date.valueOf() - a.data.date.valueOf();
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm test`
Expected: 5 项全部 PASS

- [ ] **Step 5: 定义内容集合 schema**

`src/content.config.ts`：

```ts
import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '*/index.md', base: './content/posts' }),
  schema: z.object({
    title: z.string().min(1),
    date: z.coerce.date(),
    summary: z.string().optional(),
    tags: z.array(z.string()).default([]),
    source: z.enum(['wechat']).optional(),
    visibility: z.enum(['public', 'unlisted']).default('public'),
    draft: z.boolean().default(false),
  }),
});

const projects = defineCollection({
  loader: glob({ pattern: '*/index.md', base: './content/projects' }),
  schema: ({ image }) =>
    z.object({
      name: z.string().min(1),
      tagline: z.string().min(1),
      cover: image().optional(),
      links: z
        .object({
          download: z.string().url().optional(),
          repo: z.string().url().optional(),
          website: z.string().url().optional(),
        })
        .refine((l) => l.download || l.repo || l.website, {
          message: 'links 至少填写 download / repo / website 之一',
        }),
      status: z.enum(['active', 'archived']).default('active'),
      order: z.number().default(999),
    }),
});

export const collections = { posts, projects };
```

- [ ] **Step 6: 创建示例内容（兼作约定的活文档）**

生成一张 1×1 示例图片（两处复用）：

```bash
mkdir -p content/posts/2026-07-16-hello-world content/posts/2026-07-16-unlisted-sample content/posts/2026-07-16-draft-sample content/projects/sample-tool content/projects/bare-tool
B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
echo "$B64" | base64 -d > content/posts/2026-07-16-hello-world/cover.png
echo "$B64" | base64 -d > content/projects/sample-tool/screenshot.png
```

`content/posts/2026-07-16-hello-world/index.md`：

```markdown
---
title: 你好，世界
date: 2026-07-16
summary: 站点的第一篇示例文章，展示文章目录约定。
tags: [示例]
---

这是一篇示例文章。一篇文章就是一个目录，图片放在同目录、相对路径引用：

![示例图片](./cover.png)

正式启用后可删除本文。
```

`content/posts/2026-07-16-unlisted-sample/index.md`：

```markdown
---
title: 仅链接可达的示例
date: 2026-07-16
visibility: unlisted
---

这篇文章不出现在列表、RSS、sitemap 中，页面带 noindex。知道链接的人可以访问。
```

`content/posts/2026-07-16-draft-sample/index.md`：

```markdown
---
title: 草稿示例（不会被构建）
date: 2026-07-16
draft: true
---

draft: true 的文章完全不构建，本文永远不会出现在线上。
```

`content/projects/sample-tool/index.md`：

```markdown
---
name: 示例工具
tagline: 一句话说明这个工具做什么。
cover: ./screenshot.png
links:
  repo: https://github.com/monkeychen/dreamble-site
order: 1
---

## 功能

有正文的作品会生成详情页，这里写功能介绍、使用说明、下载方式、更新记录。

正式启用后可删除本作品。
```

`content/projects/bare-tool/index.md`（正文留空 → 无详情页，纯橱窗卡片）：

```markdown
---
name: 纯卡片示例
tagline: 正文为空的作品只显示卡片，不生成详情页。
links:
  website: https://simiam.com
order: 2
---
```

`content/about.md`：

```markdown
---
title: 关于我
---

安哥，自由职业者。程序员出身，现投入 AI 相关的产品开发、企业培训与新媒体写作运营。

- 微信公众号：聊哉梦呓
- 本站文章一部分备份自公众号，一部分为本站独立发表。
```

- [ ] **Step 7: 验证 schema 生效（构建 + 故意破坏各一次）**

Run: `npm run build`
Expected: 构建成功（此时页面还没消费 collections，但 Astro 会同步并校验 content）。

再验证校验确实会拦截错误：把 `content/projects/bare-tool/index.md` 的 `links:` 三行临时删掉，运行 `npm run build`，Expected: FAIL 且报错信息指向 `bare-tool` 的 `links` 字段。**验证后恢复原文件**，再 `npm run build` 确认通过。

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: add content collections schema, helpers, and sample content"
```

---

### Task 3: 基础布局 + 全局样式 + 备案页脚

**Files:**
- Create: `src/layouts/Base.astro`、`src/styles/global.css`、`public/robots.txt`、`public/images/beian.png`（网上获取标准公安备案图标）
- Modify: `src/pages/index.astro`（改用 Base 布局）

**Interfaces:**
- Produces: `Base.astro`，Props 为 `{ title: string; description?: string; noindex?: boolean }`，含 header 导航（首页/文章/作品/关于）、footer 备案信息。后续所有页面用它包裹。

- [ ] **Step 1: 下载公安备案标准图标**

```bash
mkdir -p public/images
curl -fsSL -o public/images/beian.png "https://www.beian.gov.cn/img/ghs.png" \
  || curl -fsSL -o public/images/beian.png "http://www.beian.gov.cn/img/ghs.png"
file public/images/beian.png
```

Expected: `file` 输出 `PNG image data`。若两个 URL 均失效，用网络搜索「公安备案图标 ghs.png」找权威来源下载，务必确认是标准的公安备案徽标（圆形国徽样式小图）。

- [ ] **Step 2: 写全局样式**

`src/styles/global.css`：

```css
:root {
  --bg: #fdfdfc;
  --fg: #1f2328;
  --muted: #6b7280;
  --accent: #b45309;
  --border: #e5e7eb;
  --card-bg: #ffffff;
  --max-width: 44rem;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #16181d;
    --fg: #d6d9de;
    --muted: #8b919a;
    --accent: #e8a154;
    --border: #2c3038;
    --card-bg: #1d2026;
  }
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB",
    "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  line-height: 1.75;
  font-size: 17px;
}

header.site {
  border-bottom: 1px solid var(--border);
}
header.site nav {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 1rem 1.25rem;
  display: flex;
  gap: 1.25rem;
  align-items: baseline;
}
header.site .brand {
  font-weight: 700;
  font-size: 1.15rem;
  margin-right: auto;
}
header.site a { color: var(--fg); text-decoration: none; }
header.site a:hover { color: var(--accent); }

main {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 2rem 1.25rem 4rem;
}

a { color: var(--accent); }

h1, h2, h3 { line-height: 1.35; }
h2 .more { font-size: 0.85rem; font-weight: 400; margin-left: 0.5rem; }

article img { max-width: 100%; height: auto; }
article .meta { color: var(--muted); font-size: 0.9rem; }

pre {
  overflow-x: auto;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.85em;
}
code { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }

ul.post-list { list-style: none; padding: 0; }
ul.post-list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.4rem 0;
}
ul.post-list time { color: var(--muted); font-size: 0.9rem; white-space: nowrap; }

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: 1rem;
  padding: 0;
  list-style: none;
}
.card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  background: var(--card-bg);
}
.card h3 { margin: 0 0 0.35rem; }
.card h3 a { color: var(--fg); text-decoration: none; }
.card h3 a:hover { color: var(--accent); }
.card .tagline { color: var(--muted); margin: 0 0 0.6rem; font-size: 0.95rem; }
.card .links { display: flex; gap: 0.9rem; font-size: 0.9rem; margin: 0; }
.card .cover { width: 100%; height: auto; border-radius: 6px; margin-bottom: 0.6rem; }
.card.archived { opacity: 0.65; }

footer.site {
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.8rem;
  text-align: center;
  padding: 1.5rem 1rem 2rem;
}
footer.site a { color: var(--muted); text-decoration: none; }
footer.site p { margin: 0.3rem 0; }
footer.site .beian img { vertical-align: -2px; margin-right: 2px; }
```

- [ ] **Step 3: 写 Base 布局**

`src/layouts/Base.astro`：

```astro
---
import '../styles/global.css';

interface Props {
  title: string;
  description?: string;
  noindex?: boolean;
}

const { title, description = '聊哉梦呓——安哥的文章与作品', noindex = false } = Astro.props;
---

<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <meta name="description" content={description} />
    {noindex && <meta name="robots" content="noindex" />}
    <link rel="canonical" href={new URL(Astro.url.pathname, Astro.site)} />
    <link rel="alternate" type="application/rss+xml" title="聊哉梦呓" href="/rss.xml" />
  </head>
  <body>
    <header class="site">
      <nav>
        <a class="brand" href="/">聊哉梦呓</a>
        <a href="/posts/">文章</a>
        <a href="/projects/">作品</a>
        <a href="/about/">关于</a>
      </nav>
    </header>
    <main><slot /></main>
    <footer class="site">
      <p>© {new Date().getFullYear()} 聊哉梦呓 · simiam.com</p>
      <p class="beian">
        <a href="https://beian.miit.gov.cn" target="_blank" rel="noopener">闽ICP备18023112号</a>
        ·
        <a
          href="http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=35012102500070"
          target="_blank"
          rel="noopener"
        >
          <img src="/images/beian.png" alt="公安备案" width="14" height="14" />闽公网安备
          35012102500070号
        </a>
      </p>
    </footer>
  </body>
</html>
```

- [ ] **Step 4: 占位首页改用 Base**

`src/pages/index.astro` 整体替换为：

```astro
---
import Base from '../layouts/Base.astro';
---

<Base title="聊哉梦呓">
  <h1>聊哉梦呓</h1>
</Base>
```

- [ ] **Step 5: 创建 robots.txt**

`public/robots.txt`：

```
User-agent: *
Allow: /

Sitemap: https://simiam.com/sitemap.xml
```

- [ ] **Step 6: 验证**

```bash
npm run build
grep "闽ICP备18023112号" dist/index.html
grep "35012102500070" dist/index.html
test -f dist/images/beian.png && echo icon-ok
```

Expected: 构建成功，三条 grep/test 均命中。

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: add base layout, global styles, and ICP/PSB footer"
```

---

### Task 4: 文章页（归档 + 详情 + unlisted/draft 处理）

**Files:**
- Create: `src/pages/posts/index.astro`、`src/pages/posts/[slug].astro`

**Interfaces:**
- Consumes: `getCollection('posts')`、`Base.astro`、`postSlug`/`isListed`/`sortByDateDesc`（`src/lib/helpers.mjs`）
- Produces: URL `/posts/`（按年归档，仅 listed）与 `/posts/<slug>/`（含 unlisted，unlisted 带 noindex；draft 无页面）

- [ ] **Step 1: 写文章详情页**

`src/pages/posts/[slug].astro`：

```astro
---
import { getCollection, render } from 'astro:content';
import Base from '../../layouts/Base.astro';
import { postSlug } from '../../lib/helpers.mjs';

export async function getStaticPaths() {
  const posts = await getCollection('posts', ({ data }) => !data.draft);
  return posts.map((post) => ({ params: { slug: postSlug(post.id) }, props: { post } }));
}

const { post } = Astro.props;
const { Content } = await render(post);
const dateStr = post.data.date.toISOString().slice(0, 10);
---

<Base
  title={`${post.data.title} · 聊哉梦呓`}
  description={post.data.summary ?? post.data.title}
  noindex={post.data.visibility === 'unlisted'}
>
  <article>
    <h1>{post.data.title}</h1>
    <p class="meta">
      <time datetime={dateStr}>{dateStr}</time>
      {post.data.source === 'wechat' && <span> · 首发于微信公众号「聊哉梦呓」</span>}
      {post.data.tags.length > 0 && <span> · {post.data.tags.join(' / ')}</span>}
    </p>
    <Content />
  </article>
</Base>
```

- [ ] **Step 2: 写归档页（按年分组）**

`src/pages/posts/index.astro`：

```astro
---
import { getCollection } from 'astro:content';
import Base from '../../layouts/Base.astro';
import { postSlug, isListed, sortByDateDesc } from '../../lib/helpers.mjs';

const posts = (await getCollection('posts', ({ data }) => isListed(data))).sort(sortByDateDesc);

const byYear = new Map<number, typeof posts>();
for (const p of posts) {
  const y = p.data.date.getFullYear();
  if (!byYear.has(y)) byYear.set(y, []);
  byYear.get(y)!.push(p);
}
const years = [...byYear.keys()].sort((a, b) => b - a);
---

<Base title="文章 · 聊哉梦呓">
  <h1>文章</h1>
  {
    years.map((year) => (
      <section>
        <h2>{year}</h2>
        <ul class="post-list">
          {byYear.get(year)!.map((p) => (
            <li>
              <a href={`/posts/${postSlug(p.id)}/`}>{p.data.title}</a>
              <time>{p.data.date.toISOString().slice(0, 10)}</time>
            </li>
          ))}
        </ul>
      </section>
    ))
  }
  {posts.length === 0 && <p>还没有文章。</p>}
</Base>
```

- [ ] **Step 3: 构建并验证三类文章的行为**

```bash
npm run build
# 1) public 文章：进归档、有详情页
grep "hello-world" dist/posts/index.html
test -f dist/posts/hello-world/index.html && echo public-page-ok
# 2) unlisted：不进归档，但详情页存在且带 noindex
grep -c "unlisted-sample" dist/posts/index.html || echo not-in-archive-ok
grep 'name="robots" content="noindex"' dist/posts/unlisted-sample/index.html && echo noindex-ok
# 3) draft：完全不构建
test ! -e dist/posts/draft-sample && echo draft-absent-ok
# 4) 文章相对图片被 Astro 资产管线处理
grep -o '_astro/[^"]*' dist/posts/hello-world/index.html | head -1
```

Expected: `public-page-ok`、`not-in-archive-ok`（grep -c 返回 0 即未命中）、`noindex-ok`、`draft-absent-ok` 均输出；最后一条输出 `_astro/...` 资产路径。

- [ ] **Step 4: 单测回归**

Run: `npm test`
Expected: 全部 PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add post archive and detail pages with unlisted/draft handling"
```

---

### Task 5: 作品页（卡片墙 + 按需详情页）

**Files:**
- Create: `src/components/ProjectCard.astro`、`src/pages/projects/index.astro`、`src/pages/projects/[slug].astro`

**Interfaces:**
- Consumes: `getCollection('projects')`、`Base.astro`、`projectSlug`；作品条目的 `entry.body`（原始 markdown 字符串，空/空白 = 无详情页）
- Produces: `ProjectCard.astro`（Props `{ project }`，首页复用）；URL `/projects/` 与 `/projects/<slug>/`（仅正文非空的作品）

- [ ] **Step 1: 写作品卡片组件**

`src/components/ProjectCard.astro`：

```astro
---
import { Image } from 'astro:assets';
import { projectSlug } from '../lib/helpers.mjs';

const { project } = Astro.props;
const slug = projectSlug(project.id);
const hasDetail = Boolean(project.body?.trim());
---

<li class:list={['card', { archived: project.data.status === 'archived' }]}>
  {project.data.cover && <Image class="cover" src={project.data.cover} alt={project.data.name} />}
  <h3>
    {hasDetail ? <a href={`/projects/${slug}/`}>{project.data.name}</a> : project.data.name}
  </h3>
  <p class="tagline">{project.data.tagline}</p>
  <p class="links">
    {project.data.links.download && <a href={project.data.links.download}>下载</a>}
    {project.data.links.repo && <a href={project.data.links.repo}>源码</a>}
    {project.data.links.website && <a href={project.data.links.website}>网站</a>}
    {hasDetail && <a href={`/projects/${slug}/`}>详情 →</a>}
  </p>
</li>
```

- [ ] **Step 2: 写卡片墙页面**

`src/pages/projects/index.astro`：

```astro
---
import { getCollection } from 'astro:content';
import Base from '../../layouts/Base.astro';
import ProjectCard from '../../components/ProjectCard.astro';

const projects = (await getCollection('projects')).sort(
  (a, b) =>
    Number(a.data.status === 'archived') - Number(b.data.status === 'archived') ||
    a.data.order - b.data.order
);
---

<Base title="作品 · 聊哉梦呓" description="安哥开发的工具软件">
  <h1>作品</h1>
  <ul class="cards">
    {projects.map((project) => <ProjectCard project={project} />)}
  </ul>
  {projects.length === 0 && <p>还没有作品。</p>}
</Base>
```

- [ ] **Step 3: 写作品详情页（仅正文非空）**

`src/pages/projects/[slug].astro`：

```astro
---
import { getCollection, render } from 'astro:content';
import Base from '../../layouts/Base.astro';
import { projectSlug } from '../../lib/helpers.mjs';

export async function getStaticPaths() {
  const projects = await getCollection('projects');
  return projects
    .filter((p) => p.body?.trim())
    .map((project) => ({ params: { slug: projectSlug(project.id) }, props: { project } }));
}

const { project } = Astro.props;
const { Content } = await render(project);
const { links } = project.data;
---

<Base title={`${project.data.name} · 聊哉梦呓`} description={project.data.tagline}>
  <article>
    <h1>{project.data.name}</h1>
    <p class="meta">{project.data.tagline}</p>
    <p class="links">
      {links.download && <a href={links.download}>下载</a>}
      {links.repo && <a href={links.repo}>源码</a>}
      {links.website && <a href={links.website}>网站</a>}
    </p>
    <Content />
  </article>
</Base>
```

- [ ] **Step 4: 构建并验证**

```bash
npm run build
# 卡片墙包含两个示例作品
grep "示例工具" dist/projects/index.html && grep "纯卡片示例" dist/projects/index.html
# 有正文的作品有详情页
test -f dist/projects/sample-tool/index.html && echo detail-ok
# 无正文的作品没有详情页，卡片上也没有指向它的详情链接
test ! -e dist/projects/bare-tool && echo no-detail-ok
grep -c "/projects/bare-tool/" dist/projects/index.html || echo no-detail-link-ok
```

Expected: 四组检查全部通过（`grep -c` 为 0 即未命中）。

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add project card wall and optional detail pages"
```

---

### Task 6: 首页 + 关于页

**Files:**
- Modify: `src/pages/index.astro`（替换占位内容）
- Create: `src/pages/about.astro`

**Interfaces:**
- Consumes: 集合查询 + `ProjectCard.astro` + helpers；`content/about.md`（通过 markdown import 的 `Content` 组件渲染）
- Produces: URL `/`、`/about/`

- [ ] **Step 1: 写首页**

`src/pages/index.astro` 整体替换为：

```astro
---
import { getCollection } from 'astro:content';
import Base from '../layouts/Base.astro';
import ProjectCard from '../components/ProjectCard.astro';
import { postSlug, isListed, sortByDateDesc } from '../lib/helpers.mjs';

const posts = (await getCollection('posts', ({ data }) => isListed(data)))
  .sort(sortByDateDesc)
  .slice(0, 5);

const projects = (await getCollection('projects'))
  .filter((p) => p.data.status === 'active')
  .sort((a, b) => a.data.order - b.data.order)
  .slice(0, 4);
---

<Base title="聊哉梦呓" description="安哥的文章与作品：公众号文章备份、独立发表，以及自研工具软件展示">
  <section>
    <h1>聊哉梦呓</h1>
    <p>安哥的文字与作品。文章一部分备份自微信公众号「聊哉梦呓」，一部分为本站独立发表；工具软件皆为自研。</p>
  </section>

  <section>
    <h2>最新文章<a class="more" href="/posts/">全部 →</a></h2>
    <ul class="post-list">
      {
        posts.map((p) => (
          <li>
            <a href={`/posts/${postSlug(p.id)}/`}>{p.data.title}</a>
            <time>{p.data.date.toISOString().slice(0, 10)}</time>
          </li>
        ))
      }
    </ul>
  </section>

  <section>
    <h2>作品<a class="more" href="/projects/">全部 →</a></h2>
    <ul class="cards">
      {projects.map((project) => <ProjectCard project={project} />)}
    </ul>
  </section>
</Base>
```

- [ ] **Step 2: 写关于页**

`src/pages/about.astro`：

```astro
---
import Base from '../layouts/Base.astro';
import { Content as AboutContent, frontmatter } from '../../content/about.md';
---

<Base title={`${frontmatter.title} · 聊哉梦呓`}>
  <article>
    <h1>{frontmatter.title}</h1>
    <AboutContent />
  </article>
</Base>
```

- [ ] **Step 3: 构建并验证**

```bash
npm run build
grep "最新文章" dist/index.html && grep "hello-world" dist/index.html
grep -c "unlisted-sample" dist/index.html || echo home-no-unlisted-ok
grep "示例工具" dist/index.html
grep "聊哉梦呓" dist/about/index.html && grep "关于我" dist/about/index.html
```

Expected: 首页含最新文章与作品卡片、不含 unlisted 文章；关于页渲染 about.md。

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add home page and about page"
```

---

### Task 7: RSS + sitemap（仅 public 内容）

**Files:**
- Create: `src/pages/rss.xml.ts`、`src/pages/sitemap.xml.ts`

**Interfaces:**
- Consumes: `@astrojs/rss`、集合查询、helpers、`context.site`（来自 astro.config 的 `site`）
- Produces: `/rss.xml`、`/sitemap.xml`（robots.txt 已在 Task 3 指向后者）

- [ ] **Step 1: 写 RSS 端点**

`src/pages/rss.xml.ts`：

```ts
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { postSlug, isListed, sortByDateDesc } from '../lib/helpers.mjs';

export async function GET(context: APIContext) {
  const posts = (await getCollection('posts', ({ data }) => isListed(data))).sort(sortByDateDesc);
  return rss({
    title: '聊哉梦呓',
    description: '安哥的文章与作品',
    site: context.site!,
    items: posts.map((p) => ({
      title: p.data.title,
      pubDate: p.data.date,
      description: p.data.summary ?? '',
      link: `/posts/${postSlug(p.id)}/`,
    })),
  });
}
```

- [ ] **Step 2: 写 sitemap 端点**

`src/pages/sitemap.xml.ts`：

```ts
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { postSlug, projectSlug, isListed } from '../lib/helpers.mjs';

export async function GET(context: APIContext) {
  const posts = await getCollection('posts', ({ data }) => isListed(data));
  const projects = await getCollection('projects');

  const paths = [
    '/',
    '/posts/',
    '/projects/',
    '/about/',
    ...posts.map((p) => `/posts/${postSlug(p.id)}/`),
    ...projects.filter((p) => p.body?.trim()).map((p) => `/projects/${projectSlug(p.id)}/`),
  ];

  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...paths.map((p) => `  <url><loc>${new URL(p, context.site).href}</loc></url>`),
    '</urlset>',
  ].join('\n');

  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
```

- [ ] **Step 3: 构建并验证**

```bash
npm run build
grep "hello-world" dist/rss.xml && grep "https://simiam.com" dist/rss.xml
grep -c "unlisted-sample" dist/rss.xml || echo rss-no-unlisted-ok
grep "posts/hello-world" dist/sitemap.xml && grep "projects/sample-tool" dist/sitemap.xml
grep -Ec "unlisted-sample|bare-tool|draft-sample" dist/sitemap.xml || echo sitemap-filter-ok
```

Expected: RSS/sitemap 含 public 文章与有详情页的作品；unlisted、draft、无详情作品均被过滤。

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add RSS feed and sitemap with visibility filtering"
```

---

### Task 8: 公众号导入脚本（图片本地化）

**Files:**
- Create: `scripts/lib/wechat.mjs`、`scripts/import-wechat.mjs`
- Create: `tests/wechat.test.mjs`、`tests/fixtures/wechat-article.html`

**Interfaces:**
- Consumes: devDependencies `cheerio`、`turndown`（Task 1 已装）
- Produces: `npm run import -- <URL> <slug>` → 生成 `content/posts/YYYY-MM-DD-<slug>/`（index.md + 本地化图片）。`scripts/lib/wechat.mjs` 导出：`extractArticle(html): {title, date, contentHtml}`、`htmlToMarkdown(html): string`、`collectImages(markdown): string[]`、`imageFilename(url, index): string`、`localizeImages(markdown, mapping): string`、`buildIndexMd({title, date, markdown}): string`

- [ ] **Step 1: 创建测试 fixture**

`tests/fixtures/wechat-article.html`：

```html
<html>
  <head>
    <meta property="og:title" content="测试文章标题" />
  </head>
  <body>
    <script>
      var ct = "1752624000";
    </script>
    <div id="js_content">
      <p>第一段内容。</p>
      <img data-src="https://mmbiz.qpic.cn/mmbiz_png/abc123/640?wx_fmt=png" />
      <p>第二段内容。</p>
      <img data-src="https://mmbiz.qpic.cn/mmbiz_jpg/def456/640?wx_fmt=jpeg" />
    </div>
  </body>
</html>
```

- [ ] **Step 2: 写失败的单元测试**

`tests/wechat.test.mjs`：

```js
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
```

- [ ] **Step 3: 运行测试确认失败**

Run: `npm test`
Expected: wechat 相关测试 FAIL（模块不存在），helpers 测试仍 PASS

- [ ] **Step 4: 实现 wechat.mjs**

`scripts/lib/wechat.mjs`：

```js
import * as cheerio from 'cheerio';
import TurndownService from 'turndown';

/** 从公众号文章 HTML 提取标题、发表日期、正文 HTML（img 的 data-src 已还原为 src）。 */
export function extractArticle(html) {
  const $ = cheerio.load(html);
  const title = ($('meta[property="og:title"]').attr('content') || $('#activity-name').text()).trim();
  const m = html.match(/var\s+ct\s*=\s*"(\d+)"/);
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

export function buildIndexMd({ title, date, markdown }) {
  const d = date.toISOString().slice(0, 10);
  return `---\ntitle: ${JSON.stringify(title)}\ndate: ${d}\nsource: wechat\n---\n\n${markdown}\n`;
}
```

- [ ] **Step 5: 运行测试确认通过**

Run: `npm test`
Expected: 全部 PASS

- [ ] **Step 6: 写 CLI 入口**

`scripts/import-wechat.mjs`：

```js
#!/usr/bin/env node
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import {
  extractArticle,
  htmlToMarkdown,
  collectImages,
  imageFilename,
  localizeImages,
  buildIndexMd,
} from './lib/wechat.mjs';

const [url, slug] = process.argv.slice(2);
if (!url || !slug || !/^[a-z0-9-]+$/.test(slug)) {
  console.error('用法: npm run import -- <公众号文章URL> <英文slug>');
  console.error('slug 只能包含小写字母、数字、连字符，例如: my-first-post');
  process.exit(1);
}

const res = await fetch(url, { headers: { 'user-agent': 'Mozilla/5.0' } });
if (!res.ok) {
  console.error(`抓取失败: HTTP ${res.status}。检查链接是否可在浏览器打开。`);
  process.exit(1);
}
const html = await res.text();

const { title, date, contentHtml } = extractArticle(html);
if (!contentHtml.trim()) {
  console.error('未找到正文（#js_content）。文章可能已删除，或该链接需要在微信内打开。');
  process.exit(1);
}

let markdown = htmlToMarkdown(contentHtml);
const dir = path.join('content/posts', `${date.toISOString().slice(0, 10)}-${slug}`);
await mkdir(dir, { recursive: true });

const urls = collectImages(markdown);
const mapping = [];
for (const [i, imgUrl] of urls.entries()) {
  const filename = imageFilename(imgUrl, i);
  const imgRes = await fetch(imgUrl, { headers: { referer: 'https://mp.weixin.qq.com/' } });
  if (!imgRes.ok) {
    console.warn(`⚠️  图片下载失败(HTTP ${imgRes.status})，保留原链接: ${imgUrl}`);
    continue;
  }
  await writeFile(path.join(dir, filename), Buffer.from(await imgRes.arrayBuffer()));
  mapping.push([imgUrl, filename]);
}
markdown = localizeImages(markdown, mapping);

await writeFile(path.join(dir, 'index.md'), buildIndexMd({ title, date, markdown }));
console.log(`✅ 已导入: ${dir}（下载图片 ${mapping.length}/${urls.length} 张）`);
console.log('下一步: npm run dev 预览检查，确认后 npm run publish 发布');
```

- [ ] **Step 7: CLI 冒烟验证（无网络依赖）**

```bash
node scripts/import-wechat.mjs
node scripts/import-wechat.mjs "https://example.com" "Bad_Slug" || echo usage-check-ok
```

Expected: 两次均打印用法说明并以非零码退出，第二次输出 `usage-check-ok`（slug 校验拦截大写/下划线）。

真实 URL 的端到端验证放在 Task 10 之后由站主用真实公众号文章执行（需要网络与真实文章）。

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: add wechat article import script with image localization"
```

---

### Task 9: 发布脚本 + 服务器初始化脚本 + 部署文档

**Files:**
- Create: `scripts/publish.sh`、`scripts/server-setup.sh`、`.deploy.env.example`、`docs/deploy.md`

**Interfaces:**
- Consumes: `.deploy.env`（gitignored）定义 `DOMAIN` / `DEPLOY_HOST` / `DEPLOY_USER` / `DEPLOY_PATH` / `DEPLOY_GIT_REPO` / `SITE_URL`
- Produces: `npm run publish`（构建→rsync，失败 fallback git→健康检查）；`bash scripts/server-setup.sh`（幂等：nginx 配置 + git bare 仓库 + post-receive hook）

- [ ] **Step 1: 创建 .deploy.env.example（只含占位符，不含真实服务器信息）**

`.deploy.env.example`：

```bash
# 复制为 .deploy.env 并填入真实值。.deploy.env 已被 gitignore，不会提交。
DOMAIN=simiam.com
DEPLOY_HOST=your.server.ip
DEPLOY_USER=your-ssh-user
DEPLOY_PATH=/var/www/simiam.com
DEPLOY_GIT_REPO=/opt/site-deploy.git
SITE_URL=https://simiam.com
```

- [ ] **Step 2: 写发布脚本**

`scripts/publish.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .deploy.env ]] || { echo "缺少 .deploy.env（复制 .deploy.env.example 填写后重试）" >&2; exit 1; }
# shellcheck disable=SC1091
source .deploy.env
: "${DEPLOY_HOST:?}" "${DEPLOY_USER:?}" "${DEPLOY_PATH:?}"
REMOTE="${DEPLOY_USER}@${DEPLOY_HOST}"

echo "==> 1/2 构建（含内容 schema 校验）"
npm run build

echo "==> 2/2 同步到 ${DEPLOY_HOST}"
synced=""
if [[ "${DEPLOY_FORCE_GIT:-0}" != "1" ]] && command -v rsync >/dev/null 2>&1; then
  if rsync -az --delete dist/ "${REMOTE}:${DEPLOY_PATH}/"; then
    synced="rsync"
  else
    echo "    rsync 失败，改用 git 同步" >&2
  fi
fi

if [[ -z "$synced" ]]; then
  : "${DEPLOY_GIT_REPO:?git 同步需要 DEPLOY_GIT_REPO}"
  (
    cd dist
    rm -rf .git
    git init -q -b main
    git add -A
    git -c user.name=deploy -c user.email=deploy@local commit -qm "deploy $(date '+%Y-%m-%d %H:%M:%S')"
    git push -q -f "ssh://${REMOTE}${DEPLOY_GIT_REPO}" main
    rm -rf .git
  )
  synced="git"
fi
echo "    同步完成（通道: ${synced}）"

SITE_URL="${SITE_URL:-https://simiam.com}"
if curl -fsS -o /dev/null --max-time 10 "${SITE_URL}/"; then
  echo "✅ 发布成功: ${SITE_URL}"
else
  echo "⚠️  文件已同步，但 ${SITE_URL} 访问检查未通过。"
  echo "    首次部署尚未配置 HTTPS 时属正常，可先访问 http://${DOMAIN:-simiam.com}/ 验证。"
fi
```

- [ ] **Step 3: 写服务器初始化脚本（幂等，可重复执行）**

`scripts/server-setup.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .deploy.env ]] || { echo "缺少 .deploy.env（复制 .deploy.env.example 填写后重试）" >&2; exit 1; }
# shellcheck disable=SC1091
source .deploy.env
: "${DOMAIN:?}" "${DEPLOY_HOST:?}" "${DEPLOY_USER:?}" "${DEPLOY_PATH:?}" "${DEPLOY_GIT_REPO:?}"
REMOTE="${DEPLOY_USER}@${DEPLOY_HOST}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1) nginx 站点配置（HTTP；HTTPS 之后由 certbot --nginx 自动改写）
cat > "${TMP}/site.conf" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};
    root ${DEPLOY_PATH};
    index index.html;
    charset utf-8;

    gzip on;
    gzip_types text/css application/javascript application/xml application/rss+xml image/svg+xml;

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

# 2) git 备用同步通道的 post-receive hook
cat > "${TMP}/post-receive" <<EOF
#!/usr/bin/env bash
set -euo pipefail
git --work-tree="${DEPLOY_PATH}" --git-dir="${DEPLOY_GIT_REPO}" checkout -f main
git --work-tree="${DEPLOY_PATH}" --git-dir="${DEPLOY_GIT_REPO}" clean -fd
EOF

echo "==> 初始化目录与 git 通道"
ssh "${REMOTE}" "mkdir -p '${DEPLOY_PATH}' && { [ -d '${DEPLOY_GIT_REPO}' ] || git init --bare -b main '${DEPLOY_GIT_REPO}'; }"
scp -q "${TMP}/post-receive" "${REMOTE}:${DEPLOY_GIT_REPO}/hooks/post-receive"
ssh "${REMOTE}" "chmod +x '${DEPLOY_GIT_REPO}/hooks/post-receive'"

echo "==> 写入 nginx 配置并重载"
scp -q "${TMP}/site.conf" "${REMOTE}:/etc/nginx/conf.d/${DOMAIN}.conf"
ssh "${REMOTE}" "nginx -t && (systemctl reload nginx 2>/dev/null || nginx -s reload)"

echo "✅ 服务器初始化完成"
echo "下一步: npm run publish 首次发布；HTTPS 配置见 docs/deploy.md"
```

- [ ] **Step 4: 写部署文档**

`docs/deploy.md`：

```markdown
# 部署手册

前提：本地已能免密 SSH 登录服务器（已完成 ssh-copy-id）；`.deploy.env` 已按
`.deploy.env.example` 填好（该文件不进 git，密码不写入任何文件）。

## 首次部署

1. DNS：确认域名 A 记录指向服务器 IP：`dig +short simiam.com`
2. 服务器初始化（幂等，可重复执行）：`bash scripts/server-setup.sh`
3. 首次发布：`npm run publish`，然后访问 http://simiam.com 验证
4. 配置 HTTPS（在服务器上执行，需要人工确认）：
   - 安装 certbot：Ubuntu/Debian 用 `apt install -y certbot python3-certbot-nginx`；
     CentOS/TencentOS 用 `yum install -y certbot python3-certbot-nginx`
   - 签发并自动改写 nginx 配置：
     `certbot --nginx -d simiam.com --agree-tos -m <你的邮箱> --no-eff-email`
   - 验证自动续期：`certbot renew --dry-run`
5. 复查：`curl -I https://simiam.com/` 返回 200；http 应 301 到 https

## 日常发布

`npm run publish` —— 构建（含内容校验）→ rsync 同步 → 健康检查。
rsync 不可用时自动 fallback 到 git 通道（推送到服务器 bare 仓库，hook 自动 checkout）。
强制走 git 通道验证：`DEPLOY_FORCE_GIT=1 npm run publish`

## 安全加固（建议，是否执行由站主决定）

SSH 密钥已配好后，禁用 root 密码登录可大幅降低被爆破风险：

    # 服务器上 /etc/ssh/sshd_config 中设置：
    PasswordAuthentication no
    # 然后 systemctl reload sshd

注意：执行前务必先确认密钥登录正常，否则会把自己锁在门外。

## 回滚

站点是纯静态且内容真源在本地 git：`git checkout <旧提交> -- content/ && npm run publish` 即回滚内容。
```

- [ ] **Step 5: 语法验证**

```bash
chmod +x scripts/publish.sh scripts/server-setup.sh
bash -n scripts/publish.sh && bash -n scripts/server-setup.sh && echo syntax-ok
bash scripts/publish.sh 2>&1 | head -1 || true
```

Expected: `syntax-ok`；最后一条因缺少 `.deploy.env` 而打印「缺少 .deploy.env…」提示（此时尚未创建，属预期）。

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: add publish and server-setup scripts with deploy docs"
```

---

### Task 10: 首次部署上线 + HTTPS + 线上验证

> 本任务操作真实服务器。服务器地址、账号从站主在会话中提供的信息取得，**只写入 `.deploy.env`（gitignored），不得出现在任何提交文件或命令历史可 commit 的位置**。certbot 步骤涉及接受 Let's Encrypt 服务条款，执行前需站主确认。

**Files:**
- Create: `.deploy.env`（本地，不提交）

**Interfaces:**
- Consumes: Task 9 的两个脚本与 docs/deploy.md
- Produces: https://simiam.com 可访问的线上站点

- [ ] **Step 1: 创建 .deploy.env**

复制 `.deploy.env.example` 为 `.deploy.env`，将 `DEPLOY_HOST`、`DEPLOY_USER` 填为站主提供的服务器 IP 与用户名（其余占位值本就正确）。

```bash
cp .deploy.env.example .deploy.env
# 编辑 .deploy.env 填入真实 DEPLOY_HOST / DEPLOY_USER
git status --short | grep -c "deploy.env$" || echo env-not-tracked-ok
```

Expected: `env-not-tracked-ok`（确认 .deploy.env 未被 git 跟踪）。

- [ ] **Step 2: 检查 DNS 解析**

```bash
source .deploy.env
dig +short "$DOMAIN"
```

Expected: 输出 = 服务器 IP。若为空或不符，**暂停并请站主到域名 DNS 控制台把 `simiam.com` 的 A 记录指向服务器 IP**，生效后再继续。

- [ ] **Step 3: 验证 SSH 免密与服务器环境**

```bash
source .deploy.env
ssh -o BatchMode=yes "${DEPLOY_USER}@${DEPLOY_HOST}" "nginx -v && git --version && (command -v rsync || echo no-remote-rsync)"
```

Expected: 免密登录成功、打印 nginx 与 git 版本。若显示 `no-remote-rsync`，rsync 通道不可用，发布会自动走 git 通道（也可顺手在服务器装 rsync）。

- [ ] **Step 4: 服务器初始化**

Run: `bash scripts/server-setup.sh`
Expected: 依次输出「初始化目录与 git 通道」「写入 nginx 配置并重载」「✅ 服务器初始化完成」，无报错。

- [ ] **Step 5: 首次发布并验证 HTTP**

```bash
npm run publish
source .deploy.env
curl -fsS "http://${DOMAIN}/" | grep 聊哉梦呓 && echo http-ok
curl -fsS "http://${DOMAIN}/posts/" -o /dev/null && curl -fsS "http://${DOMAIN}/rss.xml" -o /dev/null && echo pages-ok
```

Expected: `http-ok`、`pages-ok`（此时 HTTPS 健康检查提示未通过属正常）。

- [ ] **Step 6: 验证 git fallback 通道**

Run: `DEPLOY_FORCE_GIT=1 npm run publish`
Expected: 输出「同步完成（通道: git）」，线上内容不变（`curl -fsS http://$DOMAIN/ | grep 聊哉梦呓` 仍命中）。

- [ ] **Step 7: 配置 HTTPS（需站主确认后执行）**

先向站主确认同意接受 Let's Encrypt 服务条款，然后按 docs/deploy.md 第 4 步在服务器上安装 certbot 并执行（邮箱用站主邮箱）：

```bash
source .deploy.env
ssh "${DEPLOY_USER}@${DEPLOY_HOST}" "certbot --nginx -d ${DOMAIN} --agree-tos -m cza55008@gmail.com --no-eff-email --non-interactive"
ssh "${DEPLOY_USER}@${DEPLOY_HOST}" "certbot renew --dry-run"
```

Expected: 证书签发成功；dry-run 续期通过。

- [ ] **Step 8: 线上终验**

```bash
source .deploy.env
curl -fsSI "https://${DOMAIN}/" | head -1                # HTTP/2 200
curl -fsSI "http://${DOMAIN}/" | head -3                 # 301 → https
curl -fsS "https://${DOMAIN}/sitemap.xml" | grep -c "unlisted" || echo sitemap-clean-ok
curl -fsS "https://${DOMAIN}/posts/unlisted-sample/" | grep noindex && echo unlisted-ok
npm run publish
```

Expected: 200 / 301 / `sitemap-clean-ok` / `unlisted-ok`；最后一次 publish 打印「✅ 发布成功: https://simiam.com」。

- [ ] **Step 9: Commit（如有文档修正）并汇报**

```bash
git status --short
# 若 Task 10 过程中修正过脚本或文档：
git add -A && git commit -m "fix: adjust deploy scripts after first production deployment"
```

向站主汇报：线上地址、示例内容位置（正式启用前可删除 sample 文章/作品）、日常操作三板斧（放文件 → dev 预览 → publish）、建议执行的 SSH 安全加固。

---

## 计划外事项（执行时留意）

- **示例内容**：`hello-world`、`unlisted-sample`、`sample-tool`、`bare-tool` 会随首次部署上线，兼作约定示范。站主正式启用时删除对应目录再 publish 即可。
- **导入脚本端到端**：Task 8 只做离线测试；上线后请站主提供一个真实公众号文章 URL 跑一次 `npm run import`，确认图片本地化效果。
- **glob loader 的 id 形态**：`postSlug`/`projectSlug` 已同时兼容 `dir` 与 `dir/index` 两种 id；Task 4 Step 3 的构建验证会实际确认 URL 形态正确。
- **版本记录**：实际安装为 Astro 7.x（计划撰写时按 Astro 5 描述，API 兼容，构建/测试全部通过）；`npm test` 为 `node --test`（计划原文 `node --test tests/` 在 Node 24 上不可用）。

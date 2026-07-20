# 「旧杂志」主题改版 Implementation Plan

> [!WARNING]
> 历史快照：本计划记录 `site/` 仍按独立项目实施时的过程。路径、命令、依赖版本、测试数量和代码片段不再作为当前操作依据；当前规则见 `site/AGENTS.md`，操作见 `site/README.md`。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把站点视觉改版为「暖色旧杂志」：米黄纸感配色、思源宋体分包自托管、刊头/目录页/首字下沉等杂志化版式，夜读暖黑深色。

**Architecture:** 纯视觉层改版——重写 `global.css`（两套配色变量 + 全部版式）、调整 `Base.astro` 刊头页脚结构、少量页面模板加语义类名；字体经 `@fontsource/noto-serif-sc`（unicode-range 分包）自托管，浏览器按需下载。信息架构、URL、内容 schema、脚本一律不动。

**Tech Stack:** Astro 7、@fontsource/noto-serif-sc（400/700/900）、纯 CSS（零客户端 JS）。

## Global Constraints

- **零客户端 JS**：深色只用 `prefers-color-scheme`，不加任何 `<script>`
- 配色精确值以 spec §2 为准（纸色 `--bg:#f6f0e3` / `--fg:#3a3226` / `--accent:#9c4526` 等；夜读 `--bg:#211c15` / `--accent:#cf8a58` 等），语义变量名沿用现有
- 字体权重仅 400/700/900；`font-display: swap`（fontsource 默认）；文章页首屏字体请求量目标 ≤ 300 KB
- 引用块楷体栈：`"Kaiti SC", "STKaiti", "KaiTi", "Noto Serif SC", serif`
- 栏宽 `--max-width: 38rem`；正文 17px / 行高 1.9
- 备案页脚两条信息文字与链接一字不动（样式可调）
- 不改：内容 schema、helpers、导入/发布脚本、RSS/sitemap、robots.txt、privacy.html、shiki 代码高亮配置
- commit message 用英文；不执行 `git push`；每任务结束 `npm run build` + `npm test`（17 项）通过后 commit
- 功能升级需在最终任务把本次改版记入 docs/dreamble-site-vibe-coding.md

---

### Task 1: 字体接入 + global.css 重写 + Base.astro 刊头页脚

**Files:**
- Modify: `package.json`（新增依赖，经 npm install）
- Rewrite: `src/styles/global.css`、`src/layouts/Base.astro`

**Interfaces:**
- Produces: CSS 类供 Task 2 页面使用——`.page-title`、`.foreword`、`.fleuron`、`.post-list`（含 `.leader`）、`.year-head`、`.prose`（首字下沉容器）、`.stamp`、`.cards`/`.card`（含 `.badge-archived`）；Base.astro Props 接口不变 `{ title, description?, noindex? }`

- [ ] **Step 1: 安装字体依赖**

```bash
npm install @fontsource/noto-serif-sc
test -f node_modules/@fontsource/noto-serif-sc/400.css && echo font-pkg-ok
```

Expected: `font-pkg-ok`

- [ ] **Step 2: 重写 src/styles/global.css（整体替换）**

```css
/* ── 「旧杂志」主题 ── 配色：纸色（日间）/ 夜读（暗色） ── */
:root {
  --bg: #f6f0e3;
  --fg: #3a3226;
  --muted: #756750;
  --accent: #9c4526;
  --border: #e2d7c0;
  --card-bg: #faf5ea;
  --max-width: 38rem;
  --serif: "Noto Serif SC", "Songti SC", "SimSun", serif;
  --kai: "Kaiti SC", "STKaiti", "KaiTi", "Noto Serif SC", serif;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #211c15;
    --fg: #d9cfba;
    --muted: #948a76;
    --accent: #cf8a58;
    --border: #3a332a;
    --card-bg: #2a241b;
  }
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: var(--serif);
  font-size: 17px;
  line-height: 1.9;
}

/* ── 刊头 ── */
header.site {
  text-align: center;
  padding: 2.2rem 1rem 0;
}
header.site .brand {
  display: inline-block;
  font-weight: 900;
  font-size: 2rem;
  letter-spacing: 0.35em;
  margin-right: -0.35em;
  color: var(--fg);
  text-decoration: none;
}
header.site nav.menu {
  max-width: var(--max-width);
  margin: 0.9rem auto 0;
  padding: 0.55rem 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: center;
  gap: 2.2rem;
  font-size: 0.85rem;
  letter-spacing: 0.2em;
}
header.site nav.menu a { color: var(--fg); text-decoration: none; }
header.site nav.menu a:hover { color: var(--accent); }

/* ── 正文区 ── */
main {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 2.5rem 1.25rem 4rem;
}

a { color: var(--accent); }
main a {
  color: var(--fg);
  text-decoration: underline;
  text-decoration-color: var(--accent);
  text-underline-offset: 3px;
}
main a:hover { color: var(--accent); }

h1, h2, h3 { line-height: 1.4; font-weight: 700; }

.page-title {
  text-align: center;
  font-size: 1.5rem;
  letter-spacing: 0.2em;
  margin: 0 0 1.6rem;
}

section > h2 {
  text-align: center;
  font-size: 1.15rem;
  letter-spacing: 0.15em;
  margin: 0 0 1rem;
}
h2 .more { font-size: 0.8rem; font-weight: 400; letter-spacing: 0.05em; margin-left: 0.6rem; }

/* 刊首语 / 花式分隔符 */
.foreword {
  font-family: var(--kai);
  text-align: center;
  color: var(--muted);
  max-width: 30rem;
  margin: 0 auto 1rem;
}
.fleuron {
  text-align: center;
  color: var(--muted);
  letter-spacing: 0.5em;
  margin: 2.2rem 0;
}

/* ── 目录式文章列表（dot leaders） ── */
ul.post-list { list-style: none; padding: 0; margin: 0; }
ul.post-list li {
  display: flex;
  align-items: baseline;
  gap: 0.6em;
  padding: 0.45rem 0;
}
ul.post-list .leader {
  flex: 1;
  min-width: 2em;
  border-bottom: 1px dotted var(--muted);
  transform: translateY(-0.25em);
}
ul.post-list time {
  color: var(--muted);
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

/* 归档年份章节 */
.year-head { display: flex; align-items: center; gap: 1rem; margin: 2.4rem 0 0.6rem; }
.year-head h2 { margin: 0; font-size: 1.5rem; letter-spacing: 0.1em; }
.year-head::after { content: ""; flex: 1; border-top: 1px solid var(--border); }

/* ── 文章页 ── */
article > h1 { text-align: center; font-size: 1.7rem; margin: 0 0 0.4rem; }
article .meta {
  text-align: center;
  color: var(--muted);
  font-size: 0.85rem;
  letter-spacing: 0.12em;
  margin-bottom: 2.5rem;
}
article img { max-width: 100%; height: auto; border-radius: 4px; }

/* 首段首字下沉（仅文章详情页 .prose 容器内） */
.prose > p:first-child::first-letter {
  float: left;
  font-size: 3.2em;
  line-height: 1;
  padding: 0.08em 0.12em 0 0;
  font-weight: 700;
  color: var(--accent);
}

/* 公众号「印章」标注 */
.stamp {
  display: inline-block;
  border: 1px solid var(--accent);
  border-radius: 3px;
  color: var(--accent);
  padding: 0 0.4em;
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  margin-left: 0.5em;
}

/* 引用排楷体 */
blockquote {
  margin: 1.6rem 0;
  padding: 0.2rem 1.2rem;
  border-left: 2px solid var(--accent);
  font-family: var(--kai);
  color: var(--muted);
}

/* 代码 */
pre {
  overflow-x: auto;
  padding: 1rem 1.2rem;
  border-radius: 6px;
  font-size: 0.82em;
  line-height: 1.7;
}
code { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }
:not(pre) > code {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 0 0.3em;
  font-size: 0.85em;
}

/* ── 作品纸片卡 ── */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: 1rem;
  padding: 0;
  list-style: none;
}
.card {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1.1rem 1.25rem;
  background: var(--card-bg);
}
.card h3 { margin: 0 0 0.3rem; font-size: 1.05rem; }
.card h3 a { color: var(--fg); text-decoration: none; }
.card h3 a:hover { color: var(--accent); }
.card .tagline { color: var(--muted); margin: 0 0 0.7rem; font-size: 0.9rem; }
.card .links { display: flex; gap: 1rem; font-size: 0.85rem; margin: 0; }
.card .links a { color: var(--accent); text-decoration: none; }
.card .cover { width: 100%; height: auto; border-radius: 4px; margin-bottom: 0.7rem; border: 1px solid var(--border); }
.card .badge-archived {
  position: absolute;
  top: 0.6rem;
  right: 0.6rem;
  border: 1px solid var(--border);
  border-radius: 3px;
  color: var(--muted);
  padding: 0 0.35em;
  font-size: 0.7rem;
}

/* ── 版权页 ── */
footer.site {
  border-top: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.78rem;
  letter-spacing: 0.05em;
  text-align: center;
  padding: 1.8rem 1rem 2.4rem;
}
footer.site a { color: var(--muted); text-decoration: none; }
footer.site a:hover { color: var(--accent); }
footer.site p { margin: 0.35rem 0; }
footer.site .beian img { vertical-align: -2px; margin-right: 2px; }
```

- [ ] **Step 3: 重写 src/layouts/Base.astro（整体替换）**

```astro
---
import '@fontsource/noto-serif-sc/400.css';
import '@fontsource/noto-serif-sc/700.css';
import '@fontsource/noto-serif-sc/900.css';
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
      <a class="brand" href="/">聊哉梦呓</a>
      <nav class="menu">
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

- [ ] **Step 4: 构建验证（字体分包落地 + 备案不丢）**

```bash
npm run build
ls dist/_astro/*.woff2 | wc -l          # 预期 > 50（分包数量级）
grep -rl "Noto Serif SC" dist/_astro/*.css | head -1   # 字体 CSS 存在
grep "闽ICP备18023112号" dist/index.html && grep "35012102500070" dist/index.html
grep -c "<script" dist/index.html || echo zero-js-ok
npm test
```

Expected: 分包数量 > 50、字体 CSS 命中、备案两条命中、`zero-js-ok`、17/17 PASS。

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: rebuild theme foundation with paper palette, serif webfonts, and masthead layout"
```

---

### Task 2: 页面模板杂志化

**Files:**
- Modify: `src/pages/index.astro`（整体替换）、`src/pages/posts/index.astro`（整体替换）、`src/pages/posts/[slug].astro`（整体替换）、`src/components/ProjectCard.astro`（整体替换）
- Modify: `src/pages/projects/index.astro`、`src/pages/about.astro`（仅 h1 加类名）

**Interfaces:**
- Consumes: Task 1 的 CSS 类（`.page-title`/`.foreword`/`.fleuron`/`.leader`/`.year-head`/`.prose`/`.stamp`/`.badge-archived`）；`src/lib/helpers.mjs` 的 `postSlug`/`projectSlug`/`isListed`/`sortByDateDesc`（不变）
- Produces: 无新接口（终态页面）

- [ ] **Step 1: 重写 src/pages/index.astro（整体替换）**

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
  <p class="foreword">
    安哥的文字与作品。文章一部分备份自微信公众号「聊哉梦呓」，一部分为本站独立发表；工具软件皆为自研。
  </p>

  <p class="fleuron">❦</p>

  <section>
    <h2>最新文章<a class="more" href="/posts/">全部 →</a></h2>
    <ul class="post-list">
      {
        posts.map((p) => (
          <li>
            <a href={`/posts/${postSlug(p.id)}/`}>{p.data.title}</a>
            <span class="leader" />
            <time>{p.data.date.toISOString().slice(0, 10)}</time>
          </li>
        ))
      }
    </ul>
  </section>

  <p class="fleuron">❦</p>

  <section>
    <h2>作品<a class="more" href="/projects/">全部 →</a></h2>
    <ul class="cards">
      {projects.map((project) => <ProjectCard project={project} />)}
    </ul>
  </section>
</Base>
```

（说明：原首页的 `<h1>聊哉梦呓</h1>` 删除——刊头即站名，避免重复。）

- [ ] **Step 2: 重写 src/pages/posts/index.astro（整体替换）**

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
  <h1 class="page-title">文章</h1>
  {
    years.map((year) => (
      <section>
        <div class="year-head">
          <h2>{year}</h2>
        </div>
        <ul class="post-list">
          {byYear.get(year)!.map((p) => (
            <li>
              <a href={`/posts/${postSlug(p.id)}/`}>{p.data.title}</a>
              <span class="leader" />
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

- [ ] **Step 3: 重写 src/pages/posts/[slug].astro（整体替换）**

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
      <time datetime={dateStr}>{dateStr.replaceAll('-', ' · ')}</time>
      {post.data.tags.length > 0 && <span> · {post.data.tags.join(' / ')}</span>}
      {post.data.source === 'wechat' && <span class="stamp">首发于公众号「聊哉梦呓」</span>}
    </p>
    <div class="prose"><Content /></div>
  </article>
</Base>
```

- [ ] **Step 4: 重写 src/components/ProjectCard.astro（整体替换，archived 淡化改角标）**

```astro
---
import { Image } from 'astro:assets';
import { projectSlug } from '../lib/helpers.mjs';

const { project } = Astro.props;
const slug = projectSlug(project.id);
const hasDetail = Boolean(project.body?.trim());
---

<li class="card">
  {project.data.status === 'archived' && <span class="badge-archived">已归档</span>}
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

- [ ] **Step 5: projects/index.astro 与 about.astro 的 h1 加 page-title 类**

`src/pages/projects/index.astro`：`<h1>作品</h1>` → `<h1 class="page-title">作品</h1>`
`src/pages/about.astro`：`<h1>{frontmatter.title}</h1>` → `<h1 class="page-title">{frontmatter.title}</h1>`

- [ ] **Step 6: 构建验证**

```bash
npm run build
grep "foreword" dist/index.html && grep -c "leader" dist/index.html
grep "year-head" dist/posts/index.html
grep "stamp" dist/posts/wx-kit-intro/index.html && grep "prose" dist/posts/wx-kit-intro/index.html
grep "2026 · 06 · 17" dist/posts/wx-kit-intro/index.html
grep -c "<h1" dist/index.html || echo home-no-h1-ok
npm test
```

Expected: 各类名命中；文章页日期为 `2026 · 06 · 17` 格式；首页无 `<h1>`（`home-no-h1-ok`）；17/17 PASS。

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: apply magazine typography to page templates"
```

---

### Task 3: 视觉实测 + 发布上线 + 收尾（控制器执行）

**Files:**
- Modify: `docs/dreamble-site-vibe-coding.md`（新增改版记录）

**Interfaces:**
- Consumes: Task 1-2 的全部产出

- [ ] **Step 1: 本地视觉实测**

`npm run dev` 起本地预览，浏览器逐项检查（浅色 × 深色 × 桌面 × 375px 移动宽度）：

- 首页：刊头居中、刊首语楷体、目录点线、卡片纸片感
- 归档页：年份章节线
- 文章页（wx-kit-intro）：标题居中、meta 中圆点、首字下沉赭红、印章标注、图片圆角
- 作品墙 + 详情、关于页
- 深色：暖黑而非冷黑，无刺眼纯白元素

发现视觉问题当场修（CSS 微调属本任务范围），修完重跑 `npm run build && npm test`。

- [ ] **Step 2: 记录开发日志**

按 docs/dreamble-site-vibe-coding.md「记录约定」新增条目：动机（站主反馈无设计感）、变更（配色/字体/版式要点 + 引用 spec 路径）、验证（构建/单测/视觉实测/字体请求量）、遗留。

- [ ] **Step 3: Commit + 发布**

```bash
git add -A && git commit -m "docs: log magazine theme redesign"
npm run publish
```

- [ ] **Step 4: 线上验证（含字体预算硬指标）**

```bash
curl -fsS https://simiam.com/ | grep -c "foreword"
curl -fsS https://simiam.com/posts/wx-kit-intro/ | grep -c "stamp"
# 字体首屏请求量：浏览器打开文章页，DevTools/Network 过滤 woff2 统计传输量
```

Expected: 线上类名命中；文章页首屏 woff2 传输总量 ≤ 300 KB（超标则把 900 权重仅用于刊头的字符做 font-family 降级排查，或去掉 900 只用 700）。

- [ ] **Step 5: 向站主汇报**

改版前后对比要点、字体请求量实测值、遗留事项。

---

## 计划外事项（执行时留意）

- fontsource 分包 CSS 引用全部权重文件会被 Astro 打进同一 CSS bundle，属预期；浏览器靠 unicode-range 只取所需 woff2
- 首页删除 `<h1>` 后语义上站名由刊头 `<a class="brand">` 承担，个人站可接受；若在意可后续给 brand 换 `<h1>` 包裹（仅首页），本次 YAGNI
- shiki 代码块保持现状（深色卡片感），如日后想要纸感代码主题再单独立项

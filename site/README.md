# 聊哉梦呓 · dreamble-site

个人站点 [simiam.com](https://simiam.com)：微信公众号「聊哉梦呓」的文章备份与独立发表，以及自研工具软件的作品展示。

本站代码位于 `dreamble` 源码仓库的 `site/` 子目录，不再是独立 Git 仓库。文章唯一真源是 `site/content/posts/`；仓库根目录的 `articles` 是兼容旧工作流的符号链接，指向同一目录。

## 核心理念

**目录即数据库，放文件即发表。** 没有后台、没有数据库、没有在线编辑器——把一个 markdown 目录放进约定位置，跑一条命令，就完成发表。约定不靠自觉：目录命名、日期一致性、slug 唯一性和 frontmatter 都由构建命令强制校验，填错会直接报错并指明原因。

## 首次准备

项目要求 Node 22.12 以上，推荐使用仓库 `.nvmrc` 固定的版本：

```bash
cd site
nvm use
npm ci
npm run verify
```

从 `dreamble` 仓库根目录执行站点命令时，也可以使用 `npm --prefix site run <命令>`。

## 发表文章

以发表一篇《我的第一篇文章》为例，从零到上线四步：

**第 1 步：建目录。** 在 `content/posts/` 下新建一个目录，命名规则为 `日期-英文slug`（slug 用小写字母、数字、连字符，它决定文章 URL）：

```bash
mkdir content/posts/2026-07-18-my-first-post
```

**第 2 步：写 `index.md`。** 在该目录下创建 `index.md`，开头是 frontmatter（两行 `---` 之间），后面是 markdown 正文。一篇最简文章只需要 `title` 和 `date`：

```markdown
---
title: 我的第一篇文章
date: 2026-07-18
summary: 这篇文章讲了什么（显示在列表页，可省略）
tags: [AI, 工具]
---

正文从这里开始，标准 markdown 语法。

插图放在与 index.md 相同的目录里，用相对路径引用：

![配图说明](./cover.png)
```

全部可用的 frontmatter 字段：

| 字段 | 必填 | 默认值 | 作用 |
|---|---|---|---|
| `title` | ✅ | — | 标题 |
| `date` | ✅ | — | 发表日期，格式 `2026-07-18` |
| `summary` | — | 取正文开头 | 列表页摘要 |
| `tags` | — | 无 | 标签，如 `[AI, 工具]` |
| `source` | — | 本站原创 | 填 `wechat` 表示公众号备份，文章页会标注「首发于微信公众号」 |
| `visibility` | — | `public` | 填 `unlisted`：页面存在但不进列表/RSS/sitemap、不被搜索引擎收录，只有拿到链接的人能看 |
| `draft` | — | `false` | 填 `true`：草稿，完全不构建，怎么发布都不会上线 |

字段拼错、出现未知字段、缺必填项，构建会直接报错并指明是哪个文件的哪个字段——错的内容发不出去。

目录本身也会校验：目录日期必须与 `date` 一致，不同文章不能使用同一个 slug，否则它们会争抢同一个 URL。

**第 3 步：本地预览（可选）。** 运行 `npm run dev`，按提示打开浏览器，所见即最终效果，改动实时刷新。

**第 4 步：发布。** 运行 `npm run publish`，构建成功后自动同步到服务器。文章上线地址为 `https://simiam.com/posts/my-first-post/`（即目录名去掉日期的部分）。

### 备份公众号文章（自动导入）

不用手动建目录，一条命令搞定：

```bash
npm run import -- "https://mp.weixin.qq.com/s/xxxx" my-first-post
```

它会自动完成：抓取正文转 markdown → 下载全部图片到文章目录并改写为相对链接（解决微信图床防盗链，站外引用会裂图的问题）→ 按文章**原发日期**生成目录和 frontmatter（自动带 `source: wechat`）。

> 抗反爬说明：本机装有 [wx-kit](https://github.com/monkeychen/wx-kit) 时自动优先走它（真实客户端通道，不受微信反爬影响）；未安装则用内置抓取，部分文章可能被微信拦截，此时装上 wx-kit 即可。

**批量备份历史文章**：准备一个清单文件（每行 `<文章URL> <英文slug>`，支持 `#` 注释与空行），然后：

```bash
npm run import -- --file backlog.txt
```

- 已存在同 slug 的文章自动跳过——**重跑同一清单只补新的**，适合增量备份
- 导入先写入暂存目录，正文和图片全部完成后才原子落到 `content/posts/`；失败不会留下被误判为成功的半成品
- 单篇失败不中断整批，结束时汇总失败清单，修正后重跑同一文件即可

导入后人工检查一眼（若有图片下载失败会警告并保留原链接），确认没问题再 `npm run publish`。

## 上架作品

与文章同理：一个作品一个目录，放进 `content/projects/`，目录名即 URL slug。

**第 1 步：建目录、放截图、写 `index.md`：**

```
content/projects/my-tool/
├── index.md
└── screenshot.png
```

```markdown
---
name: 我的工具
tagline: 一句话说清这个工具帮用户做什么。
cover: ./screenshot.png
links:
  download: https://example.com/download
  repo: https://github.com/you/my-tool
order: 1
---

## 这是详情页正文

写功能介绍、使用说明、常见问题、更新记录——面向使用者的中文说明书。

**正文也可以完全留空**：留空则该作品只在作品墙显示一张卡片
（名称 + 简介 + 链接按钮），不生成详情页。适合介绍已在别处
（如 GitHub README）写清楚的作品。
```

全部可用的 frontmatter 字段：

| 字段 | 必填 | 默认值 | 作用 |
|---|---|---|---|
| `name` | ✅ | — | 工具名 |
| `tagline` | ✅ | — | 一句话简介，显示在卡片上 |
| `links` | ✅（至少一项） | — | 三种链接分别渲染为按钮：`download`（下载）/ `repo`（源码）/ `website`（网站） |
| `cover` | — | 无图 | 卡片配图，相对路径 |
| `status` | — | `active` | 填 `archived`：卡片沉底并淡化显示，表示不再维护 |
| `order` | — | 999 | 卡片排序权重，数字越小越靠前 |

**第 2 步：发布。** 同样是 `npm run dev` 预览、`npm run publish` 上线。作品出现在 `https://simiam.com/projects/`，有正文的作品详情页在 `https://simiam.com/projects/my-tool/`。

> 两类内容的现成参照：文章可参考 `content/posts/2026-07-18-build-site-with-ai/`，作品可参考 `content/projects/wx-kit/`。

## 常用命令

| 命令 | 作用 |
|---|---|
| `npm run dev` | 本地预览 |
| `npm run check` | 内容约束校验 + Astro 类型检查 |
| `npm run build` | 内容约束校验 + 静态构建 |
| `npm test` | 单元测试 |
| `npm run verify` | 提交/发布前完整验收：check + test + build |
| `npm run import -- <URL> <slug>` | 导入公众号文章 |
| `npm run publish` | 构建并发布到服务器（rsync 优先，失败时走部署 Git fallback） |

## 架构

Astro 静态站点。内容真源在 `dreamble` 源码仓库，服务器上只有 nginx + 静态文件，零应用进程。

```
site/content/ 放文件 → npm run publish → 完整验收（失败则线上不变）→ rsync 同步（失败自动走部署 Git fallback）→ nginx → 线上健康检查
```

这里有两套相互独立的 Git：源码 Git 管理整个 `dreamble` 仓库，是否 `git push origin` 由站主明确决定；部署 Git fallback 只把生成的 `dist/` 临时推送到服务器 bare repo，是 `npm run publish` 的备用同步机制，不包含源码，也不会改写源码仓库历史。

```
├── content/          # 内容（文章 / 作品 / 关于页）—— 日常唯一要碰的目录
├── src/              # Astro 站点代码（schema 定义在 src/content.config.ts）
├── scripts/          # 导入 / 发布 / 服务器初始化脚本
├── public/           # 原样输出的静态文件（robots.txt、独立页面等）
└── docs/             # 设计文档 / 部署手册 / 开发日志
```

## 文档

- [设计文档](docs/superpowers/specs/2026-07-16-dreamble-site-design.md) —— 需求分析与全部架构决策的理由
- [部署手册](docs/deploy.md) —— 首次部署、HTTPS、回滚（服务器信息在 gitignored 的 `.deploy.env`，不进仓库）
- [开发日志](docs/dreamble-site-vibe-coding.md) —— 每次功能升级/优化的记录

## 版权

`content/` 目录下的文章与图片为站主原创内容，保留所有权利，转载请联系授权；代码部分可自由参考。

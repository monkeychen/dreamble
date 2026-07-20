# 聊哉梦呓 · dreamble-site

个人站点 [simiam.com](https://simiam.com)：微信公众号「聊哉梦呓」的文章备份与独立发表，以及自研工具软件的作品展示。

## 核心理念

**目录即数据库，放文件即发表。** 没有后台、没有数据库、没有在线编辑器——把一个 markdown 目录放进约定位置，跑一条命令，就完成发表。约定不靠自觉：frontmatter 由构建时 schema 强制校验，填错直接报错并指明文件与字段。

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

字段拼错、缺必填项，构建会直接报错并指明是哪个文件的哪个字段——错的内容发不出去，放心写。

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

> 两类内容的现成参照：仓库里的示例内容（`content/posts/2026-07-16-hello-world/`、`content/projects/sample-tool/` 等）就是按约定写的活模板，照着改即可。

## 常用命令

| 命令 | 作用 |
|---|---|
| `npm run dev` | 本地预览 |
| `npm run build` | 构建（含内容 schema 校验） |
| `npm test` | 单元测试 |
| `npm run import -- <URL> <slug>` | 导入公众号文章 |
| `npm run publish` | 构建并发布到服务器 |

## 架构

Astro 静态站点。内容真源在本地 git 仓库，服务器上只有 nginx + 静态文件，零应用进程。

```
content/ 放文件 → npm run publish → 构建（校验失败则线上不变）→ rsync 同步（失败自动 fallback git 通道）→ nginx
```

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

# 聊哉梦呓 · dreamble

「聊哉梦呓」的产品、内容与 AI 工作流仓库。

这里集中维护个人站 [simiam.com](https://simiam.com)、移动端文档阅读器、公众号写作 Skills 和提示词资料。各目录都是独立的工作单元，按各自说明运行，不在仓库根目录设置统一构建命令。

## 仓库内容

| 目录 | 内容 | 当前入口 |
|---|---|---|
| [`site/`](site/) | 「聊哉梦呓」个人站：文章备份、独立发表与作品展示 | [`site/README.md`](site/README.md) |
| [`apps/x-reader/`](apps/x-reader/) | 面向移动端的本地文档阅读器，支持 HTML、Markdown、JSON、Log 和纯文本 | [`apps/x-reader/GEMINI.md`](apps/x-reader/GEMINI.md) |
| [`skills/`](skills/) | 选题、素材搜集、正文写作、事实审校、标题打磨、证券研究等 Agent Skills | [`skills/README.md`](skills/README.md) |
| [`prompts/`](prompts/) | 提示词方法与可复用提示词资料 | [`prompts/prompting-guide.md`](prompts/prompting-guide.md) |

仓库根目录的 `articles` 是兼容旧工作流的符号链接，实际指向 `site/content/posts/`。文章只有这一份真源，不要在根目录另建副本。

## 快速开始

### 个人站

个人站使用 Astro 构建，要求 Node.js 22.12.0 以上，推荐使用 `site/.nvmrc` 中固定的版本。

```bash
cd site
nvm use
npm ci
npm run verify
npm run dev
```

从仓库根目录也可以运行：

```bash
npm --prefix site run verify
npm --prefix site run dev
```

日常内容放在：

- 文章：`site/content/posts/YYYY-MM-DD-<slug>/index.md`
- 作品：`site/content/projects/<slug>/index.md`

导入公众号文章：

```bash
npm --prefix site run import -- "https://mp.weixin.qq.com/s/xxxx" article-slug
```

完整的内容格式、发布方式和部署说明见 [`site/README.md`](site/README.md)。

### x-reader

x-reader 使用 Capacitor、Vite 和 TypeScript 开发，目前仓库包含 Web 端与 Android 工程。

```bash
cd apps/x-reader
npm ci
npm run build
npm run dev
```

产品目标是让用户从微信等应用的“用其他应用打开”入口直接阅读本地文档，并在应用沙盒中保留离线副本。技术方案与目录约束见 [`apps/x-reader/GEMINI.md`](apps/x-reader/GEMINI.md)。

## 外部依赖：Skills

`skills/` 存放本站开发的 Agent Skills 源码，是**开发目录**，不会自动被 AI 工具加载；要用哪个技能，需自行复制到你的用户级或项目级 skills 目录。

其中 `skills/wechat-site-publisher` 运行时依赖第三方开源项目 [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) 的技能：

| 依赖技能 | 用途 | 强度 |
|---|---|---|
| `baoyu-post-to-wechat` | 写入微信公众号草稿 | 必需 |
| `baoyu-cover-image` | 生成封面图（用户未提供封面时） | 条件必需 |
| `baoyu-article-illustrator` | 生成正文插图 | 可选 |

**这些依赖本项目不提供，需自行安装**，放到能被你的 AI 工具扫描到的位置即可（用户级如 `~/.workbuddy/skills/`，项目级如 `.codebuddy/skills/`）：

```bash
npx skills add jimliu/baoyu-skills
```

依赖强度分级与缺失时的降级行为，以 [`skills/wechat-site-publisher/SKILL.md`](skills/wechat-site-publisher/SKILL.md) 的「环境检查」章节为准。

## 项目结构

```text
dreamble/
├── apps/
│   └── x-reader/       # 移动端本地文档阅读器
├── site/               # Astro 静态个人站
├── skills/             # Agent Skills
├── prompts/            # 提示词与学习资料
└── articles -> site/content/posts
```

## 开发约定

- 进入子项目后，先阅读该目录内的 `AGENTS.md`、`CLAUDE.md` 或其他协作规范。
- 修改后运行对应项目的验证命令；站点提交前必须通过 `npm --prefix site run verify`。
- 密钥、部署账号、Token 和本地环境文件不得提交。
- 提交信息使用简洁英文。

## 版权

文章、图片及其他原创内容保留所有权利，转载请联系授权。代码和 Skills 如需复用，请先检查对应目录中的说明；仓库当前未声明统一的开源许可证。

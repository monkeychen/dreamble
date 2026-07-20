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
- 每次功能升级/优化（发表文章、上架作品除外）必须在 commit 前同步记录到 docs/dreamble-site-vibe-coding.md（格式见该文件的「记录约定」）

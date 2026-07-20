# dreamble-site 项目规范

个人站「聊哉梦呓」（simiam.com）：公众号文章备份、独立发表和工具作品展示。
本站是纯静态 Astro 项目，服务器只运行 nginx，不引入后台、数据库或客户端 JavaScript。

## 先守规则，再改实现

- 本文件是 `site/` 的规则真源。规则需要调整时，先改本文件，再改代码和内容。
- 优先维护低认知负担的内容工作流：日常发表只需要操作 `content/`。
- 功能升级或优化必须同步记录到 `docs/dreamble-site-vibe-coding.md`；发表文章、上架作品除外。
- 不为技术完整性增加用户不需要的后台、在线编辑器、评论、统计或搜索功能。

## 运行时与命令

- Node 版本以 `.nvmrc` 为准；首次进入目录执行 `nvm use && npm ci`。
- `npm run dev`：本地预览。
- `npm run check`：内容策略校验和 Astro 类型检查。
- `npm test`：单元测试。
- `npm run build`：内容策略校验和静态构建。
- `npm run verify`：提交前完整验收，必须全部通过。
- `npm run import -- <公众号文章URL> <英文slug>`：导入公众号文章。
- `npm run publish`：完整验收后发布到服务器。

## 内容目录约定

- 文章：`content/posts/YYYY-MM-DD-<slug>/index.md`，图片与正文同目录并使用相对引用。
- 文章目录日期必须与 frontmatter 的 `date` 相同。
- 不同文章的 `<slug>` 必须唯一；不能依靠日期区分同名 slug，因为 URL 会去掉日期。
- 作品：`content/projects/<slug>/index.md`。
- slug 只能包含小写字母、数字和单个连字符，不能以连字符开头或结尾。
- frontmatter 字段以 `src/content.config.ts` 为准，未知字段也必须构建失败。
- `draft: true` 的文章不生成页面；`unlisted` 文章仅生成带 `noindex` 的详情页，不进入列表、RSS 和 sitemap。
- 导入内容必须先在暂存目录完整写入，再原子移动到正式目录；失败时不能留下会被误判为已发布的半成品。

## Git、部署与安全

- commit message 使用简洁英文。
- 不自动 `git push`，等待站主明确要求。
- 服务器地址、账号只放在 gitignored 的 `.deploy.env`；密码、密钥、token 不进入仓库。
- 发布后的站点健康检查失败必须以非零状态退出，不能把“同步完成”冒充“发布成功”。
- 部署与 HTTPS 操作按 `docs/deploy.md` 执行。

## 完成标准

代码或配置变更完成前必须执行：

```bash
npm run verify
```

页面、样式或元数据变更还要检查生成后的关键页面；内容策略变更必须有对应回归测试。

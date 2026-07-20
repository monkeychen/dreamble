# dreamble-site 开发日志（vibe coding log）

本文件记录站点的每次功能升级与优化。**发表文章/上架作品不记录在此**（那是内容操作，git 历史即记录）。

## 记录约定

- 新条目追加在「记录」节顶部（新在上，旧在下）
- 每条包含：日期、动机（为什么做）、变更内容、验证方式、遗留事项
- 由当次执行变更的人/AI 在 commit 前一并写入

---

## 记录

### 2026-07-20 · 合并后仓库与部署边界同步

**动机**：站点已从独立仓库合并到 `dreamble/site`，但部分脚本仍依赖调用者位于 `site/`，文档也混用了源码 Git 与服务器部署 Git；这会导致从仓库根目录直接调用脚本时读取错误目录，并让发布通道的权限边界难以判断。
**变更**：先更新 `AGENTS.md`，明确 monorepo、内容唯一真源与两套 Git 的边界；Node 脚本统一从自身文件位置解析 `site/`，不再依赖当前工作目录，并补跨目录回归测试；README、部署手册、设计文档、历史计划提示和部署脚本术语同步到当前结构；回滚命令改为从仓库根目录显式操作 `site/content/`。
**验证**：`npm --prefix site run verify` 全过，Astro 检查 0 error / 0 warning / 0 hint，28 项单测全过；从仓库根目录与 `/tmp` 直接执行内容校验均成功。`DEPLOY_FORCE_GIT=1 npm --prefix site run publish` 实测输出 `通道: git-fallback`，服务器 bare repo 生成新的 deploy 提交并由 hook 完成 checkout；线上 15 个页面/静态资源均返回 200，HTTP 301 到 HTTPS，RSS 4 篇、sitemap 9 个 URL。
**遗留**：无。

### 2026-07-20 · Markdown 表格旧杂志主题

**动机**：Astro 能解析 GFM 表格，但站点没有表格样式，默认呈现缺少边界和层次；宽表格在手机端还可能撑破页面。
**变更**：为 Markdown 生成的表格增加账页式表头、暖色细边框、隔行底色、悬停反馈和等宽数字；深浅主题分别使用语义色变量；表格最大宽度限制在正文内，列数较多时仅表格区域横向滚动。
**验证**：`npm run verify` 全过；Playwright 实测浅色桌面、浅色 375px 手机和深色 375px 手机。移动端页面宽度与视口同为 375px，无整页横向溢出；8 列宽表格可视宽度 333px、内容宽度 832px，横向滚动仅发生在表格内部。
**遗留**：无。

### 2026-07-20 · 合并后可靠性闭环

**动机**：站点合并进 `dreamble/site` 后，直接运行会误用 Node 16；同时“约定不靠自觉”只覆盖了已声明 frontmatter 字段，非法目录、未知字段和重复 slug 仍可能构建成功，导入中断也可能留下会被批量任务跳过的半成品。
**变更**：新增 `AGENTS.md` 作为唯一规范源，固定 Node 24；增加目录格式、日期一致性、slug 唯一性和未知字段校验；接入 `astro check` 与统一 `npm run verify`；微信导入改为同盘暂存后原子移动，并区分完整文章与半成品；发布健康检查失败改为非零退出；补齐 Open Graph/Twitter 基础分享元数据。
**验证**：`npm run verify` 全过；Astro 类型检查 0 error / 0 warning / 0 hint；26 项单测全过；故意加入未知字段 `summray` 时构建按预期失败；生成产物内部链接完整且保持零客户端 JS。
**遗留**：暂未配置分享封面图，当前社交卡片提供准确标题、摘要和 URL，但不会显示专用大图。

### 2026-07-18 · 补全站点 favicon

**动机**：站点无 favicon，浏览器标签为默认灰图标，体验缺口。
**变更**：新增 `public/favicon.svg`（「聊」字印章式图标，赭红字 + 纸色圆角底，SVG 内 `prefers-color-scheme` 媒体查询深浅自适应，与主题配色一致）；`public/apple-touch-icon.png`（180×180，由 SVG 经 macOS qlmanage 渲染，兜底不支持 SVG favicon 的 iOS Safari）；`Base.astro` head 增 `rel=icon`(svg) + `apple-touch-icon` + 深浅两套 `theme-color`（让浏览器地址栏/移动状态栏配色跟随站点）。
**验证**：build 后 dist 含两文件、head link 正确；线上 `/favicon.svg` 与 `/apple-touch-icon.png` 返回 200；17 项单测无影响。
**遗留**：无。SVG 中「聊」字依赖系统衬线字体渲染，跨设备字形略有差异但「聊」字通用可读。

### 2026-07-17 · 「旧杂志」主题改版

**动机**：站主反馈原主题为功能性默认样式、无设计感，确定「暖色旧杂志」方向（设计决策与配色/版式细节见 [spec](superpowers/specs/2026-07-17-magazine-theme-design.md)）。
**变更**：纯视觉层改版——米黄纸底/夜读暖黑两套配色（`prefers-color-scheme`，零 JS 不变）；思源宋体 400/700/900 经 @fontsource unicode-range 分包自托管，引用块楷体；刊头式布局、首页刊首语与目录点线、归档年份章节、文章页居中标题/中圆点日期/赭红首字下沉/公众号印章标注、作品纸片卡与已归档角标、版权页式页脚、❦ 分隔符。栏宽最终由 38rem 调整为 50rem。信息架构/URL/schema 未动。
**验证**：build + 17 项单测通过；浏览器实测纸色/夜读 × 桌面/375px 移动 × 首页/文章/作品墙全过；构建产物 294 个字体分包、零 `<script>`、备案信息完整；发布后线上抽查 + 文章页首屏字体请求量实测（目标 ≤ 300 KB）。
**遗留**：shiki 代码块保持深色卡片样式（纸感代码主题日后单独立项）；首页 h1 为视觉隐藏元素（.visually-hidden），刊头 brand 仍为链接。
**上线后修订（同日）**：① 字体预算实测 ~1.4 MB（38 分包，正文 400 权重占 ~925 KB），原 ≤300 KB 目标对全站衬线方案不可达，站主确认接受首访 ≤1.5 MB，nginx 对 `/_astro/` 下发 `Cache-Control: public, immutable`（server-setup.sh 已同步），回访字体流量为 0；② 修复下划线越界：spec 本意「正文内链接」被实现成 `main a` 全局，目录列表/「全部→」/作品功能链接被误加下划线，现收窄为 `article a` 并对功能性链接显式去线；③ 栏宽由杂志窄栏 38rem 经 44rem 最终调为 50rem（站主反馈阅读区过窄，阅读舒适度优先于窄栏形式感，spec §3 已同步）。

### 2026-07-17 · 导入命令支持批量备份历史文章

**动机**：逐篇执行 `npm run import` 备份历史文章效率太低，需要一次交付整批。
**变更**：`npm run import -- --file <清单文件>` 批量模式，清单每行 `<URL> <slug>`（支持 # 注释/空行）。幂等设计：已存在同 slug 的文章目录自动跳过，重跑同一清单只补新的；单篇失败（含非法行）不中断整批，结束汇总成功/跳过/失败清单，有失败则退出码 1。单篇复用双通道 `importOne()`（wx-kit 优先）。新增纯函数 `parseBatchFile()`、`findPostDir()`。
**验证**：单测 17/17（新增 2 项）；真实清单端到端：已存在文章正确跳过、新文章走 wx-kit 通道导入成功、非法 slug 与格式错误行正确报告、退出码 1；单篇模式与用法提示回归通过；build 通过。
**遗留**：清单需人工准备 slug；日后若接 wx-kit 的 crawl（按公众号批量爬取）可自动生成清单草稿。

### 2026-07-17 · 导入命令抗微信反爬：优先走本机 wx-kit CLI

**动机**：`npm run import` 的内置抓取被微信反爬拦截（非浏览器请求返回无正文的验证页），首篇真实文章导入即失败。而站主自研的 wx-kit 走真实客户端通道，实测可稳定下载。
**变更**：`scripts/import-wechat.mjs` 重构为双通道——检测到本机 `wx-kit` CLI 则优先调用（`download --formats md,meta`，解析其 JSON 输出与 content.md 产物，图片由 wx-kit 本地化后拷入文章目录）；未安装或失败时自动回落原内置抓取，回落也失败时提示安装 wx-kit。新增 `fromWxkit()` 解析函数（提取标题/东八区日期、去 frontmatter 与重复 H1、图片路径改写为本站约定），`buildIndexMd()` 兼容字符串日期。
**验证**：单测 15/15（新增 3 项覆盖 fromWxkit 与字符串日期）；真实文章端到端导入走 wx-kit 通道成功（原发日期、8 图本地化、frontmatter 合规）；无效 slug 仍正确拒绝（exit 1）；build 通过。
**遗留**：wx-kit 通道依赖本机安装（README 已注明）；批量导入场景日后可加 `--urls-file` 透传。

### 2026-07-17 · 新增 x-reader 隐私政策静态页

**动机**：x-reader 应用（上架/合规）需要一个公网可访问的隐私政策页面。
**变更**：从 x-reader 项目复制 `privacy.html` 到 `public/privacy.html`（自包含单文件，Astro 原样输出到站点根路径，不走内容集合）。
**验证**：构建后 `dist/privacy.html` 存在且内容正确；线上 `https://simiam.com/privacy.html` 返回 200。
**遗留**：无。注意该页面是 x-reader 项目的副本，源头更新时需重新复制。

### 2026-07-16 ~ 2026-07-17 · 项目创建与首次上线

**动机**：需要一个个人站点：① 备份微信公众号「聊哉梦呓」文章 + 发表不适合公众号的文章；② 展示自研工具软件。核心约定：目录即数据库，放 markdown 文件即发表，无在线编辑、无后台、无数据库。

**技术选型与架构**（决策理由见 [设计文档](superpowers/specs/2026-07-16-dreamble-site-design.md)）：
- Astro 静态站点（实际安装 7.x），Content Collections 对 frontmatter 做构建时 schema 强制校验——约定由机器执行而非文档自觉
- 内容真源在本地 git 仓库；服务器上只有 nginx + 静态文件，零应用进程
- 发布链路：`npm run publish` = 构建（失败则线上不变）→ rsync 同步（失败自动走部署 Git bare repo + hook 通道；与源码 Git 无关）
- unlisted 文章三重隔离（不进列表/RSS/sitemap + noindex）；draft 完全不构建

**交付内容**（原独立 `dreamble-site` 仓库中的 13 个提交，`af8363b..23f5d48`；这些提交哈希未随内容合并进入当前 `dreamble` 仓库，仅作为历史记录）：
- 页面：首页、文章归档/详情、作品卡片墙/详情（正文为空则退化为纯卡片）、关于页、RSS、sitemap、备案页脚（ICP + 公安）
- `npm run import -- <URL> <slug>`：公众号文章导入，图片本地化解决微信图床防盗链
- `scripts/publish.sh` + `scripts/server-setup.sh`（幂等）+ [部署手册](deploy.md)
- 12 个单元测试（helpers + 导入脚本），`npm test` 全过

**开发过程中的关键修正**（均经独立代码审查确认）：
1. 计划原定测试命令 `node --test tests/` 在 Node 24 上不可用 → 改为 `node --test` 默认发现
2. 导入脚本 fetch 网络级异常未捕获会崩溃 → 文章抓取失败干净退出，单图失败保留原链接继续
3. 部署脚本加固：`dist/.git` 残留可能被同步上公网 → 构建后强制清理 + rsync `--exclude=.git`；server-setup 重跑会覆盖 certbot 的 HTTPS 配置 → 检测到 `listen 443` 即跳过
4. **终审发现的实质 bug**：导入日期按 UTC 计算，北京时间 00:00–07:59 发表的文章会错记成前一天 → 改按 Asia/Shanghai 格式化，有测试覆盖
5. `.DS_Store` 防泄漏：publish 时从 dist 中删除

**上线验证**（线上实测，非本地推断）：HTTPS 200（Let's Encrypt，续期 dry-run 通过）、HTTP 301→HTTPS、全页面 200、备案信息在线、unlisted/draft 隔离生效、rsync 与 git 两条发布通道均实测可用。

**安全**：服务器地址/账号只存 gitignored 的 `.deploy.env`，密码不落任何文件（SSH 密钥认证）。

**后续完成情况**：示例内容与 about 已替换；`/_astro/*` 缓存头和同名 slug 冲突检测已完成。仍可按需补中文 404 页与 www 子域说明。

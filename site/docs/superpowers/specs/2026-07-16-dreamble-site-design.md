# 聊哉梦呓个人站 设计文档

- 日期：2026-07-16
- 状态：已确认（设计阶段）

## 1. 背景与目标

站主经营微信公众号「聊哉梦呓」，同时开发实用工具软件。本站解决两个问题：

1. **文章**：备份公众号已发文章；发表不适合公众号平台的文章
2. **作品**：展示自研工具软件，面向包括非程序员在内的读者

核心约定：**目录即数据库，放文件即发布**。无在线编辑、无后台、无数据库。

## 2. 明确不做（YAGNI）

- 在线编辑 / 后台管理
- 评论（互动留在公众号；将来需要可嵌入第三方，不影响架构）
- 站内搜索、访问统计
- 多语言（站点界面默认中文）

## 3. 架构总览

技术栈：**Astro**（静态站点生成器，Content Collections 提供 frontmatter schema 强制校验）。

```
本地 content/ 放文件 → npm run publish → Astro 构建 → 同步 dist/ 到服务器 → nginx 伺服静态文件
```

- 内容真源在本地 git 仓库（天然备份）
- 服务器上只有构建产物，不跑任何应用进程
- 站点代码、内容、脚本同仓库（`dreamble-site`）

## 4. 目录结构

```
dreamble/site/
├── CLAUDE.md            # 项目规范
├── content/
│   ├── posts/           # 文章：一篇一目录
│   │   └── 2026-07-16-some-post/
│   │       ├── index.md
│   │       └── *.png    # 图片与正文同目录，相对路径引用
│   ├── projects/        # 作品：一个一目录
│   │   └── my-tool/
│   │       ├── index.md
│   │       └── *.png
│   └── about.md         # 关于页
├── src/                 # Astro 站点代码
├── scripts/             # import / publish 脚本
├── docs/                # 文档
└── .deploy.env          # 服务器地址等部署参数（gitignored）
```

**统一约定：一篇文章 = 一个目录**（无图也用目录），目录名 `YYYY-MM-DD-slug`，URL 为 `/posts/<slug>/`。作品目录名即 slug，URL 为 `/projects/<slug>/`。

## 5. 内容约定（frontmatter）

由自定义内容策略检查和 Astro Content Collections schema 共同强制校验：目录格式、日期一致性、slug 唯一性、未知字段、字段错误或缺少必填项都会导致构建失败。

### 5.1 文章 `content/posts/*/index.md`

| 字段 | 必填 | 说明 |
|---|---|---|
| `title` | ✅ | 标题 |
| `date` | ✅ | 发表日期 `YYYY-MM-DD` |
| `summary` | — | 列表页摘要，缺省取正文开头 |
| `tags` | — | 标签数组 |
| `source` | — | `wechat` = 公众号备份（文章页标注"首发于公众号"）；缺省 = 本站原创 |
| `visibility` | — | `public`（默认）/ `unlisted`：不进列表、RSS、sitemap，页面加 `noindex` |
| `draft` | — | `true` 则不构建，默认 `false` |

### 5.2 作品 `content/projects/*/index.md`

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | 工具名 |
| `tagline` | ✅ | 一句话简介 |
| `cover` | — | 卡片配图（相对路径） |
| `links` | ✅（至少一项） | `download` / `repo` / `website` |
| `status` | — | `active`（默认）/ `archived`（沉底展示） |
| `order` | — | 卡片排序权重，数字越小越靠前 |

正文即详情页内容；**正文为空 → 卡片不出详情链接**，退化为纯橱窗卡片。

## 6. 页面结构

- `/` 首页：简介 + 最新文章 + 精选作品
- `/posts/` 文章归档（按年分组）；`/posts/<slug>/` 文章页
- `/projects/` 作品卡片墙；`/projects/<slug>/` 作品详情页
- `/about/` 关于我
- `/rss.xml`、`sitemap.xml`：自动生成，仅含 public 且非 draft 内容
- 页脚：版权 + 备案信息（见 §9）
- 视觉：默认中文界面；暗色模式跟随系统

## 7. 日常操作界面

| 想做什么 | 操作 |
|---|---|
| 发表文章 | `content/posts/` 建目录放 `index.md` → `npm run publish` |
| 本地预览 | `npm run dev` |
| 导入公众号文章 | `npm run import -- <文章URL>` |
| 上架作品 | `content/projects/` 建目录 → `npm run publish` |

### 7.1 导入命令 `scripts/import-wechat`

解决微信图床防盗链（站外引用 `mmbiz.qpic.cn` 图片会裂图）：

1. 抓取公众号文章 HTML，正文转 markdown
2. 在 `content/.import-staging/` 暂存目录下载图片并改写相对链接
3. 生成 frontmatter（`source: wechat`，date 取文章发表日期）
4. 全部完成后原子移动到正式文章目录；失败则清理暂存内容，不留下半成品
5. 人工检查后 publish

### 7.2 发布命令 `npm run publish`

1. `npm run verify`：内容约束、类型检查、单元测试和构建，失败则中止（线上不变）
2. 同步 `dist/` 到服务器：**优先 rsync**（macOS 自带）；rsync 不可用或失败时 **fallback 到 git 同步**（dist 推送至服务器 bare 仓库，post-receive hook checkout 到 nginx 目录）
3. 对线上 URL 做健康检查：成功打印站点 URL；失败以非零状态退出并提示排查方向

## 8. 服务器与部署（一次性配置）

- 服务器：`.deploy.env`（gitignored）存 `DEPLOY_HOST` / `DEPLOY_USER` / `DEPLOY_PATH`
- **认证：SSH 密钥（站主已执行 `ssh-copy-id`，免密登录就绪）。密码不使用、不落盘、不进任何文件**
- 安全建议（写入部署文档，是否执行由站主决定）：禁用 root 密码登录（`PasswordAuthentication no`）
- nginx：服务器已安装；需新增一个 server 块指向静态目录；certbot 配置 HTTPS 自动续期
- 域名：`simiam.com`（已备案），用于 RSS / sitemap / canonical / HTTPS 证书

## 9. 备案信息（页脚）

国内网站法定要求，页脚展示：

- ICP 备案：`闽ICP备18023112号`，链接 `https://beian.miit.gov.cn`
- 公安备案：`闽公网安备 35012102500070号`，链接 `http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=35012102500070`，附公安备案标准图标（实现阶段从网上获取标准图标文件）

## 10. 错误处理

- 目录、日期、slug 或 frontmatter 不合规 → 构建报错，指明原因
- 构建失败 → 不执行同步，线上不受影响
- rsync 失败 → 自动尝试 git 同步；两者都失败 → 明确报错并提示排查方向
- unlisted 文章 → 三重隔离：不进列表页、不进 RSS/sitemap、`<meta name="robots" content="noindex">`

## 11. 验证方式

- `npm run verify` 作为统一验收入口，覆盖内容约束、`astro check`、单元测试和静态构建，publish 内置
- 本地 `npm run dev` 预览即所得（构建产物与预览一致）
- 部署后以 `curl` 抽查首页、文章页、RSS 的 HTTP 200 与内容

## 12. 待定项

无。域名（`simiam.com`）已确认；公安备案图标在实现阶段从网上获取标准图标。

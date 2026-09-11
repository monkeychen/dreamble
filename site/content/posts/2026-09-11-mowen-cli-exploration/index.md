---
title: "墨问笔记自动下载：从官方 CLI 到逆向匿名接口的完整探索"
date: 2026-09-11
summary: "从「定期获取关注的人最新文章并下载到本地」这个需求出发，分析墨问官方 CLI（mowenxd/cli）的能力边界，逆向出匿名可用的正文接口 POST note/show，并落地 bin/mowen-download.py 下载脚本。记录完整探索路径（含走错的方向），为后续产品化提供参考。"
tags: ["墨问", "mocli", "API 逆向", "自动化", "爬虫"]
---

# 墨问笔记自动下载：从官方 CLI 到逆向匿名接口的完整探索

> 目标读者：想把「墨问关注动态 → 本地 Markdown 归档」做成产品或长期自动化的人。
> 本文记录 2026-09-11 一次完整的探索：需求分析 → 官方能力评估 → 误判与纠正 → 接口逆向 → 脚本落地 → 产品化建议。

## 一、需求场景

### 1.1 原始需求

**定期获取我在墨问上关注的人最新发表的文章，并下载回本地。**

拆成四个子问题：

| 子问题 | 说明 |
|---|---|
| 发现 | 知道「关注的人」发了什么新笔记 |
| 获取 | 拿到笔记的完整正文（而不是摘要） |
| 落盘 | 以可长期阅读的格式（Markdown + 图片）存到本地 |
| 定期 | 无人值守周期性执行 |

隐含需求：

- 付费笔记拿不到全文时要有明确交代（占位/标注），不能假装成功；
- 重复执行不能重复下载（增量去重）；
- 对平台的请求要温和（限速），不能把路走死。

### 1.2 为什么是墨问

墨问（MoWen，mowen.cn）是池建强创办的微信生态知识社区，主入口是微信小程序，网页端（note.mowen.cn）做内容分发。大量独立创作者（池建强、Q 思想等）把长文首发在墨问，内容质量高但**没有任何官方导出/订阅机制**——不关注 RSS，不提供 newsletter，网页端阅读体验依赖微信生态。想本地归档只能自己动手。

## 二、官方 CLI 项目分析（mowenxd/cli）

### 2.1 项目概况

- 仓库：https://github.com/mowenxd/cli
- 形态：Go 编译的二进制（npm 包 `@mowenxd/cli` 只是下载器壳）+ 8 个 Agent Skill
- 定位：把墨问 OpenAPI 包成命令行，供 AI Agent（Claude Code / Codex / CodeBuddy 等）用自然语言操作墨问
- 认证：墨问小程序 → 我的 → 开发者 → 我的 API Key；`mocli auth init --apik <key>` 完成初始化
- 许可：MIT

### 2.2 命令全集

| 命令 | 子命令 | 用途 | 关键参数 |
|---|---|---|---|
| `mocli auth` | `init` / `info` | 配置/查看认证 | `--apik`、`--profile` |
| `mocli disco` | `activity` | **核心发现命令**：拉动态，含关注的人发新笔记 | `--recent today/yesterday/1h-24h` |
| `mocli notes` | `homepage` | 任意用户主页公开笔记（**不需要关注**） | `--uid`、`--filter all/album/fee/popular`、`--recent 1h-15d`、`--count 1-100` |
| | `mine` | 自己的笔记（含私有） | 同上 + `priv/cond-pub` 筛选 |
| | `search` | 全站关键词搜索 | `--keyword`（必填）、`--focus <uid>` |
| | `tagged` | 按标签筛自己的笔记（交集） | `--tag-name` / `--tag-id` |
| `mocli note` | `info` | 笔记详情 + 前 10 条评论 + 引用 | `--show-comment --show-refer`；`--show-atom` **仅自己笔记生效** |
| | `create` / `edit` / `set` | 写入类：创建/编辑/隐私设置 | `--file`（正文树 JSON）、`--publish`、`--tags` |
| | `tag` | 查看/管理标签 | `--reset` / `--append` / `--remove` |
| `mocli user` | `search` / `info` | 搜用户（模糊匹配昵称+简介）、看基础信息 | `--filter following/follower/friend` |
| `mocli remark` | `set` / `list` | UID ↔ 本地昵称映射（"老池"→UID） | — |
| `mocli tag` | `mine` | 自己的标签列表 | — |
| `mocli misc` | `upload` | 上传图片/音频/PDF 拿 file_id | 配额 20 次/天（Pro 200） |

### 2.3 Skill 体系（给 Agent 的自然语言路由层）

8 个 skill（mo-shared / mo-auth / mo-note / mo-tag / mo-user / mo-remark / mo-discover / mo-misc），装到 Agent 的 skills 目录后即可用自然语言触发。质量意外地高：响应 schema、事件-详情 Map 关联规则、写入操作确认门禁、覆盖风险检查都写得很细，是学习「怎么写 skill」的好样本。

### 2.4 实测结论：官方 CLI 能满足需求的多大比例

| 需求 | mocli 能力 | 结论 |
|---|---|---|
| 发现关注的人新笔记 | `disco activity --recent 24h`，type 6（普通）/ type 7（付费）事件 | ✅ 完美，元数据齐全（标题/AI 摘要/URL/作者/字数/统计） |
| 获取**他人**笔记全文 | `note info --show-atom` 仅对自己笔记生效，他人只返回元数据 | ❌ **OpenAPI 网关侧的硬限制** |
| 落盘 | CLI 只输出 JSON 到 stdout，无导出命令 | ⚠️ 需要自己解析落盘 |

第一轮探索在此得出结论：「发现可行，全文下载做不到，建议降级为摘要+链接」。**这个结论后来被证明是错的**，这是本文最有价值的部分，见第三章。

## 三、探索过程（含走错的路）

### 3.1 第一轮：匿名 curl 网页 → 误判

```
curl https://note.mowen.cn/detail/<id>
```

返回 2.3KB 的 SPA 空壳：`<div id="app"></div>` + 一个 main.js loader。head 里有 SEO 用的 meta（title/description/og 标签，摘要约 200 字），无正文。

**误判**：由此得出「网页是纯 SPA，匿名抓不到正文，全文下载做不到」。

**错在哪**：把「curl 拿不到」当成了「匿名拿不到」。SPA 的正文由 JS 发 XHR 拉取，curl 当然拿不到——但这不代表那个 XHR 本身需要登录。正确的下一步是**找到那个 XHR 直接调它**，而不是止步于 HTML 层。

### 3.2 第二轮：被 challenge 后的系统性排查

重新审视问题，四条路径依次验证：

**路径 A：mocli 二进制逆向（不通，但拿到了重要情报）**

```
strings ~/.nvm/.../bin/mocli | grep mowen
```

挖出域名矩阵：`open.mowen.cn`（OpenAPI 网关）、`note.mowen.cn`、`user.mowen.cn`、`misc.mowen.cn`，及路径模式 `/api/open/api/v1/note/info` 等。尝试手工调网关：`~/.mocli/auth.json` 里的 `api_key` 是 `enc:` 前缀的加密存储（配套 `user_key`），解密逻辑在 Go 二进制里，逆向成本高，放弃此路。

> 情报价值：确认了官方 CLI 和网页端走**两套不同 API**——CLI 走需鉴权的 OpenAPI 网关，网页走另一套。

**路径 B：真实浏览器渲染 + 网络面板（突破口）**

用 agent-browser（headless Chromium）打开笔记页，**未登录状态**下正文完整渲染（页面右上角还显示「登录」按钮）。`network requests` 列出全部 XHR，一眼定位：

```
POST https://note.mowen.cn/api/note/wxa/v1/note/show   → 200
```

路径里的 `wxa` = 微信小程序（weixin xiaochengxu）版 API，网页与小程序共用。

**路径 C：直接 curl 该接口（验证成功）**

第一次尝试 `{"note_id": "..."}` 返回 400，但验证器报错直接自曝了正确字段名：

```json
{"code":400, "reason":"VALIDATOR", "message":"invalid NoteShowRequest.Uuid: value length must be at least 1 runes"}
```

改用 `{"uuid": "<id>"}` → 200，完整 JSON，正文在 `detail.noteBase.content`（HTML）。

**路径 D：排除隐式凭证（把话说死）**

最终验证用最裸的请求——只带 `Content-Type`，UA 就是 `curl/8.7.1`，无 Origin/Referer、无 Cookie、无 Authorization——照样返回完整正文。curl 进程里根本不存在墨问登录态，从原理上排除了「隐式携带凭证」的可能。

### 3.3 方法论沉淀

这次探索的教训值得记下来：

1. **「我拿不到」≠「拿不到」**。结论要说清楚边界：是技术不可行，还是当前方法不可行。curl 对 SPA 无效是常识，但止步于此就会漏掉背后的匿名 API。
2. **错误信息是最好的 API 文档**。VALIDATOR 报错直接告诉你字段名和约束；ASSET_NOT_FOUND 告诉你付费墙的判断依据。不要怕 400，要读 400。
3. **浏览器 network 面板是逆向 SPA 的正道**。任何 SPA 渲染出来的数据必然来自某个 XHR/Fetch，headless 浏览器 + 请求列表 = 接口地图。
4. **被动接受平台限制前，先分清限制在哪一层**。mocli 的 `--show-atom` 限制在 OpenAPI 网关（保护创作者内容），网页分享场景的匿名读是产品刚需，两条通道的权限模型完全不同。

## 四、关键技术发现

### 4.1 正文接口（核心资产）

```
POST https://note.mowen.cn/api/note/wxa/v1/note/show
Content-Type: application/json

{"uuid": "<笔记ID>"}
```

**无需任何认证**（连 Origin/Referer 都不需要）。响应结构（关键字段）：

```jsonc
{
  "detail": {
    "noteBase": {
      "uuid": "笔记ID",
      "title": "标题",
      "digest": "摘要",
      "content": "<p>完整正文HTML…</p><img uuid=\"图片uuid\">",
      "createdAt": "1789091843",
      "publicAt": "1789091978",
      "uid": "作者UID"
    },
    "noteFlag": { "isPublic": true, "hasFee": false, "hasImage": true, "hasAudio": false, "hasPdf": false, … },
    "noteStat": { "duv": "阅读数", "favor": "点赞", "collect": "收藏", "comment": "评论", "share": "分享" },
    "noteTags": [ … ],
    "noteFile": {
      "images": {
        "<图片uuid>": {
          "url": "https://priv-sdn-001.mowen.cn/...jpg?Expires=…&Signature=…",
          "format": "jpg", "width": "1179", "height": "1078",
          "scale": { "w_1200": "缩放版URL", … }
        }
      }
    }
  },
  "user": { "base": { "name": "作者昵称", "intro": "简介" }, "relation": { "rel": 0 } }
}
```

行为边界：

| 笔记类型 | 接口行为 |
|---|---|
| 公开笔记 | ✅ 完整正文，不管你是否关注作者 |
| 付费笔记 | ❌ `400 ASSET_NOT_FOUND`（附 skuId），付费墙在服务端 |
| 私有笔记 | 不会出现在任何发现渠道里，无从触达 |

### 4.2 图片机制（容易踩的坑）

- 正文 HTML 里图片是 `<img uuid="xxx">`，**没有 src**；
- 实际 URL 在 `detail.noteFile.images` 里按 uuid 映射；
- URL 是 OSS 签名地址，**约 7 天过期**——Markdown 里直接引远程 URL 必然裂图，必须下载落地；
- 多规格：`scale.w_1200` 是合适的下载规格，兼顾清晰度和体积；
- 图片直链同样匿名可下，单张实测 137KB / 1179px 完整 JPEG。

### 4.3 发现链路（mocli 侧，保留使用）

- **关注动态**：`mocli disco activity --recent 24h` → 遍历 `reply.events`，type 6/7 事件按 eid 关联 `follow_notes` / `follow_fee_notes` 详情 Map → 拿 note_id 列表；
- **任意用户**（无需关注）：`mocli notes homepage --uid <uid> --recent 3d`，`--filter` 支持 all/album/fee/popular；
- **UID 获取**：`mocli user search --keyword`（注意是昵称+简介的模糊匹配，需人工辨认本尊）、主页 URL 直读（`note.mowen.cn/user/<uid>`）、`mocli remark` 做本地昵称映射；
- **去重键**：note_id（响应里有完整 ID，文件名用前 6 位短哈希辅助即可）。

### 4.4 环境事实

- mocli v0.5.4，认证信息存 `~/.mocli/auth.json`（api_key 为加密存储）；
- 发现层依赖 mocli 已认证（disco/homepage 走 OpenAPI），正文层完全匿名——两层独立，正文层永不过期，发现层的 API Key 需要偶尔关注有效性（重新生成会使旧的失效）。

## 五、落地实现：bin/mowen-download.py

### 5.1 架构

```
┌─────────────────────────┐     ┌──────────────────────────┐
│ 发现层（mocli，已认证）   │     │ 获取层（note/show，匿名）  │
│                         │     │                          │
│ --recent 24h            │     │ POST note/wxa/v1/note/   │
│   disco activity        │ ──> │      show {uuid}         │
│ --uid <UID>             │     │        ↓                 │
│   notes homepage        │     │ noteFile.images 逐张下载  │
│ --note-id ID...         │     │        ↓                 │
└─────────────────────────┘     │ HTML → Markdown 转换      │
                                └──────────┬───────────────┘
                                           ↓
                                <out>/YYYY-MM-DD-标题-ID6.md
                                <out>/assets/<note_id>/img-NN-xxxxxx.jpg
```

### 5.2 设计决策

| 决策 | 理由 |
|---|---|
| 发现用 mocli、正文用裸接口 | 发现层官方 API 稳定且已认证；正文层只有裸接口能拿全文，各取所长 |
| 图片下载到 `assets/<note_id>/`，MD 引相对路径 | OSS 签名 URL 7 天过期，远程引用必然裂图 |
| 按 note_id 前 6 位 glob 去重 | 幂等，重复跑不重复下载，适配定时任务 |
| 请求间隔 0.5s（图片 0.3s） | 温和限速，避免触发频控把匿名通道搞挂 |
| 付费笔记落 `PAID-` 前缀占位文件 | 明确交代而非静默失败，占位含跳转 URL |
| 纯标准库，零第三方依赖 | 任何有 python3 的机器直接跑，无环境负担 |
| HTML→MD 手写最小转换器 | 墨问正文标签集合有限（p/h1-3/strong/em/a/ul/ol/li/blockquote/pre/code/img），不值得引入依赖 |

### 5.3 用法

```bash
# 关注的人最近 24h 新笔记（定时任务主命令）
python3 bin/mowen-download.py --recent 24h --out <目录>

# 指定用户（不需要关注）
python3 bin/mowen-download.py --uid <UID> --uid-recent 3d --count 20

# 指定笔记
python3 bin/mowen-download.py --note-id <ID1> <ID2>

# 强制覆盖已下载
python3 bin/mowen-download.py --recent 24h --force
```

### 5.4 实测战绩（2026-09-11）

- 24h 关注动态：7 篇新笔记 → 6 篇公开全部下载成功（正文、文内链接如小宇宙播客直链完整保留），1 篇付费落占位；
- 未关注用户（relation=0 验证）：3 篇带图笔记，含 13 张图的漫画笔记，图片全部落地，抽验 JPEG 完整（1179px，w_1200 规格）；
- 匿名性：裸 curl（无任何凭证头）返回完整正文，双重验证（未登录浏览器 + 请求头审计）。

## 六、边界与风险（产品化前必读）

| 风险 | 等级 | 应对 |
|---|---|---|
| note/show 是民间逆向接口，无官方 SLA，随时可能加登录/频控 | **高** | 监控失败率；兜底方案已验证：agent-browser 带登录态渲染（headless Chromium 已装好） |
| 匿名高频请求可能触发风控，影响 IP 或账号（发现层 API Key） | 中 | 保持 0.5s 限速；个人订阅量级（几十篇/天）远低于风险阈值 |
| 付费内容匿名不可读 | 确定行为 | 占位文件明确标注；不做绕过尝试（也绕不过：权限在服务端） |
| 下载内容仅限个人阅读归档 | 合规 | 尊重创作者版权，不分发、不二次发布；订阅源限于自己关注/指定的创作者 |
| mocli API Key 重新生成会使旧 key 失效 | 低 | 发现层失败时提示重新 `mocli auth init` |
| OSS 图片 7 天过期 | 已解决 | 图片即时落盘 |

## 七、产品化建议

### 7.1 近期（一周内可落地）

1. **定时化**：WorkBuddy automation 或 cron，每天一次 `--recent 24h --out articles/mowen-feeds/`。时间窗口必须 ≤ 执行周期，否则漏笔记；宁可 `24h` 每天跑 + `3h` 高频跑双保险。
2. **输出目录规范化**：当前默认 `tmp/mowen-downloads/`（gitignore 内），产品化应固定到正式目录，按 `作者/YYYY-MM/` 或纯时间线组织，配索引文件。
3. **执行报告**：每次跑完输出摘要（新增 N 篇：作者+标题列表），作为日报推送到微信/邮件——「下载」本身不是终点，「知道今天有什么新内容」才是。

### 7.2 中期

1. **订阅配置化**：`config.yaml` 声明关注列表（disco 模式）+ 指定 UID 清单（homepage 模式）+ 各自的拉取周期。
2. **附件扩展**：音频（`noteAudio`）、PDF（`noteFile`）当前未下载，结构已探明，按图片同款模式补齐即可。
3. **合集处理**：disco 动态里 `joins` 字段表示合集新增子笔记，当前只下主笔记，应递归下子笔记。
4. **健康监控**：连续 N 次失败（接口变更信号）告警；每周对账（disco 数量 vs 本地新增数量）发现漏抓。
5. **阅读层**：本地 Markdown 已可被 Obsidian/静态站消费，可接入个人站做聚合阅读页。

### 7.3 远期（如果做成产品）

- 核心资产是**发现-获取-归档这条管道**，墨问只是第一个源。同样的方法论（官方 API 做发现、逆向接口做获取）可复制到其他无导出能力的平台。
- 需要正视合规边界：匿名接口产品化会被平台视为爬虫，规模化前必须评估。个人工具形态（单用户、限速、仅自己关注的内容）是最安全的边界。

## 八、附录

- 脚本：`bin/mowen-download.py`（278 行，纯标准库），commit `7ba92de` → `18440ed`
- 关键命令速查：

```bash
# 正文接口（核心）
curl -s -X POST https://note.mowen.cn/api/note/wxa/v1/note/show \
  -H "Content-Type: application/json" -d '{"uuid":"<笔记ID>"}'

# 发现：关注动态 / 指定用户主页
mocli disco activity --recent 24h
mocli notes homepage --uid <UID> --recent 3d

# UID 查询
mocli user search --keyword "名字"
```

- 时间线：2026-09-11 17:42 项目分析 → 17:51 UID 获取验证 → 18:00 被挑战后重验 → 18:05 note/show 突破 → 18:10 脚本 v1 → 18:15 未关注用户 + 图片落地
- 相关工具：agent-browser 1.3.0（headless Chromium，兜底方案）；mocli v0.5.4

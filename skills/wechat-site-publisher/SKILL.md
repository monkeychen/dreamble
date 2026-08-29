---
name: wechat-site-publisher
description: 接收任意已定稿 Markdown 文章，在不改写正文的前提下补齐发布元数据和视觉资产，写入微信公众号草稿，并按 dreamble/site 规范准备或发布 simiam 站点版本。适用于“把这篇文章同步公众号和个人站”“生成配图并准备双渠道发布”等请求；只发公众号使用 baoyu-post-to-wechat，文章创作或研究由对应上游 Skill 负责。
---

# 微信公众号与站点文章发布助手

把任意已定稿 Markdown 文章转换为渠道可用主稿，并完成视觉资产、微信公众号草稿和 simiam 站点版本。默认中文。源稿、发布主稿、公众号草稿和网站上线是四种不同状态，必须分别报告；本 Skill 不负责文章创作、研究、审校或改写正文。

## 环境检查（最先执行）

本 Skill 依赖第三方开源项目 [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) 的技能。**本项目不提供、不代装**，需使用者自行安装到用户级或项目级 skills 目录。动手前先探测，不要等跑到一半才失败。

### 1. 探测依赖

```bash
for s in baoyu-post-to-wechat baoyu-cover-image baoyu-article-illustrator; do
  found=""
  for d in "$HOME/.workbuddy/skills" "$HOME/.claude/skills" \
           ".codebuddy/skills" ".workbuddy/skills" ".claude/skills" ".agents/skills"; do
    [ -d "$d/$s" ] && found="$d/$s" && break
  done
  echo "$s: ${found:-缺失}"
done
```

各工具的技能目录名不同（`.codebuddy` / `.claude` / `.agents` 常互为别名），需逐个探测。下文用到的 `{skillDir}` 就是这里探到的路径（符号链接需先解析到真实路径）。

### 2. 缺失时按强度处理

| 依赖 Skill | 强度 | 缺失时的行为 |
|---|---|---|
| `baoyu-post-to-wechat` | **必需** | 停止公众号分支并告知安装方式。用户只要发网站时，网站流程照常继续 |
| `baoyu-cover-image` | 条件必需 | 仅用户未提供封面时才需要；缺失则请用户提供封面，不得声称已生成 |
| `baoyu-article-illustrator` | 可选 | 跳过正文插图，不阻断发布 |

报告缺失时给出安装命令：

```bash
npx skills add jimliu/baoyu-skills
```

### 3. 账号表定位

公众号账号表在 `baoyu-post-to-wechat` 安装目录下的 `EXTEND.md`。**位置随安装方式变化，不要写死路径**（本机常见为 `~/.baoyu-skills/baoyu-post-to-wechat/EXTEND.md`）。找不到时不传 `--account`，由其默认流程处理；**任何情况下都不自行编造账号名**。

## 开始前

1. 明确输入源稿路径。输入必须是用户或上游创作、研究、编辑 Skill 已经定稿的 Markdown 文件。
2. 源稿尚未定稿时停止发布包装，并交回对应上游完成；本 Skill 不判断主题领域，也不调用证券分析或其他内容生产 Skill。
3. 确认交付范围：只准备本地材料、保存公众号草稿、准备网站版本或发布网站。任何外部写入仍按“发布授权”处理。
4. 默认双渠道：用户未显式指定渠道时，默认同时保存公众号草稿并发布网站；只有用户显式指定单一渠道（如“只发公众号”“只发网站”）时才收窄为该渠道。

## 工作目录

每次运行使用 `tmp/wechat-site-publisher/YYYY-MM-DD-<slug>/`：

```text
article.md              # 渠道发布主稿
source.md               # 已定稿 Markdown 源稿，只读保留
imgs/
  cover.png
  ...                   # 必要的正文插图
site-post/              # 严格按 site schema 生成的待发布版本
```

- `<slug>` 使用 2–5 个小写英文单词、数字和单个连字符。
- `tmp/` 已被 Git 忽略。不要把临时生成提示词、失败图片或中间 HTML 放到仓库根目录。
- `source.md` 是不可改写的上游交付；`article.md` 是发布包装版本，只允许增加或更新 frontmatter 和 Markdown 图片引用，原正文必须保持不变。
- 两个渠道均完成并核验前保留工作目录。发布完成并核验后，默认清理本次工作目录 `tmp/wechat-site-publisher/YYYY-MM-DD-<slug>/`；用户明确说不要清理时才保留。

## 接收报告与准备主稿

1. 将已定稿 Markdown 原样保存为 `source.md`，作为本次发布的内容真源。**源稿正文一字不改**地落盘。
2. **通读源稿**。这是后续发布包装动作的前提；通读只用于理解，不改任何文字，产出两样东西：缺失 `title` / `summary` 时的补写依据（见第 4 条），以及正文插图需求判断（见「视觉资产」第 2 条）。
3. 只检查发布兼容性：文件可读、frontmatter 中存在 `title` 和 `summary`、Markdown 图片路径可解析。不得检查或修改事实、数字、观点、结论、风险和措辞。
4. **源稿缺 frontmatter，或 frontmatter 中 `title` / `summary` 为空时**（很常见，例如知识库里的纯 Markdown 笔记）：`prepare_article.py` 会以 `Source Markdown must start with YAML frontmatter` 或 `requires non-empty title` 失败。此时不要退回给用户要求补写，而是在写 `source.md` 时**在文件头补一段最小 frontmatter**——只填 `title`（取源稿首个 H1）和 `summary`（按第 2 条通读的理解自撰，不照抄正文首段），正文部分仍逐字保留源稿内容。这是第 1 条「一字不改」的唯一例外，改的只有文件头，属于发布包装，不是改写正文。
5. 使用 `scripts/prepare_article.py` 生成 `article.md`。脚本只增加规范的 `coverImage` 和正文封面引用，不改写原正文。
6. 发布主稿 frontmatter：

```yaml
---
title: 文章标题
summary: 120 字以内摘要
coverImage: ./imgs/cover.png
---
```

7. 除 frontmatter 和图片引用外，Publisher 不得重排段落、润色语言、删减内容、改写标题摘要或修正文中内容。用户要求修改正文时，交回原作者或对应上游 Skill 产出新版定稿。

## 视觉资产

1. 封面资产是必需项。用户未提供可用封面时，调用 `$baoyu-cover-image`，以 `source.md` 为输入，默认建议微信公众号宽封面 `2.35:1`，最终图片放到 `imgs/cover.png`。遵守该 Skill 的偏好读取、确认和提示词留档规则。
2. 正文插图不是默认凑数量，张数按以下顺序决定：

   - **用户显式指定张数** → 按用户说的来；超过 3 张时先确认一次。
   - **用户未指定** → 基于「接收报告与准备主稿」第 2 条通读的理解自行判断，**默认 0 张**；只有某处内容仅靠文字不易理解时才增加，**最多 3 张**。

   判断依据是那段内容本身的表达难度（结构关系、对比差异、演变过程、运作机制等），**与文章题材无关**——研报、随笔、教程一视同仁。动手生成前先说清每张图画什么、插在哪一节之后，用户有异议时按用户意见调整。
3. 调用 `$baoyu-article-illustrator` 时，它只增加图片和图片引用，不改写正文任何文字。
4. 插图应帮助理解，不把推测画成事实。精确数值优先保留源稿 Markdown 表格；AI 图片中的文字或数字不可靠时，改用少字或无字视觉。
5. 检查图片文件存在、Markdown 相对路径正确、封面可读且与标题一致，再进入发布阶段。

## 发布授权

生成本地文件不等于授权外部发布。公众号草稿写入、Git 推送和网站部署都属于外部状态变更。

- 如果用户本次请求已明确说“保存到公众号草稿”“同步/发布到网站”等，可按该范围执行，不重复确认。
- 如果用户只要求生成或准备材料，在发布前集中展示标题、摘要、封面、目标公众号账号、公众号主题和两个目标渠道，询问一次授权。
- 一个渠道失败不阻塞另一个已获授权的渠道，但必须保留主稿并分别报告结果。

## 微信公众号

### 账号解析（多账号）
`baoyu-post-to-wechat` 支持多账号（见其 `EXTEND.md` 的 `accounts:` 块）。本 Skill 按以下规则解析，不要自行创造账号名：

1. **读取账号表**：发布前按「环境检查」定位 `baoyu-post-to-wechat` 的 `EXTEND.md`，解析 `accounts:` 块的 `name` / `alias` / `default` 字段，得到「账号显示名 → 别名」映射与默认账号。
2. **用户显式指定账号**：当用户点名某账号（如“发到白话AI大模型”）时，在调用 `baoyu-post-to-wechat` 时传入 `--account <alias>`，其中 `<alias>` 是对应该账号的 `alias`（不是显示名）。用户给的是显示名时先查表映射。
3. **未指定账号（默认）**：用户未点名账号时，**静默使用 EXTEND.md 中 `default: true` 的默认账号，不向用户追问账号选择**，也不传入 `--account`——交由 `baoyu-post-to-wechat` 按默认账号处理。
4. 在发布授权展示与完成报告中，明确写出实际使用的公众号账号名（显示名）。

### 调用与发布方法
1. 调用 `$baoyu-post-to-wechat`进行发布，如果提示找不到`baoyu-post-to-wechat`这个skill，按下方步骤2的规则处理。
2. **执行方式**：用「环境检查」探到的 `{skillDir}`，读其 `SKILL.md` 并按指令执行。发布动作最终落到 `bun` 脚本，先确认 `bun` 可用（不可用则 `npx -y bun`）。它不在本会话可用 skill 列表时，不要用 Skill 工具反复重试，直接按脚本路径执行：

   ```bash
   cd <工作目录> && bun {skillDir}/scripts/wechat-api.ts article.md --theme <theme> [--remote]
   ```

   - `--theme` 必须显式传（取 EXTEND.md 的 `default_theme`）。
   - 需要远程中转时追加 `--remote`；`remote_publish_*` 已在 EXTEND.md 配置好，无需额外 CLI 参数。
3. 直接传入 `article.md`，不要预先转成 HTML。主题、主题色由该 Skill 的参数或 EXTEND.md 决定；未配置时按其首次设置流程处理。
4. 发布方法（API / browser / remote-api）由目标账号的 `default_publish_method` 决定；本 Skill 不强行覆盖方法，只在 API 路径失败时按下方规则触发远程中转。
5. 封面使用 `imgs/cover.png`。先验证标题、摘要、正文图片和链接，再写入草稿箱。

### IP 白名单失败 → 远程中转（`--remote`）
微信「公众号设置 → IP 白名单」常常只放行固定 IP。当走 API/remote-api 方法发布失败，且错误信息表明**本地 IP 不在公众号后台白名单**（典型信号：`errcode 40164`、`invalid IP`、提示“IP 地址不在白名单中”），按以下顺序处理：

1. 重新调用 `$baoyu-post-to-wechat`，在原有参数基础上追加 `--remote` 开关，走其远程中转模式：本地渲染与草稿拼接不变，仅发往 `api.weixin.qq.com` 的 HTTPS 经 SSH SOCKS5 隧道出去（远程出口 IP 视为来源）。若本次曾指定账号，保留 `--account <alias>`。
2. `--remote` 所需的 `remote_publish_*` 配置来自 EXTEND.md 的账号级或全局级字段（如已配置的 `simiam.com`）；也可用 `--remote-host` / `--remote-user` 等 CLI 项临时覆盖。
3. 若 EXTEND.md 缺少 `remote_publish_host` 等远程配置且未传 CLI 覆盖项，则停止该渠道并报错：提示需先配置远程中转主机，不要反复重试 API。
4. 远程中转仍失败（如远程出口 IP 也不在白名单、仍报 `40164`）时，停止并报告，交人工在公众号后台调整白名单。

### 草稿状态语义
1. 在本工作流中，用户所说的“发表到公众号”默认指**保存到公众号草稿箱**；只有用户明确要求正式群发时，才把它理解为群发。
2. 只有看到草稿成功证据时才报告“公众号草稿已保存”。草稿保存成功后，网站备份即可标记 `source: wechat`；这不改变公众号侧仍处于草稿状态的事实。

## 个人站

发布前阅读 `site/AGENTS.md`、`site/README.md` 和 `site/src/content.config.ts`，以当前规则为准。具体转换与状态决策见 [references/site-publishing.md](references/site-publishing.md)。

1. 用 `scripts/prepare_site_post.py` 从主稿生成 `site-post/`，去掉公众号专用 frontmatter，并复制 `imgs/`。公众号草稿保存成功后生成网站备份时传入 `--source-wechat`。
2. 人工核对生成的 `index.md`、图片引用、日期、slug、摘要和标签。
3. 获得网站发布授权后，把 `site-post/` 放入 `site/content/posts/YYYY-MM-DD-<slug>/`。
4. 执行 `npm --prefix site run verify`。失败就修复并重验，不能跳过。
5. 验证通过后执行 `npm --prefix site run publish`；该命令会提交 `site/` 变更、推送、部署并做线上健康检查。只有全部成功才报告网站已上线。

## 完成报告

分别列出：

- 源稿来源、`source.md` 路径和发布主稿路径。
- 封面与插图路径，以及实际使用的生成 Skill。
- 公众号状态：未执行 / 预览完成 / 草稿已保存 / 失败；附上实际使用的账号名与 `media_id`（如有）。
- 网站状态：待发布 / 验证通过 / 已提交推送 / 已部署上线 / 失败；上线后给出文章 URL。
- 仍需人工完成的动作，例如公众号后台最终群发、原创声明或封面裁切复核。

不要用“已发布”概括多个渠道，也不要把测试通过、草稿保存或 Git 推送冒充线上可访问。不要把发布包装描述为文章创作、研究、审校或改稿。

---
name: wechat-site-publisher
description: 接收任意已定稿 Markdown 文章，在不改写正文的前提下补齐发布元数据和视觉资产，写入微信公众号草稿，并按 dreamble/site 规范准备或发布 simiam 站点版本。适用于“把这篇文章同步公众号和个人站”“生成配图并准备双渠道发布”等请求；只发公众号使用 baoyu-post-to-wechat，文章创作或研究由对应上游 Skill 负责。
---

# 微信公众号与站点文章发布助手

把任意已定稿 Markdown 文章转换为渠道可用主稿，并完成视觉资产、微信公众号草稿和 simiam 站点版本。默认中文。源稿、发布主稿、公众号草稿和网站上线是四种不同状态，必须分别报告；本 Skill 不负责文章创作、研究、审校或改写正文。

## 开始前

1. 明确输入源稿路径。输入必须是用户或上游创作、研究、编辑 Skill 已经定稿的 Markdown 文件。
2. 源稿尚未定稿时停止发布包装，并交回对应上游完成；本 Skill 不判断主题领域，也不调用证券分析或其他内容生产 Skill。
3. 确认交付范围：只准备本地材料、保存公众号草稿、准备网站版本或发布网站。任何外部写入仍按“发布授权”处理。

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
- 两个渠道均完成并核验前保留工作目录；不要自动删除，除非用户明确要求清理。

## 接收报告与准备主稿

1. 将已定稿 Markdown 原样保存为 `source.md`，作为本次发布的内容真源。
2. 只检查发布兼容性：文件可读、frontmatter 中存在 `title` 和 `summary`、Markdown 图片路径可解析。不得检查或修改事实、数字、观点、结论、风险和措辞。
3. 使用 `scripts/prepare_article.py` 生成 `article.md`。脚本只增加规范的 `coverImage` 和正文封面引用，不改写原正文。
4. 发布主稿 frontmatter：

```yaml
---
title: 文章标题
summary: 120 字以内摘要
coverImage: ./imgs/cover.png
---
```

5. 除 frontmatter 和图片引用外，Publisher 不得重排段落、润色语言、删减内容、改写标题摘要或修正文中内容。用户要求修改正文时，交回原作者或对应上游 Skill 产出新版定稿。

## 视觉资产

1. 封面资产是必需项。用户未提供可用封面时，调用 `$baoyu-cover-image`，以 `source.md` 为输入，默认建议微信公众号宽封面 `2.35:1`，最终图片放到 `imgs/cover.png`。遵守该 Skill 的偏好读取、确认和提示词留档规则。
2. 正文插图不是默认凑数量。只有产业链结构、跨公司比较、周期演变或关键机制仅靠文字不易理解时，才调用 `$baoyu-article-illustrator`；它只增加图片和图片引用，不改写研究文字。
3. 插图应帮助理解，不把推测画成事实。精确数值优先保留源稿 Markdown 表格；AI 图片中的文字或数字不可靠时，改用少字或无字视觉。
4. 检查图片文件存在、Markdown 相对路径正确、封面可读且与标题一致，再进入发布阶段。

## 发布授权

生成本地文件不等于授权外部发布。公众号草稿写入、Git 推送和网站部署都属于外部状态变更。

- 如果用户本次请求已明确说“保存到公众号草稿”“同步/发布到网站”等，可按该范围执行，不重复确认。
- 如果用户只要求生成或准备材料，在发布前集中展示标题、摘要、封面、公众号主题和两个目标渠道，询问一次授权。
- 一个渠道失败不阻塞另一个已获授权的渠道，但必须保留主稿并分别报告结果。

## 微信公众号

1. 调用 `$baoyu-post-to-wechat`，直接传入 `article.md`；不要预先转成 HTML。
2. 主题、主题色、账号和 API/browser 方法由该 Skill 的参数或 `EXTEND.md` 决定；没有配置时按它的首次设置流程处理。
3. 封面使用 `imgs/cover.png`。先验证标题、摘要、正文图片和链接，再写入草稿箱。
4. 在本工作流中，用户所说的“发表到公众号”默认指**保存到公众号草稿箱**；只有用户明确要求正式群发时，才把它理解为群发。
5. 只有看到草稿成功证据时才报告“公众号草稿已保存”。草稿保存成功后，网站备份即可标记 `source: wechat`；这不改变公众号侧仍处于草稿状态的事实。

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
- 公众号状态：未执行 / 预览完成 / 草稿已保存 / 失败；有 `media_id` 时附上。
- 网站状态：待发布 / 验证通过 / 已提交推送 / 已部署上线 / 失败；上线后给出文章 URL。
- 仍需人工完成的动作，例如公众号后台最终群发、原创声明或封面裁切复核。

不要用“已发布”概括多个渠道，也不要把测试通过、草稿保存或 Git 推送冒充线上可访问。不要把发布包装描述为文章创作、研究、审校或改稿。

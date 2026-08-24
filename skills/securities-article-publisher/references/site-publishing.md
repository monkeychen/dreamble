# 个人站文章转换与发布

仅在生成网站版本或发布到 `site/` 时读取本文件。`site/AGENTS.md`、`site/README.md` 和 `site/src/content.config.ts` 是当前规则真源；规则冲突时以它们为准。

## 发布状态决策

本工作流将微信公众号作为文章来源渠道。文章成功写入公众号草稿箱后，网站备份即可使用 `source: wechat`，不需要等待正式群发。

- 微信公众号草稿保存成功，且网站文章是备份：生成网站版本时加 `--source-wechat`，获得网站发布授权后可以直接上线。
- 微信公众号草稿尚未保存成功：网站待发布版本暂不写 `source`；若用户只要求准备材料，可加 `--draft` 保留为本地待发布版本。
- 用户明确要求网站独立或同步首发：不写 `source`，可直接发布网站。

`source: wechat` 只表达备份来源，不代表公众号文章已经正式群发。完成报告仍要把公众号状态写成“草稿已保存”。

## 生成命令

从仓库根目录执行：

```bash
python3 skills/securities-article-publisher/scripts/prepare_site_post.py \
  tmp/securities-article-publisher/YYYY-MM-DD-<slug>/article.md \
  --output-root tmp/securities-article-publisher/YYYY-MM-DD-<slug>/site-post \
  --date YYYY-MM-DD \
  --slug <slug> \
  --title "文章标题" \
  --summary "文章摘要" \
  --tag "标签一" \
  --tag "标签二"
```

按状态追加 `--draft`、`--source-wechat`，两者可以同时使用。脚本会：

- 校验日期和 slug。
- 去掉主稿 frontmatter，只保留正文。
- 生成站点允许的 frontmatter。
- 把主稿同目录下的 `imgs/` 复制到目标文章目录。
- 目标目录已存在时拒绝覆盖，防止误伤已有文章。

输出结构为：

```text
site-post/YYYY-MM-DD-<slug>/
├── index.md
└── imgs/
```

## 入站与验收

1. 检查目标 slug 在 `site/content/posts/` 中尚未使用。
2. 将生成的完整文章目录复制到 `site/content/posts/`。
3. 运行 `npm --prefix site run verify`。
4. 若只要求准备待发布版本，到此停止并报告路径。
5. 若已授权网站发布，运行 `npm --prefix site run publish`。
6. 用最终 URL `https://simiam.com/posts/<slug>/` 做线上检查。

网站发布命令会改变 Git 和线上状态。工作区有无关改动时，只允许提交本次 `site/` 文章目录，不能夹带其他文件。

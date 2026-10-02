# xtract 文章配图与生成提示词

本篇使用内置 imagegen 生成两张原创配图，另附项目文档的工作台演示截图。图片按站点约定与正文同目录保存，正文使用相对路径。下方保存最终提示词，便于后续重做。没有修改原始生成文件。

## 文件与用途

- `cover.png`，公众号封面，暖色纸质编辑风格，宽幅约 2.35∶1。
- `creator-workflow.png`，正文流程插图，宽幅约 16∶9，注明 xtract 已有能力和创作者承担的步骤。
- `workbench-demo.png`，从 xtract 的 `docs/assets/workbench.png` 原样复制。经对应截图脚本确认，画面使用演示推文；文章已在图下说明。不是本次真实账号抓取结果。

## 封面最终提示词

```text
Use case: editorial-illustration. Create a publication-ready cover banner for a Chinese WeChat article introducing the open-source desktop tool xtract, which collects public X/Twitter posts into local source documents for content creators. This is an editorial illustration, not an application screenshot. Canvas must be wide 2.35:1, approximately 1536 by 656 pixels, full bleed, with generous safe margins for mobile cover crops. Visual direction: sophisticated warm editorial magazine, ivory paper background, charcoal typography, terracotta red accents, muted sage, subtle tactile paper and elegant realistic miniature document objects. On the left, set large, exceptionally clear lowercase product name exactly "xtract", with spacious refined serif typography. Beneath it, render exact Simplified Chinese headline "把 X 上的好内容留下来", in a bold clean Chinese font, and one smaller line exactly "给内容创作者的资料工具". On the right, create a beautiful sculptural editorial still life of a few social post cards flowing into neatly organized source document pages, one page marked with a small link symbol and another a photo thumbnail, showing the concrete transition from reading posts to saving references. Use a subtle X letter on a source card, without other brand logos. Show only abstract graphic lines as document body text; no fabricated posts, named people, dates, metrics, quotations, or fake interface. Make the image memorable through composition and paper texture, not clutter. No arrows occupying the headline, no neon sci-fi, no robot, no gradient tech grid, no extra slogans, no watermark. All Chinese text must be perfectly legible and verbatim.
```

## 正文插图最终提示词

```text
Use case: editorial-illustration. Generate a polished, original Chinese editorial illustration for the body of a WeChat article about xtract. Wide landscape canvas approximately 16:9, high resolution, warm ivory paper with charcoal Chinese type, terracotta and muted sage accents. Match a refined tactile paper-and-document editorial magazine style. This is an explanatory illustration with material objects and beautiful composition, not a fake software screenshot, not a generic tech flowchart. A very readable title at the top exactly "从 X 原文到创作材料". Show a left-to-right process in three visually distinct connected work areas, with large labeled steps and abundant breathing space. LEFT, a small group of social post cards and one open long article on paper, labeled exactly "X 上的原始内容", with four small clear source labels exactly "关注流" "指定作者" "X 列表" "关键词搜索". CENTER, a sculptural set of organized source pages with a link icon, image thumbnail, and short briefing page, labeled exactly "xtract", with three clear capability labels exactly "原文采集" "本地归档" "AI 简报". Directly underneath center, add a small terracotta pill exactly "已有能力". RIGHT, a creator's hands with a magnifier verifying a linked original source and a pencil annotating a draft page, labeled exactly "创作者", with action labels exactly "核对来源" "判断选题" "写作与演示". Underneath right, a sage annotation exactly "由创作者与外部工具完成". A few elegant thin terracotta arrows connect left to center and center to right, making responsibility completely clear. At the far bottom or right edge, show small paper pieces labeled exactly "公众号文章" "视频脚本" "培训案例", as outcomes of the creator's work, not automatic features of xtract. All labels should be legible on mobile, no more text beyond the specified labels. Document body uses abstract strokes only. No named authors, no fake quotes, no dates, no interaction metrics, no fabricated UI, no robot, no watermark, no additional brand logos. Exact Chinese characters are important. Ensure all specified wording is rendered verbatim with no punctuation added.
```


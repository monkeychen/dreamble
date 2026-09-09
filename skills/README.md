# skills

「聊哉梦呓」自研 Agent Skills 的开发源码目录。

## 定位与安装方式

- 本目录是**开发源码目录**，不挂载、不参与任何 AI 工具的技能加载。AI 工具（WorkBuddy / Codex 等）不得把 `skills/` 下的内容链入任何加载目录。
- 唯一安装路径：由站主自行把需要的技能目录复制到用户级（如 `~/.workbuddy/skills/`）或项目级（如 `.codebuddy/skills/`）skills 目录。
- 每个技能的用途、触发条件、依赖与边界以各自的 `SKILL.md` 为准；部分技能带 `scripts/`（含测试）和 `evals/`，修改后应运行对应测试。

## 技能总览

### 公众号内容生产线

按「聊哉梦呓」公众号从选题到发布的流程排列：

| 技能 | 环节 | 用途 |
|---|---|---|
| [topic-selector](topic-selector/SKILL.md) | 选题 | 找选题灵感、评估选题是否值得写、热点找角度、选题规划 |
| [material-collector](material-collector/SKILL.md) | 素材 | 选题确定后搜集事实、数据、案例、引言等支撑材料，事实先行 |
| [article-writer](article-writer/SKILL.md) | 正文 | 从选题加素材包输出成稿或初稿，润色、改写、调整开头结尾 |
| [fact-reviewer](fact-reviewer/SKILL.md) | 审校 | 对完稿文章做事实核查、数据校验、引言查证 |
| [title-crafter](title-crafter/SKILL.md) | 标题 | 起标题、评估与 A/B 对比；有底线，不做标题党 |
| [wechat-site-publisher](wechat-site-publisher/SKILL.md) | 发布 | 定稿 Markdown 补齐发布元数据和视觉资产，写公众号草稿并按 dreamble/site 规范准备或发布站点版本 |

### 风格写作器

| 技能 | 用途 |
|---|---|
| [liubei-writer](liubei-writer/SKILL.md) | 用刘备教授的风格写公众号文章（老股民茶馆夜话体）；复刻思维方式与文体，不写入原作者个人生平 |
| [maobidao-writer](maobidao-writer/SKILL.md) | 用猫笔刀的风格写财经评论、投资复盘、国际政经解读、社会观察 |

### 思维框架（角色扮演顾问）

| 技能 | 用途 |
|---|---|
| [liubei-cc](liubei-cc/SKILL.md) | 刘备教授的思维框架与表达方式，基于 269 篇文章调研提炼心智模型与决策启发式；作思维顾问分析股市、地缘、AI、社会事件 |
| [liubei-gg](liubei-gg/SKILL.md) | 刘备教授思维框架的轻量变体，基于 2 个本地语料文献提炼 |
| [liubei-3in1](liubei-3in1/SKILL.md) | 刘备教授风格三合一：写作、改写、评估与提示词工程 |
| [maobidao](maobidao/SKILL.md) | 猫笔刀的思维框架与表达方式，基于近 90 篇一手文章调研；激活后持续保持角色 |

### 证券研究

| 技能 | 用途 |
|---|---|
| [securities-analyst](securities-analyst/SKILL.md) | 证券研究与交易策略（个股/行业/宏观，覆盖 A 股、港股、美股等全球市场），最终报告可直接作公众号文章使用；带回测脚本与 evals |
| [cn-equity-deep-dive](cn-equity-deep-dive/SKILL.md) | A 股/港股买方深度研究，产出决策底稿（评级、合理价值与买入区间、Kill Criteria）；要发布的文章改用 securities-analyst |

### 基础设施

| 技能 | 用途 |
|---|---|
| [skill-kit](skill-kit/SKILL.md) | 管理 AI 编程 Agent 的 skill 安装、卸载与查看，软链接安装，操作前展示计划并确认 |
| [ima-skills](ima-skills/SKILL.md) | 腾讯 ima 笔记与知识库管理：笔记搜索与新建、知识库上传、网页/微信文章添加与检索 |

## 外部依赖

`wechat-site-publisher` 运行时依赖第三方开源项目 [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) 的技能（必需/条件必需/可选三级），本项目不随附，需自行安装。依赖强度分级与缺失时的降级行为见 [skills/wechat-site-publisher/SKILL.md](wechat-site-publisher/SKILL.md)，安装说明见仓库根 [README.md](../README.md)。

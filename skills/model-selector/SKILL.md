---
name: model-selector
description: 模型选择顾问——分析任务特征并从用户订阅的模型中推荐最合适的一个，覆盖海外（OpenAI / Anthropic / Google）和国产（智谱 GLM / MiniMax / DeepSeek）共 6 家。**只在用户显式表达选模型意图时触发**，典型触发短语：「帮我判断模型」「选模型」「用哪个模型」「这个任务适合什么模型」「我应该用哪个 AI」「Claude 还是 GPT」「Gemini 还是」「换哪个模型好」「这种任务用谁」「推荐模型」「先推荐模型」「which model」。**不要因为用户单纯描述了一个任务就触发**——用户只是想要任务结果时，直接帮他做事，不要打断流程做模型推荐。判断标准：句子里有「模型/AI/Claude/GPT/Gemini/哪个/选/换/推荐」类词 + 询问/选择语气，两者都满足才触发。
---

# 模型选择顾问

把模型选择当成**任务路由**，不是排行榜。给一个确定推荐 + 入口配置 + 升降级路径，帮用户省配额。

## 核心原则

1. **任务匹配 > 模型排名**：旗舰有旗舰的用法，轻量有轻量的舞台，混用才是浪费。
2. **省配额优先**：默认推荐能完成任务的最便宜模型；升档要有明确理由。
3. **先选入口，再选模型**：ChatGPT / Codex / Claude Code / API 的选项不是同一套，不能给用户用不到的参数。
4. **模型 + thinking level 分开推荐**：归一化到 `none/low/medium/high/xhigh/max`，映射到对应入口的真实配置项。
5. **中文场景优先国产**：在中文写作/批量/Agent 等场景，国产模型成本低 5-20 倍且质量不输 Claude/GPT。

---

## 工作流（5 步）

### 1. 判断请求维度

| 维度 | 取值 |
|---|---|
| `task` | chat、writing、coding、research、data extraction、product/strategy、multimodal、agent/tool workflow、safety-critical |
| `complexity` | low / medium / high / frontier |
| `risk` | low / medium / high（含法律、医疗、金融、安全、生产部署、不可逆操作、公开事实声明） |
| `freshness` | static / likely-current / must-current |
| `interaction` | answer only / use tools / edit code-files / browse / long-running agent |
| `language` | 中文 / 英文 / 混合（决定是否优先国产） |

### 2. 判断使用入口

- 用户明确说入口 → 按该入口推荐
- 用户没说 → 按任务推测：
  - 普通对话/写作/研究 → Chat 产品（ChatGPT / Claude.ai / Gemini App）
  - 改代码/修 CI/仓库操作 → Code 产品（Codex / Claude Code / Antigravity）
  - 构建自有产品 / 批量调用 → API

### 3. 时效与官方源核对

- 涉及「当前/最新」模型，或可能模型名变了：先查 `references/model-catalog.md` 基线，可联网时验证官方文档。
- 高时效任务（must-current）：选支持联网/搜索的强模型 + high thinking。

### 4. 推荐首选模型 + 思考等级

- 首选一个具体推荐
- 必要时给 **降级**（更便宜/更快）
- 必要时给 **升级路径**（什么时候换更强）

### 5. 解释影响

围绕用户影响：**质量、速度、成本、可靠性**，以及何时切换。中文场景额外说明「为什么不用更贵的海外模型」。

---

## 输出格式

```text
推荐：<provider> <model>，思考等级 <level>
入口：<product surface，如 ChatGPT / Codex / Claude Code / Claude.ai / Gemini App / Antigravity / API>
理由：<1-3 条，先讲对用户结果的影响，再讲为什么不需要更贵>
降级：<更便宜/更快的选项 + 触发条件>
升级：<什么时候换更强模型 + 具体型号>
注意：<时效性/来源/风险提醒/特殊参数，如需要>
```

---

## 路由总表

| 场景 | 默认模型 | thinking |
|---|---|---|
| 改写、摘要、分类、结构化抽取（英文） | small/mini/flash/haiku/nano class | none/low |
| 改写、摘要、分类（中文） | **GLM-4.7-Flash（免费）** | none |
| 普通问答、规划、写作、产品分析 | balanced flagship 或 mid-tier | medium |
| 中文公众号/课程/报告 | **GLM-4.7 或 MiniMax M2.7** | medium |
| 中文顶级文学性长文 | **Claude Opus 4.6** | high |
| 代码解释、code review、小补丁 | strong coding/general model | medium/high |
| 多文件 coding、重构、agentic tool use | coding/agentic flagship（Opus 4.7 / GPT-5.3-codex） | high/xhigh |
| 深度研究、当前事实、需要引用来源 | best model with browsing/search | high |
| 法律/医疗/金融/安全等高风险任务 | strongest available model + sources + caveats | high/xhigh |
| 图像/视频/音频理解 | provider 的 native multimodal model | medium/high |
| 实时语音或低延迟 UX | realtime/flash/haiku class | low/medium |
| **超大批量调用（>1 万次/天）** | **DeepSeek v4-flash（关 thinking）/ GLM-4.7-Flash 免费** | none |
| **超长文档（>30K 字）** | GLM-4-Long（中文）/ Gemini 3.1 Pro（英文）/ DeepSeek v4-flash | medium |

---

## 厂商偏好

- **OpenAI**：优先用于 coding agent（Codex）、tool-heavy workflow、computer use、深度研究（o3-deep-research）。
- **Anthropic**：优先用于长上下文综合、agentic coding（Opus 4.7）、**顶级中文文学性写作（Opus 4.6）**、复杂推理。
- **Google**：优先用于 multimodal（图/视频/音）、长上下文、Google 生态集成、Flash/Lite 高吞吐。
- **智谱 GLM**：优先用于中文结构化写作、中文报告分析、**免费档高频中文查询**、长程中文 Agent。
- **MiniMax**：优先用于中文叙事/创作、**低成本中文 Agent**、角色扮演（M2-her）。
- **DeepSeek**：优先用于**极低成本批量任务**、Anthropic API 兼容场景（替换 Claude Code 后端省钱）。

⚠️ 不要宣称某个厂商「全局最强」。按任务匹配，并说清楚取舍。

---

## 旗舰升档触发条件

只有明确理由才动旗舰：

| 旗舰 | 触发条件 |
|---|---|
| **Claude Opus 4.7** | Sonnet 4.6 跑失败过、10+ 步 Agent、复杂系统架构、agentic coding |
| **Claude Opus 4.6** | 需要最高文学/文风质量的长篇内容创作（4.6 写作 > 4.7） |
| **gpt-5.5** | 严格思维链推理、复杂数学、需要 o 系列推理能力 |
| **gpt-5.5-pro** | 极限推理 / 顶级专业问题（$30/$180，是 Opus 6 倍，慎用） |
| **Gemini 3.1 Pro** | 输入超 3 万字且需精确引用 / 复杂多模态深度理解 |
| **GLM-5.1 / GLM-5** | GLM-4.7 质量明显不足、长程中文 Agent |
| **MiniMax M2.7** | 已是性价比首选，无升档必要 |
| **deepseek-v4-pro** | 复杂推理但预算敏感（仍比 Opus 便宜数十倍） |

**默认主力**（覆盖 80% 任务）：Sonnet 4.6、GPT-5.4、Gemini 3.5 Flash、GLM-4.7、MiniMax M2.7、DeepSeek v4-flash。

---

## 思考等级（跨厂归一化）

| 档位 | 用途 |
|---|---|
| `none` | 确定性转换、格式整理、简单抽取 |
| `low` | 快速回答、低风险草稿、简单工具使用 |
| `medium` | **默认平衡档**，多数非平凡任务 |
| `high` | 复杂约束、代码变更、高风险事实、带工具计划 |
| `xhigh` | 最难 agentic 任务、大型重构、深度评估 |
| `max` | 错误代价极高的任务 |

⚠️ 这些是归一化标签，不是每个产品入口都原样支持。**给具体推荐时必须映射到入口自己的配置项**（ChatGPT 用 Instant/Thinking/Pro + thinking time，Codex 用 effort，Anthropic API 用 `thinking.type + output_config.effort`，Gemini API 用 `thinkingLevel/thinkingBudget`）。详见 `references/thinking-levels.md`。

---

## 边界情况

- **任务跨多个类型**：找主导部分，按主导路由。例如「分析 3 份资料然后写报告」→ 主导是综合分析 → Gemini 3.1 Pro。
- **不确定复杂度**：往低档走，跑完不满意再升档。宁可低估也别高估。
- **任务描述模糊**：问一个最关键的澄清问题（语言？长度？目的？），最多问一次，然后给推荐。
- **预算极度敏感**：优先 DeepSeek v4-flash / GLM 免费档 / MiniMax M2.7。
- **需要 Claude Code / Codex CLI 兼容**：DeepSeek 兼容 Anthropic + OpenAI 双格式，可直接接入。
- **时效模糊**：先按 `references/model-catalog.md` 给基线，可联网时再核对官方源。

---

## 详细参考

需要更深入信息时查阅：

- **完整模型清单 + 价格**（6 家 50+ 模型）→ `references/model-catalog.md`
- **产品入口矩阵**（ChatGPT / Codex / Claude Code / Gemini App / Antigravity / API 配置）→ `references/product-surfaces.md`
- **思考等级映射**（归一化 → 各厂真实参数）→ `references/thinking-levels.md`
- **中文场景特化路由**（中文写作/批量/Agent/成本对比）→ `references/chinese-scenarios.md`

---

## 时效与来源

推荐具体「当前模型」时：
- 可联网 → 引用官方文档
- 无法联网 → 说明使用的是 catalog 基线，给出 `Last checked` 日期，把模型名表述为「上次验证」

数据基线最后核对：2026-05-27。

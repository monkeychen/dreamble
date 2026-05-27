# 模型清单基线

Last checked: 2026-05-27。可联网时，以官方文档为准。

## 官方来源

**海外：**
- OpenAI Models: https://platform.openai.com/docs/models
- OpenAI Pricing: https://platform.openai.com/docs/pricing
- OpenAI Codex rate card: https://help.openai.com/en/articles/20001106-codex-rate-card
- Anthropic Models: https://docs.claude.com/en/docs/about-claude/models/overview
- Anthropic Pricing: https://www.anthropic.com/pricing
- Claude Opus 4.7 best practices: https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code
- Google Gemini Models: https://ai.google.dev/gemini-api/docs/models
- Google Gemini Pricing: https://ai.google.dev/gemini-api/docs/pricing
- Google Antigravity: https://antigravity.google/docs/models

**国产：**
- 智谱 GLM: https://bigmodel.cn/pricing
- MiniMax: https://platform.minimaxi.com/docs/guides/pricing-paygo
- DeepSeek: https://api-docs.deepseek.com/quick_start/pricing

---

## 🔵 Anthropic Claude

### 当前文本模型

| 模型 | API ID | 输入 / 输出 ($/1M) | 上下文 | 强项 |
|---|---|---|---|---|
| **Claude Opus 4.7** | `claude-opus-4-7` | $5 / $25 | 1M | 当前旗舰，agentic coding 大幅升级 |
| **Claude Opus 4.6** | `claude-opus-4-6` | $5 / $25 | 1M | 上代旗舰，**内容写作效果优于 4.7** |
| **Claude Sonnet 4.6** | `claude-sonnet-4-6` | $3 / $15 | 1M | 平衡之王，多数专业任务首选 |
| **Claude Haiku 4.5** | `claude-haiku-4-5` | $1 / $5 | 200K | 最快，高频简单任务 |
| Claude Mythos Preview | — | — | — | Project Glasswing 防御网络安全（邀请制） |

### Thinking 规则

- **Opus 4.7**：只支持 adaptive thinking（`thinking: {type: "adaptive"}`），手动 extended thinking 会被拒绝。默认 `display: "omitted"` 降低首 token 延迟。
- **Opus 4.6 / Sonnet 4.6 / Haiku 4.5**：推荐 adaptive thinking；extended thinking 仍可用但 deprecated。
- **Effort levels**：`low` / `medium` / `high` / `xhigh` / `max`。`xhigh` 仅 Opus 4.7 支持；`max` 用于 Opus 4.7/4.6 + Sonnet 4.6。
- **Opus 4.7 官方建议**：coding/agentic 从 `xhigh` 起步，普通高智能任务至少 `high`，成本敏感降到 `medium`，`max` 只给真正 frontier 问题。
- **Sonnet 4.6 官方建议**：`medium` 作多数应用默认，`low` 用于高吞吐/低延迟，`high/max` 用于复杂推理。

### Batches API
Opus 4.7、Opus 4.6、Sonnet 4.6 支持 300K 输出 token（需 `output-300k-2026-03-24` beta header）。

---

## 🟢 OpenAI

### 通用 GPT-5.5 / 5.4 系列（来自 platform.openai.com/docs/pricing）

| 模型 | 输入/输出 ($/1M，短上下文) | 长上下文输入/输出 | 强项 |
|---|---|---|---|
| **gpt-5.5** | $5 / $30 | $10 / $45 | 当前旗舰，coding/agent/专业工作 |
| **gpt-5.5-pro** | $30 / $180 | $60 / $270 | 极限算力版（慎用） |
| **gpt-5.4** | $2.50 / $15 | $5 / $22.50 | 上代旗舰，性价比 |
| **gpt-5.4-mini** | $0.75 / $4.50 | — | 经济 coding/computer use/subagent |
| **gpt-5.4-nano** | $0.20 / $1.25 | — | 极廉高吞吐 |
| **gpt-5.4-pro** | $30 / $180 | $60 / $270 | 上代极限版 |

### 编程专用 Codex 系列（rate card）

Codex rate card 列出：`GPT-5.5`、`GPT-5.4`、`GPT-5.4-Mini`、`GPT-5.3-Codex`、`GPT-5.2`，每个都支持 `low/medium/high/xhigh` effort。

| 模型 | 输入/输出 ($/1M) | 定位 |
|---|---|---|
| **gpt-5.3-codex** | $1.75 / $14 | 编程专用旗舰 |
| gpt-5.2-codex / 5.1-codex / 5.1-codex-max / 5.1-codex-mini / 5-codex | 见 docs/models | 历史版本，仍可用 |

### Pro 推理 / Specialized

| 模型 | 输入/输出 ($/1M) | 定位 |
|---|---|---|
| **gpt-5.2-pro / gpt-5-pro** | 同 5.5-pro 等级 | 顶级专业推理 |
| **o3-deep-research** | $5 / $20 | 深度研究旗舰 |
| **o4-mini-deep-research** | $1 / $4 | 经济深度研究 |
| **computer-use-preview** | $1.50 / $6 | 浏览器自动化 |
| **chat-latest** | $5 / $30 | ChatGPT 默认模型指针（不要把 UI 名等同 API ID） |

### Reasoning 规则

- API 模型用 `reasoning.effort` 控制，支持 `none/low/medium/high/xhigh`。
- 简单任务用 `none/low` 或 mini/nano。
- 普通专业任务：`gpt-5.5` + `medium`。
- 复杂 coding/research：`high/xhigh`。
- 极难且质量收益明确：`gpt-5.5-pro`，可能运行数分钟，适合 background mode。

### 多模态/专项

| 类别 | 模型 | 备注 |
|---|---|---|
| Realtime | gpt-realtime-2 / 1.5 / mini / translate | 音频对话/翻译 |
| Image | gpt-image-2 / 1.5 / 1-mini | 图像生成 |
| Video | sora-2 / sora-2-pro | 视频 |
| Transcription | gpt-4o-transcribe / mini-transcribe | 转录 |

---

## 🟡 Google Gemini

### 当前 Gemini 模型（来自 ai.google.dev/gemini-api/docs/pricing）

| 模型 | 输入/输出 ($/1M) | 长上下文 | 强项 |
|---|---|---|---|
| **Gemini 3.1 Pro Preview** | $2 / $12 | >200K: $4 / $18 | 旗舰：复杂推理、autonomous coding、agentic workflow |
| **Gemini 3.5 Flash** ⭐ | $1.50 / $9 | — | 性价比之王，agentic/coding 已超 3.1 Pro |
| **Gemini 3 Flash Preview** | $0.50 / $3 | — | 廉价 Frontier-class Flash |
| **Gemini 3.1 Flash-Lite** | $0.75 / $4.50 | — | 极廉多模态 |
| **Gemini 2.5 Pro** | $1.25 / $10 | >200K: $2.50 / $15 | 稳定 2.5，复杂推理/coding |
| **Gemini 2.5 Flash** | $0.30 / $2.50 | — | 经济通用 |
| **Gemini 2.5 Flash-Lite** | $0.10 / $0.40 | — | 极廉批量 |
| **Gemini 2.0 Flash-Lite** | $0.075 / $0.30 | — | 最便宜的 Gemini |
| **Gemini 2.5 Computer Use Preview** | $1.25 / $10 | — | 浏览器自动化 |
| **Gemini Deep Research Agent** | 按基模型 | — | 多步自主研究 |

### 多模态/专项

| 类别 | 模型 |
|---|---|
| Image | Nano Banana 2 Preview / Pro Preview / Imagen 4 |
| Video | Veo 3.1 Standard / Fast / Lite |
| Audio | Gemini 3.1 Flash Live / TTS Preview |
| Music | Lyria 3 Clip / Pro Preview |
| Robotics | Gemini Robotics-ER 1.6 Preview |
| Embeddings | Gemini Embedding 2 / Embedding |

### Thinking 规则

- **Gemini 3+**：优先用 `thinkingLevel`（不要用 `thinkingBudget`）。
- **Gemini 3 Pro**：支持 `thinkingLevel: "low"` 和 `"high"`；默认动态 `high`，不能完全关闭。
- **Gemini 3 Flash**：支持 `minimal/low/medium/high`；`minimal` 大概率不思考但非严格关闭。
- **Gemini 2.5**：用 `thinkingBudget`（`-1` 动态、`0` 关闭、正数为 token 预算）。
  - 2.5 Pro：128-32768，不能关闭
  - 2.5 Flash：0-24576，`0` 可关闭
  - 2.5 Flash-Lite：默认不 thinking，512-24576

---

## 🔴 智谱 GLM（中文场景核心）

### 旗舰系列（GLM-5/4.7/4.5）

| 模型 | ¥/百万 token（输入 ≤32K / 输出） | 强项 |
|---|---|---|
| **GLM-5.1** | ¥6 / ¥24 | 新品旗舰，最强中文综合 |
| **GLM-5-Turbo** | ¥5 / ¥22 | 高速旗舰 |
| **GLM-5** | ¥4 / ¥18 | 对标 Claude Opus 4.6，长程 Agent |
| **GLM-4.7** | ¥2 / ¥8 | 中文通用主力 |
| **GLM-4.5-Air** | ¥0.8-1.2 / ¥2-8 | 平价高性能 |

### 快速系列（Flash）

| 模型 | ¥/百万 token | 强项 |
|---|---|---|
| **GLM-4.7-FlashX** | ¥0.5 / ¥3 | 200K，低价 |
| **GLM-4.7-Flash** | **免费** | 200K，日常中文查询首选 |
| **GLM-4-Flash** | **免费** | 128K |

### 推理系列（GLM-Z1）

| 模型 | ¥/百万 token | 强项 |
|---|---|---|
| **GLM-Z1-Air** | ¥0.5 | 经济推理，128K |
| **GLM-Z1-AirX** | ¥5 | 最快推理 |
| **GLM-Z1-FlashX** | ¥0.1 | 极低价推理 |

### 专用/通用

| 模型 | ¥/百万 token | 强项 |
|---|---|---|
| **GLM-4-Long** | ¥1 | **1M 超长上下文** |
| **GLM-4-Assistant** | ¥5 | Agent 专用 |
| **GLM-4-Plus** | ¥5 | 128K 通用 |
| **GLM-4-Air** | ¥0.5 | 经济通用 |

---

## 🟣 MiniMax（中文叙事 / 编程 / Agent，价格极便宜）

| 模型 | 输入 / 输出 (¥/1M) | 强项 |
|---|---|---|
| **MiniMax-M2.7** ⭐ | ¥2.1 / ¥8.4 | 最新旗舰，自我迭代 |
| **MiniMax-M2.7-highspeed** | ¥4.2 / ¥16.8 | 高速版（效果同 M2.7） |
| **MiniMax-M2.5** | ¥2.1 / ¥8.4 | 上代旗舰 |
| **M2-her** | ¥2.1 / ¥8.4 | 角色扮演、多轮对话专用 |
| **MiniMax-M2.1** | ¥2.1 / ¥8.4 | 多语言编程 |
| **MiniMax-M2** | ¥2.1 / ¥8.4 | 高效编码 / Agent |

输出 ¥8.4/M (≈ $1.2/M)，比 Claude Opus 便宜 ~20 倍。

---

## 🟤 DeepSeek（全场最便宜 + Anthropic 兼容）

| 模型 | 输入 (Cache miss) / 输出 ($/1M) | 上下文 | 强项 |
|---|---|---|---|
| **deepseek-v4-flash** ⭐ | $0.14 / $0.28 | 1M（输出 384K） | 全场最便宜旗舰，支持 thinking/non-thinking 双模式 |
| **deepseek-v4-pro** | $0.435 / $0.87 (75% off 至 5/31) | 1M | 最强 DeepSeek，思维链推理 |

**Cache hit 价格更便宜：** v4-flash 缓存命中 $0.0028 / 1M（输入）。

### Thinking 规则

- 默认开启 thinking 模式，分类等简单任务**必须**设置 `"thinking": {"type": "disabled"}` 关闭，否则输出 token 暴涨 5-10 倍。
- 复杂推理用 `"reasoning_effort": "high"`。

### 独家优势

- **API 同时兼容 OpenAI 和 Anthropic 格式**（base_url 二选一）
- 可直接接入 Claude Code / Codex CLI 作为后端

旧名 `deepseek-chat` / `deepseek-reasoner` 将于 2026-07-24 弃用，对应 v4-flash 的 non-thinking / thinking 模式。

---

## 默认决策梯

1. **简单、低风险任务** → 先用便宜快模型（Flash/Mini/Haiku/v4-flash）。
2. **有歧义、多步推理或用户可见质量** → balanced flagship/mid-tier + `medium` thinking（Sonnet 4.6 / gpt-5.4 / Gemini 3.5 Flash / DeepSeek v4-flash thinking）。
3. **需要工具、代码编辑、当前研究或高风险事实** → flagship + `high` thinking（Opus 4.7 / gpt-5.5 / Gemini 3.1 Pro）。
4. **长程 agentic coding/research** → 最强任务专用模型 + `xhigh/max` reasoning。
5. **输出质量不够** → 先提高 thinking；仍不够再升级模型。

## 中文场景额外规则

6. **中文写作/分析/批量** → 优先国产模型（GLM/MiniMax/DeepSeek），成本低 5-20 倍，质量在中文场景不输 Claude/GPT。
7. **顶级中文文学性** → Claude Opus 4.6（4.6 写作 > 4.7，4.7 主升 coding）。

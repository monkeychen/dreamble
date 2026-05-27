# 产品入口模型矩阵

Last checked: 2026-05-27。产品 UI 变化快，可联网时优先查官方 Help/Docs/Blog。

## 核心原则

- **先选入口，再选模型**：Chat 产品、Code 产品、API 的选项不是同一套，不能混用。
- Chat 入口优先考虑：回答质量、交互体验、工具可用性、上下文窗口。
- Code 入口优先考虑：仓库理解、工具调用、长程自治、验证能力、成本/额度。
- API 入口优先考虑：可编程参数、稳定 model ID、价格、延迟、上下文和工具。
- **不要把产品 UI 名当 API model ID**：ChatGPT 的 "Instant/Thinking/Pro" 不是 OpenAI API 里的模型名。

---

## 🟢 OpenAI

### ChatGPT（Web/App 入口）

官方已核：
- **GPT-5.5 Instant**：默认体验，适合日常问答、学习、技术写作、翻译；复杂任务自动切到 Thinking。
- **GPT-5.5 Thinking**：复杂任务、需要更强跟踪和推理；可在思考中追加指令。
- **GPT-5.5 Pro**：ChatGPT 最高能力选项，最难任务和长程 workflow。
- **Thinking time**：Plus/Business 有 `Standard`、`Extended`；Pro 额外有 `Light`、`Heavy`。

产品观察（legacy）：
- GPT-5.4 Thinking / GPT-5.3 Instant / GPT-5.2 Instant+Thinking（5.2 Thinking 在 5.5 发布后保留 90 天 legacy）

**推荐：**
- 日常问答/写作/翻译 → GPT-5.5 Instant
- 复杂分析/代码解释/研究草稿 → GPT-5.5 Thinking + Standard
- 长文研究/复杂方案/高风险事实 → GPT-5.5 Thinking + Extended，或 Pro + Heavy
- 需要 Canvas → GPT-5.5 Thinking（Instant 不支持 Canvas）

### Codex（CLI/Cloud Coding 入口）

官方已核 rate card 列出：`GPT-5.5`、`GPT-5.4`、`GPT-5.4-Mini`、`GPT-5.3-Codex`、`GPT-5.2`，每个都支持 `low/medium/high/xhigh` effort。

**推荐：**
- 代码搜索、读文件、简单解释、机械修改 → GPT-5.4-Mini + low/medium
- 普通 bugfix、小范围功能 → GPT-5.4 或 GPT-5.3-Codex + medium/high
- 多文件重构、CI 修复、架构迁移、生产风险 → GPT-5.5 + high/xhigh
- 大型长程 agentic 任务 → GPT-5.5 + xhigh；成本敏感时先 GPT-5.4 + high

### OpenAI API（开发者直接调用）

用 `reasoning.effort` 控制（none/low/medium/high/xhigh）。详见 [model-catalog.md](model-catalog.md) OpenAI 部分。

---

## 🔵 Anthropic

### Claude Desktop / Claude.ai（Chat 入口）

产品矩阵：
- **Opus 4.7**：Adaptive thinking
- **Opus 4.6**：Extended thinking（仍可用）
- **Sonnet 4.6**：Adaptive thinking
- **Sonnet 4.5**：Extended thinking（legacy）
- **Haiku 4.5**：Extended thinking
- **Opus 3**：none（已弃用）

**推荐：**
- 日常对话、写作、总结 → Sonnet 4.6 Adaptive，或 Haiku 4.5 Extended（低成本）
- 复杂文档、策略分析、长上下文综合 → Sonnet 4.6 Adaptive
- 最难推理、重要决策 → Opus 4.7 Adaptive
- **顶级中文长文创作 / 高文学性 → Opus 4.6 Extended**（4.6 写作 > 4.7）
- 不需要思考的快速问答 → 关闭 thinking 的可用模型，视 UI 选项

### Claude Code（IDE/CLI 入口）

官方已核：Claude 对 Opus 4.7 的 Claude Code 建议——默认 `xhigh`，`medium/low` 用于成本/延迟敏感或边界清晰任务，`high` 平衡智能与成本，`max` 用于真正困难任务。

产品配置（每个模型都支持 `low/medium/high/max`，Opus 4.7 多一个 `xhigh`）：
- Opus 4.7 / Opus 4.6 / Sonnet 4.6 / Haiku 4.5

**推荐：**
- 代码阅读、局部修改、成本敏感 → Sonnet 4.6 + medium，或 Haiku 4.5（轻任务）
- 多文件开发、复杂 bug、较长 agentic → Sonnet 4.6 + high/max
- 最高难度、歧义大、需要强判断 → Opus 4.7 + xhigh（agentic coding 默认）或 max

### Anthropic API

- Opus 4.7：`thinking: {type: "adaptive"}` + `output_config.effort: "low/medium/high/xhigh/max"`
- Opus 4.6 / Sonnet 4.6：adaptive thinking 同上（手动 extended thinking deprecated）
- Haiku 4.5：extended thinking

详见 [model-catalog.md](model-catalog.md) Anthropic 部分。

---

## 🟡 Google

### Gemini App（Web/App Chat 入口）

产品矩阵：
- Gemini 3.1 Pro
- Gemini 3.5 Flash
- Gemini 3.5 Flash-Lite

**推荐：**
- 日常对话、信息查询、写作 → Gemini 3.5 Flash
- 多模态、复杂推理、重要分析 → Gemini 3.1 Pro
- 快速、高吞吐、低成本简单任务 → Gemini 3.5 Flash-Lite

### Antigravity（Google 的 Coding 入口）

官方已核：核心 reasoning models 包含 Gemini 3.5 Flash 和 Gemini 3.1 Pro (low)。

产品配置：
- Gemini 3.5 Flash：`low/medium/high`
- Gemini 3.1 Pro：`low/high`

**推荐：**
- 默认 coding/agentic → Gemini 3.5 Flash + medium
- 简单改动、读代码、节省 quota → Gemini 3.5 Flash + low
- 多文件重构、长程 agentic → Gemini 3.5 Flash + high
- 复杂多模态/推理 / Flash 失败后升级 → Gemini 3.1 Pro + high

### Gemini API

用 `thinkingLevel`（Gemini 3+）或 `thinkingBudget`（Gemini 2.5）。详见 [model-catalog.md](model-catalog.md) Google 部分。

---

## 🔴 智谱 GLM

### bigmodel.cn 平台（API 主入口）

- 全部模型走 API 调用，无独立 Chat 产品
- 价格按模型档位（旗舰 → 主力 → Flash → 推理 → 通用）
- **GLM-4.7-Flash / GLM-Z1-Flash / GLM-4-Flash 完全免费**，适合高频中文查询

### GLM Coding Plan（订阅）

按月订阅：Lite ($10/月) / Pro ($30/月) / Max ($80/月)，配额随档位提升。

详见 [model-catalog.md](model-catalog.md) 智谱 GLM 部分。

---

## 🟣 MiniMax

### Token Plan（订阅入口）

按月订阅 + 共享积分，资源可用于 M 系列 / 语音 / 视频 / 图像所有模态。

### MiniMax Agent（Web App）

自主多 Agent 编排，底层用 M2.7。

### MiniMax 开放平台 API

支持 OpenAI 和 Anthropic 双格式 base URL：
- OpenAI 格式：`https://api.minimax.chat/v1/text/chatcompletion_v2`
- Anthropic 格式：通过 SDK 包装

可直接接入 Claude Code / Cursor / Cline 等工具。

---

## 🟤 DeepSeek

### DeepSeek Chat（Web 入口）

Web 端直接用 v4-flash（默认 thinking 模式）。

### DeepSeek API

**独家：** 单一 API endpoint 同时兼容 OpenAI 和 Anthropic 格式：
- OpenAI 格式：`https://api.deepseek.com`
- Anthropic 格式：`https://api.deepseek.com/anthropic`

可作为 Claude Code / Codex CLI / 各种编程工具的后端模型替换。

**模型选项：**
- `deepseek-v4-flash`：默认 thinking，可关闭
- `deepseek-v4-pro`：复杂推理旗舰

---

## 入口选择决策表

| 用户场景 | 推荐入口 | 理由 |
|---|---|---|
| 一次性问答、临时翻译 | ChatGPT Instant / Gemini App / Claude.ai | 最低成本上手 |
| 长程编程任务 / 仓库改造 | Codex / Claude Code / Antigravity | 工具调用、agentic、仓库理解 |
| 批量自动化 / 自建应用 | 直接调 API | 可编程、价格透明、稳定 model ID |
| 高频中文查询 / 个人省钱 | GLM 免费档（API） | 完全免费 |
| 替换编程工具后端省钱 | DeepSeek（Anthropic 兼容 API） | 价格 1/20，工具链不变 |
| 中文叙事/创作 | MiniMax（订阅或 API） | 中文质量好，成本极低 |

---

## 入口与模型映射的常见陷阱

1. **混淆产品名和 API ID**
   - ❌ ChatGPT 里的 "GPT-5.5 Thinking" 直接当 API 模型名
   - ✅ API 用 `gpt-5.5` + `reasoning.effort: "high"`

2. **Claude Code 不支持 Haiku 4.5 effort**
   - Haiku 4.5 在 Claude Code 里 thinking 选项是 `none`
   - 想要 thinking 必须用 Sonnet 4.6 起

3. **Gemini API thinkingBudget 在 Gemini 3 Pro 上效果不佳**
   - Gemini 3+ 优先 `thinkingLevel`，不要默认套用 2.5 的 `thinkingBudget`

4. **DeepSeek 默认开启 thinking**
   - 简单分类等任务必须显式 `"thinking": {"type": "disabled"}`，否则成本暴涨

5. **MiniMax 的 highspeed 版本效果同标准版**
   - 价格翻倍只换速度，不换质量，注意性价比

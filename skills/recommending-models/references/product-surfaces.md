# 产品入口模型矩阵

Last checked: 2026-05-26。产品 UI 变化快，可联网时优先查官方 Help/Docs/Blog；无官方公开资料时，标记为“产品观察”。

## 核心原则

- 先选入口，再选模型：Chat 产品、Code 产品、API 的选项不是同一套。
- Chat 入口优先考虑回答质量、交互体验、工具可用性、上下文窗口。
- Code 入口优先考虑仓库理解、工具调用、长程自治、验证能力、成本/额度。
- API 入口优先考虑可编程参数、稳定 model ID、价格、延迟、上下文和工具。

## OpenAI

### ChatGPT

官方已核：
- `GPT-5.5 Instant`：默认体验，适合日常问答、学习、技术写作、翻译、较快响应。Instant 会在复杂任务上自动切到 Thinking。
- `GPT-5.5 Thinking`：复杂任务、需要更强跟踪和推理时使用；可在思考中继续追加指令。
- `GPT-5.5 Pro`：ChatGPT 中最高能力选项，适合最难任务和长程 workflow；部分工具限制需以当前 UI 为准。
- Thinking time：选择 `GPT-5.5 Thinking` 或 Pro 时可设置。Plus/Business 有 `Standard`、`Extended`；Pro 额外有 `Light`、`Heavy`。

产品观察：
- `GPT-5.4`：Thinking。
- `GPT-5.3`：Instant。
- `GPT-5.2`：Instant、Thinking。OpenAI Help 说明 `GPT-5.2 Thinking` 在 GPT-5.5 Thinking 发布后作为 legacy 保留 90 天。

推荐：
- 日常问答/写作/翻译：`GPT-5.5 Instant`。
- 复杂分析/代码解释/研究草稿：`GPT-5.5 Thinking` + `Standard`。
- 长文研究/复杂方案/高风险事实：`GPT-5.5 Thinking` + `Extended`，或 Pro 用户用 `Pro` + `Heavy`。
- 需要 Canvas：优先 `GPT-5.5 Thinking`，因为官方说明 Instant 不支持 Canvas。

### Codex

官方已核：
- Codex rate card 当前列出 `GPT-5.5`、`GPT-5.4`、`GPT-5.4-Mini`、`GPT-5.3-Codex`、`GPT-5.2`。

产品配置：
- `GPT-5.5`：`low`、`medium`、`high`、`xhigh`。
- `GPT-5.4`：`low`、`medium`、`high`、`xhigh`。
- `GPT-5.4-Mini`：`low`、`medium`、`high`、`xhigh`。
- `GPT-5.3-Codex`：`low`、`medium`、`high`、`xhigh`。
- `GPT-5.2`：`low`、`medium`、`high`、`xhigh`。

推荐：
- 代码搜索、读文件、简单解释、机械修改：`GPT-5.4-Mini` + `low/medium`。
- 普通 bugfix、小范围功能：`GPT-5.4` 或 `GPT-5.3-Codex` + `medium/high`。
- 多文件重构、CI 修复、架构迁移、生产风险：`GPT-5.5` + `high/xhigh`。
- 大型长程 agentic 任务：`GPT-5.5` + `xhigh`；成本敏感时先 `GPT-5.4` + `high`。

## Anthropic

### Claude Desktop chat tab

产品矩阵：
- `Opus-4.7`：Adaptive thinking。
- `Opus-4.6`：Extended thinking。
- `Opus-3`：none。
- `Sonnet-4.6`：Adaptive thinking。
- `Sonnet-4.5`：Extended thinking。
- `Haiku-4.5`：Extended thinking。

推荐：
- 日常对话、写作、总结：`Sonnet-4.6` Adaptive，或 `Haiku-4.5` Extended 用于低成本/快速场景。
- 复杂文档、策略分析、长上下文综合：`Sonnet-4.6` Adaptive。
- 最难推理、重要决策、复杂多步任务：`Opus-4.7` Adaptive。
- 不需要思考的快速问答：`Opus-3` 或关闭 thinking 的可用模型，视 UI 可选项而定。

### Claude Code tab

官方已核：
- Claude 对 Opus 4.7 的 Claude Code 官方建议：默认 `xhigh`，`medium/low` 用于成本/延迟敏感或边界清晰任务，`high` 平衡智能与成本，`max` 用于真正困难且不敏感成本的任务。

产品配置：
- `Opus-4.7`：`low`、`medium`、`high`、`max`。
- `Opus-4.6`：`low`、`medium`、`high`、`max`。
- `Sonnet-4.6`：`low`、`medium`、`high`、`max`。
- `Haiku-4.5`：none。

推荐：
- 代码阅读、局部修改、成本敏感：`Sonnet-4.6` + `medium`，或 `Haiku-4.5` 用于很轻任务。
- 多文件开发、复杂 bug、较长 agentic workflow：`Sonnet-4.6` + `high/max`。
- 最高难度、歧义大、需要强判断的代码任务：`Opus-4.7` + `high/max`。如果 UI 有 `xhigh`，优先按官方建议用 `xhigh` 作为大多数 agentic coding 默认。

## Google

### Gemini App

产品矩阵：
- `Gemini-3.1-Pro`。
- `Gemini-3.5-Flash`。
- `Gemini-3.5-Flash-lite`。

推荐：
- 日常对话、信息查询、写作：`Gemini-3.5-Flash`。
- 多模态、复杂推理、重要分析：`Gemini-3.1-Pro`。
- 快速、高吞吐、低成本简单任务：`Gemini-3.5-Flash-lite`。

### Antigravity App

官方已核：
- Google 官方博客说明 `Gemini 3.5 Flash` 面向 agents/coding，已在 Antigravity、Gemini API、AI Studio、Android Studio 等入口可用，适合 long-horizon agentic tasks。
- Antigravity 官方 models 文档显示核心 reasoning models 包含 `Gemini 3.5 Flash` 和 `Gemini 3.1 Pro (low)`。

产品配置：
- `Gemini-3.5-Flash`：`low`、`medium`、`high`。
- `Gemini-3.1-Pro`：`low`、`high`。

推荐：
- 默认 coding/agentic 工作：`Gemini-3.5-Flash` + `medium`。
- 简单改动、读代码、节省 quota：`Gemini-3.5-Flash` + `low`。
- 多文件重构、长程 agentic、复杂迁移：`Gemini-3.5-Flash` + `high`。
- 复杂多模态/推理或 Flash 失败后升级：`Gemini-3.1-Pro` + `high`。

## 查询来源

- OpenAI Help: GPT-5.5 in ChatGPT
- OpenAI Help: Codex rate card
- OpenAI API docs: Models / all models
- Anthropic: Introducing Claude Sonnet 4.6
- Claude: Working with Claude Opus 4.7
- Claude: Best practices for using Claude Opus 4.7 with Claude Code
- Google AI: Gemini thinking
- Google AI: Gemini models
- Google Blog: Gemini 3.5
- Google Antigravity docs: Models

# 模型清单基线

Last checked: 2026-05-26。可联网时，以官方文档为准。

## 官方来源

- OpenAI models: https://developers.openai.com/api/docs/models
- OpenAI latest model guide: https://developers.openai.com/api/docs/guides/latest-model
- OpenAI ChatGPT Help: https://help.openai.com/en/articles/11909943-gpt
- OpenAI Codex rate card: https://help.openai.com/en/articles/20001106-codex-rate-card
- Anthropic models: https://platform.claude.com/docs/en/about-claude/models/overview
- Claude Opus 4.7 guide: https://claude.com/resources/tutorials/working-with-claude-opus-4-7
- Claude Code Opus 4.7 best practices: https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code
- Google Gemini models: https://ai.google.dev/gemini-api/docs/models
- Google Gemini thinking: https://ai.google.dev/gemini-api/docs/thinking
- Google Gemini 3.5: https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5/
- Google Antigravity models: https://antigravity.google/docs/models

## OpenAI

通用路由基线：
- `gpt-5.5`：复杂推理、coding、专业工作、tool-heavy agent 的旗舰默认选择。
- `gpt-5.4`：更便宜但仍然强的 coding/专业工作模型。
- `gpt-5.4-mini`：低成本、低延迟，适合边界清晰的 coding、computer use、subagent。
- `gpt-5.4-nano`：可用时用于简单高吞吐任务。
- Codex variants：在 Codex 中做长程代码编辑时，优先使用当前 Codex 模型族。
- Specialized models：image、realtime、audio、transcription、embeddings、moderation、deep research 按模态/任务选择，不按通用推理排名选择。

常见 reasoning levels：`none`、`low`、`medium`、`high`、`xhigh`。除非延迟或风险要求不同，`medium` 作为默认平衡档。

OpenAI API thinking/reasoning 规则：
- API 模型如 `gpt-5.5` 通过 `reasoning.effort` 控制推理强度，支持 `none`、`low`、`medium`、`high`、`xhigh`。
- `gpt-5.5 pro` 是更高算力版本，适合最难的专业问题；请求可能运行数分钟，适合 background mode。
- `chat-latest` 是 ChatGPT 中 Latest Instant model 的 API 指针，官方建议生产 API 仍优先用 `gpt-5.5`。因此不要把 ChatGPT UI 里的 Instant/Thinking/Pro 名称直接等同于 API model ID。
- 推荐口径：简单任务用 `none/low` 或 mini/nano；普通专业任务用 `gpt-5.5` + `medium`；复杂 coding/research 用 `high/xhigh`；极难且质量收益明确时升级到 `gpt-5.5 pro`。

## Anthropic

Claude 当前基线：
- `claude-opus-4-7`：最强通用模型，适合复杂推理、agentic coding、最难综合任务。
- `claude-sonnet-4-6`：速度/智能平衡，作为多数专业任务的 Claude 默认选择。
- `claude-haiku-4-5`：最快、成本更低，适合高吞吐、简单或低延迟任务。

thinking 基线：
- 需要显式复杂推理时，Sonnet/Haiku 使用 extended thinking。
- 可用时，Opus 的 adaptive thinking 用于复杂任务。

Anthropic thinking 规则：
- Claude Opus 4.7：只支持 adaptive thinking；使用 `thinking: {type: "adaptive"}`，手动 `thinking: {type: "enabled", budget_tokens: N}` 会被拒绝。
- Claude Opus 4.6 / Claude Sonnet 4.6：推荐 adaptive thinking；手动 extended thinking 仍可用但已 deprecated。
- adaptive thinking 通过 `output_config.effort` 控制深度：`low`、`medium`、`high`、`xhigh`、`max`。其中 `xhigh` 仅 Opus 4.7 支持；`max` 可用于 Opus 4.7、Opus 4.6、Sonnet 4.6 等支持模型。
- Opus 4.7 官方建议：coding/agentic 场景从 `xhigh` 起步，普通高智能任务至少 `high`；成本敏感降到 `medium`；`max` 只给真正 frontier 问题。
- Sonnet 4.6 官方建议：显式设置 effort，`medium` 作为多数应用默认，`low` 用于高吞吐/低延迟，`high/max` 用于复杂推理。
- `display: "summarized"` 返回 thinking 摘要；`display: "omitted"` 不展示 thinking 文本但仍保留加密 signature，降低首个文本 token 延迟，不降低 thinking 成本。Opus 4.7 默认 `omitted`。

## Google

当前 Gemini 基线。实现时使用 API model code；人类显示名放在括号里：
- `gemini-3.1-pro-preview` (`Gemini 3.1 Pro Preview`)：复杂推理、复杂多模态分析、autonomous coding、agentic workflow。
- `gemini-3.5-flash` (`Gemini 3.5 Flash`, stable)：持续 frontier performance，适合 agentic/coding/长任务，在速度和成本上更均衡。
- `gemini-3-flash-preview` (`Gemini 3 Flash Preview`)：需要 Gemini 3 级能力且可以接受 preview 状态时使用。
- `gemini-3.1-flash-lite` (`Gemini 3.1 Flash-Lite`, stable)：高吞吐、低延迟、成本敏感的 multimodal 任务。
- `Nano Banana 2 Preview`：高效率 image generation/editing。
- `Nano Banana Pro Preview`：最高质量 contextual image generation/editing。
- `Gemini 3.1 Flash Live Preview`：实时对话和 voice-first AI。
- `Gemini 3.1 Flash TTS Preview`：低延迟语音生成。
- `Gemini 2.5 Pro`：复杂推理和 coding；需要稳定 2.5 支持时仍可用。
- `Gemini 2.5 Flash`：低延迟/高吞吐，同时仍需要一定推理。
- `Gemini 2.5 Flash-Lite`：2.5 系列中最快、最省的 multimodal 选项。

thinking 基线：
- Gemini 3/3.1/3.5 模型在模型页标注支持 thinking controls 时使用对应参数。Pro/frontier agentic 任务偏 `high`，`gemini-3.5-flash` 偏 `medium/high`，Flash-Lite/简单抽取在支持时用 `minimal/low`。
- Gemini 2.5 使用 `thinkingBudget`；纯抽取/格式化任务在模型支持时关闭或降低 thinking。

Google Gemini thinking 规则：
- Gemini 3 及以后优先用 `thinkingLevel`，不要优先用 `thinkingBudget`。`thinkingBudget` 虽可能兼容，但在 Gemini 3 Pro 上可能效果不佳。
- Gemini 3 Pro 支持 `thinkingLevel: "low"` 和 `"high"`；默认是动态 `high`，不能完全关闭 thinking。
- Gemini 3 Flash 支持 `minimal`、`low`、`medium`、`high`；`minimal` 不是严格关闭，只是大概率不思考。
- Gemini 2.5 使用 `thinkingBudget`：`-1` 表示动态 thinking，`0` 表示关闭 thinking（2.5 Pro 不能关闭），正数表示 token 预算。
- Gemini 2.5 Pro：动态 thinking，预算范围 `128` 到 `32768`，不能关闭。
- Gemini 2.5 Flash：动态 thinking，预算范围 `0` 到 `24576`，`0` 可关闭。
- Gemini 2.5 Flash-Lite：默认不 thinking，预算范围 `512` 到 `24576`，`0` 可关闭，`-1` 可启用动态 thinking。

## 默认决策梯

1. 简单、低风险任务，先用便宜快模型。
2. 有歧义、多步推理或用户可见质量要求，用 balanced flagship/mid-tier + `medium` thinking。
3. 需要工具、代码编辑、当前研究或高风险事实，用 flagship + `high` thinking。
4. 长程 agentic coding/research，用最强任务专用模型 + `xhigh/max` reasoning。
5. 输出质量不够时，先提高 thinking；仍不够再升级模型。

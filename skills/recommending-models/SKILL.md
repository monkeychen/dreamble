---
name: recommending-models
description: 仅当用户显式要求推荐模型时使用，例如说“先推荐模型”“推荐模型”“选模型”“用什么模型”“which model”，或要求为任务选择 OpenAI/Anthropic/Google 模型、reasoning/thinking level。
---

# 模型推荐

把模型选择当成任务路由，而不是排行榜。只在用户显式要求模型选择时使用，避免普通问题被模型建议打断。

## 工作流

1. 判断请求类型：
   - `task`：chat、writing、coding、research、data extraction、product/strategy、multimodal、agent/tool workflow、safety-critical advice。
   - `complexity`：low、medium、high、frontier。
   - `risk`：low、medium、high。high risk 包括法律、医疗、金融、安全、生产部署、不可逆操作、公开事实声明。
   - `freshness`：static、likely-current、must-current。
   - `interaction`：answer only、use tools、edit code/files、browse、long-running agent。
2. 判断使用入口：ChatGPT/Claude Desktop/Gemini App 这类 chat 产品，Codex/Claude Code/Antigravity 这类 code 产品，还是 API/自建应用。不同入口的可选模型和配置项不同，不能混用。
3. 如果用户问“当前/最新”模型，或模型名称可能已经变化，先查官方文档再给具体模型名。API/底层模型见 `references/model-catalog.md`，产品层选项见 `references/product-surfaces.md`。
4. 推荐一个首选模型；有必要时给一个更便宜的降级选项和一个升级路径。
5. 模型选择和 reasoning/thinking level 分开推荐，并映射到对应产品入口的真实配置项。
6. 解释时围绕用户影响：质量、速度、成本、可靠性，以及何时切换。

## 输出格式

显式模型选择问题使用：

```text
推荐：<provider> <model>，思考等级 <level>
入口：<product surface，如 ChatGPT / Codex / Claude Desktop / Claude Code / Gemini App / Antigravity / API>
理由：<1-3 条，先讲对用户结果的影响>
降级：<更便宜/更快的选项>
升级：<什么时候换更强模型>
注意：<时效性/来源/风险提醒，如需要>
```

如果用户没有显式要求模型选择，不要使用这个 Skill。

## 路由规则

| 场景 | 默认选择 | reasoning/thinking |
|---|---|---|
| 改写、摘要、分类、结构化抽取 | small/mini/flash/haiku class | none/low |
| 普通问答、规划、写作、产品分析 | balanced flagship 或 mid-tier | medium |
| 代码解释、code review、小补丁 | strong coding/general model | medium/high |
| 多文件 coding、重构、agentic tool use | coding/agentic flagship | high/xhigh |
| 深度研究、当前事实、需要引用来源 | best model with browsing/search | high |
| 法律/医疗/金融/安全等高风险任务 | strongest available model plus sources and caveats | high/xhigh |
| 图像/视频/音频理解 | provider 的 native multimodal model | medium/high |
| 实时语音或低延迟 UX | realtime/flash/haiku class | low/medium |

## 产品入口优先级

- 用户明确说产品入口时，按该入口推荐，不要给用户用不到的 API 参数。
- 用户没说入口时，先按任务判断最可能入口：普通对话/写作/研究默认 chat 产品；改代码/修 CI/仓库操作默认 code 产品；构建自有产品默认 API。
- 同一个厂商的 chat 与 code 入口不同：例如 ChatGPT 有 Instant/Thinking/Pro，Codex 有 `low/medium/high/xhigh`；Claude Desktop 有 Adaptive/Extended thinking，Claude Code 有 effort level；Gemini App 可能只显示模型，Antigravity 才显示 coding effort。
- 如果产品入口的 UI 选项与 API 文档不同，优先说明“这是产品层选项”，不要把 UI 名称伪装成 API model ID。

## 厂商偏好

- OpenAI：优先用于 coding agent、tool-heavy workflow、computer use，以及已经在 Codex/OpenAI API 内的任务。
- Anthropic：优先用于长上下文综合、细腻写作、复杂推理，以及可使用 Claude 时的 agentic coding。
- Google：优先用于 multimodal、长上下文、Google 生态集成、视频/音频/图像任务，以及 Flash/Lite 高吞吐任务。
- 不要宣称某个厂商“全局最强”。按任务匹配，并说清楚取舍。

## 思考等级

- `none`：确定性转换、格式整理、简单抽取。
- `low`：快速回答、低风险草稿、简单工具使用。
- `medium`：大多数非平凡任务的默认档位，质量/成本/速度最均衡。
- `high`：复杂约束、代码变更、高风险事实、带工具的计划。
- `xhigh/max`：最难的异步 agent 任务、大型重构、深度评估，或错误代价很高的任务。

这些是跨厂商归一化标签，不是每个产品入口都原样支持。给出具体推荐时，必须映射到入口自己的配置项：ChatGPT 用 Instant/Thinking/Pro 和 thinking time，Codex 用 effort level，Anthropic API 用 `thinking.type` + `output_config.effort`，Google Gemini API 用 `thinkingLevel`/`thinkingBudget`。细节见 `references/model-catalog.md` 和 `references/product-surfaces.md`。

## 时效规则

推荐具体“当前模型”时，如果可以联网，引用官方文档。无法联网时，说明使用的是 catalog 基线，给出 `Last checked` 日期，并把模型名表述为“上次验证”。 

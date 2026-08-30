# Reasoning Effort 跨厂家映射

> **DATA_STAMP: 2026-08-29**｜型号与参数变化极快，使用前按 SKILL.md 第 5 步联网核验。
> 官方核验源：
> - OpenAI `platform.openai.com/docs/guides/reasoning`、`platform.openai.com/docs/pricing`
> - Anthropic `docs.claude.com/en/docs/build-with-claude/extended-thinking`、`.../effort`
> - Google `ai.google.dev/gemini-api/docs/thinking`、`cloud.google.com/vertex-ai/generative-ai/docs/thinking`
> - 阿里云百炼 `help.aliyun.com/zh/model-studio/`
> - DeepSeek `api-docs.deepseek.com`｜智谱 `docs.bigmodel.cn`｜月之暗面 `platform.moonshot.cn`

## 一、先看这张表：各家的"粒度天花板"

这是选型的第一个过滤器——**你的目标等级，这家根本表达不出来时，谈参数没有意义。**

| 厂家 | 可控粒度 | 能表达 L0(关) | 能表达 L4(极限) | 备注 |
|---|---|---|---|---|
| **OpenAI GPT-5.6** | 6 档（none/low/medium/high/xhigh/max） | ✅ `none` | ✅ `max` | 粒度最全 |
| **Anthropic Claude 4.6+** | 4 档（low/medium/high/max） | ✅ 省略 thinking | ⚠️ `max` 仅 Opus/Mythos/Fable 系 | Sonnet 到不了 max |
| **Google Gemini 3.x** | 4 档（minimal/low/medium/high） | ⚠️ **Pro 系不能关** | ❌ 上限 high | Flash 系可 minimal |
| **通义千问 Qwen 3.7/3.8** | 布尔 + 预算 + 档位（`enable_thinking` + `thinking_budget` / `reasoning_effort`） | ✅ `false` | ❌ | opt-in，默认关；3.8-max 的 `reasoning_effort` 与 `thinking_budget` 不可同传 |
| **DeepSeek V4** | `reasoning_effort`: low/high/max（**无 medium**） | ✅ `thinking.type=disabled` 可真关 | ❌ | 默认开且默认 high；L1 与 L2 无法区分 |
| **Kimi K3** | `reasoning_effort`: low/high/max（**默认 max**） | ❌ 始终推理 | ✅ `max` | 修掉了旧版"仅 on/off"的错误；但联网搜索当前不可用 |
| **智谱 GLM-5.3** | `reasoning_effort`: low/high/max（**关不掉，默认 max**） | ❌ 始终推理 | ✅ `max` | 修掉了旧版"仅 on/off"的错误；**不设参数就烧最贵档** |
| **腾讯混元 Hy3** | 交错式思考（interleaved thinking） | 待实测核验 | 待核验 | 256K 上下文；OpenAI 兼容端点上的思考参数未见文档 |
| **豆包 Seed 2.x** | 按 model ID 选 thinking 变体 | ✅ 选非 thinking 型号 | ❌ | 无运行时参数 |
| **MiniMax M3** | 2 档（adaptive/disabled） | ✅ `disabled` | ❌ | adaptive = 模型自决 |

**读法**：目标 L1–L3 时，豆包 / MiniMax 上**三个等级塌缩成同一个参数**。此时正确的做法不是硬选，而是换厂家，或接受"粒度损失"并在 prompt 层补偿（给更多示例、拆更细的步骤）。

**⚠️「默认档」陷阱**：Kimi K3 与 GLM-5.3 的 `reasoning_effort` **默认值都是 `max`**，且不显式传参就按最贵档计费。这两家上跑任何批量任务，**必须显式写 `reasoning_effort`**，否则账单会比预估贵数倍。

## 二、统一等级 → 各家参数

### L0 · 不推理

| 厂家 | 参数 |
|---|---|
| OpenAI | `reasoning={"effort": "none"}` |
| Anthropic | 省略 `thinking`，或 `thinking={"type": "disabled"}` |
| Gemini 3 Flash / Flash-Lite | `thinking_level="minimal"` |
| Gemini 3 Pro / 3.1 Pro | ❌ **不支持，思考关不掉**，换 Flash 或换厂家 |
| Qwen 3.7/3.8 | `extra_body={"enable_thinking": False}`（默认即关闭） |
| DeepSeek V4 | `extra_body={"thinking": {"type": "disabled"}}` — **可以真关**（2026-08-30 核验，旧版"关不掉"是错的） |
| Kimi K3 | ❌ 始终推理，最低只能 `reasoning_effort="low"` |
| Kimi K2.6 | `thinking={"type": "disabled"}`（K3 不适用） |
| GLM-5.3 | ❌ 始终推理，最低只能 `reasoning_effort="low"` |
| 豆包 | 选非 `-thinking` 后缀的型号 |
| MiniMax | `thinking={"type": "disabled"}` |

### L1 · 浅推理

| 厂家 | 参数 |
|---|---|
| OpenAI | `reasoning={"effort": "low"}` |
| Anthropic | `thinking={"type":"adaptive"}, output_config={"effort":"low"}` |
| Gemini | `thinking_level="low"` |
| Qwen 3.7 | `enable_thinking=true` + 小 `thinking_budget` |
| DeepSeek V4 | `reasoning_effort` 最低档 |
| Kimi K3 / GLM-5.3 | `reasoning_effort="low"` |
| 豆包 | 选 thinking 变体型号 |

### L2 · 标准推理

| 厂家 | 参数 |
|---|---|
| OpenAI | `reasoning={"effort": "medium"}`（默认） |
| Anthropic | `output_config={"effort":"medium"}` — **Sonnet 5 官方推荐默认档** |
| Gemini | `thinking_level="medium"` — Flash 系默认档 |
| Qwen 3.7 | `enable_thinking=true` + 中 `thinking_budget` |
| DeepSeek V4 | `reasoning_effort` 中档 |
| Kimi K3 / GLM-5.3 | `reasoning_effort="high"`（无 medium，属近似映射） |

### L3 · 深度推理

| 厂家 | 参数 |
|---|---|
| OpenAI | `reasoning={"effort": "high"}` |
| Anthropic | `output_config={"effort":"high"}`（默认值，等同不传） |
| Gemini | `thinking_level="high"` — Pro 系默认档 |
| Qwen 3.7 | `enable_thinking=true` + 大 `thinking_budget` |
| DeepSeek V4 | `reasoning_effort` 高档 |
| Kimi K3 / GLM-5.3 | `reasoning_effort="high"` 或 `"max"`，用代表性任务验证 |

### L4 · 极限推理

| 厂家 | 参数 |
|---|---|
| OpenAI | `reasoning={"effort": "xhigh"}`，官方建议与 `max` 对拍 |
| Anthropic | `output_config={"effort":"max"}` — **仅 Opus / Mythos / Fable 系**；Sonnet 5、Sonnet 4.6 传 max 会报错或降级为 high |
| Gemini | ❌ 到不了，上限 `high` |
| Kimi K3 / GLM-5.3 | `reasoning_effort="max"`（能力可达不代表适合每项 L4 任务） |
| 其他国产各家 | ❌ 均无对应档 |

## 三、各厂家语法详解

### OpenAI GPT-5.6

```python
resp = client.responses.create(
    model="gpt-5.6-terra",
    reasoning={
        "effort": "low",            # none/low/medium/high/xhigh/max，默认 medium
        "mode": "standard",         # standard | pro
        "context": "all_turns",     # auto | all_turns | current_turn
    },
    text={"verbosity": "low"},      # 独立于 effort 控输出长度
    previous_response_id=prev_id,   # 配合 context=all_turns
    input=messages,
)
```

- `effort` 六档，默认 `medium`。官方场景划分：`none` 延迟关键 / `low` 要工具但要速度 / `medium` 质量可靠性重要 / `high` 硬推理复杂调试 / `xhigh` 深度研究长跑 agentic / `max` 最难任务极限推理。
- `mode: "pro"` 是**参数不是模型**——model id 不变、单价不变（0% 溢价），但 token 消耗会涨（第三方估算：简单任务 1.5–2x、复杂编码 3–5x、架构分析可能 10x，**这是估算不是官方实测**）。与 effort 正交，可 `effort: low` + `mode: pro`。判断标准只有一条：**答错的代价有多高**。
- `context: "all_turns"` 保留跨轮推理，多轮任务别每轮重建。
- `text.verbosity` 独立于 reasoning 控制输出长度，要短答案直接设 `low`，别写"请简洁"——5.6 默认输出已比 5.5 短，旧的"请简洁"规则现在可能砍掉你要的内容。
- 长上下文悬崖：**超过 272K 后整次请求**输入 2x、输出 1.5x（不是只对超出部分）。

### Anthropic Claude 4.6+

```python
resp = client.messages.create(
    model="claude-opus-5",
    max_tokens=16000,
    thinking={"type": "adaptive"},        # 4.6+ 推荐
    output_config={"effort": "medium"},   # low/medium/high/max，默认 high
    messages=[...],
)
```

- **接口在 4.6/4.7 代变更过**：`thinking={"type":"enabled","budget_tokens":N}` 在 Opus 4.7+ 直接返回 HTTP 400；Opus 4.6 / Sonnet 4.6 上仍可用但已废弃。新代码一律用 `{"type":"adaptive"}`。
- `effort` 在 `output_config` 里，**不是顶层参数**。默认 `high`（不传即等价 high）。
- `max` 仅 Opus / Mythos / Fable 系；Sonnet 5、Sonnet 4.6 不支持（传了报错或降级 high）。
- adaptive thinking 自动启用 interleaved thinking（工具调用间推理），无需 beta header。
- 官方推荐 **Sonnet 5 默认 `medium`**——多数任务不需要全深度推理。
- Sonnet 5 有个隐藏成本：新 tokenizer 对相同文本约多产出 30% token，别只比标价。

### Google Gemini 3.x

```python
resp = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="medium")
    ),
)
```

- `thinking_level`: `minimal` | `low` | `medium` | `high`。**`medium` 是 Gemini 3.1 才加的。**
- **Pro 系（Gemini 3 Pro / 3.1 Pro）不支持 `minimal`，思考关不掉**；只支持 low/medium/high，默认 high。
- Flash 系默认 `medium`（3.5/3.6 Flash）；Flash-Lite 默认 `minimal`。
- **禁止同时传 `thinking_level` 和 `thinking_budget`** → 报错。`thinking_budget` 只用于 Gemini 2.5 及更早。
- Gemini 3.6 Flash 的输出价已明确**包含思考 token**。
- 转录/分类/抽取任务必须显式传 `minimal`，否则模型会静默把输出预算花在推理上（症状：空响应 + `finishReason=MAX_TOKENS`）。
- 长上下文悬崖：Gemini 3.1 Pro 超 200K 从 $2/$12 跳到 $4/$18。

### 通义千问 Qwen 3.7（阿里云百炼）

- `enable_thinking`: bool，混合思考模型 opt-in，**默认关闭**。
- `thinking_budget`: 配合 `enable_thinking=true` 控制预算。
- 走 OpenAI SDK 时必须塞进 `extra_body`：`extra_body={"enable_thinking": True, "thinking_budget": 8192}`。走 HTTP 直接放 body 顶层。
- `preserve_thinking`: 是否把历史 assistant 的 `reasoning_content` 拼回输入（qwen3.8-max 默认 true）。
- 长上下文悬崖：Qwen 3.7 Plus 输入超 256K 后价格明显上升。
- 国产里唯一"默认关思考 + 有预算粒度"的组合，可控性最好。

### DeepSeek V4

- V4 系列**默认开启思考**，通过 `reasoning_effort` 调整推理力度（档位数需核验）。
- V3.2 / V3.2-exp / V3.1 走 `enable_thinking`（仅阿里云/硅基流动/快手万擎直供版本支持）。
- ⚠️ **旧端点 `deepseek-chat` 与 `deepseek-reasoner` 已于 2026-07-24 退役**，未迁移到 `deepseek-v4-pro` / `deepseek-v4-flash` 的代码已失效。
- 价格地板：V4-Flash ¥1/¥2 每百万，缓存命中 ¥0.02——批量抽取类任务的成本已接近普通云计算文本处理。

### Kimi、GLM、豆包、MiniMax

- **Kimi K3：始终推理**，使用顶层 `reasoning_effort="low"|"high"|"max"`，默认 `max`；K2.6 的思考开关不适用于 K3。
- **GLM-5.3：始终推理**，使用 `reasoning_effort="low"|"high"|"max"`，默认 `max`。不同代际与渠道的参数不能混用。
- **豆包：按 model ID 区分** thinking / 非 thinking 变体，无运行时参数。走自动路由时不要自动切到 `*-thinking` 型号。
- **MiniMax M3**：`thinking={"type":"adaptive"|"disabled"}`，adaptive = 模型自己决定要不要想。

**共同坑**：不要把不同型号、代际或网关的参数混为一谈。走自动路由时需显式传入已核验的思考参数；多轮 agent 是否需要回传 `reasoning_content` 也取决于具体端点，必须按官方文档处理。

## 四、映射速查（横向）

| 统一等级 | OpenAI | Anthropic 4.6+ | Gemini 3.x | Qwen 3.7 / 3.8 | DeepSeek V4 | Kimi K3 | GLM | 豆包 | MiniMax |
|---|---|---|---|---|---|---|---|---|---|
| L0 | `none` | 省略 thinking | Flash `minimal`／Pro ❌ | `enable_thinking=False` | `thinking.type=disabled` ✅ | ❌ 到不了 | ❌ 到不了 | 非 thinking 型号 | `disabled` |
| L1 | `low` | `low` | `low` | `true`+小预算 / `low` | `low` | `low` | `low` | thinking 型号 | `adaptive` |
| L2 | `medium` | `medium` | `medium` | `true`+中预算 / `medium` | `high` ⚠️ | `high` ⚠️ | `high` ⚠️ | thinking 型号 | `adaptive` |
| L3 | `high` | `high` | `high` | `true`+大预算 / `xhigh` | `max` | `high`/`max` | `high`/`max` | thinking 型号 | `adaptive` |
| L4 | `xhigh`/`max` | `max`（仅 Opus 系） | ❌ | ❌ | ❌ | `max` | `max` | ❌ | ❌ |

⚠️ = 该等级在此厂家无法与相邻等级区分。
Kimi K3 的 `reasoning_effort` **默认 max**，不显式设置即最贵档；且官方标注联网搜索当前不可用。
Qwen 3.8-max 的 `reasoning_effort`（xhigh/medium/low）与 `thinking_budget` 不可同时传，会报错。
DeepSeek V4 无 medium 档，medium 请求会被映射为 high。

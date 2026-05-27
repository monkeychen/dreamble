# Thinking / Reasoning Level 跨厂归一化

Last checked: 2026-05-27。

## 归一化标签

skill 内部用以下 5+1 档作为跨厂统一抽象。给出推荐时**必须映射到目标入口/API 的真实配置项**，不要让用户填一个目标系统不存在的参数。

| 归一化档位 | 含义 |
|---|---|
| `none` | 不思考。确定性转换、格式整理、简单抽取。 |
| `low` | 轻量思考。快速回答、低风险草稿、简单工具使用。 |
| `medium` | **默认平衡档**。大多数非平凡任务，质量/成本/速度均衡。 |
| `high` | 显式深度思考。复杂约束、代码变更、高风险事实、带工具的计划。 |
| `xhigh` | 高强度思考。最难的 agentic 编程、大型重构、深度评估。 |
| `max` | 极限思考。错误代价极高的任务（仅部分模型支持）。 |

---

## 映射到各家真实配置

### 🟢 OpenAI

**API（gpt-5.5 / gpt-5.4 系列）：** `reasoning.effort`
```python
{
  "model": "gpt-5.5",
  "reasoning": {"effort": "high"}  # none / low / medium / high / xhigh
}
```

**ChatGPT UI：** 模型选项 + Thinking time
- `Instant` ≈ none/low（自动切换）
- `Thinking` + `Standard` ≈ medium
- `Thinking` + `Extended` ≈ high
- `Pro` + `Light` ≈ high
- `Pro` + `Heavy` ≈ xhigh/max

**Codex UI：** 模型 + effort 直接对应
- effort: `low / medium / high / xhigh`（无 none/max）

| 归一化 | API `effort` | ChatGPT | Codex |
|---|---|---|---|
| none | `"none"` | Instant | low |
| low | `"low"` | Instant | low |
| medium | `"medium"` | Thinking + Standard | medium |
| high | `"high"` | Thinking + Extended | high |
| xhigh | `"xhigh"` | Pro + Heavy | xhigh |
| max | `gpt-5.5-pro` | Pro + Heavy | xhigh + gpt-5.5 |

---

### 🔵 Anthropic

**Opus 4.7：** 只支持 adaptive thinking
```python
{
  "model": "claude-opus-4-7",
  "thinking": {"type": "adaptive"},
  "output_config": {"effort": "xhigh"}  # low / medium / high / xhigh / max
}
```
手动 `thinking: {type: "enabled", budget_tokens: N}` 会被拒绝。

**Opus 4.6 / Sonnet 4.6：** 推荐 adaptive thinking
```python
{
  "model": "claude-sonnet-4-6",
  "thinking": {"type": "adaptive"},
  "output_config": {"effort": "medium"}  # low / medium / high / max（不支持 xhigh）
}
```
手动 extended thinking 仍可用但已 deprecated。

**Haiku 4.5：** 仅支持 extended thinking（非 adaptive）
```python
{
  "thinking": {"type": "enabled", "budget_tokens": 5000}
}
```

**Claude.ai UI：** Adaptive / Extended（按模型显示）

**Claude Code UI：** effort 选项 `low / medium / high / max`（Opus 4.7 额外有 `xhigh`）

| 归一化 | Opus 4.7 effort | Sonnet 4.6 effort | Claude Code UI |
|---|---|---|---|
| none | low | low | low |
| low | low | low | low |
| medium | medium | medium | medium |
| high | high | high | high |
| xhigh | xhigh | high（不支持） | xhigh（仅 Opus 4.7） |
| max | max | max | max |

---

### 🟡 Google Gemini

**Gemini 3+：** `thinkingLevel`
```python
{
  "model": "gemini-3.1-pro-preview",
  "thinkingConfig": {"thinkingLevel": "high"}
}
```

支持的值因模型而异：
- Gemini 3 Pro：`low` / `high`（默认动态 high，**不能关闭**）
- Gemini 3 Flash：`minimal` / `low` / `medium` / `high`
- Gemini 3.5 Flash：`low` / `medium` / `high`

**Gemini 2.5：** `thinkingBudget`（token 预算）
- `-1`：动态 thinking
- `0`：关闭（2.5 Pro 不能关闭）
- 正数：明确 token 预算

| 模型 | budget 范围 | 备注 |
|---|---|---|
| 2.5 Pro | 128 - 32768 | 不能关闭 |
| 2.5 Flash | 0 - 24576 | 0 可关闭 |
| 2.5 Flash-Lite | 512 - 24576 | 默认不 thinking |

**Antigravity UI：** effort `low / medium / high`

| 归一化 | Gemini 3+ thinkingLevel | Gemini 2.5 thinkingBudget | Antigravity |
|---|---|---|---|
| none | minimal（3 Flash）/ low（3 Pro） | 0（Flash/Lite）/ 不可关闭（Pro） | low |
| low | low | ~1000-3000 | low |
| medium | medium（3 Flash） | ~5000-10000 | medium |
| high | high | ~15000-24000 | high |
| xhigh | high（最高就是 high） | 24576（Flash 上限） | high |
| max | high | 32768（Pro 上限） | high + Gemini 3.1 Pro |

⚠️ **Gemini 3 Pro 不要用 thinkingBudget**，要用 thinkingLevel；2.5 Pro 不能完全关闭 thinking。

---

### 🔴 智谱 GLM

GLM-4 主线模型本身不带显式 thinking 参数。**深度推理走专门的 GLM-Z1 系列**（推理模型独立分支）。

| 归一化 | 选模型策略 |
|---|---|
| none / low | GLM-4-Flash（免费）/ GLM-4.7-Flash（免费） |
| medium | GLM-4.7 / GLM-4.5-Air |
| high | GLM-5 / GLM-5-Turbo |
| xhigh / max | GLM-5.1 |
| 推理任务（任何档位） | GLM-Z1-Air（经济）/ GLM-Z1-AirX（最快）/ GLM-Z1-FlashX（低价） |

---

### 🟣 MiniMax

M 系列默认带 thinking。`highspeed` 版本是同模型不同速度，效果一致。

| 归一化 | 选模型策略 |
|---|---|
| none / low | （MiniMax 无极廉档，可用 M2-her 多轮对话）|
| medium | MiniMax-M2.5 / M2.1 |
| high | MiniMax-M2.7 |
| xhigh / max | MiniMax-M2.7 + 详细 prompt（无更高档）|

---

### 🟤 DeepSeek

```python
{
  "model": "deepseek-v4-flash",
  "thinking": {"type": "enabled"},     # 或 "disabled"
  "reasoning_effort": "high"            # low / medium / high
}
```

⚠️ **默认 thinking 开启**。分类等简单任务必须显式 `"thinking": {"type": "disabled"}`，否则输出 token 暴涨 5-10 倍。

| 归一化 | 选模型 + 配置 |
|---|---|
| none / low | v4-flash + thinking disabled |
| medium | v4-flash + thinking enabled + effort medium |
| high | v4-flash + thinking enabled + effort high |
| xhigh | v4-pro + effort high |
| max | v4-pro + effort high（无更高档） |

---

## 选择 thinking level 的决策梯

1. **任务难度低、模式确定** → none/low（省钱省时）
2. **多步骤但可拆解、风险中等** → medium（默认）
3. **跨文件/跨域 reasoning、有歧义、高风险** → high
4. **长程 agentic、复杂重构、深度评估** → xhigh
5. **错误代价极高、不计成本** → max（仅 Opus 4.7、Opus 4.6、Sonnet 4.6 支持）

## 输出质量不够时怎么办

**优先提高 thinking 而不是换模型：**
1. 先把当前模型 effort 升一档（medium → high）
2. 不够再升一档（high → xhigh）
3. 还不够才换更强模型

理由：thinking 升档边际成本远低于换旗舰模型。Sonnet 4.6 + max 通常已经超越 Opus 4.7 + medium。

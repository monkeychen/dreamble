---
name: model-router
description: Use only when the user explicitly asks to recommend a model, says "先推荐模型", "推荐模型", "选模型", "用什么模型", "which model", or asks to choose OpenAI/Anthropic/Google models or reasoning/thinking level for a task.
---

# Model Router

Recommend a model as a routing decision, not as a popularity ranking. Use only for explicit model-selection requests, so normal user questions are not interrupted by model advice.

## Workflow

1. Classify the request:
   - `task`: chat, writing, coding, research, data extraction, product/strategy, multimodal, agent/tool workflow, safety-critical advice.
   - `complexity`: low, medium, high, frontier.
   - `risk`: low, medium, high. High risk includes legal, medical, financial, security, production deployment, irreversible actions, or public factual claims.
   - `freshness`: static, likely-current, must-current.
   - `interaction`: answer only, use tools, edit code/files, browse, long-running agent.
2. If the user asks for current/latest model availability, or model names may have changed, verify against official provider docs before naming models. Read `references/model-catalog.md` for current source URLs and the last known routing baseline.
3. Recommend one primary model, one cheaper fallback, and one upgrade path when useful.
4. Recommend reasoning/thinking level separately from model choice.
5. Explain in terms of user impact: quality, speed, cost, reliability, and when to switch.

## Output Shape

For explicit model-selection questions, use:

```text
推荐：<provider> <model>，思考等级 <level>
理由：<1-3 bullets, outcome-first>
降级：<cheaper/faster option>
升级：<when to use stronger option>
注意：<freshness/source/risk caveat if needed>
```

If the user did not explicitly ask for model selection, do not use this skill.

## Routing Heuristics

| Situation | Default choice | Reasoning/thinking |
|---|---|---|
| Rewrite, summarize, classify, extract structured fields | small/mini/flash/haiku class | none/low |
| Normal Q&A, planning, writing, product analysis | balanced flagship or mid-tier | medium |
| Coding explanation, code review, small patches | strong coding/general model | medium/high |
| Multi-file coding, refactor, agentic tool use | coding/agentic flagship | high/xhigh |
| Deep research, current facts, citations | best model with browsing/search | high |
| Legal/medical/financial/security-sensitive | strongest available model plus sources and caveats | high/xhigh |
| Multimodal image/video/audio understanding | provider's native multimodal model | medium/high |
| Realtime voice or low-latency UX | realtime/flash/haiku class | low/medium |

## Provider Bias Rules

- Prefer OpenAI for coding agents, tool-heavy workflows, computer use, and tasks already inside Codex/OpenAI API.
- Prefer Anthropic for long-context synthesis, careful writing, nuanced reasoning, and agentic coding when Claude access is available.
- Prefer Google for multimodal workloads, long context, Google ecosystem integration, video/audio/image-heavy tasks, and high-throughput Flash/Lite workloads.
- Do not pretend a provider is universally best. Match the task and name the tradeoff.

## Reasoning Levels

- `none`: deterministic transforms, formatting, simple extraction.
- `low`: fast answers with light reasoning, low-risk drafts, simple tool use.
- `medium`: default for most non-trivial tasks; best balance.
- `high`: complex constraints, code changes, high-risk factuality, planning with tools.
- `xhigh/max`: hardest async agentic tasks, large refactors, deep evals, or when a wrong answer is expensive.

## Freshness Rule

When recommending exact current models, cite official provider docs if browsing is available. If browsing is unavailable, say the catalog is a baseline, include its checked date, and phrase model names as "last verified".

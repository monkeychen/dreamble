#!/usr/bin/env python3
"""大模型选型规则引擎。

只做确定性的能力/粒度映射，不含实时价格。价格与型号存活状态必须另行核验
官方定价页，见 references/vendor-profiles.md 顶部的 DATA_STAMP 与核验源清单。

用法:
    python3 route.py --vendors openai,anthropic,deepseek \
        --reasoning L2 --context medium --latency normal --stakes medium

    python3 route.py --vendors all --task "多文件重构一个 Kafka 消费者" --stakes high
"""

import argparse
import sys

# ---------------------------------------------------------------- 厂家能力表
# tier: light / mid / flagship 三档型号
# granularity: fine=4档以上 / budget=开关+预算 / sparse=少数离散档 / variant=按型号选
# max_level: 能表达的最高统一等级
# supports_off: 能否关闭思考
VENDORS = {
    "openai": {
        "label": "OpenAI",
        "tiers": {"light": "gpt-5.6-luna", "mid": "gpt-5.6-terra", "flagship": "gpt-5.6-sol"},
        "granularity": "fine",
        "max_level": "L4",
        "supports_off": True,
        "context": "1.05M",
        "domestic": False,
        "cost": {"light": "$", "mid": "$$", "flagship": "$$$"},
        "notes": "粒度最全（none/low/medium/high/xhigh/max）。>272K 整次请求输入 2x、输出 1.5x。",
    },
    "anthropic": {
        "label": "Anthropic",
        "tiers": {"light": "claude-haiku-4-5", "mid": "claude-sonnet-5", "flagship": "claude-opus-5"},
        "granularity": "fine",
        "max_level": "L4",
        "supports_off": True,
        "context": "1M (Haiku 200K)",
        "domestic": False,
        "cost": {"light": "$", "mid": "$$", "flagship": "$$$"},
        "notes": "max 档仅 Opus/Fable/Mythos 系，Sonnet 到不了 L4。Sonnet 5 新 tokenizer 约多产 30% token。",
    },
    "google": {
        "label": "Google",
        "tiers": {"light": "gemini-3.5-flash-lite", "mid": "gemini-3.6-flash", "flagship": "gemini-3.1-pro"},
        "granularity": "fine",
        "max_level": "L3",
        "supports_off": True,
        "context": "1M",
        "domestic": False,
        "cost": {"light": "$", "mid": "$$", "flagship": "$$"},
        "notes": "Pro 系不支持 minimal；L0 必须选择 Flash/Flash-Lite。3.1 Pro 超 200K 跳 $4/$18。",
    },
    "deepseek": {
        "label": "DeepSeek",
        "tiers": {"light": "deepseek-v4-flash", "mid": "deepseek-v4-pro", "flagship": "deepseek-v4-pro"},
        "granularity": "sparse",
        "max_level": "L3",
        "supports_off": True,
        "context": "1M",
        "domestic": True,
        "cost": {"light": "$", "mid": "$", "flagship": "$"},
        "notes": "价格地板。V4 默认开思考，但可显式关闭；只有 low/high/max 三档。旧端点 deepseek-chat/reasoner 已于 2026-07-24 退役。",
    },
    "qwen": {
        "label": "通义千问",
        "tiers": {"light": "qwen3.7-plus", "mid": "qwen3.7-max", "flagship": "qwen3.7-max"},
        "granularity": "budget",
        "max_level": "L3",
        "supports_off": True,
        "context": "1M / Plus 256K+",
        "domestic": True,
        "cost": {"light": "$", "mid": "$$", "flagship": "$$"},
        "notes": "国产里可控性最好：默认关思考 + thinking_budget 预算粒度。中文长文与知识库强。",
    },
    "kimi": {
        "label": "月之暗面",
        "tiers": {"light": "kimi-k3", "mid": "kimi-k3", "flagship": "kimi-k3"},
        "granularity": "sparse",
        "max_level": "L4",
        "supports_off": False,
        "context": "1M",
        "domestic": True,
        "cost": {"light": "$$", "mid": "$$", "flagship": "$$"},
        "notes": "长文本 + agent 化。K3 始终推理，通过 low/high/max 控制，默认 max。",
    },
    "zhipu": {
        "label": "智谱",
        "tiers": {"light": "glm-5.3", "mid": "glm-5.3", "flagship": "glm-5.3"},
        "granularity": "sparse",
        "max_level": "L4",
        "supports_off": False,
        "context": "1M",
        "domestic": True,
        "cost": {"light": "$$", "mid": "$$", "flagship": "$$"},
        "notes": "MIT 开源权重，可私有化部署。GLM-5.3 始终推理，通过 low/high/max 控制，默认 max。",
    },
    "doubao": {
        "label": "火山引擎",
        "tiers": {"light": "doubao-seed-2.1-turbo", "mid": "doubao-seed-2.1-pro", "flagship": "doubao-seed-2.1-pro"},
        "granularity": "variant",
        "max_level": "L3",
        "supports_off": True,
        "context": "见控制台",
        "domestic": True,
        "cost": {"light": "$", "mid": "$$", "flagship": "$$"},
        "notes": "低延迟，国内接入顺。思考按 model ID 分变体，无运行时参数，自动路由易误切。",
    },
    "grok": {
        "label": "xAI",
        "tiers": {"light": "grok-4.3", "mid": "grok-4.5", "flagship": "grok-4.5"},
        "granularity": "unknown",
        "max_level": "L3",
        "supports_off": True,
        "context": "1M / 4.5 为 500K",
        "domestic": False,
        "cost": {"light": "$", "mid": "$$", "flagship": "$$"},
        "notes": "输出单价低，长文生成成本占优。effort 参数档位需核验。超 200K 价格大致翻倍。",
    },
    "minimax": {
        "label": "MiniMax",
        "tiers": {"light": "minimax-m3", "mid": "minimax-m3", "flagship": "minimax-m3"},
        "granularity": "sparse",
        "max_level": "L3",
        "supports_off": True,
        "context": "见官方",
        "domestic": True,
        "cost": {"light": "$", "mid": "$", "flagship": "$"},
        "notes": "五折期内极便宜。thinking 仅 adaptive/disabled 两态。",
    },
}

# 统一等级 -> 各家参数
EFFORT_MAP = {
    "openai": {
        "L0": 'reasoning={"effort": "none"}',
        "L1": 'reasoning={"effort": "low"}',
        "L2": 'reasoning={"effort": "medium"}',
        "L3": 'reasoning={"effort": "high"}',
        "L4": 'reasoning={"effort": "xhigh"}   # 官方建议与 max 对拍',
    },
    "anthropic": {
        "L0": '省略 thinking 参数，或 thinking={"type": "disabled"}',
        "L1": 'thinking={"type": "adaptive"}, output_config={"effort": "low"}',
        "L2": 'thinking={"type": "adaptive"}, output_config={"effort": "medium"}',
        "L3": 'thinking={"type": "adaptive"}, output_config={"effort": "high"}',
        "L4": 'thinking={"type": "adaptive"}, output_config={"effort": "max"}   # 仅 Opus/Fable/Mythos 系',
    },
    "google": {
        "L0": 'thinking_level="minimal"   # 仅 Flash 系；Pro 系不支持，思考关不掉',
        "L1": 'thinking_level="low"',
        "L2": 'thinking_level="medium"',
        "L3": 'thinking_level="high"',
        "L4": "不支持：Gemini 上限 high",
    },
    "deepseek": {
        "L0": 'thinking={"type": "disabled"}',
        "L1": 'reasoning_effort="low"',
        "L2": 'reasoning_effort="high"   # 无 medium，粒度损失',
        "L3": 'reasoning_effort="max"',
        "L4": "不支持",
    },
    "qwen": {
        "L0": 'enable_thinking=False（默认即关闭）',
        "L1": 'enable_thinking=True, thinking_budget=2048',
        "L2": 'enable_thinking=True, thinking_budget=8192',
        "L3": 'enable_thinking=True, thinking_budget=16384',
        "L4": "不支持",
    },
    "kimi": {
        "L0": '不支持：K3 始终推理，最低为 reasoning_effort="low"',
        "L1": 'reasoning_effort="low"',
        "L2": 'reasoning_effort="high"   # 无 medium，粒度损失',
        "L3": 'reasoning_effort="high" 或 "max"   # 按验证结果选择',
        "L4": 'reasoning_effort="max"',
    },
    "zhipu": {
        "L0": '不支持：GLM-5.3 始终推理，最低为 reasoning_effort="low"',
        "L1": 'reasoning_effort="low"',
        "L2": 'reasoning_effort="high"   # 无 medium，粒度损失',
        "L3": 'reasoning_effort="high" 或 "max"   # 按验证结果选择',
        "L4": 'reasoning_effort="max"',
    },
    "doubao": {
        "L0": "选非 -thinking 后缀的型号（无运行时参数）",
        "L1": "选 thinking 变体型号   # ⚠️ 与 L2/L3 完全相同",
        "L2": "选 thinking 变体型号   # ⚠️ 与 L1/L3 完全相同",
        "L3": "选 thinking 变体型号   # ⚠️ 与 L1/L2 完全相同",
        "L4": "不支持",
    },
    "grok": {
        "L0": "待核验官方 effort 参数",
        "L1": "待核验官方 effort 参数",
        "L2": "待核验官方 effort 参数",
        "L3": "待核验官方 effort 参数",
        "L4": "不支持",
    },
    "minimax": {
        "L0": 'thinking={"type": "disabled"}',
        "L1": 'thinking={"type": "adaptive"}   # ⚠️ 与 L2/L3 完全相同',
        "L2": 'thinking={"type": "adaptive"}   # ⚠️ 与 L1/L3 完全相同',
        "L3": 'thinking={"type": "adaptive"}   # ⚠️ 与 L1/L2 完全相同',
        "L4": "不支持",
    },
}

LEVEL_ORDER = ["L0", "L1", "L2", "L3", "L4"]

# 从任务描述推断等级的关键词
LEVEL_KEYWORDS = [
    ("L4", ["证明", "推导", "研究级", "无人值守", "兜底", "最终复核", "最难", "竞赛"]),
    ("L3", ["调试", "排查", "根因", "架构", "选型", "权衡", "评审", "审查", "优化性能",
            "debug", "architect", "review", "tradeoff"]),
    ("L0", ["分类", "抽取", "提取", "打标", "路由", "转换", "清洗", "规整", "批量", "脱敏",
            "classify", "extract", "route", "parse"]),
    ("L1", ["摘要", "总结", "翻译", "改写", "润色", "通知", "描述", "单步",
            "summar", "translat", "rewrite"]),
]
DEFAULT_LEVEL = "L2"


def infer_level(task: str) -> str:
    if not task:
        return DEFAULT_LEVEL
    lowered = task.lower()
    hits = {}
    for level, words in LEVEL_KEYWORDS:
        for w in words:
            if w in lowered:
                hits[level] = hits.get(level, 0) + 1
    if not hits:
        return DEFAULT_LEVEL
    # 冲突时取较高等级，但 L0 命中优先于泛化的 L1
    return max(hits.keys(), key=lambda lv: (LEVEL_ORDER.index(lv), hits[lv]))


def pick_tier(level: str, context: str, stakes: str, latency: str):
    """按上下文规模 + 错误代价选档位。上下文优先于推理等级——长上下文靠 effort 补不回来。

    返回 (档位, 说明)。
    """
    if context in ("large", "huge"):
        tier, why = "mid", f"上下文 {context}，轻量档长上下文能力弱，至少中档"
    elif level in ("L0", "L1") and stakes == "low":
        tier, why = "light", f"任务定级 {level} 且错误代价低，轻量档即可"
    else:
        tier, why = "mid", f"任务定级 {level}，中档是落点"

    if stakes == "high":
        tier, why = "flagship", "错误代价高，上旗舰档"
    if level == "L4":
        tier, why = "flagship", "L4 只有旗舰档撑得住"

    if latency == "realtime" and tier == "flagship" and level != "L4":
        tier = "mid"
        why += "；但实时交互扛不住旗舰档延迟，已降回中档"
    return tier, why


def evaluate(vendor_key: str, level: str, context: str, stakes: str, latency: str,
             compliance: str, budget: str) -> dict:
    v = VENDORS[vendor_key]
    reasons, warnings = [], []

    if compliance == "domestic" and not v["domestic"]:
        return {"eligible": False, "reason": "非国产，不满足数据不出境约束"}

    if LEVEL_ORDER.index(level) > LEVEL_ORDER.index(v["max_level"]):
        return {"eligible": False,
                "reason": f"需要 {level}，但本家最高只到 {v['max_level']}"}

    if level == "L0" and not v["supports_off"]:
        return {"eligible": False,
                "reason": "L0 需要关闭思考，但本家无法表达；请选择可关闭思考的模型"}

    if v["granularity"] == "sparse" and level == "L2":
        warnings.append("本家缺少与 L2 一一对应的参数，已做近似映射，必须用代表性任务验证")
    if v["granularity"] == "variant" and level in ("L1", "L2", "L3"):
        warnings.append("本家按 model ID 分变体，无运行时 effort 参数，粒度无法调节")

    if context in ("large", "huge") and vendor_key == "openai":
        warnings.append("超过 272K 后整次请求输入 2x、输出 1.5x（非仅超出部分），先裁剪再谈 effort")
    if context in ("large", "huge") and vendor_key == "google":
        warnings.append("Gemini 3.1 Pro 超 200K 从 $2/$12 跳到 $4/$18")

    tier, tier_why = pick_tier(level, context, stakes, latency)
    if tier == "flagship" and v["tiers"]["flagship"] == v["tiers"]["mid"]:
        tier_why += "（本家没有比中档更高的型号，型号不变）"
    if budget == "low" and v["cost"][tier] in ("$$", "$$$"):
        if tier == "flagship":
            tier = "mid"
        elif tier == "mid":
            tier = "light"
        warnings.append("受预算约束已降档，质量需实测确认")

    reasons.append(f"任务定级 {level}，本家可表达至 {v['max_level']}")
    reasons.append(f"选档：{tier_why}")
    reasons.append(v["notes"])

    return {
        "eligible": True,
        "vendor": v["label"],
        "model": v["tiers"][tier],
        "tier": tier,
        "cost": v["cost"][tier],
        "effort": EFFORT_MAP[vendor_key][level],
        "reasons": reasons,
        "warnings": warnings,
        "granularity": v["granularity"],
        "context": v["context"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="大模型选型规则引擎")
    ap.add_argument("--vendors", default="all",
                    help="逗号分隔的厂家 key，或 all。可选: " + ", ".join(VENDORS))
    ap.add_argument("--task", default="", help="任务描述，用于自动推断推理等级")
    ap.add_argument("--reasoning", default=None,
                    choices=LEVEL_ORDER, help="统一推理等级，不传则从 --task 推断")
    ap.add_argument("--context", default="medium",
                    choices=["small", "medium", "large", "huge"], help="上下文规模")
    ap.add_argument("--latency", default="normal",
                    choices=["realtime", "normal", "batch"], help="时延要求")
    ap.add_argument("--stakes", default="medium",
                    choices=["low", "medium", "high"], help="错误代价")
    ap.add_argument("--compliance", default="any",
                    choices=["any", "domestic"], help="合规约束")
    ap.add_argument("--budget", default="any", choices=["any", "low"], help="预算约束")
    args = ap.parse_args()

    level = args.reasoning or infer_level(args.task)
    if args.reasoning:
        inferred = None
    else:
        inferred = level

    if args.vendors.strip() == "all":
        keys = list(VENDORS)
    else:
        keys = [k.strip() for k in args.vendors.split(",") if k.strip()]
        unknown = [k for k in keys if k not in VENDORS]
        if unknown:
            print(f"未知厂家: {', '.join(unknown)}")
            print(f"可选: {', '.join(VENDORS)}")
            return 2

    results, rejected = [], []
    for k in keys:
        r = evaluate(k, level, args.context, args.stakes, args.latency,
                     args.compliance, args.budget)
        (results if r["eligible"] else rejected).append((k, r))

    cost_rank = {"$": 0, "$$": 1, "$$$": 2}
    gran_rank = {"fine": 0, "budget": 1, "sparse": 2, "variant": 3, "unknown": 4}

    if args.stakes == "high":
        # 错误代价高时不能图便宜：能力上限优先，粒度精细度次之，最后才看成本
        results.sort(key=lambda kv: (
            -LEVEL_ORDER.index(VENDORS[kv[0]]["max_level"]),
            gran_rank[VENDORS[kv[0]]["granularity"]],
            cost_rank[kv[1]["cost"]],
        ))
        sort_note = "错误代价高：按 能力上限 → 粒度精细度 → 成本 排序"
    else:
        results.sort(key=lambda kv: cost_rank[kv[1]["cost"]])
        sort_note = "按成本从低到高排序"

    print("=" * 68)
    print("任务特征")
    print("=" * 68)
    if args.task:
        print(f"  任务描述 : {args.task}")
    print(f"  推理等级 : {level}" + ("（由任务描述推断）" if inferred else "（手动指定）"))
    print(f"  上下文   : {args.context}")
    print(f"  时延     : {args.latency}")
    print(f"  错误代价 : {args.stakes}")
    print(f"  合规     : {args.compliance}")
    print(f"  预算     : {args.budget}")

    if not results:
        print("\n所有候选厂家均不满足约束：")
        for k, r in rejected:
            print(f"  - {VENDORS[k]['label']}: {r['reason']}")
        return 1

    print("\n" + "=" * 68)
    print(f"候选排序 — {sort_note}")
    print("=" * 68)
    for i, (k, r) in enumerate(results, 1):
        mark = "★ 主推" if i == 1 else f" 备选{i-1}"
        print(f"\n[{mark}] {r['vendor']} · {r['model']}   (成本量级 {r['cost']})")
        print(f"  effort 参数 : {r['effort']}")
        print(f"  上下文      : {r['context']}")
        for reason in r["reasons"]:
            print(f"  · {reason}")
        for w in r["warnings"]:
            print(f"  ⚠ {w}")

    if rejected:
        print("\n" + "-" * 68)
        print("已排除：")
        for k, r in rejected:
            print(f"  - {VENDORS[k]['label']}: {r['reason']}")

    print("\n" + "=" * 68)
    print("下一步（必做）")
    print("=" * 68)
    print("1. 核验型号、参数、地区/工具能力与价格是否仍有效 —— 只认官方文档或控制台。")
    print("2. 以代表性样本验证质量、延迟和实际总成本，再决定是否升/降 effort。")
    print("3. 检查长上下文阈值；先裁剪或分层压缩，再提高 effort。")
    print("4. 批量场景验证 batch、缓存与 cascade 是否真的降低每个已解决任务的成本。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

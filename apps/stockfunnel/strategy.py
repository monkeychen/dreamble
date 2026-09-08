"""策略筛选层：相对强度 + 平台突破 + 分市场大盘过滤。

2026-09 实战化审计修复：
- 基准收益窗口对齐：bench_n 覆盖信号日次日起 n 个交易日（原窗口错位一天）
- T+1：次日开盘买入的票，最早 t+2 才能卖出（原回测允许当天买卖）
- MA10 清仓不再依赖「先触发过 MA5 减半」（原逻辑在 MA5 死叉 MA10 后失效）
- ST/退市剔除改用信号日当天的历史名称（原用最新名称，存在后视偏差）
- 新增实战约束：信号日成交额下限、次日高开过多放弃入场、一字板/停牌不可成交
- 新增成本模型：佣金 + 印花税 + 滑点，回测同时报告毛收益与净收益
- 大盘过滤按市场映射指数（主板→沪深300，创业板/科创板→创业板指）
- 新增组合模拟（槽位制仓位）、validate（年度稳定性 + 参数敏感性）、track（实盘对账）
"""

from __future__ import annotations

import bisect
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import data_layer

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
OUTPUT = BASE / "output"

STRATEGY_PARAMS = {
    # 第一步：相对强度
    "rs_lookback": 120,
    "rs_rank_pct": 25,       # 前25%算强
    "near_high_pct": 85,     # 股价在120日高点85%以上
    "near_high_lookback": 120,
    "above_ma20": True,
    "signal_start": 120,     # 最少需要多少根K线才出信号
    # 第二步：平台整理
    "consolidation_days": 20,
    "consolidation_range": 0.25,    # 平台振幅 ≤ 25%
    "consolidation_vol_shrink": 0.8,  # 量能萎缩到 80% 以下
    # 第三步：突破确认
    "breakout_vol_ratio": 1.5,
    "breakout_pct_min": 2.0,
    "breakout_pct_max": 8.0,
    "turn_min": 2.0,
    "turn_max": 15.0,
    "ma_trend": True,       # 均线多头排列
    # 流动性约束（实战）
    "min_amount": 2e8,      # 信号日成交额下限（元），保证买得进卖得出
    # 大盘过滤（按市场映射；未命中用 market_index 兜底）
    "market_filter": True,
    "market_index_map": {
        "sh": "sh.000300",    # 沪主板 → 沪深300
        "sz": "sh.000300",    # 深主板 → 沪深300
        "star": "sz.399006",  # 科创板 → 创业板指（成长风格代理）
        "cyb": "sz.399006",   # 创业板 → 创业板指
    },
    "market_index": "sz.399006",
    "market_ma_days": 20,
    # 入场可成交性（实战）
    "max_entry_gap_pct": 4.0,  # 次日开盘高开超过该幅度视为追不进，放弃
    # 成本模型（小数，单边）
    "commission": 0.00025,   # 佣金 万2.5
    "stamp_duty": 0.0005,    # 印花税 万5（卖出）
    "slippage": 0.001,       # 滑点 0.1%（单边）
    # 组合模拟
    "max_positions": 5,          # 最大并发持仓
    "initial_capital": 1_000_000,
    # 回测
    "forward_windows": (5, 10, 20),
    "hold_cap": 20,
    "min_stock_days": 120,
}


def roundtrip_cost(p: dict) -> float:
    """一次完整交易的总成本（小数）：双边佣金 + 卖出印花税 + 双边滑点。"""
    return 2 * p["commission"] + p["stamp_duty"] + 2 * p["slippage"]


def code_market(code: str) -> str:
    """按代码前缀判断所属市场段。"""
    for seg, prefixes in data_layer.MARKET_PREFIXES.items():
        if code.startswith(prefixes):
            return seg
    return "other"


@dataclass
class StockData:
    code: str
    dates: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    amount: np.ndarray        # 成交额（元）
    tradestatus: np.ndarray   # "1"=正常交易
    turn: np.ndarray
    pct: np.ndarray
    ma5: np.ndarray
    ma10: np.ndarray
    ma20: np.ndarray
    ma60: np.ndarray
    vol_ratio: np.ndarray  # 量比：当日量 / 前5日均量


def build_stocks(df: pd.DataFrame) -> dict[str, StockData]:
    """从日线 DataFrame 构建股票对象字典（预计算均线和量比）。"""
    stocks: dict[str, StockData] = {}

    for code, g in df.sort_values("date").groupby("code"):
        if len(g) < STRATEGY_PARAMS["min_stock_days"]:
            continue
        g = g.reset_index(drop=True)
        close = g["close"].to_numpy(dtype=float)
        vol = g["volume"].to_numpy(dtype=float)

        ma5 = pd.Series(close).rolling(5).mean().to_numpy()
        ma10 = pd.Series(close).rolling(10).mean().to_numpy()
        ma20 = pd.Series(close).rolling(20).mean().to_numpy()
        ma60 = pd.Series(close).rolling(60).mean().to_numpy()

        vol_avg5 = pd.Series(vol).rolling(5).mean().to_numpy()
        prev_vol = np.roll(vol_avg5, 1)
        prev_vol[0] = np.nan
        with np.errstate(divide="ignore", invalid="ignore"):
            vol_ratio = np.where(prev_vol > 0, vol / prev_vol, np.nan)

        amount = (pd.to_numeric(g["amount"], errors="coerce").to_numpy(dtype=float)
                  if "amount" in g.columns else np.full(len(g), np.nan))
        tradestatus = (g["tradestatus"].astype(str).to_numpy()
                       if "tradestatus" in g.columns else np.full(len(g), "1"))

        stocks[code] = StockData(
            code=code,
            dates=g["date"].to_numpy(),
            open=g["open"].to_numpy(dtype=float),
            high=g["high"].to_numpy(dtype=float),
            low=g["low"].to_numpy(dtype=float),
            close=close,
            volume=vol,
            amount=amount,
            tradestatus=tradestatus,
            turn=g["turn"].to_numpy(dtype=float),
            pct=g["pctChg"].to_numpy(dtype=float),
            ma5=ma5, ma10=ma10, ma20=ma20, ma60=ma60,
            vol_ratio=vol_ratio,
        )
    return stocks


# ---------- 时点名称（ST 剔除用） ----------

def build_name_lookup(names: pd.DataFrame) -> dict[str, tuple[list[str], list[str]]]:
    """构建 code → (快照日期升序列表, 名称列表)，用于按信号日取当时名称。"""
    lookup: dict[str, tuple[list[str], list[str]]] = {}
    names_sorted = names.sort_values(["code", "date"])
    for code, g in names_sorted.groupby("code"):
        lookup[code] = (g["date"].tolist(), g["name"].tolist())
    return lookup


def name_asof(lookup: dict, code: str, date: str) -> str:
    """取某只股票在 date 当天（或之前最近一次快照）的名称。"""
    entry = lookup.get(code)
    if not entry:
        return ""
    dates, names = entry
    i = bisect.bisect_right(dates, date) - 1
    if i < 0:
        i = 0  # 早于首个快照时用最早的名称兜底
    return names[i]


def is_excluded_name(name: str) -> bool:
    """剔除 ST / *ST / 退市整理股票。"""
    n = str(name).upper()
    return "ST" in n or "退" in n


# ---------- RS 计算 ----------

def compute_daily_rs_rank(stocks: dict[str, StockData], all_dates: np.ndarray,
                          lookback: int,
                          date_idx_map: dict | None = None) -> dict[str, np.ndarray]:
    """计算每日相对强度排名（百分比，0=最强，100=最弱）。"""
    if date_idx_map is None:
        date_idx_map = {d: i for i, d in enumerate(all_dates)}
    n_dates = len(all_dates)

    stock_rets: dict[str, np.ndarray] = {}
    for code, s in stocks.items():
        ret = np.full(n_dates, np.nan)
        if len(s.close) > lookback:
            local = s.close[lookback:] / s.close[:-lookback] - 1
            gidx = np.array([date_idx_map[d] for d in s.dates[lookback:]
                             if d in date_idx_map], dtype=int)
            # local 与 gidx 对齐：只保留在 all_dates 中的日期
            keep = np.array([d in date_idx_map for d in s.dates[lookback:]])
            ret[gidx] = local[keep]
        stock_rets[code] = ret

    rs_ranks: dict[str, np.ndarray] = {c: np.full(n_dates, np.nan) for c in stocks}
    for i in range(lookback, n_dates):
        rets = [(c, stock_rets[c][i]) for c in stocks
                if np.isfinite(stock_rets[c][i])]
        if len(rets) < 50:
            continue
        rets.sort(key=lambda x: x[1], reverse=True)
        total = len(rets)
        for rank, (code, _) in enumerate(rets):
            rs_ranks[code][i] = rank / total * 100

    return rs_ranks


def check_consolidation(s: StockData, t: int, p: dict) -> bool:
    """检查 t 日之前是否有平台整理形态。"""
    n = p["consolidation_days"]
    start = t - n
    end = t - 1
    if start < 0 or end <= start:
        return False

    seg_high = s.high[start:end + 1]
    seg_low = s.low[start:end + 1]
    seg_vol = s.volume[start:end + 1]
    seg_close = s.close[start:end + 1]

    hh, ll = np.nanmax(seg_high), np.nanmin(seg_low)
    if ll <= 0 or not np.isfinite(hh) or not np.isfinite(ll):
        return False

    # 1. 区间振幅
    rng = hh / ll - 1
    if rng > p["consolidation_range"]:
        return False

    # 2. 量能萎缩（后半段均量 ≤ 前半段 × shrink_ratio）
    half = n // 2
    if half > 0:
        front = np.nanmean(seg_vol[:half])
        back = np.nanmean(seg_vol[half:])
        if front > 0 and back / front > p["consolidation_vol_shrink"]:
            return False

    # 3. 收盘价在平台中上部（偏强整理）
    last_close = seg_close[-1]
    if np.isfinite(last_close) and last_close < (hh + ll) / 2:
        return False

    return True


# ---------- 筛选上下文（RS 只算一次，供参数扫描复用） ----------

@dataclass
class ScreenContext:
    market_str: str
    df: pd.DataFrame
    stocks: dict[str, StockData]
    all_dates: np.ndarray
    date_idx_map: dict
    next_map: dict
    gidx: dict[str, np.ndarray]            # code → 各K线在 all_dates 中的位置
    rs_ranks: dict[str, np.ndarray]
    market_flags: dict[str, dict[str, bool]]  # 指数代码 → {日期: 是否在MA上}
    name_lookup: dict
    bench: pd.DataFrame


def market_above_ma(idx_df: pd.DataFrame, code: str, ma_days: int) -> dict[str, bool]:
    """大盘均线判断：指数在MA之上返回True。"""
    g = idx_df[idx_df["code"] == code].sort_values("date")
    close = g["close"].to_numpy(dtype=float)
    ma = pd.Series(close).rolling(ma_days).mean().to_numpy()
    return {d: bool(np.isfinite(ma[i]) and close[i] > ma[i])
            for i, d in enumerate(g["date"])}


def bench_returns(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    """全市场等权基准的「前瞻」收益。

    修复：bench_{n} 在日期 d 的值 = 从 d 收盘到 d+n 收盘的 n 个交易日收益
    （覆盖 d+1 .. d+n），与策略「d 日出信号、d+1 开盘入场、d+n 收盘」的窗口对齐。
    原实现 rolling(w) 的窗口结束于 d 当天，整体错位一天。
    """
    df_sorted = df.sort_values(["code", "date"])
    df_sorted["prev_close"] = df_sorted.groupby("code")["close"].shift(1)
    df_sorted["listed_day"] = df_sorted.groupby("code").cumcount()

    tradable = df_sorted[
        (df_sorted["tradestatus"] == "1")
        & (df_sorted["listed_day"] >= p["min_stock_days"])
    ].copy()
    tradable["daily_ret"] = tradable["close"] / tradable["prev_close"] - 1

    daily = tradable.groupby("date")["daily_ret"].mean().reset_index()
    daily = daily.sort_values("date").reset_index(drop=True)

    result = {}
    for w in p["forward_windows"]:
        # rolling(w) 在行 j 覆盖 j-w+1..j；shift(-w) 后在行 i 覆盖 i+1..i+w
        fwd = (1 + daily["daily_ret"]).rolling(w).apply(np.prod, raw=True).shift(-w) - 1
        result[f"bench_{w}"] = fwd.to_numpy()
    out = pd.DataFrame(result, index=pd.Index(daily["date"], name="date"))
    return out


def prepare_context(market_str: str, p: dict) -> ScreenContext:
    """加载数据并计算所有与筛选参数无关的重活（RS 排名、基准、大盘开关）。"""
    markets = data_layer.resolve_markets(market_str)

    df = data_layer.load_daily(markets)
    idx_df = data_layer.load_indices()
    names = pd.read_parquet(DATA / "names.parquet")

    all_dates = np.sort(df["date"].unique())
    date_idx_map = {d: i for i, d in enumerate(all_dates)}
    next_map = {d: all_dates[i + 1] for i, d in enumerate(all_dates[:-1])}

    stocks = build_stocks(df)
    print(f"Loaded {len(stocks)} stocks, {len(all_dates)} trading days", flush=True)

    gidx: dict[str, np.ndarray] = {}
    for code, s in stocks.items():
        gidx[code] = np.array([date_idx_map[d] for d in s.dates], dtype=int)

    print("Computing relative strength ranks...", flush=True)
    rs_ranks = compute_daily_rs_rank(stocks, all_dates, p["rs_lookback"], date_idx_map)

    # 各市场段对应指数的大盘开关
    index_codes = set(p["market_index_map"].values()) | {p["market_index"]}
    market_flags = {c: market_above_ma(idx_df, c, p["market_ma_days"]) for c in index_codes}

    bench = bench_returns(df, p)

    return ScreenContext(
        market_str=market_str, df=df, stocks=stocks, all_dates=all_dates,
        date_idx_map=date_idx_map, next_map=next_map, gidx=gidx,
        rs_ranks=rs_ranks, market_flags=market_flags,
        name_lookup=build_name_lookup(names), bench=bench,
    )


def step1_rs_candidates(ctx: ScreenContext, p: dict) -> pd.DataFrame:
    """第一步初筛：RS 排名 + 靠近高点 + 站MA20，按信号日名称剔除 ST/退市。

    向量化实现；ST 判断用时点名称（原实现用最新名称，存在后视偏差）。
    """
    pct = p["rs_rank_pct"]
    near_pct = p["near_high_pct"] / 100
    lookback = p["near_high_lookback"]
    start = p["signal_start"]

    rows = []
    for code, s in ctx.stocks.items():
        rs = ctx.rs_ranks.get(code)
        if rs is None:
            continue
        rs_local = rs[ctx.gidx[code]]

        # 靠近阶段高点：滚动窗口 lookback+1 根（含当日），与原实现一致
        roll_hi = pd.Series(s.high).rolling(lookback + 1, min_periods=1).max().to_numpy()

        with np.errstate(invalid="ignore"):
            mask = (np.isfinite(rs_local) & (rs_local <= pct)
                    & np.isfinite(s.ma20) & (s.close >= s.ma20)
                    & np.isfinite(roll_hi) & (roll_hi > 0)
                    & (s.close >= roll_hi * near_pct))
        mask[:start] = False

        cand = np.nonzero(mask)[0]
        if len(cand) == 0:
            continue
        for i in cand:
            d = s.dates[i]
            # 时点名称剔除 ST / 退市整理
            if is_excluded_name(name_asof(ctx.name_lookup, code, d)):
                continue
            rows.append({"date": d, "code": code, "t": int(i)})

    return pd.DataFrame(rows)


def screen_from_ctx(ctx: ScreenContext, p: dict,
                    cache: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """在已算好 RS 的上下文上执行筛选（参数扫描时复用 ctx，不重算 RS）。"""
    print("Step 1: RS screening...", flush=True)
    c1 = step1_rs_candidates(ctx, p)
    print(f"  Step 1 candidates: {len(c1)}", flush=True)

    if p["market_filter"]:
        idx_map = p["market_index_map"]
        fallback_idx = p["market_index"]

    funnel_rows = []
    final_rows = []

    for date, day_cands in c1.groupby("date"):
        n1 = len(day_cands)
        n2 = 0
        n3 = 0
        for _, row in day_cands.iterrows():
            code = row["code"]
            s = ctx.stocks[code]
            t = int(row["t"])

            # 大盘过滤：按股票所属市场段取对应指数
            if p["market_filter"]:
                seg = code_market(code)
                idx_code = idx_map.get(seg, fallback_idx)
                if not ctx.market_flags.get(idx_code, {}).get(date, False):
                    continue

            # 均线多头
            if p["ma_trend"]:
                if not (np.isfinite(s.ma20[t]) and np.isfinite(s.ma60[t])
                        and s.ma5[t] > s.ma10[t] > s.ma20[t] > s.ma60[t]):
                    continue

            # 突破日量价
            if s.pct[t] < p["breakout_pct_min"] or s.pct[t] > p["breakout_pct_max"]:
                continue
            if not np.isfinite(s.vol_ratio[t]) or s.vol_ratio[t] < p["breakout_vol_ratio"]:
                continue
            if s.turn[t] < p["turn_min"] or s.turn[t] > p["turn_max"]:
                continue
            # 流动性下限（实战约束）
            amt = s.amount[t]
            if not np.isfinite(amt) or amt < p["min_amount"]:
                continue

            n2 += 1

            # 平台整理
            if not check_consolidation(s, t, p):
                continue

            n3 += 1
            rs_val = ctx.rs_ranks[code][ctx.date_idx_map[date]]
            final_rows.append({
                "date": date, "code": code, "t": t,
                "close": s.close[t],
                "rs_rank": round(float(rs_val), 2) if np.isfinite(rs_val) else None,
                "pct_chg": round(s.pct[t], 2),
                "vol_ratio": round(float(s.vol_ratio[t]), 2) if np.isfinite(s.vol_ratio[t]) else None,
                "turn": round(float(s.turn[t]), 2),
                "amount_yi": round(float(amt) / 1e8, 2) if np.isfinite(amt) else None,
                "name": name_asof(ctx.name_lookup, code, date),
            })

        funnel_rows.append({"date": date, "step1": n1, "step2": n2, "step3": n3})

    signals = pd.DataFrame(final_rows)
    funnel = pd.DataFrame(funnel_rows)
    print(f"Step 2 (breakout check): {sum(r['step2'] for r in funnel_rows)} total", flush=True)
    print(f"Step 3 (consolidation): {len(signals)} signals", flush=True)

    if cache:
        try:
            if not signals.empty:
                signals.to_parquet(DATA / "last_signals.parquet")
            else:
                (DATA / "last_signals.parquet").unlink(missing_ok=True)
            (DATA / "last_signals.json").write_text(json.dumps({
                "market": ctx.market_str,
                "n_signals": len(signals),
                "run_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }, ensure_ascii=False))
        except Exception as exc:
            print(f"  warning: failed to cache signals: {exc}", flush=True)

    return signals, funnel


def run_screen(market_str: str = "all",
               params: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """运行筛选策略，返回 (信号表, 漏斗计数)。"""
    p = dict(STRATEGY_PARAMS)
    if params:
        p.update(params)
    ctx = prepare_context(market_str, p)
    return screen_from_ctx(ctx, p, cache=True)


# ---------- 回测 ----------

def entry_feasible(s: StockData, t: int, ctx: ScreenContext,
                   p: dict) -> tuple[bool, str, float]:
    """次日开盘能否实际买入。返回 (可行, 原因, 高开幅度%)。

    拦截：数据尽头 / 次日停牌或缺失 / 高开过多（追不进）/ 一字板（无法成交）。
    """
    n = len(s.close)
    if t + 1 >= n:
        return False, "no_next", float("nan")
    d = s.dates[t]
    nd = ctx.next_map.get(d)
    if nd is None or s.dates[t + 1] != nd:
        return False, "halt_or_delist", float("nan")
    if str(s.tradestatus[t + 1]) != "1":
        return False, "halt_next", float("nan")
    o = s.open[t + 1]
    if not np.isfinite(o) or o <= 0:
        return False, "bad_open", float("nan")
    gap = (o / s.close[t] - 1) * 100
    if gap > p["max_entry_gap_pct"]:
        return False, "gap_up", round(float(gap), 2)
    # 一字板：开=高=低，集合竞价封死，无法成交
    if o == s.high[t + 1] == s.low[t + 1]:
        return False, "limit_lock", round(float(gap), 2)
    return True, "ok", round(float(gap), 2)


def simulate_user_rule(s: StockData, t: int, p: dict) -> dict | None:
    """模拟操作纪律：破5日线减半，破10日线清仓，最多持有 hold_cap 天。

    修复：
    - T+1：t+1 开盘买入，最早 t+2 才能卖出（原实现当天就能卖）
    - MA10 清仓独立触发：不再要求先触发过 MA5 减半
      （原逻辑在 MA5 死叉 MA10 后、股价直接跌破 MA10 时永远不清仓）
    """
    n = len(s.close)
    if t + 1 >= n:
        return None
    entry = s.open[t + 1]
    if not np.isfinite(entry) or entry <= 0:
        return None

    cap = min(t + p["hold_cap"], n - 1)
    first_sell = t + 2  # T+1 限制
    if cap < first_sell:
        return None  # 数据尽头，无法完成卖出

    half_ret = None
    half_idx = None
    gross = None
    reason = None
    exit_idx = None

    for d in range(first_sell, cap + 1):
        c = s.close[d]
        if not np.isfinite(c):
            continue
        if half_ret is None and np.isfinite(s.ma5[d]) and c < s.ma5[d]:
            half_ret = c / entry - 1
            half_idx = d
        if np.isfinite(s.ma10[d]) and c < s.ma10[d]:
            full_ret = c / entry - 1
            if half_ret is None or half_idx == d:
                # 直接跌破 MA10（或同日双破）：全部按 MA10 价出
                gross = full_ret
            else:
                gross = 0.5 * half_ret + 0.5 * full_ret
            reason = "ma10_break"
            exit_idx = d
            break

    if gross is None:
        final_ret = s.close[cap] / entry - 1
        if half_ret is not None:
            gross = 0.5 * half_ret + 0.5 * final_ret
        else:
            gross = final_ret
        reason = "hold_cap"
        exit_idx = cap

    net = gross - roundtrip_cost(p)
    return {
        "gross": float(gross),
        "net": float(net),
        "days": int(exit_idx - t),
        "reason": reason,
        "entry_date": str(s.dates[t + 1]),
        "exit_date": str(s.dates[exit_idx]),
        "entry_price": float(entry),
    }


def evaluate_signals(signals: pd.DataFrame, ctx: ScreenContext,
                     p: dict) -> pd.DataFrame:
    """对每个信号计算可成交性、前瞻收益、超额、纪律收益，返回明细表。"""
    if signals.empty:
        return pd.DataFrame()

    rows = []
    for _, r in signals.iterrows():
        s = ctx.stocks[r["code"]]
        t = int(r["t"])
        d = r["date"]

        row = r.to_dict()
        ok, skip, gap = entry_feasible(s, t, ctx, p)
        row["feasible"] = ok
        row["skip_reason"] = skip
        row["gap_pct"] = gap

        if ok:
            entry = s.open[t + 1]
            for w in p["forward_windows"]:
                if t + w < len(s.close):
                    f = s.close[t + w] / entry - 1
                    row[f"fwd_{w}"] = float(f)
                    b = ctx.bench[f"bench_{w}"].get(d, np.nan)
                    row[f"exc_{w}"] = float(f - b) if np.isfinite(b) else np.nan
                else:
                    row[f"fwd_{w}"] = np.nan
                    row[f"exc_{w}"] = np.nan
            rule = simulate_user_rule(s, t, p)
            if rule:
                row.update({f"rule_{k}": v for k, v in rule.items()})
        rows.append(row)

    return pd.DataFrame(rows)


def simulate_portfolio(ev: pd.DataFrame, p: dict) -> dict | None:
    """槽位制组合模拟：最多 max_positions 只并发，按成本法记账。

    - 信号按入场日排序，同日用 RS 排名优先（越强越先占槽）
    - 卖出资金次日才可用（离场日 < 入场日才释放槽位，偏保守）
    - 持仓按成本计价（不含浮动盈亏），总收益/年化为近似值
    """
    if ev.empty:
        return None
    trades = ev[ev["feasible"] & ev["rule_net"].notna()].copy()
    if trades.empty:
        return None
    trades = trades.sort_values(["rule_entry_date", "rs_rank"], na_position="last")

    cash = float(p["initial_capital"])
    open_pos: list[tuple[str, float, float]] = []  # (exit_date, stake, net_ret)
    n_trades = 0
    n_skipped = 0

    for _, tr in trades.iterrows():
        entry_date = tr["rule_entry_date"]
        keep = []
        for pos in open_pos:
            if pos[0] < entry_date:  # 严格早于入场日才释放资金和槽位
                cash += pos[1] * (1 + pos[2])
            else:
                keep.append(pos)
        open_pos = keep

        if len(open_pos) >= p["max_positions"]:
            n_skipped += 1
            continue
        book = cash + sum(pos[1] for pos in open_pos)
        stake = min(cash, book / p["max_positions"])
        if stake <= 1:
            n_skipped += 1
            continue
        cash -= stake
        open_pos.append((tr["rule_exit_date"], stake, float(tr["rule_net"])))
        n_trades += 1

    for pos in open_pos:
        cash += pos[1] * (1 + pos[2])

    total_ret = cash / p["initial_capital"] - 1
    first_in = str(trades["rule_entry_date"].min())
    last_out = str(trades["rule_exit_date"].max())
    years = max((pd.Timestamp(last_out) - pd.Timestamp(first_in)).days / 365.25, 1 / 12)
    cagr = (1 + total_ret) ** (1 / years) - 1 if total_ret > -1 else -1.0

    return {
        "total_return_pct": round(total_ret * 100, 2),
        "cagr_pct": round(cagr * 100, 2),
        "n_trades": n_trades,
        "n_skipped_slots_full": n_skipped,
        "final_capital": round(cash, 0),
        "period": f"{first_in} ~ {last_out}",
    }


def run_backtest(market_str: str = "all",
                 params: dict | None = None) -> dict:
    """运行回测（含实战约束与成本），返回统计结果字典。"""
    p = dict(STRATEGY_PARAMS)
    if params:
        p.update(params)

    ctx = prepare_context(market_str, p)
    signals, _ = screen_from_ctx(ctx, p, cache=True)

    if signals.empty:
        return {"error": "no signals found"}

    ev = evaluate_signals(signals, ctx, p)
    feas = ev[ev["feasible"]]

    result: dict = {
        "market": market_str,
        "n_signals": len(signals),
        "n_signal_days": int(signals["date"].nunique()),
        "n_feasible": len(feas),
        "cost_roundtrip_pct": round(roundtrip_cost(p) * 100, 3),
        "params": {k: p[k] for k in ("max_entry_gap_pct", "min_amount",
                                     "max_positions", "commission",
                                     "stamp_duty", "slippage")},
    }

    # 不可成交原因分布
    skips = ev[~ev["feasible"]]["skip_reason"].value_counts().to_dict()
    result["entry_skips"] = {str(k): int(v) for k, v in skips.items()}

    def _stat(arr):
        arr = np.asarray(arr, dtype=float)
        arr = arr[np.isfinite(arr)]
        if len(arr) == 0:
            return 0.0, 0.0, 0
        return float(arr.mean() * 100), float((arr > 0).mean() * 100), len(arr)

    rt = roundtrip_cost(p)
    for w in p["forward_windows"]:
        col = f"fwd_{w}"
        if col in feas.columns:
            gross = feas[col].to_numpy(dtype=float)
            mean_g, win_g, n = _stat(gross)
            net = gross - rt
            finite_net = net[np.isfinite(gross)]
            mean_n = float(np.nanmean(finite_net) * 100) if len(finite_net) else 0.0
            win_n = float(np.nanmean(finite_net > 0) * 100) if len(finite_net) else 0.0
            em, ew, _ = _stat(feas[f"exc_{w}"].to_numpy(dtype=float))
            exc_net = feas[f"exc_{w}"].to_numpy(dtype=float) - rt
            emn = float(np.nanmean(exc_net[np.isfinite(exc_net)]) * 100) \
                if np.isfinite(exc_net).any() else 0.0
            result[f"{w}d_n"] = n
            result[f"{w}d_mean"] = round(mean_g, 2)
            result[f"{w}d_net"] = round(mean_n, 2)
            result[f"{w}d_winrate"] = round(win_n, 1)  # 净收益口径
            result[f"{w}d_excess"] = round(em, 2)
            result[f"{w}d_excess_net"] = round(emn, 2)
            result[f"{w}d_excess_winrate"] = round(ew, 1)

    # 均线纪律（T+1 + 独立 MA10 清仓 + 成本）
    if "rule_net" in feas.columns:
        rnet = feas["rule_net"].to_numpy(dtype=float)
        rnet = rnet[np.isfinite(rnet)]
        rgross = feas["rule_gross"].to_numpy(dtype=float)
        rgross = rgross[np.isfinite(rgross)]
        rdays = feas.loc[np.isfinite(feas["rule_net"]), "rule_days"].to_numpy(dtype=float)
        result["rule_n"] = len(rnet)
        result["rule_mean"] = round(float(rgross.mean()) * 100, 2) if len(rgross) else 0.0
        result["rule_net_mean"] = round(float(rnet.mean()) * 100, 2) if len(rnet) else 0.0
        result["rule_winrate"] = round(float((rnet > 0).mean()) * 100, 1) if len(rnet) else 0.0
        result["rule_avg_days"] = round(float(rdays.mean()), 1) if len(rdays) else 0

        reasons = feas.loc[np.isfinite(feas["rule_net"]), "rule_reason"]
        if len(reasons):
            from collections import Counter
            rc = Counter(reasons)
            total = len(reasons)
            result["exit_reasons"] = {str(k): round(v / total * 100, 1)
                                      for k, v in rc.items()}

        pf = simulate_portfolio(ev, p)
        if pf:
            result["portfolio"] = pf

    return result


# ---------- 验证：年度稳定性 + 参数敏感性 ----------

DEFAULT_VARIANTS: list[tuple[str, dict]] = [
    ("rs_rank_pct=15", {"rs_rank_pct": 15}),
    ("rs_rank_pct=35", {"rs_rank_pct": 35}),
    ("near_high_pct=80", {"near_high_pct": 80}),
    ("near_high_pct=90", {"near_high_pct": 90}),
    ("consolidation_range=0.20", {"consolidation_range": 0.20}),
    ("consolidation_range=0.30", {"consolidation_range": 0.30}),
    ("breakout_vol_ratio=1.2", {"breakout_vol_ratio": 1.2}),
    ("breakout_vol_ratio=2.0", {"breakout_vol_ratio": 2.0}),
    ("breakout_pct_max=7", {"breakout_pct_max": 7.0}),
    ("breakout_pct_max=10", {"breakout_pct_max": 10.0}),
    ("min_amount=1亿", {"min_amount": 1e8}),
    ("min_amount=5亿", {"min_amount": 5e8}),
]


def _headline_metrics(ev: pd.DataFrame, p: dict) -> dict:
    """一组信号的核心指标：10日净超额 + 纪律净收益。"""
    feas = ev[ev["feasible"]] if not ev.empty else ev
    out = {"n_signals": len(ev), "n_feasible": len(feas)}
    if feas.empty:
        out.update({"exc_10_net": None, "rule_net": None, "rule_winrate": None})
        return out
    rt = roundtrip_cost(p)
    exc_col = "exc_10" if "exc_10" in feas.columns else \
        next((c for c in feas.columns if c.startswith("exc_")), None)
    if exc_col:
        e = feas[exc_col].to_numpy(dtype=float) - rt
        e = e[np.isfinite(e)]
        out["exc_10_net"] = round(float(e.mean()) * 100, 2) if len(e) else None
    if "rule_net" in feas.columns:
        r = feas["rule_net"].to_numpy(dtype=float)
        r = r[np.isfinite(r)]
        out["rule_net"] = round(float(r.mean()) * 100, 2) if len(r) else None
        out["rule_winrate"] = round(float((r > 0).mean()) * 100, 1) if len(r) else None
    return out


def run_validate(market_str: str = "all",
                 params: dict | None = None) -> dict:
    """验证：按年度看稳定性 + 关键参数敏感性扫描（RS 只算一次）。"""
    p = dict(STRATEGY_PARAMS)
    if params:
        p.update(params)

    ctx = prepare_context(market_str, p)
    signals, _ = screen_from_ctx(ctx, p)
    ev = evaluate_signals(signals, ctx, p)

    result: dict = {
        "market": market_str,
        "baseline": _headline_metrics(ev, p),
        "yearly": [],
        "sensitivity": [],
    }

    # 年度稳定性（只看可成交信号）
    if not ev.empty:
        ev = ev.copy()
        ev["year"] = ev["date"].astype(str).str[:4]
        feas = ev[ev["feasible"]]
        rt = roundtrip_cost(p)
        for year, g in feas.groupby("year"):
            exc = g["exc_10"].to_numpy(dtype=float) - rt if "exc_10" in g.columns else np.array([])
            exc = exc[np.isfinite(exc)] if len(exc) else exc
            rn = g["rule_net"].to_numpy(dtype=float) if "rule_net" in g.columns else np.array([])
            rn = rn[np.isfinite(rn)] if len(rn) else rn
            result["yearly"].append({
                "year": str(year),
                "n": len(g),
                "exc_10_net": round(float(exc.mean()) * 100, 2) if len(exc) else None,
                "rule_net": round(float(rn.mean()) * 100, 2) if len(rn) else None,
                "rule_winrate": round(float((rn > 0).mean()) * 100, 1) if len(rn) else None,
            })

    # 参数敏感性
    for label, variant in DEFAULT_VARIANTS:
        p2 = dict(p)
        p2.update(variant)
        sig2, _ = screen_from_ctx(ctx, p2)
        ev2 = evaluate_signals(sig2, ctx, p2)
        m = _headline_metrics(ev2, p2)
        m["variant"] = label
        result["sensitivity"].append(m)
        print(f"  variant {label}: n={m['n_signals']} "
              f"exc10_net={m['exc_10_net']} rule_net={m['rule_net']}", flush=True)

    return result


# ---------- 实盘对账 ----------

def update_trade_log(days: int = 10) -> pd.DataFrame:
    """把最近信号写入 output/trade_log.csv，并自动回填次日开盘/收盘。

    工作流：晚上 screen → track 登记明日计划 → 次日按开盘价买入后，
    在 CSV 的 fill_price 列手动填实际成交价 → 之后每天 track 自动更新数据列。
    """
    sig_file = DATA / "last_signals.parquet"
    if not sig_file.exists():
        raise FileNotFoundError("没有信号缓存，请先运行 stockfunnel screen")

    signals = pd.read_parquet(sig_file)
    if signals.empty:
        raise ValueError("信号缓存为空")

    daily = pd.read_parquet(DATA / "daily.parquet",
                            columns=["date", "code", "open", "close"])
    all_dates = np.sort(daily["date"].unique())
    next_map = {d: all_dates[i + 1] for i, d in enumerate(all_dates[:-1])}
    recent_cut = all_dates[-days - 1] if len(all_dates) > days else all_dates[0]
    signals = signals[signals["date"].astype(str) >= str(recent_cut)]

    px = daily.set_index(["code", "date"])

    records = []
    for _, r in signals.iterrows():
        d = str(r["date"])
        nd = next_map.get(d)
        rec = {
            "signal_date": d,
            "code": r["code"],
            "name": r.get("name", ""),
            "signal_close": round(float(r["close"]), 2),
            "next_date": str(nd) if nd else "",
            "next_open": None,
            "next_close": None,
            "gap_pct": None,
            "fill_price": None,   # 手动：实际成交价
            "remark": None,       # 手动：备注
        }
        if nd is not None:
            try:
                row = px.loc[(r["code"], nd)]
                rec["next_open"] = round(float(row["open"]), 2)
                rec["next_close"] = round(float(row["close"]), 2)
                rec["gap_pct"] = round((float(row["open"]) / float(r["close"]) - 1) * 100, 2)
            except KeyError:
                pass  # 次日数据还没更新出来
        records.append(rec)

    log = pd.DataFrame(records)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    log_file = OUTPUT / "trade_log.csv"

    if log_file.exists():
        old = pd.read_csv(log_file, dtype={"signal_date": str, "next_date": str})
        # 保留手动列（fill_price / remark）
        manual = old[["signal_date", "code", "fill_price", "remark"]].dropna(
            subset=["fill_price", "remark"], how="all")
        log = log.merge(manual, on=["signal_date", "code"], how="left",
                        suffixes=("", "_old"))
        for col in ("fill_price", "remark"):
            if f"{col}_old" in log.columns:
                log[col] = log[col].fillna(log[f"{col}_old"])
                log = log.drop(columns=[f"{col}_old"])

    log = log.sort_values(["signal_date", "code"]).drop_duplicates(
        subset=["signal_date", "code"], keep="last")
    log.to_csv(log_file, index=False)
    return log

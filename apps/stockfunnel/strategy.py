"""策略筛选层：相对强度 + 平台突破 + 大盘过滤。

基于最终版策略，支持按市场范围筛选。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import data_layer

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

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
    # 大盘过滤
    "market_filter": True,
    "market_index": "sz.399006",  # 创业板指（全市场时用这个判断）
    "market_ma_days": 20,
    # 回测
    "forward_windows": (5, 10, 20),
    "hold_cap": 20,
    "min_stock_days": 120,
}


@dataclass
class StockData:
    code: str
    dates: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
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
    cols = ["date", "open", "high", "low", "close", "volume", "turn", "pctChg"]

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

        stocks[code] = StockData(
            code=code,
            dates=g["date"].to_numpy(),
            open=g["open"].to_numpy(dtype=float),
            high=g["high"].to_numpy(dtype=float),
            low=g["low"].to_numpy(dtype=float),
            close=close,
            volume=vol,
            turn=g["turn"].to_numpy(dtype=float),
            pct=g["pctChg"].to_numpy(dtype=float),
            ma5=ma5, ma10=ma10, ma20=ma20, ma60=ma60,
            vol_ratio=vol_ratio,
        )
    return stocks


def compute_daily_rs_rank(stocks: dict[str, StockData], all_dates: np.ndarray,
                          lookback: int) -> dict[str, np.ndarray]:
    """计算每日相对强度排名（百分比，0=最强，100=最弱）。"""
    # 收集每只股票每天的累计收益
    date_idx = {d: i for i, d in enumerate(all_dates)}
    n_dates = len(all_dates)

    # 构建收益矩阵：stocks × dates
    # 用字典存每只的序列，每天排序一次
    stock_rets: dict[str, np.ndarray] = {}
    for code, s in stocks.items():
        ret = np.full(n_dates, np.nan)
        # 对齐日期
        s_date_idx = {d: i for i, d in enumerate(s.dates)}
        for i, d in enumerate(all_dates):
            si = s_date_idx.get(d)
            if si is None or si < lookback:
                continue
            ret[i] = s.close[si] / s.close[si - lookback] - 1
        stock_rets[code] = ret

    # 每天计算排名
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


def step1_rs_candidates(stocks: dict[str, StockData],
                        rs_ranks: dict[str, np.ndarray],
                        all_dates: np.ndarray,
                        p: dict) -> pd.DataFrame:
    """第一步初筛：RS 排名 + 靠近高点 + 站MA20。"""
    pct = p["rs_rank_pct"]
    near_pct = p["near_high_pct"] / 100
    lookback = p["near_high_lookback"]
    start = p["signal_start"]

    rows = []
    for code, s in stocks.items():
        rs = rs_ranks.get(code)
        if rs is None:
            continue
        # 对齐：s.dates → all_dates
        for i, d in enumerate(s.dates):
            if i < start:
                continue
            # 在 all_dates 中的位置
            di = np.searchsorted(all_dates, d)
            if di >= len(all_dates) or all_dates[di] != d:
                continue
            if not np.isfinite(rs[di]) or rs[di] > pct:
                continue
            if not np.isfinite(s.ma20[i]) or s.close[i] < s.ma20[i]:
                continue
            # 靠近阶段高点
            lo = max(0, i - lookback)
            hh = np.nanmax(s.high[lo:i+1])
            if hh > 0 and s.close[i] < hh * near_pct:
                continue
            # 剔除 ST 和停牌
            rows.append({"date": d, "code": code, "t": i})

    return pd.DataFrame(rows)


def market_above_ma(idx_df: pd.DataFrame, code: str, ma_days: int) -> dict[str, bool]:
    """大盘均线判断：指数在MA之上返回True。"""
    g = idx_df[idx_df["code"] == code].sort_values("date")
    close = g["close"].to_numpy(dtype=float)
    ma = pd.Series(close).rolling(ma_days).mean().to_numpy()
    return {d: bool(np.isfinite(ma[i]) and close[i] > ma[i])
            for i, d in enumerate(g["date"])}


def run_screen(market_str: str = "all",
               params: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """运行筛选策略，返回 (信号表, 漏斗计数)。

    Args:
        market_str: 市场范围，如 "all", "sh,sz", "star,cyb"
        params: 策略参数覆盖，None 用默认
    """
    markets = data_layer.resolve_markets(market_str)
    p = dict(STRATEGY_PARAMS)
    if params:
        p.update(params)

    df = data_layer.load_daily(markets)
    idx_df = data_layer.load_indices()
    names = pd.read_parquet(DATA / "names.parquet")
    name_latest = names.sort_values("date").groupby("code")["name"].last()

    all_dates = np.sort(df["date"].unique())
    stocks = build_stocks(df)
    print(f"Loaded {len(stocks)} stocks, {len(all_dates)} trading days", flush=True)

    # RS计算
    print("Computing relative strength ranks...", flush=True)
    rs_ranks = compute_daily_rs_rank(stocks, all_dates, p["rs_lookback"])

    # 第一步
    print("Step 1: RS screening...", flush=True)
    c1 = step1_rs_candidates(stocks, rs_ranks, all_dates, p)
    print(f"  Step 1 candidates: {len(c1)}", flush=True)

    # 大盘过滤
    market_ok = None
    if p["market_filter"]:
        market_ok = market_above_ma(idx_df, p["market_index"], p["market_ma_days"])

    funnel_rows = []
    final_rows = []

    for date, day_cands in c1.groupby("date"):
        n1 = len(day_cands)

        if market_ok is not None and not market_ok.get(date, False):
            funnel_rows.append({"date": date, "step1": n1, "step2": 0, "step3": 0})
            continue

        n2 = 0
        n3 = 0
        for _, row in day_cands.iterrows():
            s = stocks[row["code"]]
            t = int(row["t"])

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

            n2 += 1

            # 平台整理
            if not check_consolidation(s, t, p):
                continue

            n3 += 1
            di = np.searchsorted(all_dates, date)
            rs_val = rs_ranks[row["code"]][di]
            final_rows.append({
                "date": date, "code": row["code"], "t": t,
                "close": s.close[t],
                "rs_rank": round(float(rs_val), 2) if np.isfinite(rs_val) else None,
                "pct_chg": round(s.pct[t], 2),
                "vol_ratio": round(float(s.vol_ratio[t]), 2) if np.isfinite(s.vol_ratio[t]) else None,
                "turn": round(float(s.turn[t]), 2),
                "name": name_latest.get(row["code"], ""),
            })

        funnel_rows.append({"date": date, "step1": n1, "step2": n2, "step3": n3})

    signals = pd.DataFrame(final_rows)
    funnel = pd.DataFrame(funnel_rows)
    print(f"Step 2 (breakout check): {sum(r['step2'] for r in funnel_rows)} total", flush=True)
    print(f"Step 3 (consolidation): {len(signals)} signals", flush=True)
    return signals, funnel


# --- 回测 ---

def simulate_user_rule(s: StockData, t: int, p: dict) -> tuple[float, int, str] | None:
    """模拟用户操作纪律：破5日线减半，破10日线清仓，最多持有hold_cap天。"""
    n = len(s.close)
    if t + 1 >= n:
        return None
    entry = s.open[t + 1]
    if not np.isfinite(entry) or entry <= 0:
        return None

    cap = min(t + p["hold_cap"], n - 1)
    half_ret = None
    for d in range(t + 1, cap + 1):
        if np.isfinite(s.ma5[d]) and s.close[d] < s.ma5[d] and half_ret is None:
            half_ret = s.close[d] / entry - 1
        if half_ret is not None and np.isfinite(s.ma10[d]) and s.close[d] < s.ma10[d]:
            full_ret = s.close[d] / entry - 1
            return 0.5 * half_ret + 0.5 * full_ret, d - t, "ma10_break"

    if half_ret is not None:
        return 0.5 * half_ret + 0.5 * (s.close[cap] / entry - 1), cap - t, "hold_cap"
    return s.close[cap] / entry - 1, cap - t, "hold_cap"


def bench_returns(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    """计算全市场等权基准的远期收益。"""
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
        daily[f"bench_{w}"] = daily["daily_ret"].rolling(w).apply(
            lambda x: np.prod(1 + x) - 1, raw=True)
        result[f"bench_{w}"] = daily.set_index("date")[f"bench_{w}"]

    return pd.DataFrame(result)


def run_backtest(market_str: str = "all",
                 params: dict | None = None) -> dict:
    """运行回测，返回统计结果字典。"""
    markets = data_layer.resolve_markets(market_str)
    p = dict(STRATEGY_PARAMS)
    if params:
        p.update(params)

    df = data_layer.load_daily(markets)
    signals, _ = run_screen(market_str, p)

    if signals.empty:
        return {"error": "no signals found"}

    all_dates = np.sort(df["date"].unique())
    next_map = {d: all_dates[i + 1] for i, d in enumerate(all_dates[:-1])}
    stocks = build_stocks(df)
    bench = bench_returns(df, p)
    bench_idx = {d: i for i, d in enumerate(bench.index)}

    rets = {n: [] for n in p["forward_windows"]}
    excess = {n: [] for n in p["forward_windows"]}
    rule_rets = []
    rule_days = []
    rule_reasons = []

    for _, r in signals.iterrows():
        s = stocks[r["code"]]
        t = int(r["t"])
        d = r["date"]
        has_entry = t + 1 < len(s.close) and s.dates[t + 1] == next_map.get(d)
        if not has_entry:
            continue

        for n in p["forward_windows"]:
            if t + n < len(s.close):
                f = s.close[t + n] / s.open[t + 1] - 1
                rets[n].append(f)
                bi = bench_idx.get(d)
                if bi is not None:
                    excess[n].append(f - bench.iloc[bi][f"bench_{n}"])

        rule = simulate_user_rule(s, t, p)
        if rule:
            rule_rets.append(rule[0])
            rule_days.append(rule[1])
            rule_reasons.append(rule[2])

    def _stat(lst):
        if not lst:
            return 0.0, 0.0
        arr = np.array(lst)
        return float(np.nanmean(arr) * 100), float(np.nanmean(arr > 0) * 100)

    result = {
        "market": market_str,
        "n_signals": len(signals),
        "n_signal_days": signals["date"].nunique(),
    }

    for n in p["forward_windows"]:
        mean, win = _stat(rets[n])
        em, ew = _stat(excess[n])
        result[f"{n}d_mean"] = round(mean, 2)
        result[f"{n}d_winrate"] = round(win, 1)
        result[f"{n}d_excess"] = round(em, 2)
        result[f"{n}d_excess_winrate"] = round(ew, 1)

    rmean, rwin = _stat(rule_rets)
    result["rule_mean"] = round(rmean, 2)
    result["rule_winrate"] = round(rwin, 1)
    result["rule_avg_days"] = round(np.mean(rule_days), 1) if rule_days else 0

    # 离场原因分布
    if rule_reasons:
        from collections import Counter
        rc = Counter(rule_reasons)
        total = len(rule_reasons)
        result["exit_reasons"] = {k: round(v / total * 100, 1) for k, v in rc.items()}

    return result

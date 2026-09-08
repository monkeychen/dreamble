"""指数趋势择时：双指数 MA50 开关（主策略）。

2022-06 ~ 2026-09 回测验证（含每指数往返 0.1% 切换成本）：
- 组合（沪深300 + 创业板指 50/50，收盘>MA50 持有）：年化 +7.8%，最大回撤 -15.7%
- 对照沪深300买入持有：年化 +2.6%，最大回撤 -29.7%
- 特性：熊市/转折年大胜，单边牛市跑输（进场滞后）；本质是崩盘保险
- MA40-60 为参数平台，MA20 被切换磨损，MA80+ 衰减——不要微调

口径说明（与回测一致）：
- 信号 = 昨日收盘 vs 昨日MA50（shift(1)），今日持仓按此执行
- 工作流：晚上 daily_run 后看 output/daily_timing.txt，
  翻转日在次日开盘执行 ETF 买卖（1分钟）；无翻转不动作

每日信号日志：output/timing_log.csv（date, code, close, ma, signal, distance_pct）
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import data_layer

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
OUTPUT = BASE / "output"

TIMING_PARAMS = {
    "indices": {"sh.000300": "沪深300", "sz.399006": "创业板指"},
    "weights": {"sh.000300": 0.5, "sz.399006": 0.5},
    "ma_days": 50,
    "switch_cost": 0.001,      # ETF 往返成本（保守）
    "alert_distance_pct": 2.0,  # 偏离MA小于该值 → 临界预警
    "trading_days_per_year": 244,
}


def load_index_close(code: str) -> pd.Series:
    """读取指数收盘序列（DatetimeIndex，float）。"""
    idx = pd.read_parquet(DATA / "index_daily.parquet")
    g = idx[idx["code"] == code].sort_values("date").copy()
    if g.empty:
        raise ValueError(f"指数 {code} 无数据，先运行 stockfunnel update")
    g["close"] = pd.to_numeric(g["close"], errors="coerce")
    s = g.set_index(pd.to_datetime(g["date"]))["close"].dropna()
    return s


def _signal(close: pd.Series, ma_days: int) -> tuple[pd.Series, pd.Series]:
    """当日收盘 vs MA → 持仓信号（True=持有）。返回 (sig, ma)。"""
    ma = close.rolling(ma_days).mean()
    sig = (close > ma).astype(bool)
    return sig, ma


def _state_days(sig: pd.Series) -> tuple[int, pd.Timestamp | None]:
    """当前状态已持续天数 + 最近一次翻转日。"""
    flipped = sig != sig.shift(1, fill_value=sig.iloc[0])
    flip_pos = np.nonzero(flipped.to_numpy())[0]
    if len(flip_pos) <= 1:
        return len(sig), None
    last = flip_pos[-1]
    return len(sig) - last, sig.index[last]


def _timed_returns(close: pd.Series, ma_days: int,
                   cost: float) -> tuple[pd.Series, int]:
    """回测口径：昨日信号定今日仓位，翻转日扣一次往返成本。"""
    r = close.pct_change()
    sig, _ = _signal(close, ma_days)
    pos = sig.shift(1, fill_value=False).astype(bool)
    switches = pos.astype(int).diff().abs().fillna(0)
    strat = r.where(pos, 0.0) - switches * cost
    return strat.fillna(0.0), int(switches.sum())


def _max_dd(eq: pd.Series) -> float:
    return float(((eq - eq.cummax()) / eq.cummax()).min() * 100)


def timing_backtest(p: dict) -> dict:
    """全历史回测：单指数 + 加权组合。"""
    per_index = {}
    strats = {}
    for code, name in p["indices"].items():
        close = load_index_close(code)
        strat, n_sw = _timed_returns(close, p["ma_days"], p["switch_cost"])
        eq = (1 + strat).cumprod()
        bh = (1 + close.pct_change().fillna(0)).cumprod()
        years = len(close) / p["trading_days_per_year"]
        per_index[code] = {
            "name": name,
            "total_pct": round((eq.iloc[-1] - 1) * 100, 1),
            "cagr_pct": round((eq.iloc[-1] ** (1 / years) - 1) * 100, 1),
            "mdd_pct": round(_max_dd(eq), 1),
            "bh_total_pct": round((bh.iloc[-1] - 1) * 100, 1),
            "bh_mdd_pct": round(_max_dd(bh), 1),
            "switches": n_sw,
            "on_pct": round(strat.ne(0).mean() * 100, 0),
        }
        strats[code] = strat

    # 组合：按权重合并（日期并集，缺失按0仓）
    comb = sum(strats[c] * w for c, w in p["weights"].items())
    comb = comb.sort_index()
    eq_c = (1 + comb).cumprod()
    years = len(eq_c) / p["trading_days_per_year"]
    yearly = {}
    prev = 1.0
    for y in sorted(set(eq_c.index.year)):
        v = eq_c[eq_c.index.year == y].iloc[-1]
        yearly[str(y)] = round((v / prev - 1) * 100, 1)
        prev = v
    combo = {
        "total_pct": round((eq_c.iloc[-1] - 1) * 100, 1),
        "cagr_pct": round((eq_c.iloc[-1] ** (1 / years) - 1) * 100, 1),
        "mdd_pct": round(_max_dd(eq_c), 1),
        "yearly": yearly,
        "period": f"{eq_c.index[0].date()} ~ {eq_c.index[-1].date()}",
    }
    return {"per_index": per_index, "combo": combo, "params": {
        "ma_days": p["ma_days"], "switch_cost": p["switch_cost"]}}


def _update_log(rows: list[dict]) -> Path:
    """追加当日信号到 timing_log.csv（按 date+code 去重，新数据覆盖）。"""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    log_file = OUTPUT / "timing_log.csv"
    new = pd.DataFrame(rows)
    if log_file.exists():
        old = pd.read_csv(log_file, dtype={"signal": str})
        old["date"] = old["date"].astype(str)
        combined = pd.concat([old, new], ignore_index=True)
    else:
        combined = new
    combined = combined.drop_duplicates(subset=["date", "code"], keep="last")
    combined = combined.sort_values(["date", "code"])
    combined.to_csv(log_file, index=False)
    return log_file


def run_timing(backtest: bool = False, params: dict | None = None) -> dict:
    """输出当日信号面板；backtest=True 时附全历史回测。返回结构化结果。"""
    p = dict(TIMING_PARAMS)
    if params:
        p.update(params)
    ma_days = p["ma_days"]

    log_rows = []
    panels = []
    flips = []
    alerts = []
    positions = []

    for code, name in p["indices"].items():
        close = load_index_close(code)
        sig, ma = _signal(close, ma_days)

        last_date = close.index[-1]
        cur, prev = bool(sig.iloc[-1]), bool(sig.iloc[-2]) if len(sig) > 1 else cur
        dist = (close.iloc[-1] / ma.iloc[-1] - 1) * 100
        days_in, last_flip = _state_days(sig)

        panels.append({
            "code": code, "name": name, "date": str(last_date.date()),
            "close": round(float(close.iloc[-1]), 2),
            "ma": round(float(ma.iloc[-1]), 2),
            "distance_pct": round(float(dist), 2),
            "signal": "持有" if cur else "空仓",
            "days_in_state": int(days_in),
            "last_flip": str(last_flip.date()) if last_flip is not None else None,
            "flipped": cur != prev,
        })
        if cur != prev:
            flips.append((name, "空仓→持有" if cur else "持有→空仓"))
        if abs(dist) < p["alert_distance_pct"]:
            alerts.append((name, dist, cur))
        if cur:
            positions.append(f"{p['weights'][code]*100:.0f}% {name}ETF")

        log_rows.append({
            "date": str(last_date.date()), "code": code,
            "close": round(float(close.iloc[-1]), 2),
            "ma": round(float(ma.iloc[-1]), 2),
            "signal": "hold" if cur else "cash",
            "distance_pct": round(float(dist), 2),
        })

    log_file = _update_log(log_rows)

    # ---- 面板输出 ----
    data_date = panels[0]["date"]
    print(f"\n{'=' * 62}")
    print(f"  指数择时信号 · 数据截至 {data_date}（MA{ma_days}）")
    print(f"{'=' * 62}")
    for r in panels:
        mark = "持有✓" if r["signal"] == "持有" else "空仓✗"
        flip_tag = "  ← 今日翻转!" if r["flipped"] else ""
        print(f"  {r['name']:<6} 收{r['close']:>10.2f}  MA{ma_days} {r['ma']:>10.2f}"
              f"  偏离{r['distance_pct']:>+6.2f}%  [{mark}]"
              f"  第{r['days_in_state']}天{flip_tag}")
    print()

    if flips:
        print("  ⚡ 今日操作（次日开盘执行）:")
        for name, direction in flips:
            action = "买入" if direction == "空仓→持有" else "卖出"
            w = p["weights"][[k for k, v in p["indices"].items() if v == name][0]] * 100
            print(f"     {name}: {direction} → {action} {w:.0f}% 仓位对应ETF")
    else:
        print("  今日操作: 无翻转，无需动作")

    if alerts:
        print()
        for name, dist, cur in alerts:
            side = "上方" if dist > 0 else "下方"
            print(f"  ⚠ 临界预警: {name} 距MA{ma_days}仅 {abs(dist):.2f}%"
                  f"（{side}），近几日可能翻转，留意明日信号")

    print()
    print(f"  当前组合仓位: {' + '.join(positions) if positions else '100% 现金'}")
    print(f"  信号日志: {log_file}")
    print(f"{'=' * 62}")

    result = {"panels": panels, "flips": flips, "alerts": alerts,
              "log_file": str(log_file)}

    if backtest:
        bt = timing_backtest(p)
        result["backtest"] = bt
        print(f"\n{'=' * 62}")
        print(f"  全历史回测（MA{bt['params']['ma_days']}，"
              f"切换成本{bt['params']['switch_cost']*100:.1f}%/次）")
        print(f"{'=' * 62}")
        print(f"  {'指数':<8}{'择时总收益':>10}{'择时年化':>9}{'择时回撤':>9}"
              f"{'持有总收益':>10}{'持有回撤':>9}{'切换':>6}")
        for code, s in bt["per_index"].items():
            print(f"  {s['name']:<6}{s['total_pct']:>+9.1f}%{s['cagr_pct']:>+8.1f}%"
                  f"{s['mdd_pct']:>8.1f}%{s['bh_total_pct']:>+9.1f}%"
                  f"{s['bh_mdd_pct']:>8.1f}%{s['switches']:>6}")
        c = bt["combo"]
        print(f"\n  50/50组合（{c['period']}）:")
        print(f"    总收益 {c['total_pct']:+.1f}%   年化 {c['cagr_pct']:+.1f}%   "
              f"最大回撤 {c['mdd_pct']:.1f}%")
        yearly = "  ".join(f"{y} {v:+.1f}%" for y, v in c["yearly"].items())
        print(f"    年度: {yearly}")
        print(f"{'=' * 62}")

    return result

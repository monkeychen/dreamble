"""单只股票行情查询。"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import data_layer

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"


def resolve_code(query: str) -> str:
    """把用户输入解析成 baostock 格式代码。"""
    q = query.strip().lower()
    if q.startswith(("sh.", "sz.", "bj.")):
        return q
    if q.startswith("6"):
        return f"sh.{q}"
    if q.startswith(("0", "3")):
        return f"sz.{q}"
    return f"sh.{q}"


def calc_rs_rank(df_all: pd.DataFrame, code: str, lookback: int = 120) -> float | None:
    """计算相对强度排名百分比（越小越强）。"""
    df_sorted = df_all.sort_values(["code", "date"])
    df_sorted["ret"] = df_sorted.groupby("code")["close"].pct_change(
        lookback, fill_method=None)
    last_day = df_sorted["date"].max()
    last_slice = df_sorted[df_sorted["date"] == last_day].dropna(subset=["ret"])
    if code not in last_slice["code"].values:
        return None
    rank = (last_slice["ret"] > last_slice.loc[last_slice["code"] == code, "ret"].iloc[0]).sum()
    return round(rank / len(last_slice) * 100, 1)


def query_stock(code_query: str, days: int = 20,
                ma_list: list[int] | None = None,
                vol_ratio_days: int = 5,
                rs_lookback: int = 0,
                market_str: str = "all") -> str:
    """查询单只股票行情，返回格式化字符串。"""
    if ma_list is None:
        ma_list = [5, 10, 20, 60]

    code = resolve_code(code_query)
    markets = data_layer.resolve_markets(market_str)
    df = data_layer.load_daily(markets)

    stock_df = df[df["code"] == code].sort_values("date").reset_index(drop=True)
    if stock_df.empty:
        # 试试全市场
        df_all = data_layer.load_daily(None)
        stock_df = df_all[df_all["code"] == code].sort_values("date").reset_index(drop=True)
        if stock_df.empty:
            return f"未找到 {code} 的数据\n数据范围：{df['date'].min()} ~ {df['date'].max()}\n共 {df['code'].nunique()} 只股票"

    # 名称
    names = pd.read_parquet(DATA / "names.parquet")
    name_latest = names.sort_values("date").groupby("code")["name"].last()
    name = name_latest.get(code, "未知")

    # 均线
    for m in ma_list:
        stock_df[f"ma{m}"] = stock_df["close"].rolling(m).mean()

    # 量比
    vol_avg = stock_df["volume"].rolling(vol_ratio_days).mean()
    stock_df["vol_ratio"] = stock_df["volume"] / vol_avg.shift(1)

    recent = stock_df.tail(days).copy()

    # RS排名
    rs_str = ""
    if rs_lookback > 0:
        df_all = data_layer.load_daily(None)
        rs = calc_rs_rank(df_all, code, rs_lookback)
        if rs is not None:
            rs_str = f"  RS{rs_lookback}排名: {rs}%"

    lines = []
    lines.append(f"\n{'=' * 90}")
    lines.append(f"  {code}  {name}  最近 {days} 个交易日{rs_str}")
    lines.append(f"{'=' * 90}")

    # 表头
    header = f"{'日期':<12} {'开盘':>8} {'最高':>8} {'最低':>8} {'收盘':>8} " \
             f"{'涨跌幅':>7} {'换手率':>6} {'量比':>5}"
    for m in ma_list:
        header += f" {'MA' + str(m):>7}"
    lines.append(header)
    lines.append("-" * 90)

    # 数据行
    for _, r in recent.iterrows():
        pct_str = f"{r['pctChg']:+.2f}%"
        turn_str = f"{r['turn']:.1f}%"
        vr_str = f"{r['vol_ratio']:.1f}" if pd.notna(r["vol_ratio"]) else "  - "

        # 终端颜色
        red = "\033[91m"
        green = "\033[92m"
        reset = "\033[0m"
        if not sys.stdout.isatty():
            red = green = reset = ""

        if r["pctChg"] > 0:
            pct_c = f"{red}{pct_str}{reset}"
            close_c = f"{red}{r['close']:.2f}{reset}"
        elif r["pctChg"] < 0:
            pct_c = f"{green}{pct_str}{reset}"
            close_c = f"{green}{r['close']:.2f}{reset}"
        else:
            pct_c = pct_str
            close_c = f"{r['close']:.2f}"

        line = (f"{r['date']:<12} {r['open']:>8.2f} {r['high']:>8.2f} {r['low']:>8.2f} "
                f"{close_c:>14} {pct_c:>13} {turn_str:>6} {vr_str:>5}")

        for m in ma_list:
            ma_val = r[f"ma{m}"]
            if pd.notna(ma_val):
                ma_s = f"{ma_val:>7.2f}"
                if r["close"] > ma_val:
                    ma_s = f"{red}{ma_val:>7.2f}{reset}"
                else:
                    ma_s = f"{green}{ma_val:>7.2f}{reset}"
            else:
                ma_s = "      -"
            line += f" {ma_s}"
        lines.append(line)

    lines.append(f"{'=' * 90}")

    # 关键指标
    latest = stock_df.iloc[-1]
    lines.append(f"\n  最新数据（{latest['date']}）")
    lines.append(f"    收盘价: {latest['close']:.2f}  ({latest['pctChg']:+.2f}%)")
    lines.append(f"    成交量: {latest['volume']/10000:,.0f} 手  换手率: {latest['turn']:.2f}%")
    if pd.notna(latest.get("vol_ratio")):
        lines.append(f"    量比({vol_ratio_days}日): {latest['vol_ratio']:.2f}")

    ma_status = []
    for m in sorted(ma_list):
        ma_val = latest.get(f"ma{m}")
        if pd.notna(ma_val):
            above = latest["close"] > ma_val
            ma_status.append(f"MA{m}:{'↑' if above else '↓'}")
    lines.append(f"    均线状态: {'  '.join(ma_status)}")

    for n, label in [(5, "5日"), (20, "20日"), (60, "60日")]:
        if len(stock_df) >= n:
            ret = latest["close"] / stock_df.iloc[-n]["close"] - 1
            lines.append(f"    近{label}涨跌: {ret*100:+.2f}%")

    lines.append(f"\n  近{days}日区间")
    lines.append(f"    最高: {recent['high'].max():.2f}  "
                 f"({recent.loc[recent['high'].idxmax(), 'date']})")
    lines.append(f"    最低: {recent['low'].min():.2f}  "
                 f"({recent.loc[recent['low'].idxmin(), 'date']})")
    lines.append(f"    振幅: {(recent['high'].max()/recent['low'].min()-1)*100:.1f}%")
    lines.append("")

    return "\n".join(lines)

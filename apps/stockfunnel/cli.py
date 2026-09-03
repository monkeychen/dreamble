"""股票漏斗 · 统一入口

用法：
  stockfunnel update [-m 市场]              增量更新数据
  stockfunnel rebuild [-m 市场]             全量重建数据
  stockfunnel screen [-m 市场] [--days N]   强势股筛选
  stockfunnel look <代码> [选项]            单只股票查询
  stockfunnel backtest [-m 市场]            历史回测
  stockfunnel info                          数据状态概览

市场代码：
  sh    沪市主板    sz    深市主板
  star  科创板      cyb   创业板
  main  沪深主板(sh+sz)
  all   全部（默认）

示例：
  stockfunnel update                        # 更新全市场数据
  stockfunnel update -m star                # 只更新科创板
  stockfunnel screen -m cyb --days 10       # 创业板最近10天的信号
  stockfunnel look 600519 --rs 120          # 查茅台+120日RS排名
  stockfunnel backtest -m star,cyb          # 科创+创业的回测
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# 让相对导入能工作
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent))

from stockfunnel import data_layer
from stockfunnel import strategy
from stockfunnel import query as query_mod


def cmd_info(args) -> None:
    """显示数据状态。"""
    daily_file = data_layer.DATA / "daily.parquet"
    idx_file = data_layer.DATA / "index_daily.parquet"
    names_file = data_layer.DATA / "names.parquet"

    if not daily_file.exists():
        print("暂无数据，先运行：stockfunnel rebuild")
        return

    import pandas as pd
    df = pd.read_parquet(daily_file, columns=["date", "code"])
    last_date = df["date"].max()
    total = df["code"].nunique()

    # 各市场数量
    for market in ["sh", "star", "sz", "cyb"]:
        prefixes = data_layer.get_prefixes([market])
        count = sum(1 for c in df["code"].unique()
                    if any(str(c).startswith(p) for p in prefixes))
        print(f"  {market:5s}: {count:>5} 只")

    print(f"\n  总计: {total} 只股票")
    print(f"  日期范围: {df['date'].min()} ~ {last_date}")
    print(f"  总记录: {len(df):,} 条")

    if idx_file.exists():
        idx = pd.read_parquet(idx_file)
        print(f"  指数: {idx['code'].nunique()} 个（{', '.join(sorted(idx['code'].unique()))}）")

    if names_file.exists():
        names = pd.read_parquet(names_file)
        print(f"  名称记录: {len(names)} 条")

    # 最近几个交易日有没有信号
    print("\n  最近信号:")
    signals, _ = strategy.run_screen(args.market)
    if signals.empty:
        print("    （无）")
    else:
        last_dates = sorted(signals["date"].unique())[-3:]
        for d in last_dates:
            day = signals[signals["date"] == d]
            print(f"    {d}: {len(day)} 只 — "
                  + ", ".join(f"{r['code']} {r['name']}" for _, r in day.head(3).iterrows())
                  + ("..." if len(day) > 3 else ""))


def cmd_update(args) -> None:
    """增量更新。"""
    print(f"市场范围: {args.market}")
    start = time.time()
    data_layer.update(args.market)
    elapsed = time.time() - start
    print(f"\n完成，用时 {elapsed:.0f} 秒")


def cmd_rebuild(args) -> None:
    """全量重建。"""
    print(f"市场范围: {args.market}")
    print("⚠️  全量重建会清空已有数据并从头下载，需要较长时间。")
    if not args.yes:
        resp = input("确认继续？[y/N] ").strip().lower()
        if resp not in ("y", "yes"):
            print("已取消")
            return
    start = time.time()
    data_layer.rebuild(args.market)
    elapsed = time.time() - start
    print(f"\n完成，用时 {elapsed:.0f} 秒")


def cmd_screen(args) -> None:
    """强势股筛选。"""
    print(f"市场范围: {args.market}")
    print(f"策略: RS+平台突破+大盘过滤\n")

    signals, funnel = strategy.run_screen(args.market)

    # 取交易日历：最近N个交易日（而非最近N个信号日）
    import pandas as pd
    all_trade_dates = pd.read_parquet(
        data_layer.DATA / "daily.parquet", columns=["date"]
    )["date"].drop_duplicates().sort_values().to_numpy()

    if args.all:
        if signals.empty:
            print("没有符合条件的信号。")
            return
        last_dates = sorted(signals["date"].unique())
    else:
        last_dates = list(all_trade_dates[-args.days:])

    idx_df = data_layer.load_indices()
    market_ok = strategy.market_above_ma(
        idx_df, strategy.STRATEGY_PARAMS["market_index"],
        strategy.STRATEGY_PARAMS["market_ma_days"])

    for d in last_dates:
        day = signals[signals["date"] == d] if not signals.empty else signals.iloc[0:0]
        mkt = "✓ 可操作" if market_ok.get(d, False) else "✗ 空仓观望"
        print(f"--- {d}  {mkt} ---")
        if day.empty:
            print("  （无）")
        else:
            for _, r in day.iterrows():
                print(f"  {r['code']}  {r['name']:<10}  "
                      f"收{r['close']:.2f}  涨{r['pct_chg']:+.2f}%  "
                      f"量比{r['vol_ratio']}  换手{r['turn']:.1f}%  "
                      f"RS{r['rs_rank']:.1f}%")
        print()

    if not signals.empty:
        print(f"共 {len(signals)} 个历史信号，{signals['date'].nunique()} 个信号日")

    # 漏斗统计
    if not funnel.empty:
        print(f"\n日均漏斗：第一步 {funnel['step1'].mean():.1f} 只 → "
              f"第二步 {funnel['step2'].mean():.1f} 只 → "
              f"第三步 {funnel['step3'].mean():.1f} 只")


def cmd_look(args) -> None:
    """单只股票查询。"""
    ma_list = [int(x.strip()) for x in args.ma.split(",") if x.strip()]
    result = query_mod.query_stock(
        args.code,
        days=args.days,
        ma_list=ma_list,
        vol_ratio_days=args.vol_ratio,
        rs_lookback=args.rs,
        market_str=args.market,
    )
    print(result)


def cmd_backtest(args) -> None:
    """历史回测。"""
    print(f"市场范围: {args.market}")
    print(f"策略: RS+平台突破+大盘过滤")
    print("回测中...", flush=True)

    start = time.time()
    result = strategy.run_backtest(args.market)
    elapsed = time.time() - start

    if "error" in result:
        print(f"错误: {result['error']}")
        return

    print(f"\n{'='*60}")
    print(f"  回测结果（市场：{args.market}）")
    print(f"{'='*60}")
    print(f"  信号总数:    {result['n_signals']}")
    print(f"  信号天数:    {result['n_signal_days']}")
    print(f"  计算耗时:    {elapsed:.1f} 秒")
    print()

    print(f"  {'持有期':<8} {'平均收益':>10} {'胜率':>8} {'超额收益':>10} {'超额胜率':>10}")
    print(f"  {'-'*52}")
    for n in strategy.STRATEGY_PARAMS["forward_windows"]:
        print(f"  {n}日{'':<5} {result[f'{n}d_mean']:>+9.2f}% "
              f"{result[f'{n}d_winrate']:>7.1f}% "
              f"{result[f'{n}d_excess']:>+9.2f}% "
              f"{result[f'{n}d_excess_winrate']:>8.1f}%")
    print()

    print(f"  均线纪律（破5减半/破10清仓）:")
    print(f"    平均收益:  {result['rule_mean']:+.2f}%")
    print(f"    胜率:      {result['rule_winrate']:.1f}%")
    print(f"    平均持仓:  {result['rule_avg_days']:.1f} 天")

    if "exit_reasons" in result:
        reasons = result["exit_reasons"]
        reason_names = {
            "ma10_break": "破10日线清仓",
            "hold_cap": "持有到期",
            "ma5_break": "破5日线减半",
        }
        print(f"    离场原因:")
        for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
            name = reason_names.get(k, k)
            print(f"      {name}: {v:.1f}%")

    print(f"{'='*60}")

    if args.json:
        print()
        print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="stockfunnel",
        description="强势股筛选工具 · 相对强度 + 平台突破 + 大盘过滤",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # 每个子命令都带 -m 参数
    def _add_market(p):
        p.add_argument("-m", "--market", default="all",
                       help="市场范围：all/sh/sz/star/cyb/main，可组合用逗号（默认 all）")

    # info
    p_info = sub.add_parser("info", help="数据状态概览")
    _add_market(p_info)
    p_info.set_defaults(func=cmd_info)

    # update
    p_update = sub.add_parser("update", help="增量更新数据")
    _add_market(p_update)
    p_update.set_defaults(func=cmd_update)

    # rebuild
    p_rebuild = sub.add_parser("rebuild", help="全量重建数据")
    p_rebuild.add_argument("-y", "--yes", action="store_true", help="跳过确认")
    _add_market(p_rebuild)
    p_rebuild.set_defaults(func=cmd_rebuild)

    # screen
    p_screen = sub.add_parser("screen", help="强势股筛选")
    _add_market(p_screen)
    p_screen.add_argument("--days", type=int, default=5, help="显示最近N个交易日（默认5）")
    p_screen.add_argument("--all", action="store_true", help="输出所有历史信号")
    p_screen.set_defaults(func=cmd_screen)

    # look
    p_look = sub.add_parser("look", help="单只股票查询")
    _add_market(p_look)
    p_look.add_argument("code", help="股票代码，如 600519 或 sz.000001")
    p_look.add_argument("--days", type=int, default=20, help="显示最近N天（默认20）")
    p_look.add_argument("--ma", default="5,10,20,60", help="均线周期，逗号分隔（默认5,10,20,60）")
    p_look.add_argument("--vol-ratio", type=int, default=5, help="量比参考天数（默认5）")
    p_look.add_argument("--rs", type=int, default=0, help="显示N日相对强度排名（默认不显示）")
    p_look.set_defaults(func=cmd_look)

    # backtest
    p_bt = sub.add_parser("backtest", help="历史回测")
    _add_market(p_bt)
    p_bt.add_argument("--json", action="store_true", help="输出JSON格式")
    p_bt.set_defaults(func=cmd_backtest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

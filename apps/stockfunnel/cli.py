"""股票漏斗 · 统一入口

用法：
  stockfunnel update [-m 市场]              增量更新数据
  stockfunnel rebuild [-m 市场]             全量重建数据
  stockfunnel timing [--backtest]           指数趋势择时信号（主策略）
  stockfunnel screen [-m 市场] [--days N]   强势股筛选（观察工具）
  stockfunnel look <代码> [选项]            单只股票查询
  stockfunnel backtest [-m 市场]            历史回测（含成本与可成交性约束）
  stockfunnel validate [-m 市场]            年度稳定性 + 参数敏感性验证
  stockfunnel track [--days N]              实盘对账（登记信号→回填行情→手填成交价）
  stockfunnel info                          数据状态概览

市场代码：
  sh    沪市主板    sz    深市主板
  star  科创板      cyb   创业板
  main  沪深主板(sh+sz)
  all   全部（默认）

示例：
  stockfunnel update                        # 更新全市场数据
  stockfunnel timing                        # 今日择时信号（翻转才需操作）
  stockfunnel timing --backtest             # 信号 + 全历史回测
  stockfunnel screen -m cyb --days 10       # 创业板最近10天的信号
  stockfunnel backtest --gap-max 3          # 次日高开>3%放弃入场的回测
  stockfunnel backtest --no-cost            # 关闭成本模型（对比用）
  stockfunnel validate                      # 参数敏感性 + 年度稳定性
  stockfunnel track                         # 生成/更新实盘对账表
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
from stockfunnel import timing as timing_mod
from stockfunnel import query as query_mod


def _market_params(args) -> dict | None:
    """把 CLI 覆盖参数转成 strategy params dict。"""
    overrides: dict = {}
    if getattr(args, "gap_max", None) is not None:
        overrides["max_entry_gap_pct"] = args.gap_max
    if getattr(args, "positions", None) is not None:
        overrides["max_positions"] = args.positions
    if getattr(args, "no_cost", False):
        overrides.update({"commission": 0.0, "stamp_duty": 0.0, "slippage": 0.0})
    return overrides or None


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

    # 最近信号：读上次 screen/backtest 的缓存，不重跑全量筛选（秒级返回）
    print("\n  最近信号:")
    sig_file = data_layer.DATA / "last_signals.parquet"
    meta_file = data_layer.DATA / "last_signals.json"
    meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
    if not sig_file.exists():
        print("    （尚无缓存，运行一次 stockfunnel screen 后可见）")
    else:
        signals = pd.read_parquet(sig_file)
        if signals.empty:
            print("    （无）")
        else:
            last_dates = sorted(signals["date"].unique())[-3:]
            for d in last_dates:
                day = signals[signals["date"] == d]
                print(f"    {d}: {len(day)} 只 — "
                      + ", ".join(f"{r['code']} {r['name']}" for _, r in day.head(3).iterrows())
                      + ("..." if len(day) > 3 else ""))
    if meta:
        note = ""
        if meta.get("market") and meta["market"] != args.market:
            note = f"，市场范围 {meta['market']}（当前查询 {args.market}）"
        print(f"    [缓存于 {meta.get('run_at', '?')}{note}]")


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
    print("⚠️  全量重建会清空该市场范围的已有分片并从头下载，需要较长时间。")
    print("    中断后重跑 rebuild 可续传（已重新下载的分片不会重复下载）。")
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
    print("策略: RS+平台突破+分市场大盘过滤\n")

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

    # 大盘开关：主板看沪深300，创业板/科创板看创业板指
    idx_df = data_layer.load_indices()
    p = strategy.STRATEGY_PARAMS
    flag_names = {
        "sh.000300": "主板",
        "sz.399006": "成长",
    }
    flag_maps = {}
    for idx_code in set(p["market_index_map"].values()):
        flag_maps[idx_code] = strategy.market_above_ma(
            idx_df, idx_code, p["market_ma_days"])

    for d in last_dates:
        day = signals[signals["date"] == d] if not signals.empty else signals.iloc[0:0]
        marks = "  ".join(
            f"{flag_names.get(c, c)}{'✓' if m.get(d, False) else '✗'}"
            for c, m in sorted(flag_maps.items()))
        print(f"--- {d}  [{marks}] ---")
        if day.empty:
            print("  （无）")
        else:
            for _, r in day.iterrows():
                amt = f" 额{r['amount_yi']:.1f}亿" if r.get("amount_yi") else ""
                print(f"  {r['code']}  {r['name']:<10}  "
                      f"收{r['close']:.2f}  涨{r['pct_chg']:+.2f}%  "
                      f"量比{r['vol_ratio']}  换手{r['turn']:.1f}%{amt}  "
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
    """历史回测（含成本与可成交性约束）。"""
    print(f"市场范围: {args.market}")
    print("策略: RS+平台突破+分市场大盘过滤")
    print("回测中...", flush=True)

    start = time.time()
    result = strategy.run_backtest(args.market, _market_params(args))
    elapsed = time.time() - start

    if "error" in result:
        print(f"错误: {result['error']}")
        return

    pp = result.get("params", {})
    print(f"\n{'=' * 66}")
    print(f"  回测结果（市场：{args.market}）")
    print(f"{'=' * 66}")
    print(f"  信号总数:    {result['n_signals']}（{result['n_signal_days']} 个信号日）")
    print(f"  可成交:      {result['n_feasible']}")
    if result.get("entry_skips"):
        skip_names = {
            "gap_up": f"高开>{pp.get('max_entry_gap_pct', '?')}%放弃",
            "limit_lock": "一字板无法成交",
            "halt_next": "次日停牌",
            "halt_or_delist": "次日无数据(停牌/退市)",
            "no_next": "数据尽头",
            "bad_open": "开盘价异常",
        }
        parts = [f"{skip_names.get(k, k)} {v}" for k, v in result["entry_skips"].items()]
        print(f"  不可成交:    " + "，".join(parts))
    print(f"  交易成本:    往返 {result['cost_roundtrip_pct']:.2f}%"
          f"（佣金{pp.get('commission', 0)*100:.3f}%×2"
          f" + 印花税{pp.get('stamp_duty', 0)*100:.2f}%"
          f" + 滑点{pp.get('slippage', 0)*100:.2f}%×2）")
    print(f"  计算耗时:    {elapsed:.1f} 秒")
    print()

    print(f"  {'持有期':<6} {'毛收益':>8} {'净收益':>8} {'净胜率':>8} "
          f"{'净超额':>8} {'超额胜率':>8}")
    print(f"  {'-' * 58}")
    for n in strategy.STRATEGY_PARAMS["forward_windows"]:
        if f"{n}d_mean" not in result:
            continue
        print(f"  {n}日{'':<4} {result[f'{n}d_mean']:>+7.2f}% "
              f"{result[f'{n}d_net']:>+7.2f}% "
              f"{result[f'{n}d_winrate']:>7.1f}% "
              f"{result[f'{n}d_excess_net']:>+7.2f}% "
              f"{result[f'{n}d_excess_winrate']:>7.1f}%")
    print()

    if "rule_net_mean" in result:
        print(f"  均线纪律（破5减半/破10清仓，T+1，含成本）:")
        print(f"    单笔毛收益: {result['rule_mean']:+.2f}%   "
              f"单笔净收益: {result['rule_net_mean']:+.2f}%")
        print(f"    净胜率:     {result['rule_winrate']:.1f}%   "
              f"平均持仓: {result['rule_avg_days']:.1f} 天   "
              f"样本: {result['rule_n']}")

        if "exit_reasons" in result:
            reason_names = {
                "ma10_break": "破10日线清仓",
                "hold_cap": "持有到期",
            }
            parts = [f"{reason_names.get(k, k)} {v:.1f}%"
                     for k, v in sorted(result["exit_reasons"].items(),
                                        key=lambda x: -x[1])]
            print(f"    离场原因:   " + "，".join(parts))
        print()

    if "portfolio" in result:
        pf = result["portfolio"]
        print(f"  组合模拟（最多{pp.get('max_positions', '?')}只并发，槽位制）:")
        print(f"    区间:       {pf['period']}")
        print(f"    总收益:     {pf['total_return_pct']:+.2f}%   "
              f"年化: {pf['cagr_pct']:+.2f}%")
        print(f"    成交笔数:   {pf['n_trades']}   "
              f"满仓错过: {pf['n_skipped_slots_full']}")
        print(f"    期末资金:   {pf['final_capital']:,.0f}"
              f"（初始 {strategy.STRATEGY_PARAMS['initial_capital']:,.0f}）")

    print(f"{'=' * 66}")

    if args.json:
        print()
        print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_validate(args) -> None:
    """年度稳定性 + 参数敏感性验证。"""
    print(f"市场范围: {args.market}")
    print("验证中（RS 排名只计算一次，随后扫描参数变体）...\n", flush=True)

    start = time.time()
    result = strategy.run_validate(args.market, _market_params(args))
    elapsed = time.time() - start

    print(f"\n{'=' * 66}")
    print(f"  验证报告（市场：{args.market}，耗时 {elapsed:.0f} 秒）")
    print(f"{'=' * 66}")

    b = result["baseline"]
    print(f"\n  基准参数: 信号 {b['n_signals']} 个，可成交 {b['n_feasible']}，"
          f"10日净超额 {b['exc_10_net']}%，纪律净收益 {b['rule_net']}%")

    if result["yearly"]:
        print(f"\n  年度稳定性（可成交信号）:")
        print(f"  {'年份':<6} {'信号数':>6} {'10日净超额':>10} "
              f"{'纪律净收益':>10} {'净胜率':>8}")
        print(f"  {'-' * 48}")
        for y in result["yearly"]:
            exc = f"{y['exc_10_net']:+.2f}%" if y["exc_10_net"] is not None else "-"
            rn = f"{y['rule_net']:+.2f}%" if y["rule_net"] is not None else "-"
            rw = f"{y['rule_winrate']:.1f}%" if y["rule_winrate"] is not None else "-"
            print(f"  {y['year']:<6} {y['n']:>6} {exc:>10} {rn:>10} {rw:>8}")
        pos_years = sum(1 for y in result["yearly"]
                        if (y["exc_10_net"] or 0) > 0)
        print(f"\n  → 正超额年份: {pos_years}/{len(result['yearly'])}"
              f"（全部为正说明不是单一行情的产物）")

    if result["sensitivity"]:
        print(f"\n  参数敏感性（单参数扰动）:")
        print(f"  {'变体':<26} {'信号数':>6} {'10日净超额':>10} "
              f"{'纪律净收益':>10} {'净胜率':>8}")
        print(f"  {'-' * 62}")
        for m in result["sensitivity"]:
            exc = f"{m['exc_10_net']:+.2f}%" if m.get("exc_10_net") is not None else "-"
            rn = f"{m['rule_net']:+.2f}%" if m.get("rule_net") is not None else "-"
            rw = f"{m['rule_winrate']:.1f}%" if m.get("rule_winrate") is not None else "-"
            print(f"  {m['variant']:<26} {m['n_signals']:>6} {exc:>10} {rn:>10} {rw:>8}")
        neg = [m["variant"] for m in result["sensitivity"]
               if (m.get("exc_10_net") or -1) < 0]
        print(f"\n  → 负超额变体: {len(neg)}/{len(result['sensitivity'])}"
              + (f"（{', '.join(neg)}）" if neg else "（无，参数不在刀尖上）"))

    print(f"{'=' * 66}")

    if args.json:
        print()
        print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_timing(args) -> None:
    """指数趋势择时信号。"""
    overrides: dict = {}
    if args.ma:
        overrides["ma_days"] = args.ma
    timing_mod.run_timing(backtest=args.backtest, params=overrides or None)


def cmd_track(args) -> None:
    """实盘对账表。"""
    try:
        log = strategy.update_trade_log(days=args.days)
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误: {exc}")
        return

    log_file = strategy.OUTPUT / "trade_log.csv"
    print(f"对账表已更新: {log_file}（{len(log)} 条）\n")

    pending = log[log["fill_price"].isna()]
    if not pending.empty:
        print("  待操作/待回填成交价:")
        for _, r in pending.iterrows():
            gap = f" 开盘{r['gap_pct']:+.2f}%" if r["gap_pct"] == r["gap_pct"] and r["gap_pct"] is not None else ""
            no = f" 次日开{r['next_open']:.2f}" if r["next_open"] == r["next_open"] and r["next_open"] is not None else "（次日行情未出）"
            print(f"    {r['signal_date']} → {r['next_date'] or '?'}  "
                  f"{r['code']} {r['name']}  信号收{r['signal_close']:.2f}"
                  f"{no}{gap}")
        print("\n  买入后请手动在 CSV 的 fill_price 列填写实际成交价。")
    filled = log[log["fill_price"].notna()]
    if not filled.empty:
        print(f"\n  已回填成交价: {len(filled)} 条")
        for _, r in filled.iterrows():
            nc = r["next_close"]
            pnl = ""
            if nc == nc and nc is not None and r["fill_price"]:
                pnl = f"  次日收{nc:.2f}（{(nc / float(r['fill_price']) - 1) * 100:+.2f}%）"
            print(f"    {r['signal_date']}  {r['code']} {r['name']}  "
                  f"成交{float(r['fill_price']):.2f}{pnl}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="stockfunnel",
        description="强势股筛选工具 · 相对强度 + 平台突破 + 分市场大盘过滤",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # 每个子命令都带 -m 参数
    def _add_market(p):
        p.add_argument("-m", "--market", default="all",
                       help="市场范围：all/sh/sz/star/cyb/main，可组合用逗号（默认 all）")

    def _add_bt_overrides(p):
        p.add_argument("--gap-max", type=float, default=None,
                       help="次日开盘高开超过该%%放弃入场（默认 4.0）")
        p.add_argument("--positions", type=int, default=None,
                       help="组合模拟最大并发持仓数（默认 5）")
        p.add_argument("--no-cost", action="store_true",
                       help="关闭成本模型（对比研究用）")

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
    p_bt = sub.add_parser("backtest", help="历史回测（含成本与可成交性）")
    _add_market(p_bt)
    _add_bt_overrides(p_bt)
    p_bt.add_argument("--json", action="store_true", help="输出JSON格式")
    p_bt.set_defaults(func=cmd_backtest)

    # validate
    p_val = sub.add_parser("validate", help="年度稳定性 + 参数敏感性验证")
    _add_market(p_val)
    _add_bt_overrides(p_val)
    p_val.add_argument("--json", action="store_true", help="输出JSON格式")
    p_val.set_defaults(func=cmd_validate)

    # track
    p_track = sub.add_parser("track", help="实盘对账表")
    p_track.add_argument("--days", type=int, default=10,
                         help="覆盖最近N个交易日内的信号（默认10）")
    p_track.set_defaults(func=cmd_track)

    # timing
    p_timing = sub.add_parser("timing", help="指数趋势择时信号（主策略）")
    p_timing.add_argument("--ma", type=int, default=None,
                          help="均线天数（默认50；MA40-60为参数平台，勿微调）")
    p_timing.add_argument("--backtest", action="store_true",
                          help="附全历史回测统计")
    p_timing.set_defaults(func=cmd_timing)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

"""数据层：统一的下载、更新、加载接口。

市场代码：
  sh    沪市主板（sh.600, sh.601, sh.603, sh.605）
  star  科创板（sh.688）
  sz    深市主板（sz.000, sz.001, sz.002, sz.003）
  cyb   创业板（sz.300, sz.301）
  main  沪深主板（sh + sz）
  all   全部（sh + star + sz + cyb）

指数数据始终一起下载，不单独过滤。
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import baostock as bs
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
CHUNKS = DATA / "chunks"
START_DATE = "2022-06-01"
FIELDS = "date,code,open,high,low,close,volume,amount,turn,pctChg,tradestatus"

MARKET_PREFIXES: dict[str, tuple[str, ...]] = {
    "sh": ("sh.600", "sh.601", "sh.603", "sh.605"),
    "star": ("sh.688",),
    "sz": ("sz.000", "sz.001", "sz.002", "sz.003"),
    "cyb": ("sz.300", "sz.301"),
}

INDEX_CODES: list[str] = [
    "sh.000001",  # 上证指数
    "sh.000300",  # 沪深300
    "sh.000905",  # 中证500
    "sh.000852",  # 中证1000
    "sz.399001",  # 深证成指
    "sz.399006",  # 创业板指
    "sh.000068",  # 科创50
]


def resolve_markets(market_str: str) -> list[str]:
    """把用户输入的市场字符串解析成前缀列表。

    支持别名：main = sh+sz, all = sh+star+sz+cyb
    支持逗号分隔组合：sh,star
    """
    if not market_str or market_str == "all":
        return ["sh", "star", "sz", "cyb"]
    if market_str == "main":
        return ["sh", "sz"]

    parts = [p.strip().lower() for p in market_str.split(",")]
    result: list[str] = []
    for p in parts:
        if p == "main":
            result.extend(["sh", "sz"])
        elif p == "all":
            result.extend(["sh", "star", "sz", "cyb"])
        elif p in MARKET_PREFIXES:
            result.append(p)
        else:
            print(f"warning: unknown market '{p}', skipped", file=sys.stderr)
    # 去重保序
    seen: set[str] = set()
    uniq = []
    for m in result:
        if m not in seen:
            seen.add(m)
            uniq.append(m)
    return uniq


def get_prefixes(markets: list[str]) -> tuple[str, ...]:
    """根据市场列表获取代码前缀元组。"""
    prefixes: list[str] = []
    for m in markets:
        prefixes.extend(MARKET_PREFIXES.get(m, ()))
    return tuple(prefixes)


def match_market(code: str, markets: list[str]) -> bool:
    """判断股票代码是否属于指定市场。"""
    for m in markets:
        for prefix in MARKET_PREFIXES.get(m, ()):
            if code.startswith(prefix):
                return True
    return False


# ---------- 登录辅助 ----------

def _login() -> None:
    lg = bs.login()
    if lg.error_code != "0":
        raise RuntimeError(f"baostock login failed: {lg.error_msg}")


def _logout() -> None:
    try:
        bs.logout()
    except Exception:
        pass


def _relogin() -> None:
    _logout()
    _login()


# ---------- 股票池 ----------

def build_universe(markets: list[str]) -> tuple[list[str], pd.DataFrame]:
    """构建指定市场的股票池。

    返回 (代码列表, 名称记录表)。
    """
    prefixes = get_prefixes(markets)
    end = time.strftime("%Y-%m-%d")

    # 1. 先取交易日历
    rs = bs.query_trade_dates(start_date=START_DATE, end_date=end)
    trade_days: list[str] = []
    while rs.error_code == "0" and rs.next():
        d, is_trading = rs.get_row_data()
        if is_trading == "1":
            trade_days.append(d)

    # 2. 按月快照构建主板/创业板池（能抓到退市票）
    sample_days, seen_months = [], set()
    for d in trade_days:
        month = d[:7]
        if month not in seen_months:
            seen_months.add(month)
            sample_days.append(d)
    if trade_days and trade_days[-1] != sample_days[-1]:
        sample_days.append(trade_days[-1])

    snapshots: list[tuple[str, str, str]] = []
    latest_name: dict[str, str] = {}

    # 判断是否需要 query_all_stock（主板/创业板需要，科创板不需要）
    need_all_stock = any(m in ("sh", "sz", "cyb") for m in markets)
    need_star = "star" in markets

    if need_all_stock:
        for d in sample_days:
            rs = bs.query_all_stock(day=d)
            rows = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())
            for row in rows:
                code, name = row[0], row[-1]
                if not any(code.startswith(p) for p in prefixes):
                    continue
                # 排除科创板（如果要的话走另一条路）
                if code.startswith("sh.688") and "star" not in markets:
                    continue
                snapshots.append((d, code, name))
                latest_name[code] = name
            print(f"  universe {d}: {len(latest_name)} stocks so far", flush=True)

    # 3. 科创板用 stock_basic 补（query_all_stock 查不到）
    if need_star:
        rs = bs.query_stock_basic()
        star_count = 0
        while rs.error_code == "0" and rs.next():
            row = rs.get_row_data()
            code, name, ipo_date, out_date, stype, status = row
            if not code.startswith("sh.688"):
                continue
            if status != "1":
                continue
            if ipo_date and ipo_date > trade_days[-1]:
                continue
            star_count += 1
            latest_name[code] = name
            snapshots.append((trade_days[-1], code, name))
        print(f"  STAR market: {star_count} stocks", flush=True)

    names = pd.DataFrame(snapshots, columns=["date", "code", "name"])
    codes = sorted(latest_name)
    print(f"  total universe: {len(codes)} stocks", flush=True)
    return codes, names


# ---------- 下载 ----------

def fetch_kline(code: str, start: str, end: str, max_retries: int = 3) -> list[list[str]]:
    """拉取单只股票日线，失败自动重登重试。"""
    last_err = ""
    for attempt in range(max_retries):
        try:
            rs = bs.query_history_k_data_plus(
                code, FIELDS, start_date=start, end_date=end,
                frequency="d", adjustflag="2",
            )
            if rs.error_code != "0":
                raise ConnectionError(f"{rs.error_code} {rs.error_msg}")
            rows = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())
            return rows
        except Exception as exc:
            last_err = str(exc)
            time.sleep(1.5 * (attempt + 1))
            _relogin()
    raise RuntimeError(f"retries exhausted for {code}: {last_err}")


def download_codes(codes: list[str], start: str, end: str,
                   label: str = "download") -> int:
    """下载一批股票的日线数据，写入分片文件。返回失败数。"""
    CHUNKS.mkdir(parents=True, exist_ok=True)
    todo = [c for c in codes if not (CHUNKS / f"{c}.parquet").exists()]
    print(f"{label}: {len(todo)} to download / {len(codes)} total", flush=True)

    failed: list[str] = []
    consec_err = 0
    for i, code in enumerate(todo):
        try:
            rows = fetch_kline(code, start, end)
            consec_err = 0
            if rows:
                df = pd.DataFrame(rows, columns=FIELDS.split(","))
                df.to_parquet(CHUNKS / f"{code}.parquet")
            else:
                pd.DataFrame(columns=FIELDS.split(",")).to_parquet(
                    CHUNKS / f"{code}.parquet")
        except Exception as exc:
            failed.append(code)
            consec_err += 1
            print(f"  FAIL {code}: {exc}", flush=True)
            if consec_err >= 10:
                print("  too many consecutive errors, sleeping 60s...", flush=True)
                time.sleep(60)
                consec_err = 0
        if (i + 1) % 200 == 0:
            print(f"  progress {i+1}/{len(todo)} failed={len(failed)}", flush=True)

    print(f"{label} done: {len(todo)-len(failed)} ok, {len(failed)} failed", flush=True)
    if failed:
        (DATA / f"failed_{label}.txt").write_text("\n".join(failed))
    return len(failed)


def download_indices(end: str) -> None:
    """下载所有指数日线。"""
    idx_file = DATA / "index_daily.parquet"
    all_parts = []
    for code in INDEX_CODES:
        try:
            rows = fetch_kline(code, START_DATE, end)
            if rows:
                df = pd.DataFrame(rows, columns=FIELDS.split(","))
                all_parts.append(df)
                print(f"  index {code}: {len(df)} days", flush=True)
        except Exception as exc:
            print(f"  FAIL index {code}: {exc}", flush=True)
    if all_parts:
        idx_all = pd.concat(all_parts, ignore_index=True)
        idx_all.to_parquet(idx_file)
        print(f"  index_daily.parquet: {len(idx_all)} rows saved", flush=True)


# ---------- 合并 ----------

def merge_chunks(markets: list[str] | None = None) -> pd.DataFrame:
    """合并分片到 daily.parquet。可指定市场范围，None 表示全部。"""
    files = sorted(CHUNKS.glob("*.parquet"))
    if markets:
        prefixes = get_prefixes(markets)
        files = [f for f in files if any(f.stem.startswith(p) for p in prefixes)]
    print(f"merging {len(files)} chunks...", flush=True)

    parts: list[pd.DataFrame] = []
    for i, f in enumerate(files):
        parts.append(pd.read_parquet(f))
        if (i + 1) % 1000 == 0:
            print(f"  read {i+1}/{len(files)}", flush=True)

    df = pd.concat(parts, ignore_index=True)
    numeric_cols = ["open", "high", "low", "close", "volume", "amount", "turn", "pctChg"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["tradestatus"] = df["tradestatus"].astype(str)
    df = df.sort_values(["code", "date"]).reset_index(drop=True)
    df.to_parquet(DATA / "daily.parquet")
    print(f"daily.parquet: {len(df):,} rows, {df['code'].nunique()} codes, "
          f"{df['date'].min()} ~ {df['date'].max()}", flush=True)
    return df


# ---------- 公开 API ----------

def rebuild(market_str: str = "all") -> None:
    """全量重建：清掉旧数据，从头下载。"""
    markets = resolve_markets(market_str)
    print(f"=== Rebuilding data for markets: {', '.join(markets)} ===")
    DATA.mkdir(parents=True, exist_ok=True)

    _login()
    try:
        # 1. 构建股票池
        print("Building universe...", flush=True)
        codes, names = build_universe(markets)
        names.to_parquet(DATA / "names.parquet")
        pd.DataFrame({"code": codes}).to_parquet(DATA / "universe.parquet")

        # 2. 下载个股数据
        print("Downloading stock data...", flush=True)
        end = time.strftime("%Y-%m-%d")
        download_codes(codes, START_DATE, end, label="stocks")

        # 3. 下载指数
        print("Downloading index data...", flush=True)
        download_indices(end)

        # 4. 合并
        merge_chunks(markets)
        print("Rebuild complete.")
    finally:
        _logout()


def update(market_str: str = "all") -> None:
    """增量更新：只拉取新数据，自动补全新股票。"""
    markets = resolve_markets(market_str)
    daily_file = DATA / "daily.parquet"

    if not daily_file.exists():
        print("No existing data found, running full rebuild instead.", flush=True)
        rebuild(market_str)
        return

    print(f"=== Updating data for markets: {', '.join(markets)} ===")
    _login()
    try:
        # 1. 读现有数据
        existing = pd.read_parquet(daily_file, columns=["date", "code"])
        last_date = existing["date"].max()
        existing_codes = set(existing["code"].unique())
        end = time.strftime("%Y-%m-%d")
        print(f"existing: {len(existing_codes)} stocks, last date {last_date}", flush=True)

        if last_date >= end:
            print("already up to date", flush=True)
            return

        # 2. 检查有没有新股票需要补
        print("Checking for new stocks...", flush=True)
        all_codes, names_df = build_universe(markets)
        # 合并 names
        old_names = pd.read_parquet(DATA / "names.parquet")
        combined_names = pd.concat([old_names, names_df], ignore_index=True)
        combined_names = combined_names.drop_duplicates(subset=["date", "code"], keep="last")
        combined_names.to_parquet(DATA / "names.parquet")

        new_codes = [c for c in all_codes if c not in existing_codes]
        if new_codes:
            print(f"New stocks to backfill: {len(new_codes)}", flush=True)
            download_codes(new_codes, START_DATE, end, label="new_stocks")

        # 3. 增量更新已有股票（从 last_date 开始，留一天重叠）
        start = last_date
        existing_list = [c for c in existing_codes if (CHUNKS / f"{c}.parquet").exists()]
        print(f"Updating {len(existing_list)} existing stocks from {start}...", flush=True)

        failed = 0
        consec_err = 0
        for i, code in enumerate(existing_list):
            chunk_file = CHUNKS / f"{code}.parquet"
            try:
                new_rows = fetch_kline(code, start, end)
                consec_err = 0
                if new_rows:
                    new_df = pd.DataFrame(new_rows, columns=FIELDS.split(","))
                    old_df = pd.read_parquet(chunk_file)
                    combined = pd.concat([old_df, new_df], ignore_index=True)
                    combined = combined.drop_duplicates(subset=["date"], keep="last")
                    combined = combined.sort_values("date").reset_index(drop=True)
                    combined.to_parquet(chunk_file)
            except Exception as exc:
                failed += 1
                consec_err += 1
                print(f"  FAIL {code}: {exc}", flush=True)
                if consec_err >= 10:
                    print("  too many consecutive errors, sleeping 60s...", flush=True)
                    time.sleep(60)
                    consec_err = 0
            if (i + 1) % 500 == 0:
                print(f"  progress {i+1}/{len(existing_list)} failed={failed}", flush=True)

        # 4. 更新指数
        print("Updating indices...", flush=True)
        idx_file = DATA / "index_daily.parquet"
        if idx_file.exists():
            old_idx = pd.read_parquet(idx_file)
            idx_parts = []
            for code in INDEX_CODES:
                try:
                    rows = fetch_kline(code, start, end)
                    if rows:
                        new_df = pd.DataFrame(rows, columns=FIELDS.split(","))
                        old_one = old_idx[old_idx["code"] == code]
                        if not old_one.empty:
                            combined = pd.concat([old_one, new_df], ignore_index=True)
                            combined = combined.drop_duplicates(subset=["date"], keep="last")
                            idx_parts.append(combined)
                        else:
                            idx_parts.append(new_df)
                except Exception as exc:
                    print(f"  FAIL index {code}: {exc}", flush=True)
            # 保留没更新到的指数
            updated_codes = {p["code"].iloc[0] for p in idx_parts if len(p) > 0}
            remaining = old_idx[~old_idx["code"].isin(updated_codes)]
            if not remaining.empty:
                idx_parts.append(remaining)
            if idx_parts:
                idx_all = pd.concat(idx_parts, ignore_index=True)
                idx_all = idx_all.sort_values(["code", "date"]).reset_index(drop=True)
                idx_all.to_parquet(idx_file)
                print(f"  index_daily.parquet: {len(idx_all)} rows", flush=True)
        else:
            download_indices(end)

        # 5. 重新合并
        merge_chunks(markets)
        print(f"Update done: {len(existing_list)-failed} ok, {failed} failed, "
              f"{len(new_codes)} new stocks added", flush=True)
    finally:
        _logout()


def load_daily(markets: list[str] | None = None) -> pd.DataFrame:
    """加载日线数据，可选按市场过滤。"""
    df = pd.read_parquet(DATA / "daily.parquet")
    if markets:
        prefixes = get_prefixes(markets)
        mask = df["code"].str.startswith(prefixes[0])
        for p in prefixes[1:]:
            mask |= df["code"].str.startswith(p)
        df = df[mask].reset_index(drop=True)
    return df


def load_indices() -> pd.DataFrame:
    """加载指数数据。"""
    return pd.read_parquet(DATA / "index_daily.parquet")


def get_last_date() -> str:
    """获取数据最后一个交易日。"""
    df = pd.read_parquet(DATA / "daily.parquet", columns=["date"])
    return str(df["date"].max())

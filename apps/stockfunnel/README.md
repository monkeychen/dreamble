# StockFunnel · 强势股筛选工具

从 5000 只 A 股里快速筛出「刚冒头、还没加速」的强势股。

**核心策略**：相对强度 + 平台突破 + 大盘环境过滤

- **相对强度**：120 日累计涨幅排名全市场前 25%，股价靠近阶段新高

- **平台突破**：20 日横盘整理 + 量能萎缩 + 放量突破 + 均线多头

- **大盘过滤**：创业板指在 MA20 之上才操作，熊市空仓观望

经过 3 年回测验证，10 日超额收益约 **+1.15%**（vs 全市场等权基准）。

数据源为 [baostock](http://baostock.com)（免费、无需注册），前复权日线，覆盖：

| 市场   | 代码前缀                     | 数量     |
| ---- | ------------------------ | ------ |
| 沪市主板 | sh.600 / 601 / 603 / 605 | \~1700 |
| 科创板  | sh.688                   | \~600  |
| 深市主板 | sz.000 / 001 / 002 / 003 | \~1500 |
| 创业板  | sz.300 / 301             | \~1400 |

## 目录结构

```text
stockfunnel/
├── stockfunnel          # 统一入口（直接 ./stockfunnel 执行）
├── cli.py               # 命令行解析与子命令调度
├── data_layer.py        # 数据层：下载 / 更新 / 合并 / 加载
├── strategy.py          # 策略层：筛选 + 回测
├── query.py             # 查询层：单只股票行情
├── requirements.txt     # Python 依赖
├── data/                # 本地数据缓存（git 忽略）
│   ├── daily.parquet    # 全量日线
│   ├── index_daily.parquet  # 指数日线
│   ├── names.parquet    # 股票名称
│   ├── universe.parquet # 股票池
│   └── chunks/          # 分片文件（每只一个）
└── output/              # 产物：回测报告
    └── final_report.html
```

## 快速开始

依赖：Python 3.10+

```bash
# 创建虚拟环境
python3 -m venv .venv

# 安装依赖
.venv/bin/pip install -r requirements.txt
```

`./stockfunnel` 入口脚本会自动使用 `.venv` 中的 Python，无需手动激活。

**首次使用（全量下载，约 30-60 分钟）**：

```bash
./stockfunnel rebuild
```

**日常使用**：

```bash
# 1. 增量更新数据（几秒）
./stockfunnel update

# 2. 看最近 5 天的候选股
./stockfunnel screen --days 5

# 3. 细看某只票
./stockfunnel look 600519 --rs 120
```

## 命令一览

```
./stockfunnel <子命令> [选项]
```

### `info` — 数据状态概览

```bash
./stockfunnel info
```

显示各市场股票数、日期范围、最近信号。

### `update` — 增量更新数据

```bash
./stockfunnel update              # 更新全市场
./stockfunnel update -m star      # 只更新科创板
```

只拉取最后一个交易日之后的新数据，通常几秒到几十秒。自动检测新增股票并补全历史。

### `rebuild` — 全量重建

```bash
./stockfunnel rebuild -y          # 全市场从头下载
./stockfunnel rebuild -m cyb      # 只重建创业板
```

清空已有数据，从头下载。首次使用或数据损坏时用。

### `screen` — 强势股筛选

```bash
./stockfunnel screen              # 最近 5 天全市场
./stockfunnel screen -m cyb --days 10   # 创业板最近 10 天
./stockfunnel screen -m star,cyb        # 科创+创业
```

输出每天的候选股：代码、名称、收盘价、涨跌幅、量比、换手率、RS排名。

### `look` — 单只股票查询

```bash
./stockfunnel look 600519                # 贵州茅台最近 20 天
./stockfunnel look sz.300750 --days 60   # 宁德时代最近 60 天
./stockfunnel look 688981 --rs 120       # 中芯国际 + RS 排名
./stockfunnel look 000001 --ma 5,13,21,55  # 自定义均线
```

显示 K 线、均线（红线上绿线下）、量比、近 5/20/60 日涨跌、区间振幅。

### `backtest` — 历史回测

```bash
./stockfunnel backtest            # 全市场回测
./stockfunnel backtest -m star    # 只回测科创板
./stockfunnel backtest --json     # 输出 JSON 格式
```

统计各持有周期的平均收益、胜率、超额收益、超额胜率，以及均线纪律操作的收益。

## 市场代码（`-m` 参数）

| 代码     | 含义            |
| ------ | ------------- |
| `sh`   | 沪市主板          |
| `star` | 科创板           |
| `sz`   | 深市主板          |
| `cyb`  | 创业板           |
| `main` | 沪深主板（sh + sz） |
| `all`  | 全部（默认）        |

可组合：`-m star,cyb` 表示科创板 + 创业板。

## 策略说明

### 第一步：相对强度初筛（约 1000 只）

- 120 日累计涨幅排名全市场前 25%

- 股价在 120 日最高价的 85% 以上（靠近阶段新高）

- 站在 20 日均线之上

### 第二步：平台整理 + 突破确认（每天 0-2 只）

- 过去 20 日横盘整理，振幅 ≤ 25%

- 后半段量能萎缩到前半段的 80% 以下

- 收盘价在平台中上部（偏强整理）

- 突破日涨幅 2%-8%，量比 ≥ 1.5，换手率 2%-15%

- 均线多头排列：MA5 > MA10 > MA20 > MA60

### 大盘过滤（最重要）

- 创业板指在 20 日均线之上 → 可操作

- 之下 → 空仓观望

### 操作纪律

- 入场：信号日次日开盘买入

- 持有：收盘价在 5 日均线之上不动

- 减半：收盘跌破 5 日线 → 减一半

- 清仓：跌破 10 日线 → 全部卖出

- 平均持仓：约 7-8 天

## 风险提示

- 回测基于历史数据，不代表未来表现

- 未扣除佣金、印花税、滑点，实盘收益会低 0.3-0.5%

- 策略有衰减风险，需定期验证

- 本工具仅用于策略研究，不构成投资建议


# 厂家与型号画像

> **DATA_STAMP: 2026-08-29**｜价格为标准在线档快照（USD 或 CNY / 1M token）。
> 各家调价极快（OpenAI 在 GPT-5.6 发布后三周内把 Luna 砍了 80%），**任何预算决策前必须回官方定价页核验**。
> 本章价格多数来自第三方横向评测的公开整理，已尽量交叉比对，但不替代官方定价页。

## 一、厂家速览

| 厂家 | 主力型号 | 输入/输出 | 上下文 | effort 粒度 | 一句话定位 |
|---|---|---|---|---|---|
| **OpenAI** | GPT-5.6 Sol / Terra / Luna | $4/$20* · $2/$12 · $0.20/$1.20 | 1.05M | 6 档（最全） | 粒度最细，Luna 是海外价格地板；⚠️ web_search 另收 $10/1k 次 |
| **Anthropic** | Opus 5 / Sonnet 5 / Haiku 4.5 / Fable 5 | $5/$25 · $2/$10* · $1/$5 · $10/$50 | 1M（Haiku 200K） | 4 档（max 仅 Opus 系） | 软件工程修复最强，agent 稳 |
| **Google** | Gemini 3.1 Pro / 3.6 Flash / 3.5 Flash-Lite | $2/$12** · $1.5/$7.5 · $0.30/$2.50 | 1M | 4 档（Pro 不能关） | 长上下文 + 多模态 + 高吞吐 |
| **DeepSeek** | V4-Pro / V4-Flash | 见下（高峰/空闲双轨） | 1M | `reasoning_effort` low/high/max | 价格地板，但无原生联网工具 |
| **通义千问** | Qwen3.8-Max / 3.7-Max / 3.7-Plus | ¥12/¥36 · ¥6/¥18* · ¥1.6/¥6.4* | 1M / 1M / 256K+ | 布尔 + 预算 + `reasoning_effort` | **国产里唯一**原生 web_search/web_extractor，中文源覆盖最好 |
| **月之暗面** | Kimi K3 | ¥20/¥100 | 1M | `reasoning_effort` low/high/max（默认 max） | 长文本 + agent 化，但输出价极贵、联网当前不可用 |
| **智谱** | GLM-5.3 | ¥8/¥28（缓存 ¥2） | 1M / 128K 输出 | low/high/max（**关不掉，默认 max**） | 开源权重，可私有化；原厂版有**域名限定搜索** |
| **腾讯** | 混元 hy3 / hy3-preview | ¥1/¥4（缓存 ¥0.25） | 256K | 交错式思考 | **国产价格地板**；TokenHub 一个 key 打通多家 |
| **火山引擎** | 豆包 Seed 2.1 Pro / Turbo | ¥6/¥30 · ¥3/¥15 | — | 按型号选变体 | 低延迟，国内接入顺 |
| **xAI** | Grok 4.5 / 4.3 | $2/$6** · $1.25/$2.50 | 500K / 1M | 待核验 | 输出价低，终端执行强 |
| **MiniMax** | M3 | $0.30/$1.20* | — | 2 档 | 五折期内极便宜 |

\* 限时促销价：Sonnet 5 的 $2/$10 至 2026-08-31，9 月起 $3/$15；Qwen3.7 为活动价；MiniMax M3 为五折。
\** 长上下文跳档：Gemini 3.1 Pro 超 200K → $4/$18；Grok 4.5/4.3 超 200K 大致翻倍。

## 二、逐厂画像

### OpenAI GPT-5.6

**三档定位**（数字是代际，Sol/Terra/Luna 是可独立演进的持久能力档位）：

- **Sol** — 旗舰。官方自评 SWE-Bench Pro 64.6%、Terminal Bench 2.1 88.8%（第三方称 91.9%）、GPQA Diamond 94.6%。**当前标准价 $4/$20（官方明示"促销价至少持续至 2026-11-21"，到期回调到 $5/$30），长期测算必须留余量。**
- **Terra** — 均衡主力。Coding Agent 77.4，官方定位"性能对标 5.5 但便宜一半"。$2/$12 是当前性价比甜点。
- **Luna** — 高吞吐低价。Coding Agent 74.6、GPQA 92.3，**能力没有随价格缩水**。缓存读 $0.02/1M，对有固定 system prompt 和知识库的 agent 产品，重复输入成本近乎归零。

**四档服务等级（2026-08 官方定价页）**：Standard = 标价；**Batch 与 Flex = 5 折**（Sol $2/$10、Terra $1/$6、Luna $0.10/$0.60）；**Fast mode = 2 倍**（原 Priority，2026-07-30 更名）。缓存写 = 1.25× 输入价，缓存读 = 1 折。

**⚠️ 工具单独计费（最容易被漏算）**：
- `web_search`（all models）**$10.00 / 1k 次调用**，且搜索内容 token 按模型输入费率另计。
- `web_search_preview`（非推理模型）$25 / 1k 次，但内容 token 免费。
- `file_search` 工具调用 $2.50/1k 次，存储 $0.10/GB/天（首 1GB 免费）。
- 检索密集型任务里，**搜索调用费经常远超 token 费**——选型时必须单独建模，不能只看 $/1M。

**独特优势**：effort 粒度全行业最细（none→max 六档），加上 `mode: pro` 和 `text.verbosity` 两个正交开关；Responses API 把 web_search / file_search / code_interpreter / computer_use / MCP 做成一等公民，服务端编排，客户端不用写工具循环。
**硬伤**：
1. 长上下文悬崖在 272K，且**整次请求**加价（输入 2x、输出 1.5x），不是只对超出部分——Sol 超 272K 后等价于 $8/$30。
2. web_search 结果上限约 128K token（第三方口径，需实测核验）。
3. **中国大陆访问 api.openai.com 不可靠**，需要境外中转；美元结算，无人民币发票。
4. 搜索索引以英文公开网页为主，中文内容生态（公众号、知乎、小红书）覆盖显著弱于国内引擎。

**适用场景**：英文/海外信息源的检索与分析；需要精细调节推理深度的任务；Luna + Batch 的极低成本高吞吐批处理；已经在 OpenAI 生态里的产品。

### Anthropic Claude

**型号分层**：Fable 5（$10/$50，最难推理）→ Opus 5（$5/$25，复杂 agentic coding）→ Sonnet 5（$2/$10 促销，生产主力）→ Haiku 4.5（$1/$5，分类路由）。Mythos 5 受限供应。

**独特优势**：软件工程修复能力突出——Fable 5 在 SWE-Bench Pro 上 80.0%，明显高于 GPT-5.6 Sol 的 64.6%。interleaved thinking（工具调用间逐步推理）对多步 agent 工作流可靠性提升明显。
**硬伤**：Sonnet 5 的 `max` 档缺失（到不了 L4）；Sonnet 5 新 tokenizer 对相同文本约多产出 30% token，标价比较会失真。
**适用场景**：高难度软件工程、长周期 agent、需要深度代码审查的场合。

### Google Gemini 3.x

**型号分层**：Gemini 3.1 Pro（$2/$12，难推理与多文档综合）→ 3.6 Flash / 3.5 Flash（$1.5/$7.5，agent 工具循环，Google 的新默认）→ 3.5 Flash-Lite（$0.30/$2.50）/ 3.1 Flash-Lite（$0.25/$1.50，批量）→ Nano（端侧）。

**独特优势**：全系 1M 上下文；多模态（文本/图像/音频/视频/PDF）覆盖最全；Flash-Lite 吞吐约 380 tok/s；GPQA Diamond 上 Gemini 3.1 Pro 达 94.3。
**硬伤**：**Pro 系思考关不掉**（无 `minimal`），批量抽取类任务会被迫烧推理 token；3.1 Pro 超 200K 价格翻倍。
**适用场景**：长上下文综合、多模态输入、高 QPS 批量处理（用 Flash-Lite + `minimal`）。

### DeepSeek V4

> **2026-08-30 核验更新**：旧版"¥1/¥2、¥3/¥6"的单一价格已废弃，官方改为**高峰/空闲双轨制**。

**当前官方价格**（人民币/百万 token，高峰=工作日 9:00–12:00、14:00–18:00 北京时间，其余为空闲）：

| | 输入（缓存未命中） | 输入（缓存命中） | 输出 |
|---|---|---|---|
| v4-flash 高峰 | ¥3.0 | ¥0.10 | ¥9.0 |
| v4-flash 空闲 | ¥1.5 | ¥0.05 | ¥4.5 |
| v4-pro 高峰 | ¥9.0 | ¥0.30 | ¥27 |
| v4-pro 空闲 | ¥4.5 | ¥0.15 | ¥13.5 |

**思考可控性（旧版描述有误，已修正）**：V4 **可以关闭思考**——`extra_body={"thinking": {"type": "disabled"}}`。默认是开的且 effort 默认 `high`。
**effort 档位**：`reasoning_effort` 只有 `low` / `high` / `max` 三档，**没有 medium**（medium 映射为 high，xhigh 也映射为 high）。即 L1 与 L2 在 DeepSeek 上无法区分。

**硬伤**：官方 API **无原生联网搜索/网页抓取工具**（检索类任务要自建管线，或借道百炼平台）；带 `tools` 参数时必须完整回传历史 `reasoning_content`，否则返回 400；旧端点 `deepseek-chat`/`deepseek-reasoner` 已退役。
**适用场景**：已有抓取管线、只需要模型做批量抽取/分类/清洗的场景；离线任务排到非高峰时段可再省一半。

### 通义千问 Qwen 3.7 / 3.8（阿里云百炼）

> **2026-08-30 核验更新**：3.8-Max 已上线，且百炼提供原生联网/抓取工具——这是检索类选型的关键差异点，旧版完全没提。

**在售主力**（中国内地，人民币/百万 token）：

| 型号 | 输入 | 输出 | 上下文 | 备注 |
|---|---|---|---|---|
| **qwen3.8-max** | ¥12 | ¥36 | 1M | 原价无折扣，Batch 半价，effort 三档 |
| **qwen3.7-max** | ¥6（原价12，限时5折） | ¥18（原价36） | 1M | 5 折期性价比最高的一档 |
| **qwen3.7-plus** | ¥1.6（原价2，限时8折） | ¥6.4（原价8） | ≤256K | 256K–1M 涨到 ¥4.8/¥19.2（8折） |
| qwen3.6-plus | ¥2.4 | ¥14.4 | ≤256K | 256K–1M → ¥9.6/¥57.6 |

**原生工具能力（独占优势）**：百炼 Responses API 提供 **`web_search`（联网搜索）+ `web_extractor`（网页抓取）+ `code_interpreter`**，直接解决"检索—抓取—理解"全链路，不用自建爬虫管线。支持这些工具的模型：Qwen3.8/3.7 全系、deepseek-v4-flash/pro、glm-5.2。
- ⚠️ 约束：**启用 web_search / web_extractor 时必须 `enable_thinking=True`**，思考关不掉。检索阶段会被迫烧思考 token，这是隐形成本。
- 另有独立收费的**联网搜索 MCP**（`https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp`），前 2000 次免费，之后 ¥29/千次。

**思考可控性**：国产里唯一的"`enable_thinking` 布尔开关 + `thinking_budget` 数值预算 + `reasoning_effort` 档位"三重组合，且**默认关闭**。
- qwen3.8-max 的 `reasoning_effort` 取值：`xhigh`（默认）/ `medium` / `low`；也可改用 `thinking_budget`（默认 131072）。
- ⚠️ **`reasoning_effort` 与 `thinking_budget` 不能同时传，会报错**。二选一。互转规则：low↔4096、medium↔16384、xhigh↔262144。
- ⚠️ 不显式设置时 3.8-max 默认 `xhigh` + budget 131072，**是最贵档**。L0 任务必须显式 `enable_thinking=False`。

**硬伤**：3.7-max 的 5 折、3.7-plus 的 8 折都是限时活动，到期后成本跳涨；无明显 L4 档。
**适用场景**：中文长文、知识库 RAG、需要联网检索的任务、国内合规刚需。

### 月之暗面 Kimi K3

> **2026-08-30 核验更新**：effort 不是 on/off，价格与联网状态也已变化。

**kimi-k3**：¥2（缓存命中）/ ¥20（输入）/ **¥100（输出）** 每百万 token，1M 上下文，2.8 万亿参数，原生视觉理解。
**kimi-k2.6**：¥1.10 / ¥6.5 / ¥27，256K，支持思考与非思考模式。
**kimi-k2.7-code / -highspeed**：¥1.30 / ¥6.5 / ¥27，256K。

**effort（旧版描述有误，已修正）**：K3 **始终推理**，通过顶层 `reasoning_effort` 控制，取值 `low` / `high` / `max`，**默认 max**——不显式设置就是在用最贵档。

**硬伤（新增，很重要）**：
1. **官方定价页明确标注：联网搜索（web_search）正在更新升级中，近期不建议使用**。所有依赖实时检索的任务（素材收集、调研、舆情）当前不要挂 Kimi。
2. **输出 ¥100/百万 token**，是 Qwen3.7-Max 输出价（5折 ¥18）的 5.6 倍。输出密集的选题/写作类任务成本会失控。
3. `kimi-k2.5` 与 `moonshot-v1` 系列**已于 2026-08-31 下线**，`kimi-k2` 系列 2026-05-25 已下线。
**适用场景**：长文本理解、长程软件工程、编程 agent。**不适合**：联网检索密集任务、输出量大的生成任务。

### 智谱 GLM-5.3（2026-08 发布）

¥8/¥28，缓存命中 ¥2，1M 上下文 / 128K 输出。开源权重。**注意：阿里云百炼代售版与 Z.ai 原厂版能力不同**（见下）。

**独特优势**：
- **开源可私有化部署**，有数据不出内网要求时的首选。
- 原厂版（Z.ai / api.z.ai）的 `tool_web_search` 支持 **`search_domain_filter`（限定搜索域名）** 和 **`search_recency_filter`（限定时间窗）**——这是全行业独一份的精准检索能力，适合"只搜巨潮资讯网 / 交易所 / 特定行业站"这类定向情报收集。
- 搜索便宜：约 $0.01–0.033 / 次（不同渠道口径不一，需实测）。

**硬伤**：
1. **始终推理，思考关不掉**，`reasoning_effort` 只有 low/high/max 且**默认 max**——不显式设置就在烧最贵档，长任务成本明显高于标价。
2. **阿里云百炼上架的 GLM-5.3 明确标注"联网搜索：不支持"**，也没有批量推理。要联网能力必须走 Z.ai 原厂。这点极易踩坑。

**适用场景**：私有化部署刚需、合规要求不能出境、需要限定域名的定向检索；不适合需要"关思考省成本"的批量任务。

### 腾讯混元 Hy3（2026-07 发布）

`hy3`（正式版）与 `hy3-preview`，295B 总参 / 21B 激活 MoE，256K 上下文 / 192K 输入 / 128K 输出。Apache 2.0 开源可自部署。

**价格 ¥1/¥4，缓存命中 ¥0.25** —— 国产价格地板，比 DeepSeek 空闲档还便宜 4 倍多。另有 `hunyuan-lite` **免费**。（⚠️ 第三方来源有 $0.066/$0.26 ≈ ¥0.48/¥1.88 的口径，与国内 ¥1/¥4 差约一倍，预算测算前需回官方控制台核验。）

**接入方式（两套端点并存，容易混淆）**：
- **TokenHub**：`https://tokenhub.tencentmaas.com/v1` — OpenAI Chat Completions / Responses / Anthropic Messages **三协议全兼容**，**一个 API Key 访问平台上架的全部模型**（Hy3 自研 + DeepSeek-V4-Pro/Flash、GLM-5.1、Kimi-K2.6、MiniMax-M2.7）。**跨厂家对拍时这是最省事的接入方式。**
- 混元自有端点：`https://api.hunyuan.cloud.tencent.com/v1`。
- 腾讯云 ES 的 `ChatCompletions`（`es.ai.tencentcloudapi.com`）是**另一套旧接口**，PascalCase 参数，带 `OnlineSearch` / `Citation`（引用角标）/ `ForceSearchEnhancement` 等搜索增强开关，但模型列表较老。

**独特优势**：价格地板 + TokenHub 一键跨厂家 + 中文语料（腾讯生态）。`hy3-preview` 支持交错式思考、结构化输出、Function Calling、Cache 缓存，定位 agent 工作负载。
**硬伤**：**上下文只有 256K**，是几家里最窄的——一份 A 股年报 PDF 就约 130K–200K token，装不下"年报 + 多份研报 + 公告"的组合，必须做分层压缩。另外 `hy3` 的联网搜索参数在 OpenAI 兼容端点上未见文档，**需实测核验**。
**适用场景**：大批量分层摘要、格式规整、成本敏感的长文本预处理；不适合做最终综合研判（上下文不够）。

### 火山引擎豆包 Seed 2.1

Pro ¥6/¥30，Turbo ¥3/¥15（低延迟版）。

**独特优势**：低延迟；国内接入与支付环境顺。
**硬伤**：思考按 model ID 分变体，无运行时参数，自动路由时容易误切。
**适用场景**：国内实时交互、对延迟敏感的业务。

### xAI Grok 4.5 / 4.3

Grok 4.5 $2/$6（输出价只有 Terra 的一半），Terminal Bench 2.1 达 83.3。Grok 4.3 $1.25/$2.50，1M 上下文。

**独特优势**：输出单价低，对输出密集的任务（长文生成）成本优势明显。
**硬伤**：超 200K 后输入/缓存/输出价格大致翻倍。
**适用场景**：输出量大、输入量可控的生成类任务。

## 三、单次任务成本排序

统一口径：10 万输入 + 2 万输出，无缓存、无工具、不触发长上下文阶梯，美元按 1:6.8 折算。

| 排名 | 模型 | 单次成本 |
|---|---|---|
| 1 | DeepSeek V4 Flash | ¥0.14 |
| 2 | Qwen 3.7 Plus | ¥0.29 |
| 3 | GPT-5.6 Luna | ¥0.30 |
| 4 | MiniMax M3 | ¥0.37 |
| 5 | Gemini 3.1 Flash-Lite | ¥0.37 |
| 6 | DeepSeek V4 Pro | ¥0.42 |
| 7 | Gemini 3.5 Flash-Lite | ¥0.54 |
| 8 | 豆包 Seed 2.1 Turbo | ¥0.60 |
| 9 | Qwen 3.7 Max | ¥0.96 |
| 10 | Grok 4.3 | ¥1.19 |
| 11 | Claude Haiku 4.5 | ¥1.36 |
| 12 | GLM-5.2 | ¥1.36 |
| 13 | Gemini 3.6 Flash | ¥2.04 |
| 14 | Grok 4.5 | ¥2.18 |
| 15 | Claude Sonnet 5 | ¥2.72 |
| 16 | GPT-5.6 Terra | ¥2.99 |
| 17 | Kimi K3 | ¥4.08 |
| 18 | Claude Opus 5 | ¥6.80 |
| 19 | GPT-5.6 Sol | ¥7.48 |
| 20 | Claude Fable 5 | ¥13.60 |

**读法**：最贵与最便宜差约 **97 倍**。但便宜 ≠ 划算——弱模型需要三次重试或更大 few-shot 时，总成本可能反超。这是"每次任务成本"与"每 token 单价"的区别。

## 四、硬约束过滤矩阵

| 约束 | 可选厂家 |
|---|---|
| **数据不能出境 / 政务金融国企** | DeepSeek、Qwen、GLM、Kimi、豆包、MiniMax |
| **必须私有化部署** | GLM（MIT 开源权重）、DeepSeek（开源）、Qwen（部分开源） |
| **上下文 > 800K** | Gemini 3.x（1M）、Claude Opus/Sonnet（1M）、DeepSeek V4（1M）、Kimi K3（1M）、Qwen3.7（1M）、GPT-5.6（1.05M） |
| **多模态输入（图像/音频/视频）** | Gemini 3.x、GPT-5.6、Claude、Qwen3-VL/Omni、GLM-4.6V |
| **需要 L4 极限推理** | OpenAI（xhigh/max）、Anthropic Opus/Fable/Mythos 系 |
| **需要精细调节推理深度** | OpenAI（6 档）、Anthropic（4 档）、Gemini（4 档）、Qwen（布尔+预算） |
| **人民币结算** | DeepSeek、Qwen、GLM、豆包、MiniMax |

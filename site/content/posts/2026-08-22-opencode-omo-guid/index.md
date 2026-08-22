---
title: OpenCode 加 OMO 上手记，把我在自己机器上踩过的疑惑一次讲清
date: 2026-08-22
summary: 基于本机实际验证，逐一拆解 OpenCode 与 Oh My OpenAgent 的安装配置、agent 体系、ulw 关键词与 LSP 接管等常见疑惑。
tags: [OpenCode, AI, 编程工具]
---

我在这台 Mac 上装了 OpenCode 1.18.21 和 Oh My OpenAgent 4.19.4（下面都叫 OMO），用了几天，攒下一堆疑惑。在 TUI 里敲 `/agents`，只看到四个选项，网上文章说的 Oracle、Librarian 一个都没出现。右侧状态栏写着 LSPs are disabled，我以为语言服务坏了。听说有个 ultrawork 模式，翻遍命令面板找不到 `/ulw`。想改插件配置，照旧教程去编辑 `~/.config/opencode/oh-my-openagent.jsonc`，发现文件根本不存在。

这篇文章就是把这几个疑惑逐个拆开。答案全部来自我这台机器，查过 OMO 打包后的源码 `dist/index.js`，跑过它自带的 doctor 和 CLI，版本就是上面那两个。OMO 迭代很快，配置路径在 4.x 里搬过一次家，如果你用的版本更新，先跑一遍 `bunx oh-my-openagent doctor` 再对照本文。

## OpenCode 和 OMO 各是什么

OpenCode 是一个跑在终端里的 AI 编程助手，开源，不绑定任何模型厂商。你在里面接 OpenAI、Anthropic、Google 或者国产模型的 key，它负责读文件、改代码、跑命令这些底座能力。安装包名 `opencode-ai`，仓库在 anomalyco/opencode。

OMO 是装在 OpenCode 上的一个插件，npm 包名 oh-my-openagent。它做的事用作者自己在 README 里的比喻最准确，OpenCode 是 Debian，OMO 是开箱即用的 Ubuntu。你在 OpenCode 的配置里注册这个插件，它就会接管 agent 体系、塞进十几个专门调优过的角色、自带 LSP 工具和一批工作流技能。

为什么有人要做这么一层。作者的原始动机写在 README 里，他为了做个人项目烧掉了两万四千美元的 API token，把市面上每个号称好用的编程 agent 都试了一遍，最后把自己踩坑的解法硬编码进了这个插件。其中一个例子是文件编辑，OMO 给每行代码附上内容哈希，agent 改代码前必须先校验哈希，文件变了就拒绝落笔。README 里给的数据是同一个模型 Grok Code Fast 1 换上这套编辑工具后，修改成功率从 6.7% 涨到 68.3%。这是作者自己的数字，我没办法复核，但机制本身在源码里确实存在。

安装顺序永远先是 OpenCode，再是 OMO，因为后者是前者的插件。

## 安装

OpenCode 官方给三种装法，任选其一。

```bash
curl -fsSL https://opencode.ai/install | bash
```

```bash
brew install anomalyco/tap/opencode
```

```bash
npm install -g opencode-ai
```

装完先登录模型，凭据存在 `~/.local/share/opencode/auth.json`。

```bash
opencode auth login
```

然后装 OMO。

```bash
bunx oh-my-openagent install
```

安装器是交互式的，会问你有哪些订阅，Claude、OpenAI、Gemini、Copilot、Kimi、智谱、百炼、MiniMax 都列在里面，照实勾选就行，它会按可用性排好模型优先级。这里有个容易迷惑的点，OMO 正在从旧包名 oh-my-opencode 过渡到新名 oh-my-openagent，`bunx oh-my-openagent --help` 打出来的用法行里写的还是 oh-my-opencode。功能没区别，别被吓到。

装完跑自检。

```bash
bunx oh-my-openagent doctor
```

我机器上的输出是 `✓ System OK (opencode 1.18.21 · oh-my-openagent 4.19.4)`。看到 System OK 就可以进 TUI 了。

OMO 默认开启匿名遥测，统计活跃安装数，每台机器每个 UTC 日发一次哈希化标识。介意的话设环境变量 `OMO_SEND_ANONYMOUS_TELEMETRY=0` 关掉。

## 两份配置文件，管两件不同的事

第一份是 OpenCode 自己的配置，`~/.config/opencode/opencode.json`。OMO 在这里的痕迹只有一个 plugin 数组。

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "你的默认模型",
  "plugin": ["oh-my-openagent@latest"]
}
```

你的默认模型、MCP 服务器、权限规则也都写在这份里，这是 OpenCode 的地盘。

第二份是 OMO 的统一配置，`~/.omo/omo.jsonc`。这就是前面疑惑的答案，旧教程让你编辑的 `~/.config/opencode/oh-my-openagent.jsonc` 是老版本的路径，4.x 已经搬走。我机器上 `~/.omo/` 目录里躺着迁移备份文件夹，名字里带着日期，说明升级时它自己动过一次迁移。

如果你手里还有旧配置想搬过来，OMO 提供了迁移命令，先空跑预览，确认无误再去掉 `--dry-run` 真跑。

```bash
bunx oh-my-openagent config migrate --dry-run
bunx oh-my-openagent config migrate
```

统一配置里最常改的是 agent 和模型映射。下面是我机器上的实际内容，去掉了私有信息，可以直接当模板。每个 agent 配什么模型、开多高强度的推理，都在 `[opencode].agents` 里改。JSONC 支持注释和尾逗号。

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-openagent/dev/assets/omo.schema.json",
  "[opencode]": {
    "agents": {
      "sisyphus": { "model": "zhipuai-coding-plan/glm-5.2" },
      "hephaestus": { "model": "openai/gpt-5.6-sol", "reasoning": "medium" },
      "prometheus": { "model": "zhipuai-coding-plan/glm-5.2" },
      "oracle": { "model": "openai/gpt-5.6-sol", "reasoning": "high" },
      "librarian": { "model": "openai/gpt-5.6-luna-fast", "reasoning": "low" },
      "explore": { "model": "alibaba-token-plan-cn/deepseek-v4-flash-0731" },
      "multimodal-looker": { "model": "alibaba-token-plan-cn/qwen3.6-flash" },
      "metis": { "model": "openai/gpt-5.6-sol", "reasoning": "high" },
      "momus": { "model": "openai/gpt-5.6-terra", "reasoning": "high" },
      "atlas": { "model": "openai/gpt-5.6-sol", "reasoning": "medium" },
      "sisyphus-junior": { "model": "openai/gpt-5.6-sol", "reasoning": "medium" }
    },
    "categories": {
      "visual-engineering": { "model": "zhipuai-coding-plan/glm-5.3" },
      "ultrabrain": { "model": "openai/gpt-5.6-sol", "reasoning": "xhigh" },
      "quick": { "model": "alibaba-token-plan-cn/qwen3.6-flash", "reasoning": "low" }
    }
  }
}
```

配置经验只有一条，贵的模型放在需要它的位置上。推理强度 high 给 Oracle 和 Metis 这种顾问角色，deepseek 和 qwen 的 flash 系给检索和杂活，主 agent 用你订阅里额度最充裕的那个。改完任何一份配置都要重启 OpenCode 才生效，配置只在启动时读一次。

## 四个可选 agent，七个内部 agent

回到第一个疑惑，`/agents` 只显示四个。这是设计好的，OMO 把 agent 分成了两类。

primary 模式的 agent 会出现在 `/agents` 选择列表里，你可以随时切过去跟它对话，当前会话的上下文保留，但系统提示词、模型、工具权限整套换掉。源码里写死的顺序就是这四个。

| 名字 | 角色 | 我机器上的模型 |
|---|---|---|
| Sisyphus | 主编排，接需求后派活给专家，验证后交付 | glm-5.2 |
| Hephaestus | 深度执行，给目标就闷头干完，适合大块自主实现 | gpt-5.6-sol medium |
| Prometheus | 规划，访谈你的需求后产出工作计划 | glm-5.2 |
| Atlas | 计划执行，拿着写好的计划文件逐项落实 | gpt-5.6-sol medium |

subagent 模式的 agent 不进选择列表，只有主 agent 通过内部派单调用它们，你在界面上看不到对话过程。这就是为什么你在 `/agents` 里找不到 Oracle。想看全量列表有个命令行办法，`opencode agent list` 会把十七个条目全列出来，包括 OpenCode 原生但被 OMO 降级隐藏的 build 和 plan。

| 名字 | 干什么 | 什么时候你会感知到它 |
|---|---|---|
| Oracle | 高强度推理顾问，架构取舍、疑难调试 | 你说"这问题修了两次没修好"之后 |
| Librarian | 查官方文档和外部代码库 | 用到不熟的库时 |
| Explore | 代码库内快速检索 | 你问"这个函数在哪定义"时 |
| Multimodal Looker | 看图、看 PDF、看截图 | 你丢一张报错截图过去时 |
| Metis | 计划顾问，审计划里的矛盾和缺口 | 走规划流程时自动出场 |
| Momus | 计划批评家，专挑不完整和不可验证 | 同上，且以苛刻著称 |
| Sisyphus-Junior | 受控执行者，接编排 agent 的分类任务 | 每次派单都在用 |

顺带纠正一个我自己犯过的错。我先前跟人说 Prometheus 有 edit deny 的权限硬锁，物理上改不了代码。查了 4.19.4 的源码，它的运行时权限对象其实四项全开，edit、bash、webfetch、question 都是 allow。它不写产品代码的约束写在系统提示词里，原话是 You create plans. You do not implement.。这是提示词层面的纪律，加上了源码里对规划 agent 过滤执行类关键词的机制，但确实没有权限级的硬锁。这类细节以后以 doctor 和源码为准。

## 类别是路由标签，又一批容易认成 agent 的东西

配置里那串 categories，visual-engineering、ultrabrain、deep、quick 这些，经常被当成 agent 理解。它们其实是派单时的路由标签。Sisyphus 给子任务标注"这是个前端活"或"这是个改错字的杂活"，框架按标签查 categories 配置，找到对应模型去执行。标签决定用哪个模型干，agent 决定以什么人格和工具面干，两套东西正交。

标签里值得记的就两个。ultrabrain 走最强推理配置，留给硬逻辑和架构。quick 走便宜快的 flash 模型，改错字、单文件小修走这条道，省钱。其他标签名字见义即可。

## ulw 是关键词，不是命令

第三个疑惑的答案最反直觉。ulw 和 ultrawork 触发的执行模式，靠 OMO 的关键词检测器实现。它在源码里的正则是 `/\b(ultrawork|ulw)\b/i`，扫每条用户消息，命中就在对话里注入一大段执行纪律指令，强制先写失败测试再实现、强制拿证据交付、禁止"简化版"收工。

所以你在命令面板里永远找不到 `/ulw`。更讽刺的是，检测器会跳过以斜杠开头的消息，你真敲 `/ulw` 反而不触发。正确用法是在普通消息里自然带上这个词，比如"ulw 帮我重构这个模块并补测试"。

这个模式有成本，TDD、证据链、todo 跟踪全套拉满，改一行配置文件的小事用它纯属浪费。反过来，有明确验收标准的编码任务用它很值。哪天嫌关键词检测烦，可以在 `~/.omo/omo.jsonc` 里加一行配置关掉，`disabled_keywords` 数组接受 ultrawork、team、hyperplan、hyperplan-ultrawork 四个值。

ulw-plan 和 ulw-research 又高一层的抽象，它们是技能。技能是装在 OMO 包里的一沓说明书，主 agent 判断任务匹配时加载它，按里面的剧本走。ulw-plan 的剧本是探索代码库、只问材料解决不了的取舍问题、等你点头后写一份执行者零提问的工作计划到 `.omo/plans/` 下。ulw-research 的剧本是并行派一堆检索 agent 扫代码库、文档和网络，交叉验证后出带引用的报告。

技能和切换 agent 的关系，我用一句话记。顺手规划用技能，严肃立项用 Prometheus。对话中途想先理清思路，直接说"ulw plan 一下这个功能"，当前 agent 加载技能原地变身，上下文全保留。全新的大任务想从头按规划人格走，就切到 Prometheus，它是独立的提示词和模型。两条路产出的计划文件格式一致，下游执行不区分计划是谁写的。

技能在 `/skills` 菜单里的显示情况要分开说。OpenCode 原生技能体系扫 `~/.claude/skills` 和 `~/.agents/skills` 这些目录，你装过的 aihot、dashi-ppt 都会出现。OMO 的共享技能走插件自己的注册通道，进 agent 侧的技能表，我在 TUI 的技能浏览菜单里没看到它们，但这属于 4.19.4 的实现细节，OMO 的合并逻辑每一版都在动。稳妥的判断方式，界面上找不到就对 agent 说技能名，它能加载就是可用。

## 右侧栏的 LSP 提示，一个善意的误会

TUI 右侧栏写 LSPs are disabled，指的只是 OpenCode 原生 LSP 子系统没启动。OMO 在配置迁移阶段会显式删掉原生 lsp 配置，然后用自己的 LSP 守护进程接管，以 MCP 工具的形式提供 lsp_diagnostics、goto definition、find references、rename 这一整套。

我在自己机器上验证的结果，LSP 状态查询显示 42 个 server 已配置，4 个已装好，basedpyright、clangd、sourcekit-lsp、dart，agent 调用诊断和跳转定义全部正常工作。进程列表里能看到 oh-my-openagent 的 lsp-daemon 活着。

所以侧栏那行字翻译过来就是，原生面板没数据，因为活被 OMO 接走了。对 agent 能力零影响。真要在意的话，检查你主力语言对应的 server 装没装，比如常写 TypeScript 的话把 typescript server 装上，对诊断覆盖有实际收益。这个行为绑定 OpenCode 1.18.21 加 OMO 4.19.4，两个任意一方升级都可能变。

## 什么时候用什么

把前面所有机制压成一张决策表。我的习惯是默认留在 Sisyphus，特殊需求才动。

| 场景 | 动作 |
|---|---|
| 改错字、单文件小修 | 留在 Sisyphus，别带 ulw 词 |
| 有验收标准的中型编码任务 | 消息里带 ulw，吃执行纪律 |
| 大块自主实现，想撒手不管 | 切 Hephaestus，给目标不给步骤 |
| 复杂任务想先想清楚 | 说"ulw plan"，或切 Prometheus |
| 计划已批，逐项落实 | 切 Atlas 或用 start-work 流程 |
| 疑难 bug 修了两轮没好 | 留在 Sisyphus，明说让 Oracle 会诊 |
| 用到不熟的库 | 直接问，Librarian 自动出场 |
| 开放课题要深度调研 | 说"ulw-research 研究一下 XX" |

## 装完后的自查清单

一套五分钟走完的验证，全部通过说明装好了。

```bash
opencode --version
bunx oh-my-openagent --version
bunx oh-my-openagent doctor
opencode agent list
```

然后进 TUI 做两件事。敲 `/agents`，应看到恰好四个 primary 选项，Sisyphus、Hephaestus、Prometheus、Atlas。随便发一条消息让 agent 读一个代码文件再问诊断，能返回结果说明 LSP 链路通。最后确认 `~/.omo/omo.jsonc` 存在且 agent 映射是你想要的模型。全部通过，就可以放心用了。

## 来源

- OpenCode 官方文档，https://opencode.ai/docs/
- OpenCode 仓库，https://github.com/anomalyco/opencode
- OMO 仓库与中文 README，https://github.com/code-yeongyu/oh-my-openagent
- OMO 安装指南，https://github.com/code-yeongyu/oh-my-openagent/blob/dev/docs/guide/installation.md
- 本机核验材料，OMO 4.19.4 打包产物 `dist/index.js`、`~/.omo/omo.jsonc`、`opencode agent list` 与 `bunx oh-my-openagent doctor` 输出

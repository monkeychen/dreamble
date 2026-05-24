---
name: skill-kit
description: 管理 AI 编程 Agent（Claude Code、Gemini CLI、Codex）的 skill 安装、卸载与查看。当用户想要安装 skill、添加技能、部署插件、卸载/移除/删除/清除已安装的 skill、或查看/列出已安装了哪些 skill 时触发。支持本地路径和 git URL，使用复选框交互选择目标 agent 和 skill，统一使用软链接安装，操作前展示计划并等待用户确认。
---

# Agent Skill 管理

帮助用户安装、卸载或查看 AI agent 的 skill，统一通过软链接管理，源文件始终保留。

## 各 Agent 的 Skills 标准目录

| Agent | Skills 目录 |
|-------|------------|
| Claude Code | `~/.claude/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| Codex | `~/.codex/skills/` |

## 判断操作模式

首先判断用户意图：
- **安装**：提到"安装"、"添加"、"部署"、给出路径或 URL → 进入安装流程
- **卸载**：提到"卸载"、"移除"、"删除"、"remove"、"uninstall"、"取消安装"、"清除" → 进入卸载流程
- **更新**：提到"更新"、"update"、"pull"、"升级" → 进入更新流程
- **查看**：提到"查看"、"列出"、"list"、"已安装"、"有哪些" → 进入查看流程

用户在请求中已说明的信息（agent 名称、skill 名称、路径）直接采用，不重复询问。

---

## 查看流程

扫描三个标准 agent 目录，列出其中所有软链接：

```bash
for dir in ~/.claude/skills ~/.gemini/skills ~/.codex/skills; do
  echo "=== $dir ==="
  find "$dir" -maxdepth 1 -type l -exec basename {} \; 2>/dev/null || echo "(空)"
done
```

以表格形式展示结果，列出每个 skill 在哪些 agent 中已安装。示例：

```
已安装的 Skill：

Skill 名称              Claude Code  Gemini CLI  Codex
─────────────────────────────────────────────────────
liubei                  ✓            ✓           —
skill-kit               ✓            —           —
anything-to-notebooklm  ✓            ✓           —
```

---

## 安装流程

### 第一步：收集信息

向用户确认两件事（用户已在请求中说明的直接采用，不用再问）：

1. **Skill 来源**：本地路径或 git 仓库 URL。

2. **安装目标 Agent**：使用 `AskUserQuestion` 工具，以复选框形式让用户选择，`multiSelect: true`：

   ```
   question: "要安装到哪些 Agent？"
   header: "目标 Agent"
   multiSelect: true
   options:
     - label: "Claude Code",  description: "~/.claude/skills/"
     - label: "Gemini CLI",   description: "~/.gemini/skills/"
     - label: "Codex",        description: "~/.codex/skills/"
     - label: "自定义路径",    description: "安装到其他 Agent 的 skills 目录（勾选后会追问路径）"
   ```

   注意：复选框无预选状态，用户需主动勾选目标 agent。勾选"自定义路径"后，用文字追问输入完整目录路径（支持多个，换行或逗号分隔）。

### 第二步：获取 Skill 源码

**如果是本地路径**：直接使用该路径，跳到第三步。

**如果是 git URL**：从 URL 最后一段提取仓库名（去掉 `.git` 后缀），克隆到 `~/workspace/ai/`：

```bash
mkdir -p ~/workspace/ai
git clone <URL> ~/workspace/ai/<仓库名>
```

- 若目标目录已存在，告知用户并询问：是否 `git pull` 更新现有目录，或指定其他目标路径？
- 克隆完成后，目标目录为 `~/workspace/ai/<仓库名>`，继续第三步。

### 第三步：判断目录类型

同时检测根目录和子目录：

```bash
# 根目录是否有 SKILL.md
ls <目录>/SKILL.md 2>/dev/null

# 子目录中有多少个 SKILL.md
find <目录> -mindepth 2 -maxdepth 2 -name "SKILL.md" | xargs -I{} dirname {}
```

**情况 A — 单一 Skill**：根目录有 `SKILL.md`，且子目录中**没有** `SKILL.md`。整个目录作为安装目标，进入第四步。

**情况 B — Skill 集合**：根目录**无** `SKILL.md`，子目录有多个 `SKILL.md`。让用户从子 skill 中选择。

**情况 C — 根目录有 SKILL.md，子目录也有 SKILL.md**（集合型仓库根目录放了说明文件）：
- 使用 `AskUserQuestion` 询问安装范围，`multiSelect: false`：
  ```
  question: "检测到根目录和子目录都有 SKILL.md，请选择安装方式"
  header: "安装范围"
  options:
    - label: "安装整个集合（根目录作为一个 skill）"
      description: "将 <目录名> 整体安装为一个 skill"
    - label: "从子 skill 中选择"
      description: "扫描子目录，逐一选择要安装的 skill"
  ```
- 用户选"安装整个集合"→ 同情况 A；选"从子 skill 中选择"→ 同情况 B。

**情况 B / C 子 skill 选择**，用 `AskUserQuestion` 复选框，`multiSelect: true`：
```
question: "选择要安装的 Skill"
header: "选择 Skill"
multiSelect: true
options:
  - label: "<skill目录名>", description: "<绝对路径>"
  - label: "<skill目录名>", description: "<绝对路径>"
  ...（每个子 skill 一个 option）
```
等用户选择后，进入第四步。

### 第四步：生成安装计划

整理安装信息展示给用户：

```
准备安装以下 Skill：

Skill 来源：<绝对路径>
Skill 名称：<目录名>

安装目标：
  ✓ Claude Code   → /Users/xxx/.claude/skills/<skill名>  → <绝对路径>
  ✓ Gemini CLI    → /Users/xxx/.gemini/skills/<skill名>   → <绝对路径>
  ⚠️ Codex        → /Users/xxx/.codex/skills/<skill名>    → 已存在
  ✓ 自定义路径     → /custom/path/skills/<skill名>        → <绝对路径>

执行命令（新目标）：
  ln -s <绝对路径> /Users/xxx/.claude/skills/<skill名>
  ln -s <绝对路径> /Users/xxx/.gemini/skills/<skill名>
  ln -s <绝对路径> /custom/path/skills/<skill名>

确认执行？(y/n)
```

如果有 ⚠️ 已存在的目标，在确认问题下方**单独**追加一行询问：

```
⚠️ Codex 下已存在同名链接，是否覆盖？(y=覆盖 / n=跳过)
```

用户需分别回答两个问题：第一个确认执行新目标，第二个决定是否覆盖已存在目标。若所有目标都已存在（无新目标可安装），则只问覆盖确认，不展示空的"执行命令"块。

**注意**：
- 只列出用户选择的 agent，未选择的不出现。
- 始终使用展开后的绝对路径（`~` → `/Users/xxx`），避免软链接失效。

### 第五步：用户确认后执行

```bash
mkdir -p <目标 skills 目录>   # 目录不存在时先创建
ln -s <绝对路径> <目标路径>
```

执行完成后，逐行输出每个链接的创建结果。

## 安装常见情况处理

**链接已存在**：在安装计划展示后，单独询问是否覆盖（`ln -sf`），不要把覆盖选项藏在计划文本里。

**本地路径不存在**：报错并请用户检查路径。

**git clone 失败**：显示错误信息，请用户确认 URL 和网络。

**自定义目标目录不存在**：询问是否自动创建（`mkdir -p`），确认后创建再安装。

---

## 卸载流程

卸载只删除软链接，源文件目录始终保留。

### 第一步：选择从哪些 Agent 卸载

使用 `AskUserQuestion` 复选框，`multiSelect: true`：

```
question: "从哪些 Agent 卸载？"
header: "目标 Agent"
multiSelect: true
options:
  - label: "Claude Code",  description: "~/.claude/skills/"
  - label: "Gemini CLI",   description: "~/.gemini/skills/"
  - label: "Codex",        description: "~/.codex/skills/"
  - label: "自定义路径",    description: "其他 Agent 的 skills 目录（勾选后会追问路径）"
```

勾选"自定义路径"后，用文字追问输入目录路径。

注意：`AskUserQuestion` 的 options 至少需要 2 项，追问自定义路径时不能用单选项的 AskUserQuestion，应直接用文字提问让用户输入路径。

### 第二步：扫描已安装的 Skill 并让用户选择

扫描选定的所有 agent 目录，列出软链接（跳过非软链接条目）：

```bash
find <skills目录> -maxdepth 1 -type l -exec basename {} \;
```

将各 agent 中找到的 skill 合并去重，用 `AskUserQuestion` 复选框展示，`multiSelect: true`：

```
question: "选择要卸载的 Skill"
header: "选择 Skill"
multiSelect: true
options:
  - label: "liubei",                  description: "存在于: Claude Code, Gemini CLI"
  - label: "skill-kit",               description: "存在于: Claude Code"
  - label: "anything-to-notebooklm",  description: "存在于: Claude Code, Gemini CLI"
```

### 第三步：展示卸载计划并确认

```
准备卸载以下 Skill：

  ✓ liubei   → /Users/xxx/.claude/skills/liubei
  ✓ liubei   → /Users/xxx/.gemini/skills/liubei

执行命令：
  rm /Users/xxx/.claude/skills/liubei
  rm /Users/xxx/.gemini/skills/liubei

注意：仅删除软链接，源文件目录不受影响。

确认执行？(y/n)
```

### 第四步：执行删除

用户确认后执行所有 `rm` 命令，完成后逐行输出结果。

## 卸载常见情况处理

**目标是真实目录而非软链接**：从卸载列表剔除并告知用户，避免误删源文件。

**选定范围内没有软链接**：告知用户当前 agent 中没有可卸载的 skill。

---

## 更新流程

更新只针对软链接指向的 git 仓库，在源目录执行 `git pull`，不修改软链接本身。

### 第一步：扫描可更新的 Skill

扫描所有 agent 的 skills 目录，找出软链接，并检测链接目标是否是 git 仓库：

```bash
# 对每个软链接，检查目标目录是否有 .git
for link in ~/.claude/skills/* ~/.gemini/skills/* ~/.codex/skills/*; do
  [ -L "$link" ] || continue
  target=$(readlink "$link")
  [ -d "$target/.git" ] && echo "git: $(basename $link) → $target"
done
```

### 第二步：让用户选择要更新的 Skill

将所有可更新的 skill（目标为 git 仓库的软链接）用 `AskUserQuestion` 复选框展示：

```
question: "选择要更新的 Skill（将对源目录执行 git pull）"
header: "选择 Skill"
multiSelect: true
options:
  - label: "<skill名>", description: "源目录: <绝对路径>"
  ...
```

如果没有任何 skill 指向 git 仓库，告知用户"当前已安装的 skill 均非 git 仓库，无法自动更新"。

### 第三步：展示更新计划并确认

```
准备更新以下 Skill：

  ✓ skill-kit → /Users/xxx/workspace/ai/skills/skill-kit  (git pull)
  ✓ liubei    → /Users/xxx/workspace/ai/skills/liubei     (git pull)

注意：只更新源目录代码，软链接不变，已安装的 agent 无需重新操作。

确认执行？(y/n)
```

### 第四步：执行 git pull

```bash
cd <源目录> && git pull
```

逐个执行，输出每个 skill 的 pull 结果（成功 / 已是最新 / 冲突报错）。

## 更新常见情况处理

**git pull 有冲突**：显示冲突信息，告知用户需手动进入目录解决，不自动强制覆盖。

**目标不是 git 仓库**：跳过该 skill，说明"该 skill 非 git 安装，跳过更新"。

**网络失败**：显示错误，建议用户检查网络后重试。

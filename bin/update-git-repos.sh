#!/usr/bin/env bash
# update-git-repos.sh — 自动扫描指定目录下所有 git 仓库并 ff-only 更新
#
# 用法:
#   ./update-git-repos.sh                       # 全量扫描 + 更新（深度 3）
#   ./update-git-repos.sh --dry-run             # 只显示状态，不做任何拉取
#   ./update-git-repos.sh --depth N             # 覆盖默认深度
#   ./update-git-repos.sh --root <dir>          # 覆盖扫描根目录
#   ./update-git-repos.sh --recheck             # 重新拉取黑名单中标记为 gone 的仓库
#
# 行为约定:
#   - 自动扫描 <根目录> 下所有 git 仓库（默认深度 3，即 BASE_DIR/组/仓库/.git）
#   - 只做 fast-forward 更新，绝不产生 merge commit 或覆盖本地提交
#   - 工作区有未提交改动的仓库自动 stash → pull → stash pop，本地改动不丢失；
#     若 pop 时冲突，改动保留在 stash 中并警告，需手动处理
#   - 个人仓库（remote owner == 当前 GitHub 用户）会标 (个人)
#   - 黑名单 <根目录>/.repo-skip：每行一条相对路径或 glob；
#     支持空行与 # 开头注释；脚本在拉取失败时会自动追加 # gone: DATE: reason
#   - antv-skills 等非 git 目录会在末尾提示一次
#   - find 不跟随符号链接，避免 guizang-ppt-skill 这类 symlink 重复处理

set -u

BASE_DIR_DEFAULT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKIP_FILE_DEFAULT="$BASE_DIR_DEFAULT/.repo-skip"

ROOT="$BASE_DIR_DEFAULT"
DEPTH=3
DRY_RUN=false
RECHECK=false
SKIP_FILE="$SKIP_FILE_DEFAULT"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)   DRY_RUN=true ;;
    --recheck)   RECHECK=true ;;
    --depth)     DEPTH="${2:-}"; [[ -z "$DEPTH" ]] && { echo "ERROR: --depth 需要数字" >&2; exit 2; }; shift ;;
    --root)      ROOT="${2:-}"; [[ -z "$ROOT" ]] && { echo "ERROR: --root 需要路径" >&2; exit 2; }; shift ;;
    --skip-file) SKIP_FILE="${2:-}"; [[ -z "$SKIP_FILE" ]] && { echo "ERROR: --skip-file 需要路径" >&2; exit 2; }; shift ;;
    -h|--help)
      sed -n '2,20p' "$0"; exit 0 ;;
    *)
      echo "ERROR: 未知参数 $1（试试 --help）" >&2; exit 2 ;;
  esac
  shift
done

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'

# ---------- 辅助函数 ----------

# --recheck：清除所有 # gone: 注释块及其后紧跟的路径行（仅限 gone 标记，
# 用户手写的路径不被删），让脚本重新尝试这些仓库
if $RECHECK && [[ -f "$SKIP_FILE" ]]; then
  tmp="${SKIP_FILE}.tmp.$$"
  awk '
    /^[[:space:]]*# gone:/ { skipping=1; next }
    skipping==1 && /^[[:space:]]*[^[:space:]#]/ { skipping=0; next }
    skipping==1 && /^[[:space:]]*$/ { next }
    { skipping=0; print }
  ' "$SKIP_FILE" > "$tmp" && mv "$tmp" "$SKIP_FILE"
fi

# 从 remote URL 提取 owner（兼容 GitHub / Gitee / 自建 host）
extract_owner() {
  local url="$1"
  [[ -z "$url" ]] && { echo ""; return; }
  url="${url#git@}"; url="${url#https://}"; url="${url#http://}"; url="${url#ssh://}"
  url="${url#git://}"
  url="${url%.git}"
  # SSH 形如 git@github.com:owner/repo → 取冒号后半
  url="${url##*:}"
  echo "${url%%/*}"
}

# 当前 GitHub 用户（用于「个人仓库」标记）
detect_self() {
  gh api user -q .login 2>/dev/null || echo ""
}

# 扫描根目录下所有 git 仓库的根目录（不含 .git）
# depth=N 表示仓库根目录最深在第 N 层（BASE_DIR 算第 1 层）；
# 用 shell 递归遍历实现，避开 find 在 macOS 上的 maxdepth 语义差异
# （实测：macOS BSD find 与 bfs 的 -maxdepth 都按绝对路径组件数计算，
# 而不是从起始目录算起的层级）
scan_repos() {
  local root="$1" depth="$2"
  [[ -d "$root" ]] || return 0
  _walk_repo "$root" 1 "$depth"
}

_walk_repo() {
  local dir="$1" cur="$2" max="$3"
  [[ $cur -gt $max ]] && return 0
  if [[ -d "$dir/.git" ]]; then
    printf '%s\n' "$dir"
    return 0
  fi
  [[ $cur -eq $max ]] && return 0
  local entry
  for entry in "$dir"/*/; do
    [[ -d "$entry" ]] || continue
    _walk_repo "${entry%/}" $((cur + 1)) "$max"
  done
}

# 加载黑名单路径（去掉注释与空行）
load_skip() {
  [[ -f "$1" ]] || return 0
  grep -v '^[[:space:]]*#' "$1" | grep -v '^[[:space:]]*$' || true
}

# 判断 relpath 是否被黑名单命中（精确匹配或前缀匹配）
is_skipped() {
  local relpath="$1"
  local pattern
  while IFS= read -r pattern; do
    [[ -z "$pattern" ]] && continue
    if [[ "$relpath" == "$pattern" ]] || [[ "$relpath" == "$pattern"/* ]]; then
      return 0
    fi
  done < <(load_skip "$SKIP_FILE")
  return 1
}

# 拉取失败时把仓库标记为 gone
mark_gone() {
  local relpath="$1" reason="$2"
  printf '\n# gone: %s: %s\n%s\n' "$(date +%F)" "$reason" "$relpath" >> "$SKIP_FILE"
}

# ---------- 主流程 ----------

SELF="$(detect_self)"

mode="pull --ff-only"
$DRY_RUN && mode="dry-run"
extra=""
[[ "$ROOT" != "$BASE_DIR_DEFAULT" ]] && extra=" | root=$ROOT"
printf "${CYAN}== 更新 git 仓库 (%s%s) ==${NC}\n" "$mode" "$extra"
printf "${CYAN}   root=%s depth=%d skip=%s self=%s${NC}\n" "$ROOT" "$DEPTH" "$SKIP_FILE" "${SELF:-unknown}"
echo

updated=0; stash_conflict=0; failed=0; uptodate=0; missing=0; skipped=0
gone_marked=0

# 把 find 输出喂给 while 循环（避免子 shell 看不到变量更新）
while IFS= read -r dir; do
  [[ -z "$dir" ]] && continue

  relpath="${dir#"$ROOT"/}"

  # 黑名单命中
  if is_skipped "$relpath"; then
    printf "${YELLOW}[跳过]${NC} %s — 在黑名单 .repo-skip 中\n" "$relpath"
    skipped=$((skipped + 1))
    continue
  fi

  # 非 git 目录（理论上 find 已经过滤，这里是双保险）
  if [[ ! -d "$dir/.git" ]]; then
    printf "${RED}[缺失]${NC} %s — 目录不存在或不是 git 仓库\n" "$relpath"
    missing=$((missing + 1))
    continue
  fi

  branch="$(git -C "$dir" branch --show-current 2>/dev/null)"
  remote_url="$(git -C "$dir" remote get-url origin 2>/dev/null || echo '')"
  owner="$(extract_owner "$remote_url")"
  tag=""
  if [[ -n "$SELF" && "$owner" == "$SELF" ]]; then
    tag=" (个人)"
  fi

  dirty=false
  if [[ -n "$(git -C "$dir" status --porcelain --untracked-files=no 2>/dev/null)" ]]; then
    dirty=true
  fi

  if $DRY_RUN; then
    note=""
    $dirty && note="（有本地改动，将 stash 后更新）"
    printf "${CYAN}[待更]${NC} %s%s — 分支 %s ← %s %s\n" "$relpath" "$tag" "${branch:-detached}" "${remote_url:-无远程}" "$note"
    continue
  fi

  # dirty → stash → pull → pop
  if $dirty; then
    if ! git -C "$dir" stash push -q -m "update-git-repos auto-stash $(date +%F)" 2>/dev/null; then
      printf "${RED}[失败]${NC} %s%s — stash 本地改动失败，跳过\n" "$relpath" "$tag"
      failed=$((failed + 1))
      continue
    fi
  fi

  output="$(git -C "$dir" pull --ff-only 2>&1)"
  status=$?

  if $dirty; then
    if ! git -C "$dir" stash pop -q 2>/dev/null; then
      printf "${YELLOW}[冲突]${NC} %s%s — 更新成功但本地改动与上游冲突，改动保留在 stash，请手动执行: git -C %s stash pop\n" "$relpath" "$tag" "$dir"
      stash_conflict=$((stash_conflict + 1))
    fi
  fi

  if [[ $status -ne 0 ]]; then
    err="$(echo "$output" | tail -1)"
    printf "${RED}[失败]${NC} %s%s — %s\n" "$relpath" "$tag" "$err"
    # 检测「仓库不存在」类永久错误 → 写进黑名单
    if echo "$output" | grep -qE 'could not be found|not found|Repository not found|does not exist|and the repository exists' \
       || echo "$err" | grep -qE 'HTTP [0-9]+'; then
      mark_gone "$relpath" "auto: $err"
      gone_marked=$((gone_marked + 1))
    fi
    failed=$((failed + 1))
  elif [[ "$output" == *"Already up to date."* || "$output" == *"已经是最新"* ]]; then
    printf "${GREEN}[最新]${NC} %s%s\n" "$relpath" "$tag"
    uptodate=$((uptodate + 1))
  else
    printf "${GREEN}[更新]${NC} %s%s — %s\n" "$relpath" "$tag" "$(echo "$output" | grep -E 'Fast-forward|files? changed|^Updating' | head -1)"
    updated=$((updated + 1))
  fi
done < <(scan_repos "$ROOT" "$DEPTH")

echo
printf "${CYAN}== 汇总 ==${NC} 已更新 %d | 已最新 %d | stash冲突 %d | 失败 %d | 缺失 %d | 跳过 %d\n" \
  "$updated" "$uptodate" "$stash_conflict" "$failed" "$missing" "$skipped"

if [[ "$gone_marked" -gt 0 ]]; then
  printf "${YELLOW}提示:${NC} %d 个仓库失败疑似永久失效，已自动写入 %s；用 --recheck 强制重试。\n" "$gone_marked" "$SKIP_FILE"
fi

# antv-skills 等「名字像仓库但非 git」的目录——末尾一次性提示
for name in antv-skills; do
  if [[ -d "$BASE_DIR_DEFAULT/$name" && ! -d "$BASE_DIR_DEFAULT/$name/.git" ]]; then
    printf "${YELLOW}提示:${NC} %s 不是 git 仓库，已自动跳过；如需跟踪上游请到官方仓库重新 clone。\n" "$name"
  fi
done

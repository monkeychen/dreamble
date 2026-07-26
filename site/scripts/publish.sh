#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .deploy.env ]] || { echo "缺少 .deploy.env（复制 .deploy.env.example 填写后重试）" >&2; exit 1; }
# shellcheck disable=SC1091
source .deploy.env
: "${DEPLOY_HOST:?}" "${DEPLOY_USER:?}" "${DEPLOY_PATH:?}"
REMOTE="${DEPLOY_USER}@${DEPLOY_HOST}"

echo "==> 1/3 完整验收（内容约束、类型、测试、构建）"
npm run verify
rm -rf dist/.git   # 上次部署 Git fallback 失败可能残留，绝不能同步到公网
find dist -name .DS_Store -delete   # Finder 元数据不上公网（rsync 与部署 Git fallback 都覆盖）

echo "==> 2/3 同步到 ${DEPLOY_HOST}"
synced=""
if [[ "${DEPLOY_FORCE_GIT:-0}" != "1" ]] && command -v rsync >/dev/null 2>&1; then
  if rsync -az --delete --exclude=.git dist/ "${REMOTE}:${DEPLOY_PATH}/"; then
    synced="rsync"
  else
    echo "    rsync 失败，改用部署 Git fallback 通道" >&2
  fi
fi

if [[ -z "$synced" ]]; then
  : "${DEPLOY_GIT_REPO:?部署 Git fallback 需要 DEPLOY_GIT_REPO}"
  (
    cd dist
    rm -rf .git
    git init -q -b main
    git add -A
    git -c user.name=deploy -c user.email=deploy@local commit -qm "deploy $(date '+%Y-%m-%d %H:%M:%S')"
    git push -q -f "ssh://${REMOTE}${DEPLOY_GIT_REPO}" main
    rm -rf .git
  )
  synced="git-fallback"
fi
echo "    同步完成（通道: ${synced}）"

echo "==> 3/3 线上健康检查"
SITE_URL="${SITE_URL:-https://simiam.com}"
if curl -fsS -o /dev/null --max-time 10 "${SITE_URL}/"; then
  echo "✅ 发布成功: ${SITE_URL}"
else
  echo "❌ 文件已同步，但 ${SITE_URL} 访问检查未通过。" >&2
  echo "   请检查 nginx、DNS 和 HTTPS；首次部署可暂时把 .deploy.env 的 SITE_URL 改为 http://${DOMAIN:-simiam.com}。" >&2
  exit 1
fi

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .deploy.env ]] || { echo "缺少 .deploy.env（复制 .deploy.env.example 填写后重试）" >&2; exit 1; }
# shellcheck disable=SC1091
source .deploy.env
: "${DEPLOY_HOST:?}" "${DEPLOY_USER:?}" "${DEPLOY_PATH:?}"
REMOTE="${DEPLOY_USER}@${DEPLOY_HOST}"

echo "==> 1/2 构建（含内容 schema 校验）"
npm run build
rm -rf dist/.git   # 上次 git 通道失败可能残留，绝不能同步到公网
find dist -name .DS_Store -delete   # Finder 元数据不上公网（rsync 与 git 通道都覆盖）

echo "==> 2/2 同步到 ${DEPLOY_HOST}"
synced=""
if [[ "${DEPLOY_FORCE_GIT:-0}" != "1" ]] && command -v rsync >/dev/null 2>&1; then
  if rsync -az --delete --exclude=.git dist/ "${REMOTE}:${DEPLOY_PATH}/"; then
    synced="rsync"
  else
    echo "    rsync 失败，改用 git 同步" >&2
  fi
fi

if [[ -z "$synced" ]]; then
  : "${DEPLOY_GIT_REPO:?git 同步需要 DEPLOY_GIT_REPO}"
  (
    cd dist
    rm -rf .git
    git init -q -b main
    git add -A
    git -c user.name=deploy -c user.email=deploy@local commit -qm "deploy $(date '+%Y-%m-%d %H:%M:%S')"
    git push -q -f "ssh://${REMOTE}${DEPLOY_GIT_REPO}" main
    rm -rf .git
  )
  synced="git"
fi
echo "    同步完成（通道: ${synced}）"

SITE_URL="${SITE_URL:-https://simiam.com}"
if curl -fsS -o /dev/null --max-time 10 "${SITE_URL}/"; then
  echo "✅ 发布成功: ${SITE_URL}"
else
  echo "⚠️  文件已同步，但 ${SITE_URL} 访问检查未通过。"
  echo "    首次部署尚未配置 HTTPS 时属正常，可先访问 http://${DOMAIN:-simiam.com}/ 验证。"
fi

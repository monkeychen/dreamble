#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .deploy.env ]] || { echo "缺少 .deploy.env（复制 .deploy.env.example 填写后重试）" >&2; exit 1; }
# shellcheck disable=SC1091
source .deploy.env
: "${DOMAIN:?}" "${DEPLOY_HOST:?}" "${DEPLOY_USER:?}" "${DEPLOY_PATH:?}" "${DEPLOY_GIT_REPO:?}"
REMOTE="${DEPLOY_USER}@${DEPLOY_HOST}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1) nginx 站点配置（HTTP；HTTPS 之后由 certbot --nginx 自动改写）
cat > "${TMP}/site.conf" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};
    root ${DEPLOY_PATH};
    index index.html;
    charset utf-8;

    gzip on;
    gzip_types text/css application/javascript application/xml application/rss+xml image/svg+xml;

    # /_astro/ 下均为内容哈希文件名（字体分包、样式、图片），可永久强缓存
    location /_astro/ {
        expires max;
        add_header Cache-Control "public, immutable";
        try_files \$uri =404;
    }

    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

# 2) git 备用同步通道的 post-receive hook
cat > "${TMP}/post-receive" <<EOF
#!/usr/bin/env bash
set -euo pipefail
git --work-tree="${DEPLOY_PATH}" --git-dir="${DEPLOY_GIT_REPO}" checkout -f main
git --work-tree="${DEPLOY_PATH}" --git-dir="${DEPLOY_GIT_REPO}" clean -fd
EOF

echo "==> 初始化目录与 git 通道"
ssh "${REMOTE}" "mkdir -p '${DEPLOY_PATH}' && { [ -d '${DEPLOY_GIT_REPO}' ] || git init --bare -b main '${DEPLOY_GIT_REPO}'; }"
scp -q "${TMP}/post-receive" "${REMOTE}:${DEPLOY_GIT_REPO}/hooks/post-receive"
ssh "${REMOTE}" "chmod +x '${DEPLOY_GIT_REPO}/hooks/post-receive'"

echo "==> 写入 nginx 配置并重载"
if ssh "${REMOTE}" "grep -q 'listen 443' '/etc/nginx/conf.d/${DOMAIN}.conf' 2>/dev/null"; then
  echo "    检测到已有 HTTPS 配置（certbot 已接管），跳过 nginx 配置写入以免覆盖"
else
  scp -q "${TMP}/site.conf" "${REMOTE}:/etc/nginx/conf.d/${DOMAIN}.conf"
  ssh "${REMOTE}" "nginx -t && (systemctl reload nginx 2>/dev/null || nginx -s reload)"
fi

echo "✅ 服务器初始化完成"
echo "下一步: npm run publish 首次发布；HTTPS 配置见 docs/deploy.md"

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f .deploy.env ]] || { echo "缺少 .deploy.env（复制 .deploy.env.example 填写后重试）" >&2; exit 1; }
node scripts/stats-config.mjs ensure-credentials

# shellcheck disable=SC1091
source .deploy.env
: "${DOMAIN:?}" "${DEPLOY_HOST:?}" "${DEPLOY_USER:?}" "${STATS_USER:?}" "${STATS_PASSWORD:?}"
[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || { echo "DOMAIN 格式不合法" >&2; exit 1; }
[[ "$STATS_USER" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "STATS_USER 只能包含字母、数字、点、下划线和连字符" >&2; exit 1; }

REMOTE="${DEPLOY_USER}@${DEPLOY_HOST}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "==> 1/4 安装统计组件"
ssh "$REMOTE" '
  set -e
  if command -v dnf >/dev/null 2>&1; then
    dnf -y -q install goaccess httpd-tools
  elif command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq goaccess apache2-utils
  else
    echo "不支持的服务器包管理器，需要手动安装 goaccess 与 htpasswd" >&2
    exit 1
  fi
'

echo "==> 2/4 生成私有面板与定时任务配置"
scp -q "${REMOTE}:/etc/nginx/conf.d/${DOMAIN}.conf" "${TMP}/site.conf"
node scripts/stats-config.mjs patch-nginx "${TMP}/site.conf" "$DOMAIN"

cat > "${TMP}/stats-nginx.conf" <<EOF
access_log /var/log/simiam/access.log combined;

location = /stats {
    return 301 /stats/;
}

location ^~ /stats/ {
    auth_basic "${DOMAIN} statistics";
    auth_basic_user_file /etc/nginx/.${DOMAIN}-stats.htpasswd;
    alias /var/lib/simiam-stats/;
    index index.html;
    add_header Cache-Control "private, no-store";
    access_log off;
}
EOF

cat > "${TMP}/update-stats" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

logs=()
for log in /var/log/simiam/access.log /var/log/simiam/access.log.1 /var/log/simiam/access.log.*.gz; do
  [[ -f "$log" ]] && logs+=("$log")
done
[[ ${#logs[@]} -gt 0 ]] || exit 0

tmp="$(mktemp --suffix=.html)"
trap 'rm -f "$tmp"' EXIT
{
  for log in "${logs[@]}"; do
    if [[ "$log" == *.gz ]]; then
      gzip -cd -- "$log"
    else
      cat -- "$log"
    fi
  done
} | /usr/bin/goaccess - \
  --log-format=COMBINED \
  --no-global-config \
  --no-query-string \
  --anonymize-ip \
  --anonymize-level=3 \
  --ignore-panel=HOSTS \
  --ignore-statics=panel \
  --output="$tmp"

install -m 0640 "$tmp" /var/lib/simiam-stats/index.html
install -m 0640 "$tmp" "/var/lib/simiam-stats/archive/$(date +%Y-%m).html"
EOF

cat > "${TMP}/simiam-stats.service" <<'EOF'
[Unit]
Description=Generate simiam.com private traffic report
After=nginx.service

[Service]
Type=oneshot
User=nginx
Group=nginx
ExecStart=/usr/local/sbin/update-simiam-stats
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadOnlyPaths=/var/log/simiam
ReadWritePaths=/var/lib/simiam-stats
EOF

cat > "${TMP}/simiam-stats.timer" <<'EOF'
[Unit]
Description=Refresh simiam.com traffic report every five minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
EOF

cat > "${TMP}/simiam-stats.logrotate" <<'EOF'
/var/log/simiam/access.log {
    daily
    rotate 30
    missingok
    notifempty
    compress
    delaycompress
    create 0640 nginx root
    sharedscripts
    postrotate
        /bin/kill -USR1 `cat /run/nginx.pid 2>/dev/null` 2>/dev/null || true
    endscript
}
EOF

echo "==> 3/4 应用认证、日志与 nginx 配置"
ssh "$REMOTE" '
  set -e
  install -d -m 0750 -o nginx -g nginx /var/log/simiam
  install -d -m 0750 -o nginx -g nginx /var/lib/simiam-stats /var/lib/simiam-stats/archive
  touch /var/log/simiam/access.log
  chown nginx:root /var/log/simiam/access.log
  chmod 0640 /var/log/simiam/access.log
  install -d -m 0755 /etc/nginx/snippets
'
printf '%s\n' "$STATS_PASSWORD" | ssh "$REMOTE" "htpasswd -i -Bc '/etc/nginx/.${DOMAIN}-stats.htpasswd' '$STATS_USER' >/dev/null"
ssh "$REMOTE" "chown root:nginx '/etc/nginx/.${DOMAIN}-stats.htpasswd'; chmod 0640 '/etc/nginx/.${DOMAIN}-stats.htpasswd'"

scp -q "${TMP}/stats-nginx.conf" "${REMOTE}:/etc/nginx/snippets/${DOMAIN}-stats.conf"
scp -q "${TMP}/update-stats" "${REMOTE}:/usr/local/sbin/update-simiam-stats"
scp -q "${TMP}/simiam-stats.service" "${REMOTE}:/etc/systemd/system/simiam-stats.service"
scp -q "${TMP}/simiam-stats.timer" "${REMOTE}:/etc/systemd/system/simiam-stats.timer"
scp -q "${TMP}/simiam-stats.logrotate" "${REMOTE}:/etc/logrotate.d/simiam-stats"
scp -q "${TMP}/site.conf" "${REMOTE}:/etc/nginx/conf.d/${DOMAIN}.conf.stats-new"

ssh "$REMOTE" "
  set -e
  chmod 0644 '/etc/nginx/snippets/${DOMAIN}-stats.conf' /etc/systemd/system/simiam-stats.service /etc/systemd/system/simiam-stats.timer /etc/logrotate.d/simiam-stats
  chmod 0755 /usr/local/sbin/update-simiam-stats
  cp '/etc/nginx/conf.d/${DOMAIN}.conf' '/etc/nginx/conf.d/${DOMAIN}.conf.stats-backup'
  mv '/etc/nginx/conf.d/${DOMAIN}.conf.stats-new' '/etc/nginx/conf.d/${DOMAIN}.conf'
  if ! nginx -t; then
    cp '/etc/nginx/conf.d/${DOMAIN}.conf.stats-backup' '/etc/nginx/conf.d/${DOMAIN}.conf'
    nginx -t
    exit 1
  fi
  systemctl reload nginx
  systemctl daemon-reload
  systemctl enable --now simiam-stats.timer
"

echo "==> 4/4 生成首份报告并检查私密访问"
curl -fsS -o /dev/null --max-time 10 "https://${DOMAIN}/"
ssh "$REMOTE" "systemctl start simiam-stats.service; test -s /var/lib/simiam-stats/index.html"
unauthorized="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "https://${DOMAIN}/stats/")"
authorized="$(curl -sS -u "${STATS_USER}:${STATS_PASSWORD}" -o /dev/null -w '%{http_code}' --max-time 10 "https://${DOMAIN}/stats/")"
[[ "$unauthorized" == "401" ]] || { echo "未认证访问应返回 401，实际为 ${unauthorized}" >&2; exit 1; }
[[ "$authorized" == "200" ]] || { echo "认证访问应返回 200，实际为 ${authorized}" >&2; exit 1; }

echo "✅ 私有流量统计已启用: https://${DOMAIN}/stats/"
echo "   查看账号密码: npm --prefix site run stats:credentials"

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  ensureStatsCredentials,
  patchNginxConfig,
  readEnvValue,
} from '../scripts/stats-config.mjs';

test('ensureStatsCredentials 生成凭据且重复运行保持不变', () => {
  const source = 'DOMAIN=simiam.com\nSTATS_USER=\nSTATS_PASSWORD=\n';
  const first = ensureStatsCredentials(source, 'fixed-secret');
  const second = ensureStatsCredentials(first, 'other-secret');

  assert.equal(readEnvValue(first, 'STATS_USER'), 'stats');
  assert.equal(readEnvValue(first, 'STATS_PASSWORD'), 'fixed-secret');
  assert.equal(second, first);
});

test('patchNginxConfig 在主 server 中幂等加入统计配置', () => {
  const source = `server {
    server_name simiam.com;
    root /var/www/simiam.com;
    charset utf-8;
    listen 443 ssl;
}
server {
    listen 80;
    server_name simiam.com;
}
`;
  const first = patchNginxConfig(source, 'simiam.com');
  const second = patchNginxConfig(first, 'simiam.com');

  assert.match(first, /charset utf-8;\n    include \/etc\/nginx\/snippets\/simiam\.com-stats\.conf;/);
  assert.equal((first.match(/simiam\.com-stats\.conf/g) ?? []).length, 1);
  assert.equal(second, first);
  assert.throws(() => patchNginxConfig(source, 'other.example'), /未找到/);
});

test('setup-stats 强制认证并避免在报告中暴露原始访客信息', () => {
  const script = readFileSync(
    fileURLToPath(new URL('../scripts/setup-stats.sh', import.meta.url)),
    'utf8',
  );

  assert.match(script, /auth_basic_user_file/);
  assert.match(script, /alias \/var\/lib\/simiam-stats\//);
  assert.match(script, /index index\.html/);
  assert.match(script, /access_log off/);
  assert.match(script, /--no-query-string/);
  assert.match(script, /--anonymize-level=3/);
  assert.match(script, /--ignore-panel=HOSTS/);
  assert.match(script, /\[\[ -f "\$log" \]\]/);
  assert.match(script, /mktemp --suffix=\.html/);
  assert.match(script, /rotate 30/);
});

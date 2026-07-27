#!/usr/bin/env node

import { randomBytes } from 'node:crypto';
import { chmodSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const DEFAULT_ENV_PATH = fileURLToPath(new URL('../.deploy.env', import.meta.url));

function envPattern(key) {
  return new RegExp(`^${key}=([^\\r\\n]*)$`, 'm');
}

export function readEnvValue(content, key) {
  return content.match(envPattern(key))?.[1].trim() ?? '';
}

function setEnvValue(content, key, value) {
  const line = `${key}=${value}`;
  if (envPattern(key).test(content)) return content.replace(envPattern(key), line);
  const separator = content.length === 0 || content.endsWith('\n') ? '' : '\n';
  return `${content}${separator}${line}\n`;
}

export function ensureStatsCredentials(content, password = randomBytes(18).toString('base64url')) {
  let next = content;
  if (!readEnvValue(next, 'STATS_USER')) next = setEnvValue(next, 'STATS_USER', 'stats');
  if (!readEnvValue(next, 'STATS_PASSWORD')) next = setEnvValue(next, 'STATS_PASSWORD', password);
  return next;
}

export function rotateStatsPassword(content, password = randomBytes(18).toString('base64url')) {
  return setEnvValue(content, 'STATS_PASSWORD', password);
}

export function patchNginxConfig(content, domain) {
  if (!/^[A-Za-z0-9.-]+$/.test(domain)) throw new Error('非法域名');
  if (!content.includes(`server_name ${domain}`)) throw new Error(`nginx 配置中未找到 ${domain}`);

  const includeLine = `include /etc/nginx/snippets/${domain}-stats.conf;`;
  if (content.includes(includeLine)) return content;

  const firstServer = content.search(/server\s*\{/);
  if (firstServer === -1) throw new Error('nginx 配置中未找到 server 块');

  const remainder = content.slice(firstServer);
  const charsetMatch = /^[ \t]*charset\s+utf-8;\s*$/m.exec(remainder);
  let insertionPoint;
  let indentation = '    ';

  if (charsetMatch) {
    const charsetStart = firstServer + charsetMatch.index;
    insertionPoint = content.indexOf('\n', charsetStart);
    insertionPoint = insertionPoint === -1 ? content.length : insertionPoint + 1;
    indentation = charsetMatch[0].match(/^[ \t]*/)?.[0] || indentation;
  } else {
    const openingEnd = content.indexOf('{', firstServer) + 1;
    insertionPoint = content.indexOf('\n', openingEnd);
    insertionPoint = insertionPoint === -1 ? openingEnd : insertionPoint + 1;
  }

  return `${content.slice(0, insertionPoint)}${indentation}${includeLine}\n${content.slice(insertionPoint)}`;
}

function ensureCredentials(envPath) {
  const current = readFileSync(envPath, 'utf8');
  const next = ensureStatsCredentials(current);
  if (next !== current) writeFileSync(envPath, next, { mode: 0o600 });
  chmodSync(envPath, 0o600);
  console.log('统计面板访问凭据已配置在 site/.deploy.env');
}

function showCredentials(envPath) {
  const content = readFileSync(envPath, 'utf8');
  const domain = readEnvValue(content, 'DOMAIN');
  const user = readEnvValue(content, 'STATS_USER');
  const password = readEnvValue(content, 'STATS_PASSWORD');
  if (!domain || !user || !password) throw new Error('统计面板凭据尚未配置，请先运行 stats:setup');
  console.log(`地址: https://${domain}/stats/`);
  console.log(`用户名: ${user}`);
  console.log(`密码: ${password}`);
}

function rotateCredentials(envPath) {
  const current = readFileSync(envPath, 'utf8');
  writeFileSync(envPath, rotateStatsPassword(current), { mode: 0o600 });
  chmodSync(envPath, 0o600);
  console.log('统计面板密码已轮换，正在同步服务器认证配置');
}

function patchConfig(configPath, domain) {
  const current = readFileSync(configPath, 'utf8');
  const next = patchNginxConfig(current, domain);
  if (next !== current) writeFileSync(configPath, next);
}

function main() {
  const [command, ...args] = process.argv.slice(2);
  if (command === 'ensure-credentials') {
    ensureCredentials(args[0] ?? DEFAULT_ENV_PATH);
  } else if (command === 'rotate-credentials') {
    rotateCredentials(args[0] ?? DEFAULT_ENV_PATH);
  } else if (command === 'show-credentials') {
    showCredentials(args[0] ?? DEFAULT_ENV_PATH);
  } else if (command === 'patch-nginx') {
    if (!args[0] || !args[1]) throw new Error('用法: stats-config.mjs patch-nginx <配置文件> <域名>');
    patchConfig(args[0], args[1]);
  } else {
    throw new Error('用法: stats-config.mjs <ensure-credentials|rotate-credentials|show-credentials|patch-nginx>');
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    main();
  } catch (error) {
    console.error(`❌ ${error.message}`);
    process.exit(1);
  }
}

#!/usr/bin/env node

import { execFileSync } from 'node:child_process';
import { relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const SITE_ROOT = fileURLToPath(new URL('..', import.meta.url));
const DEFAULT_COMMIT_MESSAGE = 'Publish site updates';

function git(args, cwd, options = {}) {
  return execFileSync('git', args, {
    cwd,
    encoding: 'utf8',
    ...options,
  });
}

function fail(message) {
  console.error(`❌ ${message}`);
  process.exit(1);
}

function main() {
  let repoRoot;
  try {
    repoRoot = git(['rev-parse', '--show-toplevel'], SITE_ROOT).trim();
  } catch {
    fail('site/ 不在 Git 仓库中，无法同步源码。');
  }

  const sitePath = relative(repoRoot, SITE_ROOT).split(sep).join('/');
  if (!sitePath || sitePath.startsWith('../')) {
    fail('无法确认 site/ 在源码仓库中的路径，已停止以避免提交错误范围。');
  }

  let branch;
  try {
    branch = git(['symbolic-ref', '--short', 'HEAD'], repoRoot).trim();
  } catch {
    fail('源码仓库当前处于 detached HEAD，无法安全推送。');
  }
  if (branch !== 'main') {
    fail(`源码仓库当前分支为 ${branch}；发布只允许从 main 执行。`);
  }

  const changes = git(
    ['status', '--porcelain', '--untracked-files=all', '--', sitePath],
    repoRoot,
  ).trim();

  if (changes) {
    const commitMessage = process.env.PUBLISH_COMMIT_MESSAGE?.trim() || DEFAULT_COMMIT_MESSAGE;
    git(['add', '-A', '--', sitePath], repoRoot, { stdio: 'inherit' });
    git(['commit', '-m', commitMessage, '--', sitePath], repoRoot, { stdio: 'inherit' });

    const remaining = git(
      ['status', '--porcelain', '--untracked-files=all', '--', sitePath],
      repoRoot,
    ).trim();
    if (remaining) {
      fail('提交后 site/ 仍有变更，可能是 Git hook 修改了文件；请检查后重试发布。');
    }
  } else {
    console.log('    site/ 没有待提交变更');
  }

  git(['push', 'origin', 'main'], repoRoot, { stdio: 'inherit' });
  console.log('    源码已同步到 origin/main');
}

main();

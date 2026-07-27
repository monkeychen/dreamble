import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import {
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const SOURCE_SCRIPT = fileURLToPath(new URL('../scripts/sync-source.mjs', import.meta.url));

function run(command, args, cwd, env = {}) {
  return execFileSync(command, args, {
    cwd,
    encoding: 'utf8',
    env: { ...process.env, ...env },
  });
}

function git(args, cwd) {
  return run('git', args, cwd);
}

test('sync-source 只提交 site 变更、保留外部改动并推送 main', (t) => {
  const sandbox = mkdtempSync(join(tmpdir(), 'dreamble-source-sync-'));
  const remote = join(sandbox, 'remote.git');
  const repo = join(sandbox, 'repo');
  const script = join(repo, 'site', 'scripts', 'sync-source.mjs');
  t.after(() => rmSync(sandbox, { recursive: true, force: true }));

  mkdirSync(dirname(script), { recursive: true });
  git(['init', '--bare', '-q', remote], sandbox);
  git(['init', '-q', '-b', 'main', repo], sandbox);
  git(['config', 'user.name', 'Test User'], repo);
  git(['config', 'user.email', 'test@example.com'], repo);

  copyFileSync(SOURCE_SCRIPT, script);
  writeFileSync(join(repo, 'site', 'article.md'), 'old article\n');
  writeFileSync(join(repo, 'site', 'delete-me.md'), 'delete this\n');
  writeFileSync(join(repo, 'outside.txt'), 'old outside\n');
  git(['add', '-A'], repo);
  git(['commit', '-qm', 'Initial'], repo);
  git(['remote', 'add', 'origin', remote], repo);
  git(['push', '-q', '-u', 'origin', 'main'], repo);

  writeFileSync(join(repo, 'site', 'article.md'), 'new article\n');
  writeFileSync(join(repo, 'site', 'new-file.md'), 'new file\n');
  rmSync(join(repo, 'site', 'delete-me.md'));
  writeFileSync(join(repo, 'outside.txt'), 'new outside\n');
  git(['add', 'outside.txt'], repo);

  const output = run(
    process.execPath,
    [script],
    repo,
    { PUBLISH_COMMIT_MESSAGE: 'Test site publish' },
  );

  assert.match(output, /源码已同步到 origin\/main/);
  assert.equal(git(['log', '-1', '--pretty=%s'], repo).trim(), 'Test site publish');
  assert.equal(git(['show', 'HEAD:site/article.md'], repo), 'new article\n');
  assert.equal(git(['show', 'HEAD:site/new-file.md'], repo), 'new file\n');
  assert.equal(git(['ls-tree', '--name-only', 'HEAD', 'site/delete-me.md'], repo), '');
  assert.equal(git(['show', 'HEAD:outside.txt'], repo), 'old outside\n');
  assert.equal(git(['--git-dir', remote, 'rev-parse', 'main']).trim(), git(['rev-parse', 'HEAD'], repo).trim());
  assert.equal(git(['status', '--short', '--', 'outside.txt'], repo), 'M  outside.txt\n');
  assert.equal(readFileSync(join(repo, 'outside.txt'), 'utf8'), 'new outside\n');
});

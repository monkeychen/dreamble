import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  IMPORT_STAGING_ROOT,
  POSTS_ROOT,
  PROJECTS_ROOT,
  SITE_ROOT,
} from '../scripts/lib/project-paths.mjs';

const expectedSiteRoot = path.resolve(fileURLToPath(new URL('..', import.meta.url)));

test('项目路径始终指向 site 目录', () => {
  assert.equal(SITE_ROOT, expectedSiteRoot);
  assert.equal(POSTS_ROOT, path.join(expectedSiteRoot, 'content/posts'));
  assert.equal(PROJECTS_ROOT, path.join(expectedSiteRoot, 'content/projects'));
  assert.equal(IMPORT_STAGING_ROOT, path.join(expectedSiteRoot, 'content/.import-staging'));
});

test('内容校验不依赖调用者当前工作目录', () => {
  const script = fileURLToPath(new URL('../scripts/validate-content.mjs', import.meta.url));
  const result = spawnSync(process.execPath, [script], {
    cwd: os.tmpdir(),
    encoding: 'utf8',
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /内容约束校验通过/);
});

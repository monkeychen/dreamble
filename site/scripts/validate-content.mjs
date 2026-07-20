#!/usr/bin/env node
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import {
  frontmatterDate,
  validatePostRecords,
  validateProjectNames,
} from './lib/content-policy.mjs';
import { POSTS_ROOT, PROJECTS_ROOT } from './lib/project-paths.mjs';

const errors = [];

async function contentDirectories(directory, label) {
  const entries = await readdir(directory, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isDirectory()) errors.push(`${label}目录中不应直接放文件：${entry.name}`);
  }
  return entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name);
}

async function readIndex(directory, name, label) {
  try {
    return await readFile(path.join(directory, name, 'index.md'), 'utf8');
  } catch (error) {
    if (error.code === 'ENOENT') {
      errors.push(`${label} ${name} 缺少 index.md`);
      return '';
    }
    throw error;
  }
}

const postNames = await contentDirectories(POSTS_ROOT, '文章');
const postRecords = [];
for (const name of postNames) {
  const markdown = await readIndex(POSTS_ROOT, name, '文章');
  postRecords.push({ name, date: frontmatterDate(markdown) });
}
errors.push(...validatePostRecords(postRecords));

const projectNames = await contentDirectories(PROJECTS_ROOT, '作品');
for (const name of projectNames) await readIndex(PROJECTS_ROOT, name, '作品');
errors.push(...validateProjectNames(projectNames));

if (errors.length > 0) {
  console.error('内容约束校验失败：');
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(`内容约束校验通过：文章 ${postNames.length} 篇，作品 ${projectNames.length} 个`);

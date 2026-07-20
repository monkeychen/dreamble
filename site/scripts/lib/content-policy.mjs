export const POST_DIRECTORY_PATTERN = /^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)$/;
export const PROJECT_DIRECTORY_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

/** 从 Markdown frontmatter 中读取严格的 YYYY-MM-DD 日期。 */
export function frontmatterDate(markdown) {
  const frontmatter = markdown.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/)?.[1];
  if (!frontmatter) return null;
  return frontmatter.match(/^date:\s*["']?(\d{4}-\d{2}-\d{2})["']?\s*$/m)?.[1] ?? null;
}

/** records: Array<{ name: string, date: string | null }> */
export function validatePostRecords(records) {
  const errors = [];
  const slugs = new Map();

  for (const record of records) {
    const match = record.name.match(POST_DIRECTORY_PATTERN);
    if (!match) {
      errors.push(
        `文章目录 ${record.name} 不合规，应为 YYYY-MM-DD-<slug>，slug 仅含小写字母、数字和单个连字符`
      );
      continue;
    }

    const [, directoryDate, slug] = match;
    if (!record.date) {
      errors.push(`文章 ${record.name}/index.md 缺少 YYYY-MM-DD 格式的 date`);
    } else if (record.date !== directoryDate) {
      errors.push(`文章 ${record.name} 的目录日期 ${directoryDate} 与 frontmatter date ${record.date} 不一致`);
    }

    const previous = slugs.get(slug);
    if (previous) {
      errors.push(`文章 slug 重复：${previous} 与 ${record.name} 都会生成 /posts/${slug}/`);
    } else {
      slugs.set(slug, record.name);
    }
  }

  return errors;
}

export function validateProjectNames(names) {
  return names
    .filter((name) => !PROJECT_DIRECTORY_PATTERN.test(name))
    .map((name) => `作品目录 ${name} 不合规，slug 仅含小写字母、数字和单个连字符`);
}

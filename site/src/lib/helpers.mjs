/** 内容集合 id → URL slug。id 可能是 "2026-07-16-foo" 或 "2026-07-16-foo/index"。 */
export function postSlug(id) {
  const dir = id.split('/')[0];
  const m = dir.match(/^\d{4}-\d{2}-\d{2}-(.+)$/);
  return m ? m[1] : dir;
}

export function projectSlug(id) {
  return id.split('/')[0];
}

/** 是否进入列表页 / RSS / sitemap */
export function isListed(data) {
  return isBuildable(data) && data.visibility === 'public';
}

/** 是否生成文章详情页 */
export function isBuildable(data) {
  return !data.draft;
}

export function sortByDateDesc(a, b) {
  return b.data.date.valueOf() - a.data.date.valueOf();
}

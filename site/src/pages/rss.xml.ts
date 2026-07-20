import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { postSlug, isListed, sortByDateDesc } from '../lib/helpers.mjs';

export async function GET(context: APIContext) {
  const posts = (await getCollection('posts', ({ data }) => isListed(data))).sort(sortByDateDesc);
  return rss({
    title: '聊哉梦呓',
    description: '安哥的文章与作品',
    site: context.site!,
    items: posts.map((p) => ({
      title: p.data.title,
      pubDate: p.data.date,
      description: p.data.summary ?? '',
      link: `/posts/${postSlug(p.id)}/`,
    })),
  });
}

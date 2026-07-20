import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { postSlug, projectSlug, isListed } from '../lib/helpers.mjs';

export async function GET(context: APIContext) {
  const posts = await getCollection('posts', ({ data }) => isListed(data));
  const projects = await getCollection('projects');

  const paths = [
    '/',
    '/posts/',
    '/projects/',
    '/about/',
    ...posts.map((p) => `/posts/${postSlug(p.id)}/`),
    ...projects.filter((p) => p.body?.trim()).map((p) => `/projects/${projectSlug(p.id)}/`),
  ];

  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...paths.map((p) => `  <url><loc>${new URL(p, context.site).href}</loc></url>`),
    '</urlset>',
  ].join('\n');

  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}

import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '*/index.md', base: './content/posts' }),
  schema: z.object({
    title: z.string().min(1),
    date: z.coerce.date(),
    summary: z.string().optional(),
    tags: z.array(z.string()).default([]),
    source: z.enum(['wechat']).optional(),
    visibility: z.enum(['public', 'unlisted']).default('public'),
    draft: z.boolean().default(false),
  }),
});

const projects = defineCollection({
  loader: glob({ pattern: '*/index.md', base: './content/projects' }),
  schema: ({ image }) =>
    z.object({
      name: z.string().min(1),
      tagline: z.string().min(1),
      cover: image().optional(),
      links: z
        .object({
          download: z.string().url().optional(),
          repo: z.string().url().optional(),
          website: z.string().url().optional(),
        })
        .refine((l) => l.download || l.repo || l.website, {
          message: 'links 至少填写 download / repo / website 之一',
        }),
      status: z.enum(['active', 'archived']).default('active'),
      order: z.number().default(999),
    }),
});

export const collections = { posts, projects };

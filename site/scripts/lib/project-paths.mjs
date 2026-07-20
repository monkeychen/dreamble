import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const SITE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const POSTS_ROOT = path.join(SITE_ROOT, 'content/posts');
export const PROJECTS_ROOT = path.join(SITE_ROOT, 'content/projects');
export const IMPORT_STAGING_ROOT = path.join(SITE_ROOT, 'content/.import-staging');

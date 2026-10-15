import type { MetadataRoute } from 'next';
import { getIndexableRoutes } from '../lib/legacy-content';
import { sitemapExcludedRoutes } from '../lib/seo-overrides';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const routes = await getIndexableRoutes();
  return [
    ...routes
      .filter((page) => !sitemapExcludedRoutes.has(page.route))
      .map((page) => ({ url: `https://brightluxx.com${page.route === '/' ? '' : page.route}` })),
    { url: 'https://brightluxx.com/luxury-home-cinema' },
  ];
}
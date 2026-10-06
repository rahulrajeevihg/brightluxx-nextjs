import type { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  if (process.env.NEXT_PUBLIC_STAGING === '1') return { rules: { userAgent: '*', disallow: '/' } };
  return { rules: [{ userAgent: '*', allow: '/', disallow: ['/admin', '/api', '/configurator', '/calculator', '/compare$', '/__migration-parity'] }], sitemap: 'https://brightluxx.com/sitemap.xml' };
}
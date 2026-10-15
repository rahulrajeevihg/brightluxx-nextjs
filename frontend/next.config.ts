import type { NextConfig } from 'next';

if (!process.env.API_ORIGIN) throw new Error('API_ORIGIN must be configured');

const legacyRedirects = [
  ['/our-works', '/projects'], ['/digital-solutions', '/solutions'], ['/products/led-display', '/products'],
  ['/products/indoor-led-display', '/indoor-led'], ['/products/outdoor-led-display', '/outdoor-led'],
  ['/products/spherical-led-display', '/products'], ['/products/transparent-led-display', '/glassmorph'],
  ['/products/rental-led-display', '/products'], ['/products/flexible-led-display', '/products'],
  ['/download-catalog', '/products'], ['/about-us', '/about'], ['/contact-us', '/contact'],
  ['/portfolio', '/projects'], ['/gallery', '/projects'], ['/led-screen-dubai', '/led-screen-suppliers-dubai'],
  ['/led-display-abu-dhabi', '/abu-dhabi'], ['/led-screen-saudi-arabia', '/saudi-arabia'], ['/led-screen-qatar', '/qatar'],
  ['/products/led-display-modules', '/products'], ['/products/outdoor-led-display-modules', '/products'],
  ['/products/outdoor-smd-led-display', '/outdoor-led'], ['/products/outdoor-dip-led-display', '/outdoor-led'],
  ['/products/transparent-glass-led-display', '/glassmorph'], ['/products/curtain-led-display', '/glassmorph'],
  ['/products/soft-flexible-led-display-modules', '/products/bl-flx150'], ['/products/curve-flexible-led-display', '/products/bl-flx150'],
  ['/products/floor-led-display', '/products/immersafloor-p39'], ['/products/road-signal-led-display', '/products/bl-obx390'],
  ['/perimeter-led-display', '/products/bl-spx470'], ['/die-cast-rental-led-display', '/products/bl-rpx290'],
  ['/shelf-led-display', '/products/bl-shf120'], ['/lumimorph-elite', '/lumimorph/elite'],
];

const nextConfig: NextConfig = {
  output: 'standalone',
  turbopack: { root: process.cwd() },
  skipTrailingSlashRedirect: true,
  async redirects() {
    return [
      ...legacyRedirects.flatMap(([source, destination]) => [
        { source, destination, statusCode: 301 },
        { source: `${source}/`, destination, statusCode: 301 },
      ]),
      {
        source: '/products',
        has: [{ type: 'query', key: 'category', value: 'luxury-home-cinema' }],
        destination: '/luxury-home-cinema',
        statusCode: 301,
      },
    ];
  },
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${process.env.API_ORIGIN}/api/:path*` }];
  },
  async headers() {
    if (process.env.NEXT_PUBLIC_STAGING !== '1') return [];
    return [{ source: '/:path*', headers: [{ key: 'X-Robots-Tag', value: 'noindex, nofollow, noarchive' }] }];
  },
};

export default nextConfig;
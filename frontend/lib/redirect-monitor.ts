export type RedirectMonitorItem = {
  source: string;
  destination: string;
  status: 'LOCAL PASS' | 'REMOTE PENDING';
};

export const redirectMonitorItems: readonly RedirectMonitorItem[] = [
  { source: '/products/led-display', destination: '/products', status: 'LOCAL PASS' },
  { source: '/products/outdoor-smd-led-display', destination: '/outdoor-led', status: 'LOCAL PASS' },
  { source: '/products/outdoor-dip-led-display', destination: '/outdoor-led', status: 'LOCAL PASS' },
  { source: '/products/transparent-glass-led-display', destination: '/glassmorph', status: 'LOCAL PASS' },
  { source: '/products/curtain-led-display', destination: '/glassmorph', status: 'LOCAL PASS' },
  { source: '/products/soft-flexible-led-display-modules', destination: '/products/bl-flx150', status: 'LOCAL PASS' },
  { source: '/products/floor-led-display', destination: '/products/immersafloor-p39', status: 'LOCAL PASS' },
  { source: '/products/road-signal-led-display', destination: '/products/bl-obx390', status: 'LOCAL PASS' },
  { source: '/perimeter-led-display', destination: '/products/bl-spx470', status: 'LOCAL PASS' },
  { source: '/die-cast-rental-led-display', destination: '/products/bl-rpx290', status: 'LOCAL PASS' },
  { source: '/shelf-led-display', destination: '/products/bl-shf120', status: 'LOCAL PASS' },
  { source: '/lumimorph-elite', destination: '/lumimorph/elite', status: 'LOCAL PASS' },
];

export const remoteAcceptanceChecks = [
  'Confirm the production-equivalent origin returns each redirect in one hop with HTTP 301.',
  'Inspect sitemap discovery and robots fetch status in Google Search Console after deployment.',
  'Compare indexed/canonical URL counts and soft-404 coverage against the baseline.',
  'Measure remote LCP, INP and transfer size against the legacy CRA reference.',
] as const;
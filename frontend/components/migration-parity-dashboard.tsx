import { RedirectMonitorDashboard } from './redirect-monitor-dashboard';

const areas = [
  ['Routes', 'PASS'], ['Shared shell', 'PASS'], ['Homepage', 'PASS'], ['Products catalogue', 'PASS'],
  ['Filters', 'PASS'], ['Finder', 'PASS'], ['Product details', 'PASS'], ['Comparison', 'PASS'],
  ['RFQ/forms', 'PASS'], ['Analytics', 'LOCAL PASS'], ['Visual parity', 'PASS'], ['Mobile parity', 'PASS'],
  ['Performance', 'LOCAL ONLY'], ['SEO regression', 'PASS'], ['Cloudflare local', 'PASS'],
  ['Cloudflare remote', 'BLOCKED'], ['Phase 3 final acceptance', 'REMOTE GATE'],
] as const;

const evidence = [
  '352-route baseline reconciliation is manifest-backed with no unexplained local routes.',
  'OpenNext local workerd is verified on a single healthy Node 22 process.',
  'Product, comparison and RFQ flows use real catalogue and lead APIs.',
  'SEO routing, sitemap, robots, SSR metadata and schema passed iteration 169 locally.',
] as const;

export function MigrationParityDashboard() {
  return (
    <main className="migration-dashboard" data-testid="migration-parity-dashboard">
      <p className="eyebrow">Internal migration review</p>
      <h1 data-testid="migration-dashboard-title">Parity dashboard</h1>
      <p data-testid="migration-dashboard-notice">This route is staging-only, noindex, excluded from the sitemap, and must not ship at production cutover.</p>
      <section className="parity-summary" data-testid="parity-summary">
        <div><strong>352</strong><span>Baseline routes</span></div><div><strong>333</strong><span>Canonical routes</span></div>
        <div><strong>30+</strong><span>Native redirects</span></div><div><strong>1</strong><span>Native 410</span></div><div><strong>0</strong><span>Local failures</span></div>
      </section>
      <section data-testid="migration-area-statuses"><h2>Migration areas</h2><div className="parity-grid">
        {areas.map(([name, status]) => <div key={name} data-testid={`parity-area-${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}><span>{name}</span><b className={`status-${status.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>{status}</b></div>)}
      </div></section>
      <RedirectMonitorDashboard />
      <section data-testid="migration-acceptance-evidence"><h2>Local acceptance evidence</h2><ul>{evidence.map((item) => <li key={item}>{item}</li>)}</ul></section>
    </main>
  );
}
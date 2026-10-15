import { redirectMonitorItems, remoteAcceptanceChecks } from '../lib/redirect-monitor';

export function RedirectMonitorDashboard() {
  return (
    <section className="redirect-monitor" data-testid="redirect-monitor-dashboard">
      <div className="redirect-monitor__heading">
        <div>
          <p className="eyebrow">Search readiness</p>
          <h2 data-testid="redirect-monitor-title">Redirect monitor</h2>
        </div>
        <p data-testid="redirect-monitor-local-status">Local workerd: verified · iteration 169</p>
      </div>
      <div className="redirect-monitor__summary" data-testid="redirect-monitor-summary">
        <div><strong>{redirectMonitorItems.length}</strong><span>brief redirects</span></div>
        <div><strong>1</strong><span>intentional 410</span></div>
        <div><strong>0</strong><span>local failures</span></div>
        <div><strong>Pending</strong><span>remote GSC check</span></div>
      </div>
      <div className="redirect-monitor__table-wrap" style={{ maxWidth: '100%', overflow: 'visible' }}>
        <table data-testid="redirect-monitor-table" style={{ minWidth: 0, tableLayout: 'fixed' }}>
          <thead><tr><th style={{ overflowWrap: 'anywhere' }}>Legacy URL</th><th style={{ overflowWrap: 'anywhere' }}>Destination</th><th style={{ overflowWrap: 'anywhere' }}>Local result</th></tr></thead>
          <tbody>
            {redirectMonitorItems.map((item) => (
              <tr key={item.source} data-testid={`redirect-monitor-row-${item.source.slice(1).replace(/[^a-z0-9]+/g, '-')}`}>
                <td style={{ overflowWrap: 'anywhere', wordBreak: 'break-word' }}><code>{item.source}</code></td><td style={{ overflowWrap: 'anywhere', wordBreak: 'break-word' }}><code>{item.destination}</code></td><td style={{ overflowWrap: 'anywhere', wordBreak: 'break-word' }}><b className="status-pass">{item.status}</b></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="redirect-monitor__mobile-list" data-testid="redirect-monitor-mobile-list">
        {redirectMonitorItems.map((item) => (
          <article key={item.source} className="redirect-monitor__mobile-item" data-testid={`redirect-monitor-mobile-item-${item.source.slice(1).replace(/[^a-z0-9]+/g, '-')}`}>
            <span>Legacy URL</span><code>{item.source}</code><span>Destination</span><code>{item.destination}</code><b className="status-pass">{item.status}</b>
          </article>
        ))}
      </div>
      <div className="redirect-monitor__remote" data-testid="redirect-monitor-remote-gate">
        <p className="eyebrow">Remote acceptance gate</p>
        <h3>Requires authorized staging</h3>
        <ul>{remoteAcceptanceChecks.map((check) => <li key={check}>{check}</li>)}</ul>
      </div>
    </section>
  );
}
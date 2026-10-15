import { SafeLink as Link } from './safe-link';
import { getShortHeading, type LegacyPage } from '../lib/legacy-content';

const routeLinks = [
  ['Explore LED displays', '/products'],
  ['Plan a solution', '/solutions'],
  ['Technical resources', '/resources'],
  ['Talk to an engineer', '/contact'],
] as const;

export function SeoContentBlock({ page }: { page: LegacyPage }) {
  const topic = getShortHeading(page);
  const links = page.route === '/blog/led-display-solutions-abu-dhabi-guide'
    ? [...routeLinks, ['Abu Dhabi video walls', '/abu-dhabi']] as const
    : routeLinks;
  return <section className="seo-content-block" data-testid="seo-content-block">
    <p className="eyebrow">Specification guidance</p>
    <h2>{topic} — project planning</h2>
    <div className="seo-content-block__copy"><p>{page.description} Brightluxx helps teams translate viewing distance, ambient light, operating hours and site constraints into an LED display specification that can be installed, maintained and expanded with confidence.</p><p>Start with the audience and environment, then confirm pixel pitch, brightness, processing, power access and serviceability. Our engineering team can review drawings, recommend a suitable display family and coordinate the practical requirements for delivery and commissioning.</p></div>
    <nav className="seo-content-block__links" aria-label="Related Brightluxx resources">{links.map(([label, href]) => <Link href={href} prefetch={false} key={href} data-testid={`seo-internal-link-${href.slice(1).replace(/[^a-z0-9]+/g, '-') || 'home'}`}>{label}<span>→</span></Link>)}</nav>
  </section>;
}
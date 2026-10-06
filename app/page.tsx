import type { Metadata } from 'next';
import { SafeLink as Link } from '../components/safe-link';
import { getLegacyPage } from '../lib/legacy-content';
import { StructuredData } from '../components/structured-data';
import { HomeCounters } from '../components/home-counters';
import { HomeVideoHero } from '../components/home-video-hero';

const solutionPaths = [['Retail & Hospitality', '/solutions/retail'], ['Corporate & Control Rooms', '/solutions/corporate'], ['Architecture & Public Realm', '/solutions/architecture'], ['Digital Signage', '/signage-solutions']];
const projects = [['Dubai Mall', 'Retail LED', '/projects'], ['SZR Network', 'DOOH', '/projects'], ['ADNOC HQ', 'Control Room', '/projects']];
const families = [['FINE-PITCH & MICROLED', 'LumiMorph™', '/lumimorph', 'https://files.ihgbrands.com/brightluxx/site-images/opt-family-lumimorph.webp'], ['ARCHITECTURAL DISPLAYS', 'NaturaTex™', '/naturatex', 'https://files.ihgbrands.com/brightluxx/site-images/opt_fam_naturatex.webp'], ['INTERACTIVE SIGNAGE', 'SignaTouch™', '/signatouch', 'https://files.ihgbrands.com/brightluxx/site-images/opt_fam_signatouch.webp'], ['TRANSPARENT LED', 'GlassMorph™', '/glassmorph', 'https://files.ihgbrands.com/brightluxx/site-images/opt_fam_glassmorph.webp']];
const pathways = [['For Specifiers', '/for-architects'], ['Abu Dhabi Video Walls', '/abu-dhabi'], ['Smart Signage', '/signage-solutions'], ['Expert Resources', '/resources'], ['Virtual Showroom', '/showroom']];

export async function generateMetadata(): Promise<Metadata> { const page = await getLegacyPage('/'); return { title: page?.title, description: page?.description, alternates: { canonical: page?.canonical } }; }

export default async function HomePage() {
  const page = await getLegacyPage('/');
  return <main className="homepage" data-testid="homepage"><StructuredData items={page?.jsonLd || []} />
    <HomeVideoHero />
    <HomeCounters />
    <section className="home-band home-editorial-intro" data-testid="home-discovery-paths"><p className="eyebrow">LED display applications</p><div className="home-editorial-intro__heading"><h2>Made for the moment a space changes.</h2><p>Start with the environment, the audience and the purpose. We align display technology with the operational details that make a project last.</p></div><div className="home-link-grid">{solutionPaths.map(([label, href]) => <Link key={label} href={href} data-testid={`home-solution-link-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>{label}<span>→</span></Link>)}</div></section>
    <section className="home-band" data-testid="featured-projects-section"><p className="eyebrow">Installed across the GCC</p><h2>Real Projects</h2><div className="home-link-grid">{projects.map(([title, type, href]) => <Link key={title} href={href} data-testid={`home-featured-project-${title.toLowerCase().replace(/[^a-z]+/g, '-')}`}><small>{type}</small>{title}<span>View Project →</span></Link>)}</div></section>
    <section className="home-band" data-testid="product-families-section"><p className="eyebrow">LED display technologies</p><h2>Display Tech</h2><div className="home-family-grid">{families.map(([type, name, href, image]) => <Link href={href} key={name}><img src={image} alt={`${type} — ${name}`} loading="lazy"/><span>{type}</span><h3>{name}</h3></Link>)}</div></section>
    <section className="home-band" data-testid="why-brightluxx-section"><h2>Why Brightluxx</h2><div className="home-link-grid">{[['Since 2005','Two decades of LED excellence.'],['In-house production','Complete manufacturing control.'],['Local stock','Ready for project planning in Dubai.'],['Fast delivery','Regional delivery coordination.']].map(([title,text]) => <article key={title}><h3>{title}</h3><p>{text}</p></article>)}</div></section>
    <section className="home-band" data-testid="home-professional-pathways"><h2>For Specifiers</h2><div className="home-link-grid">{pathways.map(([title, href]) => <Link key={title} href={href} data-testid={`home-pathway-${title.toLowerCase().replace(/[^a-z]+/g, '-')}`}>{title}<span>Explore →</span></Link>)}</div></section>
    <section className="home-band" data-testid="home-insights-section"><p className="eyebrow">From the technical desk</p><h2>Latest Thinking</h2><div className="home-link-grid">{[['Pricing Guide', '/blog/led-display-pricing-guide-uae'],['Indoor or Outdoor', '/blog/indoor-vs-outdoor-led-screen-dubai'],['Buyer’s Checklist', '/blog/led-wall-buyers-checklist']].map(([title, href]) => <Link key={title} href={href}>{title}<span>Read →</span></Link>)}</div></section>
    <section className="home-band home-cta" data-testid="cta-section"><h2>Start Here</h2><p>Plan your display with Brightluxx engineering.</p><nav><Link href="/contact" data-testid="home-cta-contact">Start Project</Link><Link href="/calculator" data-testid="home-cta-calculator">Screen Calculator</Link></nav></section>
  </main>;
}
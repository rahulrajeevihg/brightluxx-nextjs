import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { MigrationParityDashboard } from '../../components/migration-parity-dashboard';
import { FamilyProductSchema } from '../../components/family-product-schema';
import { BrandVideoShowcase } from '../../components/brand-video-showcase';
import { RouteSeoDetail } from '../../components/route-seo-detail';
import { SeoContentBlock } from '../../components/seo-content-block';
import { StructuredData } from '../../components/structured-data';
import { enrichLegacyHtml, getIndexableRoutes, getLegacyPage, getPageKeywords, getSeoDescription, getSeoTitle } from '../../lib/legacy-content';

type Props = {
  params: Promise<{ slug: string[] }>;
};

const routeFromParams = (slug: string[]) => `/${slug.join('/')}`;
const isDedicatedRoute = (route: string) => (
  route === '/' ||
  route === '/products' ||
  route === '/compare' ||
  route === '/contact' ||
  route === '/luxury-home-cinema' ||
  route.startsWith('/products/')
);

export const dynamicParams = true;

export async function generateStaticParams() {
  const pages = await getIndexableRoutes();
  return pages
    .filter((page) => !isDedicatedRoute(page.route))
    .map((page) => ({ slug: page.route.slice(1).split('/') }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const route = routeFromParams((await params).slug);
  if (route === '/__migration-parity') {
    return {
      title: 'Migration Parity Dashboard',
      robots: { index: false, follow: false },
    };
  }
  const page = await getLegacyPage(route);
  if (!page) return {};
  return {
    title: getSeoTitle(page),
    description: getSeoDescription(page),
    keywords: getPageKeywords(page),
    alternates: { canonical: page.canonical },
  };
}

export default async function LegacyParityPage({ params }: Props) {
  const route = routeFromParams((await params).slug);
  if (route === '/__migration-parity') return <MigrationParityDashboard />;

  const page = await getLegacyPage(route);
  if (!page) notFound();

  return (
    <main className="legacy-page" data-testid="next-server-rendered-parity-page">
      <StructuredData items={page.jsonLd || []} />
      <FamilyProductSchema route={route} />
      <article
        className="legacy-page__content"
        data-testid="legacy-page-content"
        dangerouslySetInnerHTML={{ __html: enrichLegacyHtml(page.html, page) }}
      />
      <SeoContentBlock page={page} />
      <RouteSeoDetail route={route} />
      <BrandVideoShowcase route={route} />
    </main>
  );
}
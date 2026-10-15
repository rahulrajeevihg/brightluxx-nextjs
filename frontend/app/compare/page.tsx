import type { Metadata } from 'next';
import { CompareWorkspace } from '../../components/compare-workspace';
import { StructuredData } from '../../components/structured-data';
import { getCatalogue } from '../../lib/catalogue';
import { getLegacyPage } from '../../lib/legacy-content';

export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  const page = await getLegacyPage('/compare');
  return {
    title: page?.title || 'Compare LED Products',
    description: page?.description,
    alternates: { canonical: page?.canonical || 'https://brightluxx.com/compare' },
  };
}

export default async function ComparePage() {
  const [products, page] = await Promise.all([getCatalogue(), getLegacyPage('/compare')]);
  return (
    <main className="compare-page" data-testid="compare-page">
      <StructuredData items={page?.jsonLd || []} />
      <header>
        <p className="eyebrow">Specification engine</p>
        <h1 data-testid="compare-page-title">Compare Displays</h1>
        <p>Select up to three displays to review engineering specifications side by side.</p>
      </header>
      <CompareWorkspace products={products} />
    </main>
  );
}
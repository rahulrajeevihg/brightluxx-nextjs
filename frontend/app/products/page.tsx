import type { Metadata } from 'next';
import { ProductCatalogue } from '../../components/product-catalogue';
import { getCatalogue } from '../../lib/catalogue';
import { getLegacyPage } from '../../lib/legacy-content';
import { StructuredData } from '../../components/structured-data';

export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  const page = await getLegacyPage('/products');
  return { title: page?.title || 'LED Display Products | Supplier Dubai UAE', description: page?.description, alternates: { canonical: page?.canonical || 'https://brightluxx.com/products' } };
}

export default async function ProductsPage() {
  const [products, page] = await Promise.all([getCatalogue(), getLegacyPage('/products')]);
  return <main className="products-page" data-testid="products-page"><StructuredData items={page?.jsonLd || []} /><section className="products-hero" data-testid="products-hero"><img src="https://files.ihgbrands.com/site-images_opt_ext_00eecd7267f8.webp" alt="LED display technology" fetchPriority="high" /><div><p className="eyebrow">Brightluxx catalogue</p><h1 data-testid="products-page-title">LED Displays</h1><p>94 professional LED display solutions for every application.</p></div></section><ProductCatalogue products={products} /></main>;
}
import type { Metadata } from 'next';
import { ProductCard } from '../../components/product-card';
import { StructuredData } from '../../components/structured-data';
import { getCachedCatalogue } from '../../lib/catalogue';

export const metadata: Metadata = {
  title: 'Luxury Home Cinema LED Displays | Brightluxx',
  description: 'Explore luxury home cinema LED displays with specification support for private screening rooms, living spaces and outdoor cinema projects.',
  alternates: { canonical: 'https://brightluxx.com/luxury-home-cinema' },
};

export default async function LuxuryHomeCinemaPage() {
  const products = (await getCachedCatalogue()).filter((product) => product.category === 'home-cinema');
  const schema = { '@context': 'https://schema.org', '@type': 'CollectionPage', name: 'Luxury Home Cinema LED Displays', url: 'https://brightluxx.com/luxury-home-cinema' };
  return (
    <main className="products-page" data-testid="luxury-home-cinema-page">
      <StructuredData items={[JSON.stringify(schema)]} />
      <section className="products-hero" data-testid="luxury-home-cinema-hero">
        <img src="https://files.ihgbrands.com/hero-video-poster.webp" alt="Luxury home cinema LED display installation" fetchPriority="high" />
        <div><p className="eyebrow">Private cinema</p><h1 data-testid="luxury-home-cinema-title">Luxury Home Cinema</h1><p>LED display options for private screening rooms, living spaces, outdoor cinema and simulation environments.</p></div>
      </section>
      <section className="home-band" data-testid="luxury-home-cinema-guidance"><h2>Specify for the room</h2><p>Start with the closest viewer, ambient light, content format and architectural constraints. Brightluxx coordinates pixel pitch, screen size, processing, mounting, power and service access so a home cinema display can be assessed as a complete system.</p></section>
      <section className="catalogue" data-testid="luxury-home-cinema-products"><div className="catalogue-grid">{products.map((product) => <ProductCard product={product} key={product.id || product.slug} />)}</div></section>
    </main>
  );
}
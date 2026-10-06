import { familyProductSchemas } from '../lib/seo-overrides';
import { StructuredData } from './structured-data';

export function FamilyProductSchema({ route }: { route: string }) {
  const family = familyProductSchemas[route as keyof typeof familyProductSchemas];
  if (!family) return null;
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: family.name,
    sku: family.sku,
    image: family.image,
    description: family.description,
    brand: { '@type': 'Brand', name: 'Brightluxx' },
    offers: {
      '@type': 'AggregateOffer',
      lowPrice: '2500',
      highPrice: '12000',
      priceCurrency: 'AED',
      availability: 'https://schema.org/InStock',
    },
  };
  return <StructuredData items={[JSON.stringify(schema)]} />;
}
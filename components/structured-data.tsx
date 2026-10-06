import { safeJsonLd } from '../lib/content-safety';

export function StructuredData({ items }: { items: string[] }) {
  return items.map(safeJsonLd).flatMap((item, index) => item ? [<script key={index} type="application/ld+json" dangerouslySetInnerHTML={{ __html: item }} />] : []);
}
'use client';

import { SafeLink as Link } from './safe-link';
import type { Product } from '../lib/catalogue';

function comparedCodes() {
  try { return JSON.parse(window.localStorage.getItem('brightluxx_compare_products') || '[]') as string[]; } catch { return []; }
}

export function ProductCard({ product }: { product: Product }) {
  const addToCompare = () => {
    const current = comparedCodes();
    if (current.includes(product.product_code)) return;
    if (current.length >= 3) { window.dispatchEvent(new CustomEvent('brightluxx-compare-notice', { detail: 'You can compare up to three products at a time.' })); return; }
    window.localStorage.setItem('brightluxx_compare_products', JSON.stringify([...current, product.product_code]));
    window.dispatchEvent(new Event('brightluxx-compare-change'));
  };
  return <article className="catalogue-card" data-testid={`products-product-card-${product.slug}`}>
    <Link href={`/products/${product.slug}`} prefetch={false} className="catalogue-card__image" data-testid={`products-product-image-${product.slug}`}>
      {product.image_url ? <img src={product.image_url} alt={`${product.name}${product.pixel_pitch ? ` ${product.pixel_pitch}` : ''} LED display for ${product.application || 'professional installations'}`} loading="lazy" /> : <span aria-hidden="true">LED</span>}
      {product.pixel_pitch && <b>{product.pixel_pitch}</b>}
    </Link>
    <div className="catalogue-card__body"><p>{product.category.replaceAll('-', ' ')}</p><h3>{product.name}</h3>
      {product.application && <small>Best for: {product.application}</small>}
      <div className="catalogue-specs">{product.pixel_pitch && <span>{product.pixel_pitch}</span>}{product.brightness && <span>{product.brightness}</span>}{product.refresh_rate && <span>{product.refresh_rate}</span>}</div>
      <div className="catalogue-card__actions"><Link href={`/products/${product.slug}`} prefetch={false} data-testid={`products-view-product-${product.slug}`}>View Product <span>→</span></Link><button type="button" onClick={addToCompare} data-testid={`products-compare-${product.slug}`}>Compare</button></div>
    </div>
  </article>;
}
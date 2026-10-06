'use client';

import { useState } from 'react';
import { trackEvent } from '../lib/analytics';

function codes() { try { return JSON.parse(localStorage.getItem('brightluxx_compare_products') || '[]') as string[]; } catch { return []; } }

export function ProductDetailActions({ code, name }: { code: string; name: string }) {
  const [notice, setNotice] = useState('');
  const compare = () => { const current = codes(); if (current.includes(code)) { localStorage.setItem('brightluxx_compare_products', JSON.stringify(current.filter((item) => item !== code))); setNotice('Removed from comparison.'); trackEvent('product_compare_remove', { product_code: code, product_name: name }); } else if (current.length >= 3) setNotice('Comparison already has three products.'); else { localStorage.setItem('brightluxx_compare_products', JSON.stringify([...current, code])); setNotice('Added to comparison.'); trackEvent('product_compare_add', { product_code: code, product_name: name }); } window.dispatchEvent(new Event('brightluxx-compare-change')); };
  return <div className="product-detail-actions"><a href={`/contact?products=${encodeURIComponent(code)}`} onClick={() => trackEvent('RFQ_started', { product_code: code, product_name: name, form_type: 'product_detail' })} data-testid="product-request-pricing-link">Request Project Pricing</a><button type="button" onClick={compare} data-testid="product-compare-button">Add to Compare</button><a href={`https://wa.me/971559954274?text=${encodeURIComponent(`Hi, I need pricing for ${code} - ${name}`)}`} onClick={() => trackEvent('WhatsApp_click', { product_code: code, product_name: name })} target="_blank" rel="noreferrer" data-testid="product-whatsapp-link">WhatsApp</a>{notice && <p role="status" data-testid="product-compare-notice">{notice} <a href="/compare" data-testid="product-compare-now-link">Compare now</a></p>}</div>;
}
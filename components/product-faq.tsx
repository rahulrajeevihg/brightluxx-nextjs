'use client';

import { useState } from 'react';

export function ProductFaq({ items }: { items: { q: string; a: string }[] }) {
  const [open, setOpen] = useState<number | null>(null);
  return <div className="product-faq" data-testid="product-faq-section">{items.map((item, index) => <article key={item.q}><button type="button" onClick={() => setOpen(open === index ? null : index)} aria-expanded={open === index} data-testid={`product-faq-toggle-${index}`}><span>{item.q}</span><b>{open === index ? '−' : '+'}</b></button>{open === index && <p data-testid={`product-faq-answer-${index}`}>{item.a}</p>}</article>)}</div>;
}
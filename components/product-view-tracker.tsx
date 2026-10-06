'use client';

import { useEffect } from 'react';
import { trackEvent } from '../lib/analytics';

export function ProductViewTracker({ code, name, category }: { code: string; name: string; category: string }) {
  useEffect(() => { trackEvent('product_view', { product_code: code, product_name: name, filters: category }); }, [code, name, category]);
  return null;
}
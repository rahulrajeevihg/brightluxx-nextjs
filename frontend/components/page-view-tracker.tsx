'use client';

import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { trackEvent } from '../lib/analytics';

export function PageViewTracker() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  useEffect(() => {
    const query = searchParams.toString();
    const timer = window.setTimeout(() => trackEvent('page_view', { page: query ? `${pathname}?${query}` : pathname }), 350);
    return () => window.clearTimeout(timer);
  }, [pathname, searchParams]);
  return null;
}
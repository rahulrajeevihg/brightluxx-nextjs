import type { Metadata } from 'next';
import { Suspense } from 'react';
import { PageViewTracker } from '../components/page-view-tracker';
import { SiteHeader } from '../components/site-header';
import { SiteFooter } from '../components/site-footer';
import { CookieConsent } from '../components/cookie-consent';
import { FloatingActions } from '../components/floating-actions';
import './styles.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://brightluxx.com'),
  title: { default: 'Brightluxx — Premium LED Display Solutions', template: '%s' },
  ...(process.env.NEXT_PUBLIC_STAGING === '1' ? { robots: { index: false, follow: false, nocache: true } } : {}),
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><Suspense fallback={null}><PageViewTracker /></Suspense><SiteHeader />{children}<SiteFooter /><FloatingActions /><CookieConsent /></body></html>;
}
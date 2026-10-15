import type { Metadata } from 'next';
import { ContactChannels } from '../../components/contact-channels';
import { ContactForm } from '../../components/contact-form';
import { StructuredData } from '../../components/structured-data';
import { getLegacyPage } from '../../lib/legacy-content';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

type Props = {
  searchParams: Promise<{ products?: string }>;
};

export async function generateMetadata(): Promise<Metadata> {
  const page = await getLegacyPage('/contact');
  return {
    title: page?.title || 'Contact Brightluxx',
    description: page?.description,
    alternates: { canonical: page?.canonical || 'https://brightluxx.com/contact' },
  };
}

export default async function ContactPage({ searchParams }: Props) {
  const [page, query] = await Promise.all([getLegacyPage('/contact'), searchParams]);
  const productCodes = (query.products || '')
    .split(',')
    .map((code) => code.trim())
    .filter(Boolean)
    .slice(0, 3);

  return (
    <main className="contact-page" data-testid="contact-page">
      <StructuredData items={page?.jsonLd || []} />
      <header>
        <p className="eyebrow">Brightluxx Dubai</p>
        <h1 data-testid="contact-page-title">Get in Touch</h1>
        <p>Talk to an LED display specialist about your site, timeline and technical requirements.</p>
      </header>
      <section className="contact-layout">
        <aside data-testid="contact-details">
          <p className="eyebrow">Contact details</p>
          <h2 data-testid="contact-details-title">Engineering support for every stage</h2>
          <ContactChannels />
          <p data-testid="contact-address">Jebel Ali Industrial Area 1<br />Dubai, United Arab Emirates</p>
        </aside>
        <ContactForm productCodes={productCodes} />
      </section>
    </main>
  );
}
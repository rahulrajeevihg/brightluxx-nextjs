'use client';

import { trackEvent } from '../lib/analytics';

export function ContactChannels() { return <><a href="tel:+97142585754" onClick={() => trackEvent('phone_click', { form_type: 'contact' })} data-testid="contact-phone-link">+971 4 258 5754</a><a href="mailto:sales@brightluxx.com" data-testid="contact-email-link">sales@brightluxx.com</a><a href="https://wa.me/971559954274" onClick={() => trackEvent('WhatsApp_click', { form_type: 'contact' })} target="_blank" rel="noreferrer" data-testid="contact-whatsapp-link">WhatsApp</a></>; }
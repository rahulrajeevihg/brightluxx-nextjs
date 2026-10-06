'use client';

import { useEffect, useState } from 'react';
import { trackEvent } from '../lib/analytics';
import { ContactFormFields } from './contact-form-fields';
import { emptyContactFields, type ContactFields } from './contact-form-types';

type SubmissionStatus = 'idle' | 'success' | 'error';

export function ContactForm({ productCodes }: { productCodes: string[] }) {
  const [fields, setFields] = useState<ContactFields>(emptyContactFields);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<SubmissionStatus>('idle');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (productCodes.length) {
      trackEvent('RFQ_started', { comparison_codes: productCodes, form_type: 'contact_rfq' });
    }
  }, [productCodes.join(',')]);

  const change = (key: keyof ContactFields, value: string) => {
    setFields((current) => ({ ...current, [key]: value }));
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setStatus('idle');
    try {
      const response = await fetch('/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...fields,
          product_interest: productCodes.length ? productCodes.join(', ') : undefined,
          source: productCodes.length ? 'comparison_request' : 'contact_form',
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to submit your request.');
      setStatus('success');
      setMessage(data.message || 'Thank you. Our team will be in touch shortly.');
      trackEvent('contact_submission', {
        form_type: productCodes.length ? 'comparison_request' : 'contact_form',
        comparison_codes: productCodes,
      });
      if (productCodes.length) {
        trackEvent('RFQ_completed', { form_type: 'comparison_request', comparison_codes: productCodes });
      }
      setFields(emptyContactFields);
    } catch (error) {
      setStatus('error');
      setMessage(error instanceof Error ? error.message : 'Unable to submit your request.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="contact-form" onSubmit={submit} data-testid="contact-form">
      <h2 data-testid="contact-form-title">Request project pricing</h2>
      {productCodes.length > 0 && (
        <p className="contact-product-context" data-testid="contact-product-context">
          Pricing request for <strong>{productCodes.join(', ')}</strong>
        </p>
      )}
      {status !== 'idle' && (
        <p className={`contact-form__status ${status}`} role="status" data-testid="contact-form-status">
          {message}
        </p>
      )}
      <ContactFormFields fields={fields} onChange={change} />
      <button type="submit" disabled={submitting} data-testid="contact-submit-button">
        {submitting ? 'Submitting…' : 'Send request →'}
      </button>
      <p className="contact-form__note" data-testid="contact-form-note">
        Hardware, processing and cabling are scoped first. Installation and structural works follow a site survey.
      </p>
    </form>
  );
}
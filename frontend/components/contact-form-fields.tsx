import type { ContactFields } from './contact-form-types';

type ContactFormFieldsProps = {
  fields: ContactFields;
  onChange: (key: keyof ContactFields, value: string) => void;
};

export function ContactFormFields({ fields, onChange }: ContactFormFieldsProps) {
  return (
    <>
      <div className="contact-form__grid">
        <label>
          Full name <b>*</b>
          <input required value={fields.name} onChange={(event) => onChange('name', event.target.value)} data-testid="contact-name-input" />
        </label>
        <label>
          Company
          <input value={fields.company} onChange={(event) => onChange('company', event.target.value)} data-testid="contact-company-input" />
        </label>
        <label>
          Email <b>*</b>
          <input type="email" required value={fields.email} onChange={(event) => onChange('email', event.target.value)} data-testid="contact-email-input" />
        </label>
        <label>
          Phone <b>*</b>
          <input type="tel" required value={fields.phone} onChange={(event) => onChange('phone', event.target.value)} data-testid="contact-phone-input" />
        </label>
        <label>
          City <b>*</b>
          <input required value={fields.city} onChange={(event) => onChange('city', event.target.value)} data-testid="contact-city-input" />
        </label>
        <label>
          Application <b>*</b>
          <select required value={fields.application} onChange={(event) => onChange('application', event.target.value)} data-testid="contact-application-select">
            <option value="">Select application</option>
            <option value="Retail">Retail & shopping malls</option>
            <option value="Corporate">Corporate & boardrooms</option>
            <option value="Outdoor">Outdoor advertising</option>
            <option value="Events">Events & staging</option>
            <option value="Hospitality">Hospitality</option>
            <option value="Government">Government</option>
            <option value="Other">Other</option>
          </select>
        </label>
        <label>
          Timeline
          <select value={fields.timeline} onChange={(event) => onChange('timeline', event.target.value)} data-testid="contact-timeline-select">
            <option value="">Select timeline</option>
            <option value="Urgent (1-2 weeks)">Urgent (1–2 weeks)</option>
            <option value="1-3 months">1–3 months</option>
            <option value="3-6 months">3–6 months</option>
            <option value="6+ months">6+ months</option>
            <option value="Just exploring">Just exploring</option>
          </select>
        </label>
        <label>
          Budget range
          <select value={fields.budget} onChange={(event) => onChange('budget', event.target.value)} data-testid="contact-budget-select">
            <option value="">Select budget</option>
            <option value="Under AED 200k">Under AED 200k</option>
            <option value="AED 200k - 400k">AED 200k – 400k</option>
            <option value="AED 400k - 1M">AED 400k – 1M</option>
            <option value="AED 1M+">AED 1M+</option>
            <option value="Not decided">Not decided</option>
          </select>
        </label>
      </div>
      <label>
        Project details
        <textarea rows={5} value={fields.message} onChange={(event) => onChange('message', event.target.value)} data-testid="contact-message-input" />
      </label>
      <div className="contact-honeypot" aria-hidden="true">
        <input tabIndex={-1} autoComplete="off" value={fields.website} onChange={(event) => onChange('website', event.target.value)} data-testid="contact-website-honeypot" />
        <input tabIndex={-1} autoComplete="off" value={fields.fax} onChange={(event) => onChange('fax', event.target.value)} data-testid="contact-fax-honeypot" />
      </div>
    </>
  );
}
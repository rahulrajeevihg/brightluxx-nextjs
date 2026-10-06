import { routeSeoDetails } from '../lib/seo-overrides';

export function RouteSeoDetail({ route }: { route: string }) {
  const detail = routeSeoDetails[route];
  if (!detail) return null;

  return (
    <section className="seo-content-block route-seo-detail" data-testid={`route-seo-detail-${route.slice(1).replace(/[^a-z0-9]+/g, '-')}`}>
      <p className="eyebrow">Project-specific guidance</p>
      <h2>{detail.heading}</h2>
      <div className="seo-content-block__copy">
        <div>{detail.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}</div>
        <ul data-testid={`route-seo-checklist-${route.slice(1).replace(/[^a-z0-9]+/g, '-')}`}>
          {detail.checklist.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </div>
    </section>
  );
}
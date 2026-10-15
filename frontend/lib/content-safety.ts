const unsafeHtml = /<\s*(script|iframe|object|embed|base|form)\b|\bon[a-z]+\s*=|(?:href|src)\s*=\s*["']?\s*javascript:|data:\s*text\/html/i;

export function validateTrustedHtml(html: string) {
  if (unsafeHtml.test(html)) throw new Error('Unsafe legacy HTML content was rejected');
  return html;
}

export function safeJsonLd(item: string) {
  try {
    const parsed: unknown = JSON.parse(item);
    if (!parsed || typeof parsed !== 'object') return null;
    return JSON.stringify(parsed).replace(/</g, '\\u003c').replace(/>/g, '\\u003e').replace(/&/g, '\\u0026');
  } catch { return null; }
}
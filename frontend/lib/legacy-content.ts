import { validateTrustedHtml } from './content-safety';
import { citySeo } from './seo-overrides';

export type LegacyPage = { route: string; title: string; description: string; canonical: string; h1: string; schemaTypes: string[] };

type EmbeddedPage = LegacyPage & { classification: string; html: string; jsonLd: string[] };
const assetPath = '/_data/legacy-pages.json';
let pagesPromise: Promise<EmbeddedPage[]> | undefined;
const displayHeadings: Record<string, string> = {
  '/dubai': 'Dubai Displays', '/abu-dhabi': 'Abu Dhabi', '/oman': 'Oman Displays', '/qatar': 'Qatar Displays', '/saudi-arabia': 'Saudi Displays', '/bahrain': 'Bahrain Displays', '/kuwait': 'Kuwait Displays',
  '/solutions/education': 'Education Displays', '/solutions/retail': 'Retail Displays', '/solutions/corporate': 'Corporate Displays', '/solutions/hospitality': 'Hospitality Displays', '/solutions/outdoor': 'Outdoor Displays', '/solutions/control-rooms': 'Control Rooms',
  '/resources': 'LED Resources', '/case-studies': 'Project Stories', '/inspirations': 'Display Ideas', '/ar-ae/dubai': 'شاشات دبي',
};

async function loadPages(): Promise<EmbeddedPage[]> {
  const { readFile } = await import('node:fs/promises');
  return validatePages(JSON.parse(await readFile(`${process.cwd()}/public/_data/legacy-pages.json`, 'utf8')) as EmbeddedPage[]);
}

function validatePages(pages: EmbeddedPage[]) {
  return pages.map((page) => ({ ...page, html: validateTrustedHtml(page.html), jsonLd: page.jsonLd.filter((item) => typeof item === 'string') }));
}

async function getPages() {
  pagesPromise ||= loadPages();
  return pagesPromise;
}

export async function getInventory(): Promise<EmbeddedPage[]> {
  return getPages();
}

export async function getLegacyPage(route: string) {
  const pages = await getPages();
  return pages.find((candidate) => candidate.route === route) || null;
}

export async function getIndexableRoutes() {
  const inventory = await getInventory();
  return inventory.filter((page) => page.classification === 'indexable' && Array.isArray(page.schemaTypes) && page.schemaTypes.length > 0);
}

export function getPageKeywords(page: LegacyPage) {
  const routeTerms = page.route.split('/').filter(Boolean).flatMap((part) => part.split('-')).filter((term) => term.length > 2);
  return Array.from(new Set([...page.title.replace(/[|—–]/g, ' ').split(/\s+/), ...routeTerms, 'LED display', 'digital signage', 'Brightluxx', 'UAE', 'GCC'])).filter((term) => term.length > 2).slice(0, 14);
}

export function getShortHeading(page: LegacyPage) {
  const city = citySeo[page.route as keyof typeof citySeo];
  return city?.heading || displayHeadings[page.route] || page.h1;
}

export function getSeoTitle(page: LegacyPage) {
  const city = citySeo[page.route as keyof typeof citySeo];
  return (city?.title || page.title).replace(/(\|\s*Brightluxx){2,}$/i, '| Brightluxx');
}

export function getSeoDescription(page: LegacyPage) {
  const city = citySeo[page.route as keyof typeof citySeo];
  return city?.description || page.description;
}

export function enrichLegacyHtml(html: string, page: LegacyPage) {
  const alt = `${page.h1} — Brightluxx LED display and digital signage solution`.replace(/"/g, '&quot;');
  const heading = getShortHeading(page).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  return html.replace(/<img(?![^>]*\balt=)/gi, `<img alt="${alt}"`).replace(/(<h1\b[^>]*>)[\s\S]*?(<\/h1>)/i, `$1${heading}$2`);
}
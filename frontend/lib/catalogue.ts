export type Product = {
  id: string;
  slug: string;
  name: string;
  product_code: string;
  category: string;
  sub_category?: string;
  application?: string;
  applications?: { title: string; description?: string }[];
  pixel_pitch?: string;
  brightness?: string;
  resolution?: string;
  refresh_rate?: string;
  image_url?: string;
  gallery?: string[];
  tagline?: string;
  description?: string;
  key_specs?: { label: string; value: string }[];
  faq?: { q: string; a: string }[];
};

type ProductsResponse = Product[] | { products?: Product[]; data?: Product[] };

export const categoryLabels: Record<string, string> = {
  'cob-microled': 'COB MicroLED', mip: 'MiP', indoor: 'Fine Pitch Indoor', 'all-in-one': 'All-in-One',
  'cinema-led': 'Cinema LED', dvled: 'DVLED Cinema', outdoor: 'Outdoor', transparent: 'Transparent',
  flexible: 'Flexible / Creative', 'custom-shapes': 'Custom Shapes', sphere: 'LED Sphere', 'naked-eye-3d': 'Naked-Eye 3D',
  'ceiling-led': 'Ceiling / Sky Screen', 'digital-signage': 'Digital Signage', 'smart-tv': 'Smart TVs',
  'ready-made': 'Ready-Made', interactive: 'Interactive Floor', 'virtual-production': 'Virtual Production',
  'poster-totem': 'LED Poster / Totem', 'shelf-edge': 'Shelf Edge', 'road-signal': 'Road Signals', accessories: 'Accessories',
  'art-immersive': 'Art & XR', 'home-cinema': 'Home Cinema',
};

function normalizedProduct(product: Product): Product {
  const refresh = product.refresh_rate || product.key_specs?.find((item) => item.label.toLowerCase() === 'refresh rate')?.value;
  return { ...product, refresh_rate: refresh };
}

export async function getCatalogue(): Promise<Product[]> {
  const apiOrigin = process.env.API_ORIGIN;
  if (!apiOrigin) throw new Error('API_ORIGIN must be configured');
  const response = await fetch(`${apiOrigin}/api/products`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Catalogue request failed: ${response.status}`);
  const payload = await response.json() as ProductsResponse;
  const products = Array.isArray(payload) ? payload : (payload.products || payload.data || []);
  return products.map(normalizedProduct);
}

export async function getCachedCatalogue(): Promise<Product[]> {
  const apiOrigin = process.env.API_ORIGIN;
  if (!apiOrigin) throw new Error('API_ORIGIN must be configured');
  const response = await fetch(`${apiOrigin}/api/products`, { next: { revalidate: 3600 } });
  if (!response.ok) throw new Error(`Catalogue request failed: ${response.status}`);
  const payload = await response.json() as ProductsResponse;
  const products = Array.isArray(payload) ? payload : (payload.products || payload.data || []);
  return products.map(normalizedProduct);
}

export async function getProduct(slug: string): Promise<Product | null> {
  const apiOrigin = process.env.API_ORIGIN;
  if (!apiOrigin) throw new Error('API_ORIGIN must be configured');
  const response = await fetch(`${apiOrigin}/api/products/${encodeURIComponent(slug)}`, { cache: 'no-store' });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Product request failed: ${response.status}`);
  return normalizedProduct(await response.json() as Product);
}
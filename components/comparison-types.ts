import type { Product } from '../lib/catalogue';

export type ComparisonRow = {
  label: string;
  value: (product: Product) => string;
};
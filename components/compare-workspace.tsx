'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { trackEvent } from '../lib/analytics';
import type { Product } from '../lib/catalogue';
import { ComparePicker } from './compare-picker';
import { ComparisonResults } from './comparison-results';
import type { ComparisonRow } from './comparison-types';
import { SafeLink as Link } from './safe-link';

const maxProducts = 3;

function storedCodes() {
  try {
    return JSON.parse(localStorage.getItem('brightluxx_compare_products') || '[]').slice(0, maxProducts) as string[];
  } catch {
    return [];
  }
}

function saveCodes(codes: string[]) {
  localStorage.setItem('brightluxx_compare_products', JSON.stringify(codes));
  window.dispatchEvent(new Event('brightluxx-compare-change'));
}

export function CompareWorkspace({ products }: { products: Product[] }) {
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Product[]>([]);
  const [notice, setNotice] = useState('');
  const [differences, setDifferences] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [compareError, setCompareError] = useState('');
  const selectedRef = useRef<string[]>([]);

  useEffect(() => {
    const initial = storedCodes();
    selectedRef.current = initial;
    setSelected(initial);
  }, []);

  const matches = useMemo(() => {
    const normalizedQuery = query.toLowerCase();
    return products.filter((item) => (
      `${item.name} ${item.product_code} ${item.category}`.toLowerCase().includes(normalizedQuery)
    )).slice(0, 10);
  }, [products, query]);

  const chosen = products.filter((product) => selected.includes(product.product_code));
  const rows = buildComparisonRows(results, differences);

  const toggle = (code: string) => {
    const current = selectedRef.current;
    if (current.includes(code)) {
      const next = current.filter((item) => item !== code);
      selectedRef.current = next;
      setSelected(next);
      saveCodes(next);
      setResults([]);
      trackEvent('product_compare_remove', { product_code: code, comparison_codes: next });
      return;
    }
    if (current.length >= maxProducts) {
      setNotice('You can compare a maximum of three products.');
      return;
    }
    const next = [...current, code];
    selectedRef.current = next;
    setSelected(next);
    saveCodes(next);
    setQuery('');
    setNotice('');
    setResults([]);
    trackEvent('product_compare_add', { product_code: code, comparison_codes: next });
  };

  const compare = async () => {
    const codes = selectedRef.current;
    if (codes.length < 2 || isComparing) return;
    setIsComparing(true);
    setCompareError('');
    try {
      const response = await fetch('/api/products/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(codes),
      });
      const data = await response.json();
      if (!response.ok || !data.products?.length) {
        throw new Error('Comparison data is temporarily unavailable.');
      }
      setResults(data.products);
      trackEvent('product_compare_view', { comparison_codes: codes });
    } catch (error) {
      setCompareError(error instanceof Error ? error.message : 'Comparison data is temporarily unavailable.');
    } finally {
      setIsComparing(false);
    }
  };

  const clear = () => {
    selectedRef.current = [];
    setSelected([]);
    saveCodes([]);
    setResults([]);
    setCompareError('');
  };

  return (
    <section className="compare-workspace" data-testid="compare-workspace">
      <ComparePicker
        chosen={chosen}
        matches={matches}
        query={query}
        selected={selected}
        notice={notice}
        compareError={compareError}
        isComparing={isComparing}
        onQueryChange={setQuery}
        onToggle={toggle}
        onCompare={compare}
        onClear={clear}
      />
      {isComparing && <p role="status" data-testid="compare-loading-status">Preparing comparison…</p>}
      {results.length > 0 ? (
        <ComparisonResults
          products={results}
          rows={rows}
          selected={selected}
          differences={differences}
          onDifferencesChange={setDifferences}
          onPrint={() => {
            trackEvent('comparison_print', { comparison_codes: selected });
            window.print();
          }}
          onRequestPricing={() => trackEvent('comparison_pricing_request', {
            comparison_codes: selected,
            form_type: 'comparison',
          })}
        />
      ) : (
        <div className="compare-empty" data-testid="compare-empty-state">
          <h3>Choose products to compare</h3>
          <p>Search the catalogue above to build a side-by-side specification view.</p>
          <Link href="/products" data-testid="compare-browse-products-link">Browse products →</Link>
        </div>
      )}
    </section>
  );
}

function buildComparisonRows(results: Product[], differences: boolean): ComparisonRow[] {
  const labels = Array.from(new Set(results.flatMap((product) => (
    product.key_specs?.map((item) => item.label) || []
  ))));
  const baseRows: ComparisonRow[] = [
    { label: 'Category', value: (product) => product.category },
    { label: 'Pixel Pitch', value: (product) => product.pixel_pitch || 'Not published' },
    { label: 'Brightness', value: (product) => product.brightness || 'Not published' },
    { label: 'Resolution', value: (product) => product.resolution || 'Not published' },
    { label: 'Application', value: (product) => product.application || 'Not published' },
    ...labels.map((label) => ({
      label,
      value: (product: Product) => product.key_specs?.find((item) => item.label === label)?.value || 'Not published',
    })),
  ];
  return baseRows.filter((row) => !differences || new Set(results.map(row.value)).size > 1);
}
import { SafeLink as Link } from './safe-link';
import type { Product } from '../lib/catalogue';
import type { ComparisonRow } from './comparison-types';

type ComparisonResultsProps = {
  products: Product[];
  rows: ComparisonRow[];
  selected: string[];
  differences: boolean;
  onDifferencesChange: (checked: boolean) => void;
  onPrint: () => void;
  onRequestPricing: () => void;
};

export function ComparisonResults({
  products,
  rows,
  selected,
  differences,
  onDifferencesChange,
  onPrint,
  onRequestPricing,
}: ComparisonResultsProps) {
  return (
    <div className="compare-results" data-testid="compare-results">
      <div className="compare-result-controls" data-testid="compare-result-controls">
        <label>
          <input
            type="checkbox"
            checked={differences}
            onChange={(event) => onDifferencesChange(event.target.checked)}
            data-testid="compare-differences-toggle"
          />
          Show differences only
        </label>
        <button type="button" onClick={onPrint} data-testid="compare-print-button">
          Print / Save PDF
        </button>
      </div>
      <div className="compare-table-wrap">
        <table data-testid="compare-results-table">
          <thead>
            <tr>
              <th>Specification</th>
              {products.map((product) => (
                <th key={product.product_code} data-testid={`compare-result-product-${product.product_code}`}>
                  <img src={product.image_url} alt={product.name} />
                  <strong>{product.name}</strong>
                  <small>{product.product_code}</small>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} data-testid={`compare-row-${row.label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>
                <th>{row.label}</th>
                {products.map((product) => <td key={product.product_code}>{row.value(product)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="compare-cta">
        <Link
          href={`/contact?products=${encodeURIComponent(selected.join(','))}`}
          onClick={onRequestPricing}
          data-testid="compare-pricing-link"
        >
          Request Project Pricing →
        </Link>
      </div>
    </div>
  );
}
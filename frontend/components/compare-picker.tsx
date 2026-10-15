import type { Product } from '../lib/catalogue';

type ComparePickerProps = {
  chosen: Product[];
  matches: Product[];
  query: string;
  selected: string[];
  notice: string;
  compareError: string;
  isComparing: boolean;
  onQueryChange: (query: string) => void;
  onToggle: (code: string) => void;
  onCompare: () => void;
  onClear: () => void;
};

export function ComparePicker({
  chosen,
  matches,
  query,
  selected,
  notice,
  compareError,
  isComparing,
  onQueryChange,
  onToggle,
  onCompare,
  onClear,
}: ComparePickerProps) {
  return (
    <div className="compare-picker" data-testid="compare-picker">
      <div>
        <p className="eyebrow">Decision workspace</p>
        <h2 data-testid="compare-picker-title">Select up to three products</h2>
      </div>
      <label>
        <span>Search products</span>
        <input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search by product or code"
          data-testid="compare-search-input"
        />
      </label>
      {query && (
        <div className="compare-options" data-testid="compare-product-dropdown">
          {matches.map((product) => (
            <button
              type="button"
              key={product.product_code}
              onClick={() => onToggle(product.product_code)}
              data-testid={`compare-option-${product.product_code}`}
            >
              <img src={product.image_url} alt="" />
              <span>
                {product.name}
                <small>{product.product_code} · {product.pixel_pitch}</small>
              </span>
              <b>{selected.includes(product.product_code) ? 'Selected' : 'Add'}</b>
            </button>
          ))}
        </div>
      )}
      <div className="compare-chips" data-testid="compare-selected-products">
        {chosen.map((product) => (
          <span key={product.product_code} data-testid={`compare-chip-${product.product_code}`}>
            {product.name}
            <button
              type="button"
              onClick={() => onToggle(product.product_code)}
              aria-label={`Remove ${product.name}`}
              data-testid={`compare-remove-${product.product_code}`}
            >
              ×
            </button>
          </span>
        ))}
      </div>
      {notice && <p role="status" data-testid="compare-max-notice">{notice}</p>}
      {compareError && <p role="alert" data-testid="compare-error">{compareError}</p>}
      <div className="compare-actions" data-testid="compare-actions">
        <button
          type="button"
          disabled={selected.length < 2 || isComparing}
          onClick={onCompare}
          data-testid="compare-submit-button"
        >
          {isComparing ? 'Comparing…' : `Compare ${selected.length} products`}
        </button>
        {selected.length > 0 && (
          <button type="button" onClick={onClear} data-testid="compare-clear-button">
            Clear
          </button>
        )}
      </div>
    </div>
  );
}
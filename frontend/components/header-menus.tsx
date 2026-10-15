import { SafeLink as Link } from './safe-link';
import { moreLinks, navigationTestId, productGroups, solutionLinks, type NavLink } from './navigation-data';

type HeaderMenuProps = {
  onNavigate: () => void;
};

function SimpleHeaderMenu({ links, prefix, className, testId, onNavigate }: HeaderMenuProps & {
  links: readonly NavLink[];
  prefix: string;
  className?: string;
  testId: string;
}) {
  return (
    <div className={className} data-testid={testId}>
      {links.map(([label, href]) => (
        <Link
          href={href}
          key={label}
          onClick={onNavigate}
          data-testid={navigationTestId(prefix, label)}
        >
          {label}
        </Link>
      ))}
    </div>
  );
}

export function ProductHeaderMenu({ onNavigate }: HeaderMenuProps) {
  return (
    <div className="site-mega-menu" data-testid="products-mega-menu">
      {productGroups.map((group) => (
        <section key={group.title}>
          <p>{group.title}</p>
          {group.links.map(([label, href]) => (
            <Link
              href={href}
              key={label}
              onClick={onNavigate}
              data-testid={navigationTestId('nav-product', label)}
            >
              {label}
            </Link>
          ))}
        </section>
      ))}
      <div className="site-mega-menu__footer">
        <Link href="/products" onClick={onNavigate} data-testid="nav-products-all-link">View All Products</Link>
        <Link href="/products#product-finder" onClick={onNavigate} data-testid="nav-products-finder-link">Find the Right Display</Link>
        <Link href="/compare" onClick={onNavigate} data-testid="nav-products-compare-link">Compare Displays</Link>
        <Link href="/for-architects" onClick={onNavigate} data-testid="nav-products-architects-link">For Architects</Link>
      </div>
    </div>
  );
}

export function SolutionsHeaderMenu({ onNavigate }: HeaderMenuProps) {
  return (
    <SimpleHeaderMenu
      links={solutionLinks}
      prefix="nav-solution"
      className="site-small-menu"
      testId="nav-solutions-dropdown"
      onNavigate={onNavigate}
    />
  );
}

export function MoreHeaderMenu({ onNavigate }: HeaderMenuProps) {
  return (
    <SimpleHeaderMenu
      links={moreLinks}
      prefix="nav-more"
      className="site-small-menu site-small-menu--right"
      testId="nav-more-dropdown"
      onNavigate={onNavigate}
    />
  );
}
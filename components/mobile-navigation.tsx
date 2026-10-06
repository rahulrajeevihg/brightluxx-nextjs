import { SafeLink as Link } from './safe-link';
import { mobileLinks, navigationTestId } from './navigation-data';

type MobileNavigationProps = {
  pathname: string;
  onNavigate: () => void;
};

export function MobileNavigation({ pathname, onNavigate }: MobileNavigationProps) {
  return (
    <nav className="mobile-nav-panel" data-testid="mobile-navigation-menu">
      {mobileLinks.map(([label, href]) => (
        <Link
          href={href}
          key={label}
          onClick={onNavigate}
          className={pathname === href ? 'active' : ''}
          data-testid={navigationTestId('mobile-nav', label)}
        >
          {label}
        </Link>
      ))}
      <Link href="/compare" onClick={onNavigate} data-testid="mobile-nav-compare-link">
        Compare Displays
      </Link>
    </nav>
  );
}
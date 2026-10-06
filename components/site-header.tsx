'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { MoreHeaderMenu, ProductHeaderMenu, SolutionsHeaderMenu } from './header-menus';
import { MobileNavigation } from './mobile-navigation';
import { SafeLink as Link } from './safe-link';

type OpenMenu = 'products' | 'solutions' | 'more' | null;

export function SiteHeader() {
  const [open, setOpen] = useState<OpenMenu>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    setOpen(null);
    setMobileOpen(false);
  }, [pathname]);

  const closeNavigation = () => {
    setOpen(null);
    setMobileOpen(false);
  };

  const toggleMenu = (menu: Exclude<OpenMenu, null>) => {
    setOpen(open === menu ? null : menu);
  };

  return (
    <>
      <header className="site-header" data-testid="site-header-nav">
        <div className="site-header__inner">
          <Link href="/" className="site-logo" data-testid="logo-link">
            <img src="https://files.ihgbrands.com/assets_brightluxx-logo-nav.png" alt="Brightluxx" />
          </Link>
          <nav className="site-nav" aria-label="Primary navigation" data-testid="desktop-navigation-menu">
            <button type="button" onClick={() => toggleMenu('products')} data-testid="nav-products">
              PRODUCTS <span>⌄</span>
            </button>
            <button type="button" onClick={() => toggleMenu('solutions')} data-testid="nav-solutions">
              SOLUTIONS <span>⌄</span>
            </button>
            <Link href="/lumimorph" data-testid="nav-lumimorph">LUMIMORPH</Link>
            <Link href="/naturatex" data-testid="nav-naturatex">NATURATEX</Link>
            <Link href="/signatouch" data-testid="nav-signatouch">SIGNATOUCH</Link>
            <Link href="/glassmorph" data-testid="nav-glassmorph">GLASSMORPH</Link>
            <button type="button" onClick={() => toggleMenu('more')} data-testid="nav-more-btn">
              ☰ <span>⌄</span>
            </button>
          </nav>
          <button
            className="mobile-menu-button"
            type="button"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-expanded={mobileOpen}
            aria-label="Toggle navigation"
            data-testid="mobile-menu-toggle"
          >
            {mobileOpen ? '×' : '☰'}
          </button>
          {open === 'products' && <ProductHeaderMenu onNavigate={closeNavigation} />}
          {open === 'solutions' && <SolutionsHeaderMenu onNavigate={closeNavigation} />}
          {open === 'more' && <MoreHeaderMenu onNavigate={closeNavigation} />}
        </div>
      </header>
      {mobileOpen && <MobileNavigation pathname={pathname} onNavigate={closeNavigation} />}
    </>
  );
}
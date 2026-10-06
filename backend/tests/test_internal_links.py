"""
Regression tests for the Internal Linking feature.

Covers:
- Backend: GET /api/prerender/internal-links?path=... returns correctly-shaped
  link graph for various page types (home, product family, product sub-page,
  knowledge article, SEO geo-landing).
- Prerender proxy: Crawler (Googlebot) HTML contains grouped <nav aria-label>
  blocks, anchor tags, JSON-LD BreadcrumbList + SiteNavigationElement.
- Regular user HTML still has empty <div id="root"></div> (no injected links).

NOTE: Requests to the prerender proxy are serialized with a small sleep
between them to avoid known concurrent socket issues.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://app-router-parity.preview.emergentagent.com",
).rstrip("/")

_SESSION = requests.Session()

GOOGLEBOT_UA = "Googlebot/2.1 (+http://www.google.com/bot.html)"
REGULAR_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _get(path, ua, timeout=25):
    """Serialized GET to avoid prerender proxy concurrency issue."""
    time.sleep(0.6)
    return _SESSION.get(
        f"{BASE_URL}{path}", headers={"User-Agent": ua}, timeout=timeout
    )


def _get_api(path, timeout=15):
    return requests.get(f"{BASE_URL}{path}", timeout=timeout)


# ── Backend API tests ────────────────────────────────────────────────
class TestInternalLinksAPI:
    """GET /api/prerender/internal-links"""

    def test_response_shape(self):
        r = _get_api("/api/prerender/internal-links?path=/glassmorph")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for entry in data:
            assert set(entry.keys()) >= {"path", "name", "rel"}
            assert isinstance(entry["path"], str) and entry["path"].startswith("/")
            assert isinstance(entry["name"], str) and entry["name"]
            assert isinstance(entry["rel"], str) and entry["rel"]

    def test_glassmorph_returns_20_links_with_expected_rels(self):
        r = _get_api("/api/prerender/internal-links?path=/glassmorph")
        assert r.status_code == 200
        data = r.json()
        # Per problem statement: 20 links for /glassmorph
        assert len(data) == 20, f"Expected 20 links, got {len(data)}"
        rels = {l["rel"] for l in data}
        for expected in ("child", "sibling-family", "related-guide", "related-solution"):
            assert expected in rels, f"missing rel '{expected}' in {rels}"
        # Should link to children like /glassmorph/smart-film
        children_paths = [l["path"] for l in data if l["rel"] == "child"]
        assert "/glassmorph/smart-film" in children_paths
        assert "/glassmorph/led-film" in children_paths

    def test_home_returns_26_plus_links(self):
        r = _get_api("/api/prerender/internal-links?path=/")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 26, f"Expected >=26 links, got {len(data)}"
        rels = {l["rel"] for l in data}
        for expected in ("product-family", "lifestyle", "geo-landing"):
            assert expected in rels, f"missing rel '{expected}' in {rels}"

    def test_product_subpage_has_parent_link(self):
        r = _get_api("/api/prerender/internal-links?path=/glassmorph/smart-film")
        assert r.status_code == 200
        data = r.json()
        parents = [l for l in data if l["rel"] == "parent"]
        assert len(parents) == 1
        assert parents[0]["path"] == "/glassmorph"
        # Siblings present
        sibling_paths = [l["path"] for l in data if l["rel"] == "sibling"]
        assert "/glassmorph/led-film" in sibling_paths

    def test_knowledge_article_links(self):
        r = _get_api("/api/prerender/internal-links?path=/knowledge/pixel-pitch-guide")
        assert r.status_code == 200
        data = r.json()
        rels = {l["rel"] for l in data}
        assert "related-product" in rels
        assert "sibling-article" in rels
        # Parent is knowledge hub
        parents = [l for l in data if l["rel"] == "parent"]
        assert any(p["path"] == "/knowledge" for p in parents)

    def test_geo_landing_sibling_locations(self):
        r = _get_api("/api/prerender/internal-links?path=/led-screen-dubai")
        assert r.status_code == 200
        data = r.json()
        sibling_loc_paths = [l["path"] for l in data if l["rel"] == "sibling-location"]
        for loc in (
            "/led-display-abu-dhabi",
            "/led-screen-saudi-arabia",
            "/led-screen-qatar",
            "/led-screen-kuwait",
        ):
            assert loc in sibling_loc_paths, f"missing sibling location {loc}"

    def test_signatouch_touch_kiosk_siblings(self):
        r = _get_api("/api/prerender/internal-links?path=/signatouch/touch-kiosk")
        assert r.status_code == 200
        data = r.json()
        sib_paths = [l["path"] for l in data if l["rel"] == "sibling"]
        assert "/signatouch/smart-signage" in sib_paths
        assert "/signatouch/self-service" in sib_paths

    def test_dedup_no_duplicate_paths(self):
        r = _get_api("/api/prerender/internal-links?path=/")
        assert r.status_code == 200
        data = r.json()
        paths = [l["path"] for l in data]
        assert len(paths) == len(set(paths)), "duplicate paths found"


# ── Crawler prerender HTML injection ────────────────────────────────
class TestCrawlerInternalLinksInjection:
    """Googlebot receives grouped <nav> blocks + JSON-LD."""

    def test_glassmorph_has_products_in_this_range_nav(self):
        r = _get("/glassmorph", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") == "true"
        assert '<nav aria-label="Products in This Range">' in r.text
        # Child product links present
        assert 'href="/glassmorph/smart-film"' in r.text
        assert 'href="/glassmorph/led-film"' in r.text

    def test_glassmorph_has_other_product_families_nav(self):
        r = _get("/glassmorph", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert '<nav aria-label="Other Product Families">' in r.text
        # Sibling families linked
        for sib in ("/lumimorph", "/naturatex", "/signatouch", "/pixelvue"):
            assert f'href="{sib}"' in r.text

    def test_product_subpage_has_parent_link(self):
        r = _get("/glassmorph/smart-film", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") == "true"
        # Parent nav section + link
        assert '<nav aria-label="Part of">' in r.text
        assert 'href="/glassmorph"' in r.text

    def test_led_screen_dubai_has_sibling_location_links(self):
        r = _get("/led-screen-dubai", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") == "true"
        assert '<nav aria-label="Other Locations">' in r.text
        for loc in (
            "/led-display-abu-dhabi",
            "/led-screen-saudi-arabia",
            "/led-screen-qatar",
            "/led-screen-kuwait",
        ):
            assert f'href="{loc}"' in r.text

    def test_home_has_26_plus_internal_links(self):
        r = _get("/", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") == "true"
        # Count anchor tags inside injected root snippet — use raw count of href=
        # in the <div id="root"> block (find slice).
        root_start = r.text.find('<div id="root">')
        root_end = r.text.find("</div>", root_start)
        assert root_start != -1 and root_end != -1
        root_block = r.text[root_start:root_end]
        anchor_count = root_block.count("<a href=")
        assert anchor_count >= 26, f"expected >=26 anchors, got {anchor_count}"
        # Key rel-group labels present
        assert '<nav aria-label="Product Families">' in r.text
        assert '<nav aria-label="LED Screens by Location">' in r.text

    def test_signatouch_touch_kiosk_has_sibling_links(self):
        r = _get("/signatouch/touch-kiosk", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") == "true"
        assert '<nav aria-label="Also in This Range">' in r.text
        assert 'href="/signatouch/smart-signage"' in r.text
        assert 'href="/signatouch/self-service"' in r.text

    def test_crawler_has_jsonld_breadcrumb(self):
        r = _get("/glassmorph", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert '<script type="application/ld+json">' in r.text
        assert '"@type":"BreadcrumbList"' in r.text or '"@type": "BreadcrumbList"' in r.text
        assert "Glassmorph" in r.text or "GlassMorph" in r.text

    def test_crawler_has_jsonld_sitenavigation(self):
        r = _get("/glassmorph", GOOGLEBOT_UA)
        assert r.status_code == 200
        # SiteNavigationElement schema injected (via @graph array)
        assert '"SiteNavigationElement"' in r.text
        # Multiple nav items should exist (absolute URLs to brightluxx.com)
        assert r.text.count('"SiteNavigationElement"') >= 5


# ── Regular user still gets empty root ──────────────────────────────
class TestRegularUserNoInjection:
    def test_regular_user_glassmorph_empty_root(self):
        r = _get("/glassmorph", REGULAR_UA)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") != "true"
        assert '<div id="root"></div>' in r.text
        # No injected nav blocks / product links
        assert '<nav aria-label="Products in This Range">' not in r.text
        assert '"SiteNavigationElement"' not in r.text

    def test_regular_user_home_loads(self):
        r = _get("/", REGULAR_UA)
        assert r.status_code == 200
        assert '<div id="root"></div>' in r.text

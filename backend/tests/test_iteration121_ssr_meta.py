"""
Iteration 121 — SSR meta injection tests.

Covers:
  * Backend GET /api/ssr/meta?path=...  (routes/ssr_meta.py)
  * Prerender-server HTML meta injection (frontend/prerender-server.js)
  * Regressions: /api/health, admin login, anti-spam
"""
import os
import re

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL is missing")
BASE_URL = base_url.rstrip("/")
PROD = "https://brightluxx.com"
OLD_GENERIC_TITLE = "Brightluxx — Premium LED Display Solutions"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


@pytest.fixture(scope="module")
def html_client():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    })
    return s


def get_meta(client, path):
    r = client.get(f"{BASE_URL}/api/ssr/meta", params={"path": path}, timeout=30)
    assert r.status_code == 200, f"{path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


# ── /api/ssr/meta endpoint ────────────────────────────────────────
class TestSsrMetaEndpoint:

    @pytest.mark.parametrize("path,expect_in_title", [
        ("/", None),
        ("/products", "Product"),
        ("/technology", "LED Display Technology"),
        ("/technology/cob-led", "COB LED Technology"),
        ("/calculator", "LED Screen Size Calculator"),
        ("/solutions/retail", "LED Displays for Retail"),
    ])
    def test_titles(self, client, path, expect_in_title):
        m = get_meta(client, path)
        assert isinstance(m["title"], str) and m["title"].strip()
        assert "Brightluxx" in m["title"], f"{path} title missing site suffix: {m['title']}"
        if expect_in_title:
            assert expect_in_title in m["title"], f"{path} title = {m['title']!r}"

    def test_titles_are_unique_across_paths(self, client):
        paths = ["/", "/products", "/technology", "/technology/cob-led", "/calculator",
                 "/solutions/retail", "/contact", "/about", "/blog", "/indoor-led"]
        titles = {p: get_meta(client, p)["title"] for p in paths}
        assert len(set(titles.values())) == len(paths), f"duplicate titles: {titles}"

    @pytest.mark.parametrize("path", [
        "/", "/products", "/technology", "/technology/cob-led", "/calculator",
        "/solutions/retail", "/contact", "/about", "/blog", "/indoor-led",
        "/outdoor-led", "/faq", "/glassmorph", "/pixelvue", "/qatar",
        "/knowledge/pixel-pitch-guide", "/products/some-product-slug",
    ])
    def test_canonical_is_self_referencing(self, client, path):
        m = get_meta(client, path)
        assert m["canonical"] == f"{PROD}{path}", \
            f"{path} canonical = {m['canonical']!r} (expected {PROD}{path})"

    def test_home_canonical(self, client):
        assert get_meta(client, "/")["canonical"] == f"{PROD}/"

    def test_trailing_slash_normalised(self, client):
        assert get_meta(client, "/technology/")["canonical"] == f"{PROD}/technology"

    @pytest.mark.parametrize("path", ["/", "/products", "/technology", "/calculator",
                                      "/technology/cob-led", "/solutions/retail"])
    def test_description_non_empty(self, client, path):
        m = get_meta(client, path)
        assert m["description"] and len(m["description"]) > 30, f"{path}: {m['description']!r}"

    def test_unknown_path_readable_title(self, client):
        m = get_meta(client, "/some-random-page")
        assert m["title"] == "Some Random Page | Brightluxx", m["title"]
        assert m["canonical"] == f"{PROD}/some-random-page"
        assert m["h1"] == "Some Random Page"

    def test_unknown_nested_path_readable_title(self, client):
        m = get_meta(client, "/foo-bar/baz-qux")
        assert "Foo Bar" in m["title"] and "Baz Qux" in m["title"], m["title"]
        assert m["canonical"] == f"{PROD}/foo-bar/baz-qux"

    def test_required_fields_present(self, client):
        m = get_meta(client, "/products")
        for key in ["title", "description", "canonical", "h1", "keywords",
                    "og_title", "og_description", "og_image", "og_image_alt", "noindex"]:
            assert key in m, f"missing {key}"
        assert m["og_image"].startswith("http")
        assert isinstance(m["noindex"], bool)

    def test_missing_path_param_is_422(self, client):
        r = client.get(f"{BASE_URL}/api/ssr/meta", timeout=30)
        assert r.status_code == 422

    def test_og_title_has_no_double_suffix(self, client):
        for p in ["/", "/products", "/technology"]:
            m = get_meta(client, p)
            assert m["og_title"].count("Brightluxx") <= 1, f"{p}: {m['og_title']!r}"
            assert not m["og_title"].startswith(" |"), f"{p}: {m['og_title']!r}"

    def test_clear_cache_endpoint(self, client):
        r = client.post(f"{BASE_URL}/api/ssr/meta/clear-cache", timeout=30)
        assert r.status_code == 200
        assert r.json() == {"cleared": True}


# ── HTML injection via prerender-server ───────────────────────────
def fetch_html(html_client, path):
    r = html_client.get(f"{BASE_URL}{path}", timeout=60)
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    return r


def title_of(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return m.group(1).strip() if m else None


def canonical_of(html):
    m = re.search(r'<link rel="canonical" href="([^"]*)"', html)
    return m.group(1) if m else None


def description_of(html):
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    return m.group(1) if m else None


class TestHtmlInjection:

    @pytest.mark.parametrize("path,expect", [
        ("/", None),
        ("/products", "Products"),
        ("/technology", "Technology"),
        ("/technology/cob-led", "COB"),
    ])
    def test_title_injected(self, html_client, path, expect):
        r = fetch_html(html_client, path)
        t = title_of(r.text)
        assert t, f"{path}: no <title>"
        assert t != OLD_GENERIC_TITLE, f"{path}: still generic default title"
        if expect:
            assert expect in t, f"{path} title = {t!r}"

    @pytest.mark.parametrize("path", ["/", "/products", "/technology",
                                      "/technology/cob-led", "/calculator"])
    def test_canonical_injected_self_referencing(self, html_client, path):
        r = fetch_html(html_client, path)
        c = canonical_of(r.text)
        assert c == f"{PROD}{path}", f"{path} canonical = {c!r}"

    @pytest.mark.parametrize("path", ["/", "/products"])
    def test_description_injected(self, html_client, path):
        r = fetch_html(html_client, path)
        d = description_of(r.text)
        assert d and len(d) > 30, f"{path} description = {d!r}"

    @pytest.mark.parametrize("path", ["/", "/products", "/technology"])
    def test_x_ssr_meta_header(self, html_client, path):
        r = fetch_html(html_client, path)
        assert r.headers.get("X-SSR-Meta") == "injected", \
            f"{path}: X-SSR-Meta={r.headers.get('X-SSR-Meta')!r}; headers={dict(r.headers)}"

    def test_titles_unique_in_html(self, html_client):
        paths = ["/", "/products", "/technology", "/technology/cob-led", "/contact"]
        titles = {p: title_of(fetch_html(html_client, p).text) for p in paths}
        assert len(set(titles.values())) == len(paths), f"duplicate HTML titles: {titles}"

    def test_og_url_matches_canonical(self, html_client):
        r = fetch_html(html_client, "/products")
        og = re.search(r'<meta property="og:url" content="([^"]*)"', r.text)
        assert og and og.group(1) == f"{PROD}/products", og.group(1) if og else None

    def test_noscript_h1_injected(self, html_client):
        # BUG: prerender-server regex /<noscript><div><h1>/ has no whitespace tolerance,
        # while public/index.html has newlines+indent -> H1 is never replaced.
        r = fetch_html(html_client, "/technology/cob-led")
        m = re.search(r"<noscript>\s*<div>\s*<h1>(.*?)</h1>", r.text, re.S)
        assert m, "noscript H1 block not found"
        assert "COB" in m.group(1), f"noscript H1 not page-specific: {m.group(1)!r}"


GBOT = ("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)")


# ── Crawler path (googlebot) ──────────────────────────────────────
class TestCrawlerPath:
    @pytest.mark.parametrize("path", ["/", "/products", "/indoor-led", "/blog"])
    def test_crawler_known_routes_get_unique_meta(self, path):
        r = requests.get(f"{BASE_URL}{path}", headers={"User-Agent": GBOT}, timeout=60)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") == "true"
        t, c = title_of(r.text), canonical_of(r.text)
        assert t and t != OLD_GENERIC_TITLE, f"crawler title = {t!r}"
        assert c == f"{PROD}{path}", f"crawler canonical = {c!r}"

    @pytest.mark.parametrize("path", [
        "/technology", "/technology/cob-led", "/technology/microled",
        "/solutions/retail", "/solutions/corporate",
        "/calculator", "/viewing-distance", "/power-estimator",
        "/compare-brands", "/government-solutions",
    ])
    def test_crawler_must_not_404_real_routes(self, path):
        # BUG: KNOWN_ROUTES/DYNAMIC_PATTERNS in prerender-server.js are stale,
        # so Googlebot receives 404 + noindex for these live React routes.
        r = requests.get(f"{BASE_URL}{path}", headers={"User-Agent": GBOT}, timeout=60)
        assert r.status_code == 200, (
            f"Googlebot got {r.status_code} for real route {path}; "
            f"X-Robots-Tag={r.headers.get('X-Robots-Tag')}"
        )


# ── Regressions ───────────────────────────────────────────────────
class TestRegressions:
    def test_health(self, client):
        r = client.get(f"{BASE_URL}/api/health", timeout=30)
        assert r.status_code == 200
        assert r.json().get("status") in ("ok", "healthy")

    def test_admin_login(self, client):
        r = client.post(f"{BASE_URL}/api/admin/login",
                        json={"email": "admin@brightluxx.com", "password": "brightluxx2026"},
                        timeout=30)
        if r.status_code == 429:
            pytest.skip("rate limited by brute-force limiter")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("access_token") or data.get("token")

    def test_products_no_mongo_id(self, client):
        r = client.get(f"{BASE_URL}/api/products", timeout=30)
        assert r.status_code == 200
        items = r.json() if isinstance(r.json(), list) else r.json().get("products", [])
        assert items, "no products returned"
        assert "_id" not in items[0]

    def test_antispam_rejects_disposable_email(self, client):
        r = client.post(f"{BASE_URL}/api/leads", json={
            "name": "TEST_QA SSR",
            "email": "test.qa.ssr@mailinator.com",
            "phone": "+971500000000",
            "message": "TEST_QA disposable email check for SSR iteration",
        }, timeout=30)
        assert r.status_code in (400, 422), f"expected rejection, got {r.status_code}: {r.text[:200]}"

    @pytest.mark.parametrize("path", ["/", "/products", "/contact"])
    def test_pages_render_root_div(self, html_client, path):
        r = fetch_html(html_client, path)
        assert 'id="root"' in r.text

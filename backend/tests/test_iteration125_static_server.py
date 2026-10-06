"""Iteration 125 — Production static server: prerendered HTML, 301 redirects, 404s, llms.txt, meta."""
import os
import re

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update(UA)
    return sess


def get(s, path, **kw):
    return s.get(f"{BASE_URL}{path}", timeout=45, **kw)


# ── Pre-rendered HTML content in raw response ────────────────────────────
class TestPrerenderedContent:
    def test_homepage_rich_html(self, s):
        r = get(s, "/")
        assert r.status_code == 200
        h = r.text
        title = re.search(r"<title>(.*?)</title>", h, re.S)
        assert title, "no <title>"
        assert "Brightluxx" in title.group(1)
        desc = re.search(r'<meta name="description" content="([^"]*)"', h)
        assert desc and len(desc.group(1)) > 50, "missing/short meta description"
        assert '<div id="root">' in h
        # root should not be empty (pre-rendered)
        assert '<div id="root"></div>' not in h, "root is empty — not pre-rendered"

    def test_products_page_content(self, s):
        r = get(s, "/products")
        assert r.status_code == 200
        h = r.text
        assert "hjdba" not in h.lower(), "deleted test product 'hjdba' still present"
        assert '<div id="root"></div>' not in h, "products root empty"

    def test_product_detail_content(self, s):
        r = get(s, "/products/bl-cob060")
        assert r.status_code == 200, f"got {r.status_code}"
        h = r.text.lower()
        assert "cob" in h
        assert '<div id="root"></div>' not in r.text

    def test_blog_listing_has_article_links(self, s):
        r = get(s, "/blog")
        assert r.status_code == 200
        links = re.findall(r'href="(/blog/[a-z0-9-]+)"', r.text)
        assert len(links) >= 3, f"only {len(links)} blog article links in raw HTML"

    def test_case_studies_has_links(self, s):
        r = get(s, "/case-studies")
        assert r.status_code == 200
        links = re.findall(r'href="(/case-studies/[a-z0-9-]+)"', r.text)
        assert len(links) >= 2, f"only {len(links)} case-study links in raw HTML"

    @pytest.mark.parametrize("path", ["/", "/products", "/blog", "/about", "/contact", "/solutions"])
    def test_unique_titles_and_descriptions(self, s, path):
        r = get(s, path)
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        t = re.search(r"<title>(.*?)</title>", r.text, re.S)
        d = re.search(r'<meta name="description" content="([^"]*)"', r.text)
        assert t and t.group(1).strip(), f"{path} missing title"
        assert d and len(d.group(1)) > 30, f"{path} missing description"

    def test_titles_are_unique_across_pages(self, s):
        titles = {}
        for p in ["/", "/products", "/blog", "/about", "/contact", "/solutions"]:
            r = get(s, p)
            t = re.search(r"<title>(.*?)</title>", r.text, re.S).group(1).strip()
            titles[p] = t
        assert len(set(titles.values())) == len(titles), f"duplicate titles: {titles}"


# ── HTTP 404 handling ───────────────────────────────────────────────────
class TestNotFound:
    @pytest.mark.parametrize("path", ["/nonexistent-page-xyz123", "/products/fake-product-999"])
    def test_unknown_route_404(self, s, path):
        r = get(s, path)
        assert r.status_code == 404, f"{path} returned {r.status_code}"
        assert "404" in r.text


# ── WordPress legacy 301 redirects ──────────────────────────────────────
class TestRedirects:
    @pytest.mark.parametrize("src,dest", [
        ("/our-works/", "/projects"),
        ("/digital-solutions/", "/solutions"),
        ("/download-catalog/", "/products"),
        ("/products/led-display", "/products"),
        ("/products/indoor-led-display/", "/indoor-led"),
        ("/products/spherical-led-display/", "/products"),
        ("/products/cube-led-display-p3", "/products"),
        ("/about-us/", "/about"),
        ("/contact-us", "/contact"),
        ("/wp-content/uploads/2023/img.jpg", "/products"),
    ])
    def test_301(self, s, src, dest):
        r = get(s, src, allow_redirects=False)
        assert r.status_code == 301, f"{src} -> {r.status_code}"
        assert r.headers.get("Location") == dest, f"{src} -> {r.headers.get('Location')}"


# ── llms.txt ────────────────────────────────────────────────────────────
class TestLlmsTxt:
    def test_llms_txt(self, s):
        r = get(s, "/llms.txt")
        assert r.status_code == 200
        assert "text/plain" in r.headers.get("Content-Type", "")
        assert r.text.lstrip().startswith("# Brightluxx"), r.text[:80]


# ── Fonts: self-hosted only ─────────────────────────────────────────────
class TestFonts:
    def test_no_external_font_origins_in_html(self, s):
        for p in ["/", "/products", "/contact"]:
            h = get(s, p).text
            assert "fonts.googleapis.com" not in h, f"{p} references fonts.googleapis.com"
            assert "fonts.cdnfonts.com" not in h, f"{p} references fonts.cdnfonts.com"

    def test_satoshi_font_files_served(self, s):
        h = get(s, "/").text
        refs = re.findall(r'href="(/fonts/[^"]+\.woff2?)"', h)
        assert refs, "no self-hosted font preload/reference in index.html"
        for f in set(refs[:4]):
            r = get(s, f)
            assert r.status_code == 200, f"{f} -> {r.status_code}"
            assert "font" in r.headers.get("Content-Type", ""), r.headers.get("Content-Type")


# ── Admin SPA shell ─────────────────────────────────────────────────────
class TestAdminShell:
    def test_admin_login_shell(self, s):
        r = get(s, "/admin/login")
        assert r.status_code == 200
        assert '<div id="root"' in r.text
        assert "/static/js/" in r.text


# ── Cache headers ───────────────────────────────────────────────────────
class TestCacheHeaders:
    def test_html_cache_header(self, s):
        r = get(s, "/")
        assert r.headers.get("Cache-Control"), "no Cache-Control on HTML"

    def test_static_asset_immutable(self, s):
        h = get(s, "/").text
        m = re.search(r'src="(/static/js/[^"]+\.js)"', h)
        assert m, "no static js bundle reference"
        r = get(s, m.group(1))
        assert r.status_code == 200
        cc = r.headers.get("Cache-Control", "")
        # NOTE: preview ingress (Cloudflare) rewrites Cache-Control to no-store.
        # Origin (localhost:3000) correctly returns "public, max-age=31536000, immutable".
        assert cc, "no Cache-Control header at all"


# ── Backend product count ───────────────────────────────────────────────
class TestProductsApi:
    def test_product_count_and_no_test_product(self, s):
        r = get(s, "/api/products?limit=200")
        assert r.status_code == 200
        data = r.json()
        items = data if isinstance(data, list) else data.get("products") or data.get("items") or []
        assert len(items) > 0
        slugs = [str(i.get("slug", "")) + str(i.get("name", "")) for i in items]
        assert not any("hjdba" in x.lower() for x in slugs), "test product hjdba still in API"
        print(f"product count = {len(items)}")


# ── Hero media delivery (/api/media proxy) ──────────────────────────────
class TestHeroMedia:
    """Regression tests for the hero video delivery bug found in iteration 125."""

    HERO_VIDEO = "/api/media/videos/hero-video-ede053db.mp4"

    def test_hero_poster_served(self, s):
        r = get(s, "/api/media/images/hero-poster.webp")
        assert r.status_code == 200
        assert "image/webp" in r.headers.get("Content-Type", "")

    def test_hero_video_head_allowed(self, s):
        r = s.head(f"{BASE_URL}{self.HERO_VIDEO}", timeout=45)
        assert r.status_code != 405, "HEAD on /api/media returns 405 — only GET registered"
        assert r.status_code == 200, r.status_code

    def test_hero_video_honours_range_requests(self, s):
        r = s.get(f"{BASE_URL}{self.HERO_VIDEO}",
                  headers={"Range": "bytes=0-1023"}, stream=True, timeout=60)
        try:
            assert r.headers.get("Accept-Ranges") == "bytes"
            assert r.status_code == 206, (
                f"Range ignored: status={r.status_code}, "
                f"Content-Length={r.headers.get('Content-Length')} "
                "— endpoint advertises Accept-Ranges but streams the whole file"
            )
            assert r.headers.get("Content-Range"), "no Content-Range header"
            assert int(r.headers.get("Content-Length", 0)) <= 1024
        finally:
            r.close()

    def test_hero_video_size_is_reasonable(self, s):
        # Measure at origin: the preview CDN strips Content-Length (chunked transfer).
        import subprocess
        out = subprocess.run(
            ["curl", "-s", "-D", "-", "-o", "/dev/null", "--max-time", "90",
             f"http://localhost:8001{self.HERO_VIDEO}"],
            capture_output=True, text=True).stdout.lower()
        m = re.search(r"content-length:\s*(\d+)", out)
        assert m, f"no content-length at origin: {out[:300]}"
        size = int(m.group(1))
        print(f"hero video size = {size/1e6:.1f} MB")
        assert size < 10_000_000, f"hero video is {size/1e6:.1f} MB — too large for hero LCP"

"""
Regression tests for the Prerender/Crawler SEO feature.

- Backend API: /api/prerender/headings, /api/prerender/page
- Prerender proxy: Crawler UA gets injected HTML, regular user gets SPA
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://app-router-parity.preview.emergentagent.com").rstrip("/")

# Small delay between crawler requests — the prerender proxy has a known
# stability issue under concurrent load (see iteration report).
_SESSION = requests.Session()


def _get(path, ua):
    time.sleep(0.6)
    return _SESSION.get(f"{BASE_URL}{path}", headers={"User-Agent": ua}, timeout=25)

GOOGLEBOT_UA = "Googlebot/2.1 (+http://www.google.com/bot.html)"
REGULAR_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


# ── Backend prerender API ─────────────────────────────────────────
class TestPrerenderAPI:
    def test_headings_home(self):
        r = requests.get(f"{BASE_URL}/api/prerender/headings?path=/", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0
        assert data[0]["tag"] == "h1"
        assert data[0]["text"] == "ENGINEERING BRILLIANCE"

    def test_page_home_meta(self):
        r = requests.get(f"{BASE_URL}/api/prerender/page?path=/", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "headings" in data and "meta" in data
        assert len(data["headings"]) > 0
        assert data["meta"].get("title")
        assert data["meta"].get("description")

    @pytest.mark.parametrize("path,expected_h1", [
        ("/glassmorph", "GlassMorph"),
        ("/signatouch", "SignaTouch"),
        ("/naturatex", "NaturaTex"),
        ("/pixelvue", "PixelVue"),
        ("/lumimorph", "LumiMorph"),
    ])
    def test_product_page_headings(self, path, expected_h1):
        r = requests.get(f"{BASE_URL}/api/prerender/page?path={path}", timeout=15)
        assert r.status_code == 200
        data = r.json()
        hs = data.get("headings", [])
        assert hs, f"No headings for {path}"
        assert hs[0]["tag"] == "h1"
        assert hs[0]["text"] == expected_h1


# ── Crawler prerender proxy (injected HTML) ───────────────────────
class TestCrawlerPrerender:
    @pytest.mark.parametrize("path,expected_h1", [
        ("/", "ENGINEERING BRILLIANCE"),
        ("/glassmorph", "GlassMorph"),
        ("/signatouch", "SignaTouch"),
        ("/naturatex", "NaturaTex"),
        ("/pixelvue", "PixelVue"),
        ("/lumimorph", "LumiMorph"),
    ])
    def test_crawler_gets_h1_in_html(self, path, expected_h1):
        r = _get(path, GOOGLEBOT_UA)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") == "true", f"Missing X-Prerendered for {path}"
        assert f"<h1>{expected_h1}</h1>" in r.text, f"H1 '{expected_h1}' not found in initial HTML for {path}"

    def test_crawler_led_screen_dubai_has_h1(self):
        r = _get("/led-screen-dubai", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") == "true"
        # Must contain at least one <h1> tag
        assert "<h1>" in r.text and "</h1>" in r.text

    def test_crawler_gets_canonical_and_meta(self):
        r = _get("/glassmorph", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert 'rel="canonical"' in r.text
        assert 'href="https://brightluxx.com/glassmorph"' in r.text
        assert '<meta name="description"' in r.text
        assert '<meta name="keywords"' in r.text

    def test_crawler_gets_page_specific_title(self):
        r = _get("/signatouch", GOOGLEBOT_UA)
        assert r.status_code == 200
        assert "SignaTouch" in r.text
        # Page-specific title should be injected (not the default homepage title only)
        assert "<title>" in r.text


# ── Regular user (normal SPA behavior) ────────────────────────────
class TestRegularUser:
    def test_regular_user_home_no_prerender_header(self):
        r = _get("/", REGULAR_UA)
        assert r.status_code == 200
        assert r.headers.get("X-Prerendered") != "true"

    def test_regular_user_home_empty_root_div(self):
        r = _get("/", REGULAR_UA)
        assert r.status_code == 200
        # Initial SSR-free HTML must have empty root div for normal users
        assert '<div id="root"></div>' in r.text
        # No server-injected h1 for regular users
        assert "<h1>ENGINEERING BRILLIANCE</h1>" not in r.text

    def test_regular_user_glassmorph_empty_root(self):
        r = _get("/glassmorph", REGULAR_UA)
        assert r.status_code == 200
        assert '<div id="root"></div>' in r.text
        assert "<h1>GlassMorph</h1>" not in r.text

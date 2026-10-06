"""SEO / AI-search audit fixes: WP redirects, 404 handling, llms.txt, noscript, robots.txt."""
import os
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")

CRAWLER_UA = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"}


# ── WordPress legacy redirects (prerender-server level) ──
@pytest.mark.parametrize("src,dst", [
    ("/our-works/", "/projects"),
    ("/our-works", "/projects"),
    ("/products/led-display", "/products"),
    ("/products/indoor-led-display/", "/indoor-led"),
    ("/products/outdoor-led-display", "/outdoor-led"),
    ("/products/transparent-led-display", "/glassmorph"),
    ("/about-us/", "/about"),
    ("/contact-us/", "/contact"),
    ("/digital-solutions/", "/solutions"),
    ("/portfolio", "/projects"),
    ("/gallery/", "/projects"),
    ("/download-catalog/", "/products"),
    ("/wp-content/uploads/test", "/products"),
    ("/wp-admin/", "/products"),
])
def test_wp_redirect(src, dst):
    r = requests.get(f"{BASE_URL}{src}", allow_redirects=False, timeout=30)
    assert r.status_code == 301, f"{src} -> {r.status_code}"
    assert r.headers.get("Location", "").endswith(dst), f"{src} -> {r.headers.get('Location')}"


# ── 404 handling for crawlers ──
@pytest.mark.parametrize("path", ["/nonexistent-xyz123", "/foo/bar-baz"])
def test_404_for_crawler(path):
    r = requests.get(f"{BASE_URL}{path}", headers=CRAWLER_UA, timeout=30)
    assert r.status_code == 404
    assert "noindex" in (r.headers.get("X-Robots-Tag", "") + r.text).lower()


def test_known_route_not_404_for_crawler():
    r = requests.get(f"{BASE_URL}/glassmorph", headers=CRAWLER_UA, timeout=30)
    assert r.status_code == 200


# ── llms.txt ──
def test_llms_txt_static():
    r = requests.get(f"{BASE_URL}/llms.txt", timeout=30)
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("Content-Type", "")
    assert "Brightluxx" in r.text


def test_llms_txt_api():
    r = requests.get(f"{BASE_URL}/api/llms.txt", timeout=30)
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("Content-Type", "")
    assert "Brightluxx" in r.text


# ── wp-redirect API ──
def test_wp_redirect_api_hit():
    r = requests.get(f"{BASE_URL}/api/wp-redirect", params={"path": "/our-works/"}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data["redirect"] is True
    assert data["target"] == "/projects"


def test_wp_redirect_api_miss():
    r = requests.get(f"{BASE_URL}/api/wp-redirect", params={"path": "/some-random"}, timeout=30)
    assert r.status_code == 200
    assert r.json()["redirect"] is False


# ── noscript content in initial HTML ──
def test_homepage_noscript_content():
    r = requests.get(f"{BASE_URL}/", timeout=30)
    assert r.status_code == 200
    assert "Premium LED Display Solutions in Dubai" in r.text
    for href in ["/lumimorph", "/naturatex", "/signatouch", "/glassmorph"]:
        assert f'href="{href}"' in r.text, f"missing noscript link {href}"


def test_regular_user_root_empty():
    r = requests.get(f"{BASE_URL}/", timeout=30)
    assert '<div id="root"></div>' in r.text


# ── crawler prerender ──
def test_crawler_home_root_injected():
    r = requests.get(f"{BASE_URL}/", headers=CRAWLER_UA, timeout=40)
    assert r.status_code == 200
    assert '<div id="root"></div>' not in r.text
    assert "<h1>" in r.text


def test_crawler_glassmorph_title():
    r = requests.get(f"{BASE_URL}/glassmorph", headers=CRAWLER_UA, timeout=40)
    assert "GlassMorph" in r.text.split("</title>")[0]


# ── robots.txt ──
def test_robots_ai_crawlers():
    r = requests.get(f"{BASE_URL}/robots.txt", timeout=30)
    assert r.status_code == 200
    for bot in ["GPTBot", "ClaudeBot", "PerplexityBot"]:
        assert bot in r.text
    assert "llms.txt" in r.text

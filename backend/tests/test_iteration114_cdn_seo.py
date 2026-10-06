"""Iteration 114: CDN asset availability, WP redirects, 404 noindex, llms.txt,
prerender H1 for crawlers, and Home Cinema products API."""
import os

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL is missing")
BASE_URL = base_url.rstrip("/")

CDN = "https://files.ihgbrands.com"
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    return s


# ---------------- CDN assets (old nested + new flat formats) ----------------
CDN_PATHS = [
    "/brightluxx/uploads/08e3e5d388dd_nft1.webp?v=4",
    "/brightluxx/videos/hero-video-converted.mp4",
    "/brightluxx/downloaded-images/ext_00eecd7267f8.jpg?v=4",
    "/brightluxx/site-images/opt_ext_bc8c12ee1348.webp?v=4",
    "/brightluxx/homepage/grande-hero.webp?v=4",
    "/homepage_grande-hero.webp",
    "/emergent-images/theaterpro_complete.jpeg",
]


@pytest.mark.parametrize("path", CDN_PATHS)
def test_cdn_asset_returns_200(client, path):
    r = client.get(f"{CDN}{path}", timeout=60, stream=True)
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    ctype = r.headers.get("content-type", "")
    assert ctype.startswith(("image/", "video/")), f"{path} content-type {ctype}"
    length = int(r.headers.get("content-length", "0"))
    assert length > 1000, f"{path} suspiciously small: {length} bytes"
    r.close()


def test_cdn_video_supports_range(client):
    r = client.get(
        f"{CDN}/brightluxx/videos/hero-video-converted.mp4",
        headers={"Range": "bytes=0-1023"},
        timeout=60,
    )
    assert r.status_code in (200, 206)


# ---------------- WordPress legacy redirects ----------------
@pytest.mark.parametrize(
    "src,dest",
    [
        ("/our-works/", "/projects"),
        ("/products/led-display", "/products"),
    ],
)
def test_wp_redirects(client, src, dest):
    r = client.get(f"{BASE_URL}{src}", allow_redirects=False, timeout=30)
    assert r.status_code == 301, f"{src} -> {r.status_code}"
    assert r.headers.get("location", "").rstrip("/") .endswith(dest.rstrip("/")), r.headers.get("location")


# ---------------- 404 handling for crawlers ----------------
def test_nonexistent_url_returns_404_with_noindex(client):
    r = client.get(
        f"{BASE_URL}/this-page-does-not-exist-114",
        headers={"User-Agent": GOOGLEBOT},
        timeout=30,
    )
    assert r.status_code == 404, f"expected 404 got {r.status_code}"
    assert "noindex" in r.text.lower()


# ---------------- llms.txt ----------------
def test_llms_txt(client):
    r = client.get(f"{BASE_URL}/llms.txt", timeout=30)
    assert r.status_code == 200
    assert "text/plain" in r.headers.get("content-type", "")
    assert "Brightluxx" in r.text


# ---------------- Prerender for crawlers ----------------
@pytest.mark.parametrize("path", ["/", "/products", "/lumimorph", "/glassmorph", "/contact"])
def test_googlebot_gets_h1(client, path):
    r = client.get(f"{BASE_URL}{path}", headers={"User-Agent": GOOGLEBOT}, timeout=60)
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    assert "<h1" in r.text.lower(), f"No H1 in prerendered HTML for {path}"


# ---------------- Home Cinema products ----------------
def test_home_cinema_products(client):
    r = client.get(f"{BASE_URL}/api/products?category=home-cinema&limit=100", timeout=30)
    assert r.status_code == 200
    data = r.json()
    products = data.get("products", data if isinstance(data, list) else [])
    assert len(products) >= 10, f"expected >=10 home-cinema products, got {len(products)}"
    for p in products:
        assert p.get("category") == "home-cinema"
        assert p.get("slug")
        assert p.get("name")


def test_home_cinema_product_detail(client):
    r = client.get(f"{BASE_URL}/api/products?category=home-cinema&limit=1", timeout=30)
    slug = r.json()["products"][0]["slug"]
    d = client.get(f"{BASE_URL}/api/products/{slug}", timeout=30)
    assert d.status_code == 200
    assert d.json().get("slug") == slug

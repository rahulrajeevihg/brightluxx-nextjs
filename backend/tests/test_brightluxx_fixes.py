"""Tests for Brightluxx fixes: product/project limits, CDN redirects, cache headers, tombstone."""
import os
import pytest
import requests
from pathlib import Path

# Load REACT_APP_BACKEND_URL from frontend/.env
_env = Path(__file__).resolve().parents[2] / "frontend" / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            os.environ.setdefault("REACT_APP_BACKEND_URL", line.split("=", 1)[1].strip())

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"
LOCAL_URL = "http://localhost:8001"


# --- Products limit ---
class TestProductsLimit:
    def test_products_limit_4_featured(self):
        r = requests.get(f"{BASE_URL}/api/products", params={"limit": 4, "featured": "true"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "products" in data
        assert len(data["products"]) == 4, f"Expected 4, got {len(data['products'])}"
        for p in data["products"]:
            assert p.get("featured") is True

    def test_products_no_limit_returns_full_catalog(self):
        r = requests.get(f"{BASE_URL}/api/products", timeout=30)
        assert r.status_code == 200
        products = r.json()["products"]
        # Full catalog should be substantially larger than a small limit; expect ~94
        assert len(products) >= 50, f"Expected full catalog >=50, got {len(products)}"

    def test_products_category_filter(self):
        # Use category from response
        all_r = requests.get(f"{BASE_URL}/api/products", timeout=30).json()["products"]
        assert len(all_r) > 0
        cat = all_r[0]["category"]
        r = requests.get(f"{BASE_URL}/api/products", params={"category": cat}, timeout=30)
        assert r.status_code == 200
        prods = r.json()["products"]
        assert len(prods) > 0
        assert all(p["category"] == cat for p in prods)


# --- Projects ---
class TestProjects:
    def test_projects_returns_8_with_valid_webp_urls(self):
        r = requests.get(f"{BASE_URL}/api/projects", timeout=30)
        assert r.status_code == 200
        projects = r.json()["projects"]
        assert len(projects) == 8, f"Expected 8 projects, got {len(projects)}"
        for p in projects:
            url = p.get("image_url", "")
            assert url.startswith("https://files.ihgbrands.com/brightluxx/site-images/"), f"Bad prefix: {url}"
            assert url.endswith(".webp"), f"Not .webp: {url}"

    def test_projects_image_urls_reachable(self):
        r = requests.get(f"{BASE_URL}/api/projects", timeout=30)
        projects = r.json()["projects"]
        for p in projects:
            url = p["image_url"]
            head = requests.head(url, timeout=15, allow_redirects=True)
            assert head.status_code == 200, f"{url} returned {head.status_code}"
            ct = head.headers.get("content-type", "")
            assert "image/webp" in ct or "image" in ct, f"{url} content-type={ct}"

    def test_projects_limit_3_featured(self):
        r = requests.get(f"{BASE_URL}/api/projects", params={"limit": 3, "featured": "true"}, timeout=30)
        assert r.status_code == 200
        projects = r.json()["projects"]
        assert len(projects) <= 3


# --- CDN redirect ---
class TestCdnRedirect:
    def test_cdn_redirect_301(self):
        # Do not follow redirect
        r = requests.get(f"{BASE_URL}/api/cdn/anything.png", allow_redirects=False, timeout=15)
        assert r.status_code == 301, f"Expected 301, got {r.status_code}"
        loc = r.headers.get("Location", "")
        assert loc == "https://files.ihgbrands.com/uploads_anything.png", f"Bad Location: {loc}"

    def test_cdn_redirect_nested_path_flattened(self):
        r = requests.get(f"{BASE_URL}/api/cdn/foo/bar.jpg", allow_redirects=False, timeout=15)
        assert r.status_code == 301
        loc = r.headers.get("Location", "")
        assert loc == "https://files.ihgbrands.com/uploads_foo_bar.jpg", f"Bad Location: {loc}"


# --- Tombstone / 404 ---
class TestTombstone:
    def test_hjdba_returns_404(self):
        r = requests.get(f"{BASE_URL}/api/products/hjdba", timeout=15)
        assert r.status_code == 404


# --- Cache-Control (localhost only) ---
class TestCacheHeaders:
    @pytest.mark.parametrize("path", [
        "/api/homepage-content",
        "/api/site-settings",
        "/api/seo/page-meta?path=/",
        "/api/products",
    ])
    def test_cache_control_localhost(self, path):
        r = requests.get(f"{LOCAL_URL}{path}", timeout=15)
        assert r.status_code == 200, f"{path} status {r.status_code}"
        cc = r.headers.get("Cache-Control", "")
        assert "public" in cc and "max-age=300" in cc, f"{path} Cache-Control={cc!r}"

"""
Iteration 130 - Product discovery API verification
- Search synonym coverage for /api/products
- Finder category output compatibility via existing query filters
"""

import os
import json
import re
from pathlib import Path
import pytest
import requests


def _read_backend_url_from_frontend_env() -> str | None:
    env_path = Path("/app/frontend/.env")
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip()
    return None


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or _read_backend_url_from_frontend_env()
if not BASE_URL:
    pytest.skip("REACT_APP_BACKEND_URL is not set", allow_module_level=True)
BASE_URL = BASE_URL.rstrip("/")


@pytest.mark.parametrize(
    "query",
    ["P1.2", "COB", "video wall", "meeting room", "transparent display", "digital totem"],
)
def test_products_search_synonyms_return_results(query):
    """/api/products search returns non-zero results for discovery terms."""
    response = requests.get(f"{BASE_URL}/api/products", params={"search": query}, timeout=20)
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, dict)
    assert "products" in payload

    products = payload["products"]
    assert isinstance(products, list)
    assert len(products) > 0, f"Expected non-zero results for query '{query}'"

    first = products[0]
    assert isinstance(first.get("name"), str) and first["name"].strip()
    assert isinstance(first.get("category"), str) and first["category"].strip()


@pytest.mark.parametrize(
    "category",
    ["outdoor", "cob-microled", "transparent", "interactive", "indoor", "all-in-one", "cinema-led", "flexible"],
)
def test_finder_recommended_categories_work_with_existing_products_query_filter(category):
    """Finder-recommended categories must work through /api/products?category=... only."""
    response = requests.get(f"{BASE_URL}/api/products", params={"category": category}, timeout=20)
    assert response.status_code == 200

    payload = response.json()
    assert "products" in payload
    products = payload["products"]
    assert len(products) > 0, f"Expected products for finder category '{category}'"

    for product in products[:10]:
        assert product.get("category") == category
        assert isinstance(product.get("slug"), str) and product["slug"].strip()


def test_products_payload_has_decision_ready_fields_available():
    """Product list returns decision fields when available for cards."""
    response = requests.get(f"{BASE_URL}/api/products", params={"limit": 25}, timeout=20)
    assert response.status_code == 200

    products = response.json().get("products", [])
    assert len(products) > 0

    # At least one product should expose each expected card field in real catalogue data.
    assert any(p.get("pixel_pitch") for p in products), "No products expose pixel_pitch"
    assert any(p.get("brightness") for p in products), "No products expose brightness"
    assert any(p.get("refresh_rate") for p in products), "No products expose refresh_rate"
    assert any(p.get("application") for p in products), "No products expose application"


def test_static_products_build_has_single_h1_canonical_and_internal_links():
    """build/products/index.html keeps static non-SPA SEO-critical structure."""
    static_file = Path("/app/frontend/build/products/index.html")
    assert static_file.exists(), "Missing static products build output"

    html = static_file.read_text(encoding="utf-8")
    assert "<div id=\"root\"><h1>LED Display Products</h1>" in html

    h1_matches = re.findall(r"<h1[^>]*>", html, flags=re.IGNORECASE)
    assert len(h1_matches) == 1, f"Expected one H1, found {len(h1_matches)}"

    assert '<link rel="canonical" href="https://brightluxx.com/products">' in html

    internal_links = re.findall(r"<a href=\"/(?!/)[^\"]+\"", html)
    assert len(internal_links) >= 10, "Expected internal href links in static body"


def test_seo_regression_report_has_zero_critical_failures():
    """SEO regression report remains PASS with zero fail count."""
    report_file = Path("/app/frontend/seo-reports/seo-regression-report.json")
    assert report_file.exists(), "Missing SEO regression report"

    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report.get("result") == "PASS"
    assert report.get("failCount") == 0

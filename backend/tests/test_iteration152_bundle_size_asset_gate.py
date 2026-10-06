"""
Iteration 152 - Bundle-size gate regression after moving legacy payload to static asset.
# Modules/features: raw SSR contracts, SEO routes, live APIs, and static asset/non-embed checks.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests


NEXT_PREVIEW_URL = "http://127.0.0.1:8787".rstrip("/")
PAGE_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36",
}

REPRESENTATIVE_PATHS = [
    "/",
    "/products",
    "/products/bl-cob125",
    "/dubai",
    "/compare",
    "/contact",
]


def _get(path: str, **kwargs):
    return requests.get(f"{NEXT_PREVIEW_URL}{path}", timeout=35, **kwargs)


def _post(path: str, payload):
    return requests.post(f"{NEXT_PREVIEW_URL}{path}", json=payload, timeout=45)


def _get_page(path: str, **kwargs):
    merged_headers = {**PAGE_HEADERS, **kwargs.pop("headers", {})}
    return requests.get(f"{NEXT_PREVIEW_URL}{path}", timeout=35, headers=merged_headers, **kwargs)


def _extract_canonical(html: str) -> str | None:
    match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _h1_count(html: str) -> int:
    return len(re.findall(r"<h1(?:\\s|>)", html, flags=re.IGNORECASE))


def _sitemap_paths() -> list[str]:
    response = _get("/sitemap.xml")
    assert response.status_code == 200
    locs = re.findall(r"<loc>([^<]+)</loc>", response.text)
    paths: list[str] = []
    for loc in locs:
        parsed = urlparse(loc.strip())
        if parsed.path:
            paths.append(parsed.path)
    return paths


def _pick_content_paths() -> tuple[str, str, str]:
    paths = _sitemap_paths()
    solution = next((p for p in paths if p.startswith("/solutions/") and p != "/solutions"), "/solutions")
    case_study = next((p for p in paths if p.startswith("/case-studies/") and p != "/case-studies"), "/case-studies")
    resource = next((p for p in paths if p.startswith("/resources/") and p != "/resources"), "/resources")
    return solution, case_study, resource


@pytest.mark.parametrize(
    "path,keyword,h1_marker",
    [
        ("/", "Engineered Vision", 'data-testid="hero-title"'),
        ("/products", "LED Display Products", 'data-testid="products-page-title"'),
        ("/products/bl-cob125", "Request Project Pricing", 'data-testid="product-detail-title"'),
        ("/dubai", "Dubai", None),
        ("/compare", "Compare LED Products", 'data-testid="compare-page-title"'),
        ("/contact", "Get in touch", 'data-testid="contact-page-title"'),
    ],
)
def test_raw_html_core_routes_have_canonical_h1_content_and_no_asset_errors(path: str, keyword: str, h1_marker: str | None):
    response = _get_page(path)
    assert response.status_code == 200
    html = response.text

    canonical = _extract_canonical(html)
    assert canonical is not None
    assert canonical.startswith("https://brightluxx.com")

    literal_h1 = _h1_count(html)
    if literal_h1 != 1 and h1_marker is not None:
        assert h1_marker in html
    else:
        assert literal_h1 == 1

    assert keyword.lower() in html.lower()
    assert "Legacy page asset binding is unavailable" not in html
    assert "Legacy page asset request failed" not in html


def test_products_raw_html_has_exactly_94_cards_pre_hydration_and_json_ld():
    response = _get_page("/products")
    assert response.status_code == 200
    html = response.text
    cards = re.findall(r'data-testid="products-product-card-[^"]+"', html)
    assert len(cards) == 94
    assert "application/ld+json" in html


def test_legacy_solution_case_study_resource_routes_render_primary_content_and_json_ld():
    solution, case_study, resource = _pick_content_paths()
    for path in [solution, case_study, resource]:
        response = _get_page(path)
        assert response.status_code == 200
        html = response.text

        canonical = _extract_canonical(html)
        assert canonical is not None
        assert canonical.startswith("https://brightluxx.com")
        assert _h1_count(html) == 1
        assert "application/ld+json" in html


def test_native_seo_and_routing_contracts_redirect_gone_404_sitemap_robots_llms():
    redirect = _get("/our-works", allow_redirects=False)
    assert redirect.status_code == 308
    assert redirect.headers.get("location") == "/projects"

    gone = _get("/products/hjdba", allow_redirects=False)
    assert gone.status_code == 410

    unknown = _get_page("/__iteration-152-unknown-route__", allow_redirects=False)
    assert unknown.status_code == 404
    assert "404" in unknown.text

    sitemap = _get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "https://brightluxx.com" in sitemap.text

    robots = _get("/robots.txt")
    assert robots.status_code == 200
    assert "Sitemap: https://brightluxx.com/sitemap.xml" in robots.text

    llms = _get("/llms.txt")
    assert llms.status_code == 200
    assert len(llms.text.strip()) > 20


def test_live_products_search_compare_apis_with_real_data():
    products_response = _get("/api/products")
    assert products_response.status_code == 200
    products_payload = products_response.json()
    products = products_payload if isinstance(products_payload, list) else products_payload.get("products", [])
    assert isinstance(products, list)
    assert len(products) == 94

    detail_response = _get("/api/products/bl-cob125")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail.get("slug") == "bl-cob125"
    assert isinstance(detail.get("product_code"), str) and detail["product_code"].strip()

    search_response = _get("/api/search", params={"q": "video wall"})
    assert search_response.status_code == 200
    search_payload = search_response.json()
    search_products = search_payload.get("products", []) if isinstance(search_payload, dict) else []
    assert isinstance(search_products, list)
    assert len(search_products) > 0

    codes = [item.get("product_code") for item in products if item.get("product_code")][:3]
    compare_response = _post("/api/products/compare", codes[:2])
    assert compare_response.status_code == 200
    compare_payload = compare_response.json()
    compared = compare_payload.get("products", []) if isinstance(compare_payload, dict) else []
    compared_codes = [item.get("product_code") for item in compared]
    assert set(compared_codes) == set(codes[:2])


def test_contact_backend_validation_and_submission_route():
    invalid = {
        "name": "TEST Invalid Phone Iter152",
        "email": "qa.invalid.phone.iter152@brightluxx-example.test",
        "phone": "123",
        "city": "Dubai",
        "application": "Corporate",
        "message": "Validation regression check.",
        "website": "",
        "fax": "",
    }
    invalid_response = _post("/api/leads", invalid)
    assert invalid_response.status_code == 422
    invalid_payload = invalid_response.json()
    assert "phone" in str(invalid_payload.get("detail", "")).lower()

    valid = {
        "name": "TEST Local Regression Iteration152",
        "company": "TEST Brightluxx QA",
        "email": "qa.iter152@brightluxx-example.test",
        "phone": "+971501234567",
        "city": "Dubai",
        "application": "Corporate",
        "timeline": "1-3 months",
        "budget": "AED 200k - 400k",
        "message": "Local regression submission check. Please ignore.",
        "source": "comparison_request",
        "product_interest": "BL-COB125, BL-OH6",
        "website": "",
        "fax": "",
    }
    valid_response = _post("/api/leads", valid)
    assert valid_response.status_code < 500
    valid_payload = valid_response.json()
    if valid_response.status_code == 200:
        assert valid_payload.get("success") is True
    else:
        assert valid_response.status_code in (400, 422, 429)
        assert isinstance(valid_payload.get("detail"), str) and valid_payload["detail"].strip()


def test_static_legacy_payload_is_served_as_public_asset():
    response = _get("/_data/legacy-pages.json")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "").lower()
    assert "application/json" in content_type or "text/json" in content_type
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) > 100
    assert any(item.get("route") == "/products" for item in payload if isinstance(item, dict))


def test_bundled_worker_no_direct_legacy_html_payload_embedding():
    worker_path = Path("/app/nextjs/bundled/worker.js")
    assert worker_path.exists()
    worker_js = worker_path.read_text(encoding="utf-8", errors="ignore")

    # Unique long phrase from legacy-pages.json home html should not be embedded in worker bundle.
    assert "Design, supply, engineering, installation and lifecycle support for premium LED displays" not in worker_js
    assert "LED Display & Digital Signage Solutions for UAE & GCC" not in worker_js


def test_legacy_content_loader_uses_shared_asset_source_for_build_and_runtime():
    source = Path("/app/nextjs/lib/legacy-content.ts").read_text(encoding="utf-8", errors="ignore")
    assert "public/_data/legacy-pages.json" in source
    assert "env.ASSETS" in source
    assert "/_data/legacy-pages.json" in source


def test_runtime_pages_do_not_render_legacy_asset_runtime_errors():
    for path in REPRESENTATIVE_PATHS:
        response = _get_page(path)
        assert response.status_code == 200
        html = response.text
        assert "Legacy page asset binding is unavailable" not in html
        assert "Legacy page asset request failed" not in html


def test_reference_asset_and_loader_consistency():
    asset_path = Path("/app/nextjs/public/_data/legacy-pages.json")
    assert asset_path.exists()
    content = json.loads(asset_path.read_text(encoding="utf-8"))
    assert isinstance(content, list)
    assert any(page.get("route") == "/compare" for page in content if isinstance(page, dict))
    assert any(page.get("route") == "/contact" for page in content if isinstance(page, dict))

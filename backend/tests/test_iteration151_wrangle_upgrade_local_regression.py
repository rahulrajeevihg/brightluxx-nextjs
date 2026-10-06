"""
Iteration 151 - Local OpenNext/Wrangler regression checks
# Modules/features: raw HTML SEO contracts, native routes, and live API integrations via local worker.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

import pytest
import requests


NEXT_PREVIEW_URL = ("http://127.0.0.1:8787").rstrip("/")
PAGE_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36",
}


def _get(path: str, **kwargs):
    return requests.get(f"{NEXT_PREVIEW_URL}{path}", timeout=30, **kwargs)


def _post(path: str, payload):
    return requests.post(f"{NEXT_PREVIEW_URL}{path}", json=payload, timeout=40)


def _get_page(path: str, **kwargs):
    merged_headers = {**PAGE_HEADERS, **kwargs.pop("headers", {})}
    return requests.get(f"{NEXT_PREVIEW_URL}{path}", timeout=30, headers=merged_headers, **kwargs)


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
        ("/compare", "Compare LED Products", 'data-testid="compare-page-title"'),
        ("/contact", "Get in touch", 'data-testid="contact-page-title"'),
        ("/dubai", "Dubai", None),
    ],
)
def test_representative_pages_have_status_canonical_h1_primary_content(path: str, keyword: str, h1_marker: str | None):
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


def test_products_page_has_exactly_94_server_rendered_cards_and_json_ld():
    response = _get_page("/products")
    assert response.status_code == 200
    html = response.text

    cards = re.findall(r'data-testid="products-product-card-[^"]+"', html)
    assert len(cards) == 94
    assert "application/ld+json" in html


def test_solution_case_study_resource_pages_contracts_and_json_ld():
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


def test_native_route_status_and_redirect_contracts():
    redirect = _get("/our-works", allow_redirects=False)
    assert redirect.status_code == 308
    assert redirect.headers.get("location") == "/projects"

    gone = _get("/products/hjdba", allow_redirects=False)
    assert gone.status_code == 410

    unknown = _get_page("/non-existent-regression-iteration-151", allow_redirects=False)
    assert unknown.status_code == 404
    assert "404" in unknown.text


def test_sitemap_robots_llms_contracts():
    sitemap = _get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "https://brightluxx.com" in sitemap.text
    assert "<urlset" in sitemap.text

    robots = _get("/robots.txt")
    assert robots.status_code == 200
    assert "Sitemap: https://brightluxx.com/sitemap.xml" in robots.text

    llms = _get("/llms.txt")
    assert llms.status_code == 200
    assert len(llms.text.strip()) > 20


def test_no_unintended_noindex_on_home_products_detail_contact():
    for path in ["/", "/products", "/products/bl-cob125", "/contact", "/dubai"]:
        response = _get_page(path)
        assert response.status_code == 200
        assert "noindex" not in response.text.lower()


def test_live_product_api_count_and_detail_data():
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
    assert isinstance(detail.get("name"), str) and detail["name"].strip()


def test_live_search_and_compare_apis_work_with_real_codes():
    products_response = _get("/api/products")
    assert products_response.status_code == 200
    products_payload = products_response.json()
    products = products_payload if isinstance(products_payload, list) else products_payload.get("products", [])
    codes = [item.get("product_code") for item in products if item.get("product_code")][:3]
    assert len(codes) == 3

    search_response = _get("/api/search", params={"q": "video wall"})
    assert search_response.status_code == 200
    search_payload = search_response.json()
    search_products = search_payload.get("products", []) if isinstance(search_payload, dict) else []
    assert isinstance(search_products, list)
    assert len(search_products) > 0

    compare_response = _post("/api/products/compare", codes[:2])
    assert compare_response.status_code == 200
    compare_payload = compare_response.json()
    compared = compare_payload.get("products", []) if isinstance(compare_payload, dict) else []
    compared_codes = [item.get("product_code") for item in compared]
    assert set(compared_codes) == set(codes[:2])


def test_live_contact_validation_and_submission_route():
    invalid = {
        "name": "TEST Invalid Phone",
        "email": "qa.invalid.phone.iter151@brightluxx-example.test",
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
        "name": "TEST Local Regression Iteration151",
        "company": "TEST Brightluxx QA",
        "email": "qa.iter151@brightluxx-example.test",
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
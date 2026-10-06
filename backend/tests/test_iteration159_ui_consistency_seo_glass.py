"""
Iteration 159 acceptance sweep.
# Modules/features: homepage hero contract, products catalogue/raw SEO parity,
# BL-COB125 detail content, sampled and full SEO-route semantic-block coverage,
# and critical platform route contracts (redirect/410/sitemap/robots/llms).
"""

from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path

import pytest
import requests


BASE_URL = "http://127.0.0.1:8787".rstrip("/")
TIMEOUT = 40


def _get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)


def _extract_h1_texts(html: str) -> list[str]:
    hits = re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.IGNORECASE | re.DOTALL)
    values: list[str] = []
    for hit in hits:
        no_tags = re.sub(r"<[^>]+>", "", hit)
        values.append(unescape(re.sub(r"\s+", " ", no_tags).strip()))
    return values


def _meta_content(html: str, name: str) -> str | None:
    match = re.search(
        rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']*)["\']',
        html,
        flags=re.IGNORECASE,
    )
    return unescape(match.group(1).strip()) if match else None


def _title(html: str) -> str | None:
    match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return unescape(re.sub(r"\s+", " ", match.group(1)).strip())


def _canonical(html: str) -> str | None:
    match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _seo_block_present(html: str) -> bool:
    return 'data-testid="seo-content-block"' in html


def _is_spa_shell(html: str) -> bool:
    return 'id="root"></div>' in html or "You need to enable JavaScript" in html


def _legacy_inventory() -> list[dict]:
    response = _get("/_data/legacy-pages.json")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    return payload


def _indexable_routes() -> list[str]:
    inventory = _legacy_inventory()
    return [
        item["route"]
        for item in inventory
        if item.get("classification") == "indexable" and isinstance(item.get("schemaTypes"), list) and item.get("schemaTypes")
    ]


def _sample_routes_for_content_block(indexable_routes: list[str]) -> list[str]:
    picked: list[str] = []

    def add(candidates: list[str], limit: int) -> None:
        for route in candidates:
            if route not in picked:
                picked.append(route)
            if len([r for r in picked if r in candidates]) >= limit:
                break

    solution = [r for r in indexable_routes if r.startswith("/solutions/")]
    resource = [r for r in indexable_routes if r.startswith("/resources") or r.startswith("/blog/")]
    application = [r for r in indexable_routes if r.startswith("/applications/")]
    arabic = [r for r in indexable_routes if r.startswith("/ar")]
    location_tokens = ("dubai", "abu-dhabi", "uae", "saudi", "riyadh", "jeddah", "qatar", "doha", "oman", "kuwait")
    location = [r for r in indexable_routes if any(token in r for token in location_tokens)]

    add(solution, 4)
    add(resource, 4)
    add(application, 4)
    add(arabic, 4)
    add(location, 4)

    for route in indexable_routes:
        if len(picked) >= 20:
            break
        if route not in picked:
            picked.append(route)

    return picked[:20]


def test_homepage_raw_h1_exact_and_shell_free():
    response = _get("/")
    assert response.status_code == 200
    html = response.text
    h1s = _extract_h1_texts(html)
    assert h1s == ["Brilliant Displays."]
    assert not _is_spa_shell(html)
    assert "hydration" not in html.lower()


def test_products_api_and_products_raw_html_show_94_cards_with_descriptive_image_alt():
    api_response = _get("/api/products")
    assert api_response.status_code == 200
    api_payload = api_response.json()
    products = api_payload.get("products") if isinstance(api_payload, dict) else None
    assert isinstance(products, list)
    assert len(products) == 94

    page_response = _get("/products")
    assert page_response.status_code == 200
    html = page_response.text
    card_count = len(re.findall(r'data-testid="products-product-card-[^"]+"', html))
    assert card_count == 94

    img_matches = re.findall(
        r'data-testid="products-product-image-[^"]+"[^>]*>\s*<img[^>]+alt="([^"]+)"',
        html,
        flags=re.IGNORECASE,
    )
    assert len(img_matches) == 94
    assert all("LED" in alt and "display" in alt.lower() for alt in img_matches)


def test_bl_cob125_contains_engineering_context_internal_link_specs_gallery_related_alts_and_ctas():
    response = _get("/products/bl-cob125")
    assert response.status_code == 200
    html = response.text

    assert 'data-testid="product-detailed-description"' in html
    assert "Designed around the installation" in html
    assert 'data-testid="product-category-internal-link"' in html
    assert 'data-testid="product-full-specifications"' in html
    assert 'data-testid="product-gallery"' in html
    assert 'data-testid="product-request-pricing-link"' in html
    assert 'data-testid="product-compare-button"' in html

    related_alts = re.findall(r'data-testid="related-product-[^"]+"[^>]*>\s*<img[^>]+alt="([^"]+)"', html)
    assert related_alts
    assert all("LED display" in alt for alt in related_alts)


def test_sampled_20_seo_routes_have_semantic_block_internal_links_keywords_meta_and_single_h1():
    indexable = _indexable_routes()
    sampled = _sample_routes_for_content_block(indexable)
    assert len(sampled) == 20

    for route in sampled:
        if route in {"/", "/products", "/compare", "/contact"} or route.startswith("/products/"):
            continue

        response = _get(route)
        assert response.status_code == 200, f"Route failed: {route}"
        html = response.text

        assert _seo_block_present(html), f"Missing seo content block: {route}"
        assert 'data-testid="seo-internal-link-products"' in html, f"Missing internal links: {route}"
        assert _canonical(html), f"Missing canonical: {route}"
        assert _title(html), f"Missing title: {route}"
        assert _meta_content(html, "description"), f"Missing description: {route}"
        assert _meta_content(html, "keywords"), f"Missing keywords: {route}"
        assert len(_extract_h1_texts(html)) == 1, f"Duplicate/missing h1: {route}"
        assert not _is_spa_shell(html), f"SPA shell detected: {route}"


def test_static_inventory_has_333_indexable_routes_and_generic_renderer_contract_holds():
    indexable = _indexable_routes()
    assert len(indexable) == 333

    generic_expected = [
        r
        for r in indexable
        if r not in {"/", "/products", "/compare", "/contact"} and not r.startswith("/products/")
    ]
    assert len(generic_expected) == 235

    source = Path("/app/nextjs/app/[...slug]/page.tsx").read_text(encoding="utf-8")
    assert "generateStaticParams" in source
    assert "getIndexableRoutes" in source
    assert "<SeoContentBlock page={page} />" in source

    # Runtime verification for every generic-rendered indexable route.
    for route in generic_expected:
        response = _get(route)
        assert response.status_code == 200
        assert _seo_block_present(response.text), f"Missing generic SEO block: {route}"


@pytest.mark.parametrize(
    "path,expected_status",
    [
        ("/our-works", 301),
        ("/products/hjdba", 410),
        ("/sitemap.xml", 200),
        ("/robots.txt", 200),
        ("/llms.txt", 200),
    ],
)
def test_platform_route_contracts(path: str, expected_status: int):
    response = _get(path, allow_redirects=False)
    assert response.status_code == expected_status

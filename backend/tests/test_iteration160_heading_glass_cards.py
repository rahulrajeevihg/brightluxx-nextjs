"""
Iteration 160 regression gate.
# Modules/features: generic legacy heading compaction + metadata integrity,
# dedicated hero headings, products SSR card volume/alts, and platform route contracts.
"""

from __future__ import annotations

import re
from html import unescape

import requests


BASE_URL = "http://127.0.0.1:8787".rstrip("/")
TIMEOUT = 45


def _get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)


def _extract_heading_texts(html: str, tag: str) -> list[str]:
    hits = re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", html, flags=re.IGNORECASE | re.DOTALL)
    values: list[str] = []
    for hit in hits:
        no_tags = re.sub(r"<[^>]+>", "", hit)
        values.append(unescape(re.sub(r"\s+", " ", no_tags).strip()))
    return values


def _title(html: str) -> str | None:
    match = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return unescape(re.sub(r"\s+", " ", match.group(1)).strip())


def _meta_description(html: str) -> str | None:
    match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
        html,
        flags=re.IGNORECASE,
    )
    return unescape(match.group(1).strip()) if match else None


def _canonical(html: str) -> str | None:
    match = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        html,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _word_count(text: str) -> int:
    return len([w for w in re.sub(r"[^A-Za-z0-9\s-]", " ", text).split() if w.strip()])


def _significant_words(text: str) -> list[str]:
    words = re.sub(r"<[^>]+>", "", text)
    words = re.sub(r"[|—–:]", " ", words)
    stop = {"the", "for", "and", "in", "of", "to", "with"}
    return [w for w in re.split(r"\s+", words) if w and w.lower() not in stop]


def _inventory() -> list[dict]:
    response = _get("/_data/legacy-pages.json")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    return data


def test_generic_indexable_routes_h1_metadata_and_seo_block_contracts():
    pages = _inventory()
    indexable = [
        item
        for item in pages
        if item.get("classification") == "indexable"
        and isinstance(item.get("schemaTypes"), list)
        and item.get("schemaTypes")
    ]
    assert len(indexable) >= 235

    generic = [
        item
        for item in indexable
        if item["route"] not in {"/", "/products", "/compare", "/contact"}
        and not item["route"].startswith("/products/")
    ]
    assert len(generic) == 235

    for item in generic:
        route = item["route"]
        response = _get(route)
        assert response.status_code == 200, f"route failed: {route}"
        html = response.text

        h1s = _extract_heading_texts(html, "h1")
        assert len(h1s) == 1, f"expected exactly one h1: {route}"

        assert _title(html), f"missing title: {route}"
        assert _meta_description(html), f"missing description: {route}"
        assert _canonical(html), f"missing canonical: {route}"

        assert 'data-testid="seo-content-block"' in html, f"missing seo block: {route}"
        assert 'data-testid="seo-internal-link-products"' in html, f"missing seo links: {route}"

        source_h1 = str(item.get("h1", ""))
        rendered_h1 = h1s[0]
        transformed_english = (not route.startswith("/ar")) and len(_significant_words(source_h1)) > 3
        if transformed_english:
            assert _word_count(rendered_h1) <= 3, f"non-concise transformed h1 on {route}: {rendered_h1}"
            h2s = _extract_heading_texts(html, "h2")
            assert any(rendered_h1 in h2 and "project planning" in h2.lower() for h2 in h2s), (
                f"seo h2 not aligned with compact heading on {route}"
            )


def test_dedicated_h1_contracts_and_valid_solution_route():
    homepage = _get("/")
    assert homepage.status_code == 200
    assert _extract_heading_texts(homepage.text, "h1") == ["Brilliant Displays."]

    products = _get("/products")
    assert products.status_code == 200
    assert _extract_heading_texts(products.text, "h1") == ["LED Displays"]

    compare = _get("/compare")
    assert compare.status_code == 200
    assert _extract_heading_texts(compare.text, "h1") == ["Compare Displays"]

    education = _get("/solutions/education")
    assert education.status_code == 200
    assert len(_extract_heading_texts(education.text, "h1")) == 1


def test_products_ssr_keeps_94_cards_and_descriptive_alts():
    api = _get("/api/products")
    assert api.status_code == 200
    payload = api.json()
    products = payload.get("products") if isinstance(payload, dict) else None
    assert isinstance(products, list)
    assert len(products) == 94

    page = _get("/products")
    assert page.status_code == 200
    html = page.text

    cards = re.findall(r'data-testid="products-product-card-[^"]+"', html)
    assert len(cards) == 94

    alts = re.findall(
        r'data-testid="products-product-image-[^"]+"[^>]*>\s*<img[^>]+alt="([^"]+)"',
        html,
        flags=re.IGNORECASE,
    )
    assert len(alts) == 94
    assert all(len(alt.strip()) > 12 for alt in alts)


def test_routes_sitemap_robots_llms_redirect_and_410_contracts():
    checks = [
        ("/sitemap.xml", 200),
        ("/robots.txt", 200),
        ("/llms.txt", 200),
        ("/our-works", 301),
        ("/products/hjdba", 410),
    ]
    for path, status in checks:
        response = _get(path, allow_redirects=False)
        assert response.status_code == status, f"{path} expected {status}, got {response.status_code}"

    sitemap = _get("/sitemap.xml")
    assert "<urlset" in sitemap.text and "https://brightluxx.com/products" in sitemap.text

    robots = _get("/robots.txt")
    assert "Disallow: /compare" in robots.text
    assert "Sitemap: https://brightluxx.com/sitemap.xml" in robots.text
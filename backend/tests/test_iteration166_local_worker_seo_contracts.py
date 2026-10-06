"""
Iteration 166
# Modules/features: local workerd SEO/routing contracts and SSR content checks.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests


BASE_URL = "http://127.0.0.1:8787"


def _get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=30, **kwargs)


def _canonical(html: str) -> str | None:
    match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html, flags=re.IGNORECASE)
    return match.group(1) if match else None


def test_luxury_home_cinema_page_contracts() -> None:
    response = _get("/luxury-home-cinema")
    assert response.status_code == 200
    html = response.text

    assert "data-testid=\"luxury-home-cinema-page\"" in html
    assert "data-testid=\"luxury-home-cinema-products\"" in html
    assert len(re.findall(r'data-testid="products-product-card-[^"]+"', html)) > 0
    assert _canonical(html) == "https://brightluxx.com/luxury-home-cinema"
    assert "500" not in html[:2000]


@pytest.mark.parametrize(
    "source,target",
    [
        ("/products/led-display", "/products"),
        ("/products/outdoor-smd-led-display", "/outdoor-led"),
        ("/products/outdoor-dip-led-display", "/outdoor-led"),
        ("/products/transparent-glass-led-display", "/glassmorph"),
        ("/products/curtain-led-display", "/glassmorph"),
        ("/products/soft-flexible-led-display-modules", "/products/bl-flx150"),
        ("/products/floor-led-display", "/products/immersafloor-p39"),
        ("/products/road-signal-led-display", "/products/bl-obx390"),
        ("/perimeter-led-display", "/products/bl-spx470"),
        ("/die-cast-rental-led-display", "/products/bl-rpx290"),
        ("/shelf-led-display", "/products/bl-shf120"),
        ("/lumimorph-elite", "/lumimorph/elite"),
    ],
)
def test_legacy_redirects_and_trailing_slash_one_hop(source: str, target: str) -> None:
    for candidate in (source, f"{source}/"):
        response = _get(candidate, allow_redirects=False)
        assert response.status_code == 301
        location = response.headers.get("location", "")
        assert urlparse(location).path == target


def test_category_redirect_and_destination_canonical() -> None:
    redirected = _get("/products?category=luxury-home-cinema", allow_redirects=False)
    assert redirected.status_code == 301
    location = redirected.headers.get("location", "")
    assert urlparse(location).path == "/luxury-home-cinema"

    destination = _get(location if location.startswith("/") else "/luxury-home-cinema")
    assert destination.status_code == 200
    assert _canonical(destination.text) == "https://brightluxx.com/luxury-home-cinema"


def test_404_and_410_contracts() -> None:
    unknown = _get("/totally-unknown-iteration-166-route", allow_redirects=False)
    assert unknown.status_code == 404

    gone = _get("/products/hjdba", allow_redirects=False)
    assert gone.status_code == 410


def test_robots_and_sitemap_contracts() -> None:
    robots = _get("/robots.txt")
    assert robots.status_code == 200
    assert "Disallow: /compare$" in robots.text

    sitemap = _get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "https://brightluxx.com/luxury-home-cinema" in sitemap.text
    assert "https://brightluxx.com/lumimorph-elite" not in sitemap.text


def test_inspirations_routes_from_source_sitemap_are_reachable() -> None:
    routes_path = Path("/app/migration-baseline/routes.json")
    payload = json.loads(routes_path.read_text(encoding="utf-8"))
    expected_routes = {
        row["route"]
        for row in payload
        if row.get("route", "").startswith("/inspirations")
        and row.get("classification") == "indexable"
        and row.get("sitemapStatus") == "expected"
    }

    sitemap = _get("/sitemap.xml")
    assert sitemap.status_code == 200
    locs = set(re.findall(r"<loc>https://brightluxx.com([^<]+)</loc>", sitemap.text))
    for route in sorted(expected_routes):
        assert route in locs
        live = _get(route)
        assert live.status_code == 200


def test_abu_dhabi_title_description_h1_contracts() -> None:
    response = _get("/abu-dhabi")
    assert response.status_code == 200
    html = response.text
    assert "<title>Video Walls &amp; LED Screens in Abu Dhabi | Brightluxx</title>" in html
    assert (
        '<meta name="description" content="Plan video walls and LED screens for Abu Dhabi projects with Brightluxx engineering support, specification guidance and installation coordination."'
        in html
    )
    assert re.search(r"<h1[^>]*>Video Walls &amp; LED Screens in Abu Dhabi</h1>", html)


@pytest.mark.parametrize(
    "route,snippet",
    [
        ("/applications/retail", "Retail display planning"),
        ("/for-contractors", "Contractor specification support"),
        ("/resource-library", "LED display specification resources"),
        ("/compare-products", "Compare LED display specifications"),
    ],
)
def test_route_guidance_content_in_server_html(route: str, snippet: str) -> None:
    response = _get(route)
    assert response.status_code == 200
    assert snippet in response.text


def test_blog_guide_contains_internal_abu_dhabi_link() -> None:
    response = _get("/blog/led-display-solutions-abu-dhabi-guide")
    assert response.status_code == 200
    html = response.text
    assert 'href="/abu-dhabi"' in html or 'href="https://brightluxx.com/abu-dhabi"' in html


@pytest.mark.parametrize("route", ["/pixelvue", "/lumimorph", "/glassmorph", "/naturatex", "/signatouch"])
def test_family_routes_have_product_aggregateoffer_without_aggregaterating(route: str) -> None:
    response = _get(route)
    assert response.status_code == 200
    html = response.text
    scripts = re.findall(r"<script type=\"application/ld\+json\">(.*?)</script>", html)
    assert scripts

    matched = False
    for raw in scripts:
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        if payload.get("@type") == "Product":
            matched = True
            assert payload.get("offers", {}).get("@type") == "AggregateOffer"
            assert "aggregateRating" not in payload
            break

    assert matched

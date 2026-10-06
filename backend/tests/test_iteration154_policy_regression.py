"""
Iteration 154 - Post-fix route-policy regression checks.
# Modules/features: baseline policy counts/statuses, root/compare/contact SEO contract, 410 and sitemap contract.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

import requests


BASE_URL = "http://127.0.0.1:8787".rstrip("/")
BASELINE_PATH = Path("/app/migration-baseline/routes.json")


def _get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=35, **kwargs)


def _load_baseline() -> list[dict]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def test_baseline_policy_matrix_and_status_contracts():
    baseline = _load_baseline()
    assert len(baseline) == 352

    indexable = [r for r in baseline if r.get("classification") == "indexable"]
    redirects = [r for r in baseline if r.get("classification") == "redirect"]
    gone = [r for r in baseline if str(r.get("statusIntent")) == "410" or r.get("classification") == "gone"]

    assert len(indexable) == 333
    assert len(redirects) == 18
    assert len(gone) == 1

    mismatches: list[tuple[str, int, int]] = []
    for route_def in baseline:
        route = route_def["route"]
        expected_status = int(route_def.get("statusIntent", "200"))
        response = _get(route, allow_redirects=False)
        if response.status_code != expected_status:
            mismatches.append((route, expected_status, response.status_code))

    assert not mismatches, f"Status mismatches found: {mismatches[:10]}"


def test_root_compare_contact_h1_and_noindex_contracts():
    home = _get("/")
    assert home.status_code == 200
    assert 'rel="canonical" href="https://brightluxx.com"' in home.text
    assert "LED Display &amp; Digital Signage Solutions for UAE &amp; GCC" in home.text

    compare = _get("/compare")
    assert compare.status_code == 200
    assert "Compare LED Display Products Side by Side | Brightluxx" in compare.text
    assert not re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
        compare.text,
        flags=re.IGNORECASE,
    )
    assert "x-robots-tag" not in {k.lower(): v for k, v in compare.headers.items()}

    contact = _get("/contact")
    assert contact.status_code == 200
    assert "<h1 data-testid=\"contact-page-title\">Get in Touch</h1>" in contact.text


def test_native_410_and_sitemap_contract():
    gone = _get("/products/hjdba", allow_redirects=False)
    assert gone.status_code == 410

    baseline = _load_baseline()
    indexable_routes = {item["route"] for item in baseline if item.get("classification") == "indexable"}

    sitemap = _get("/sitemap.xml")
    assert sitemap.status_code == 200
    sitemap_locs = re.findall(r"<loc>([^<]+)</loc>", sitemap.text)
    sitemap_paths = {urlparse(loc).path or "/" for loc in sitemap_locs}

    missing = sorted(indexable_routes - sitemap_paths)
    unexpected = sorted(sitemap_paths - indexable_routes)
    assert not missing, f"Sitemap missing routes sample: {missing[:10]}"
    assert not unexpected, f"Sitemap unexpected routes sample: {unexpected[:10]}"

"""
Iteration 153 - Full local SEO regression for OpenNext worker bundle-size refactor.
# Modules/features: 352 baseline route audit, canonical/meta/H1/schema validation, sitemap/robots/llms,
# known redirect/410/404 contracts, and API->SSR products parity checks.
"""

from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests


BASE_URL = "http://127.0.0.1:8787".rstrip("/")
BASELINE_PATH = Path("/app/migration-baseline/routes.json")
ARTIFACT_DIR = Path("/app/test_reports/artifacts/iteration_153")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_SUMMARY_PATH = ARTIFACT_DIR / "baseline_route_audit_summary.json"

PAGE_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36",
}


def _get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=35, **kwargs)


def _get_html(path: str, **kwargs) -> requests.Response:
    headers = {**PAGE_HEADERS, **kwargs.pop("headers", {})}
    return requests.get(f"{BASE_URL}{path}", timeout=35, headers=headers, **kwargs)


def _load_baseline() -> list[dict]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _extract_first(pattern: str, html: str) -> str | None:
    match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    return unescape(match.group(1).strip()) if match else None


def _extract_title(html: str) -> str | None:
    return _extract_first(r"<title>(.*?)</title>", html)


def _extract_description(html: str) -> str | None:
    return _extract_first(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', html)


def _extract_canonical(html: str) -> str | None:
    return _extract_first(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', html)


def _extract_h1_texts(html: str) -> list[str]:
    texts = re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.IGNORECASE | re.DOTALL)
    cleaned: list[str] = []
    for text in texts:
        no_tags = re.sub(r"<[^>]+>", "", text)
        cleaned.append(unescape(re.sub(r"\\s+", " ", no_tags).strip()))
    return cleaned


def _extract_jsonld_blocks(html: str) -> list[str]:
    return re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _collect_schema_types(data, sink: set[str]) -> None:
    if isinstance(data, dict):
        schema_type = data.get("@type")
        if isinstance(schema_type, str):
            sink.add(schema_type)
        elif isinstance(schema_type, list):
            sink.update({item for item in schema_type if isinstance(item, str)})
        for value in data.values():
            _collect_schema_types(value, sink)
    elif isinstance(data, list):
        for item in data:
            _collect_schema_types(item, sink)


def _normalize(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _alnum_normalize(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def _path_from_canonical(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path or "/"


def _write_summary(payload: dict) -> None:
    AUDIT_SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def test_baseline_352_routes_status_and_seo_contracts():
    baseline = _load_baseline()
    assert len(baseline) == 352, "Baseline route inventory count changed unexpectedly"

    totals = {
        "baseline_total": len(baseline),
        "baseline_indexable": sum(1 for r in baseline if r.get("classification") == "indexable"),
        "baseline_redirect": sum(1 for r in baseline if r.get("classification") == "redirect"),
        "baseline_410": sum(1 for r in baseline if str(r.get("statusIntent")) == "410"),
        "indexable_passed": 0,
        "redirect_passed": 0,
        "status_mismatches": 0,
        "unexplained_gaps": 0,
        "unexpected_status_changes": 0,
        "critical_seo_failures": 0,
    }
    issues: list[dict] = []

    for route_def in baseline:
        route = route_def["route"]
        classification = route_def.get("classification")
        expected_status = int(route_def.get("statusIntent", "200"))

        if classification == "redirect":
            response = _get(route, allow_redirects=False)
            if response.status_code != expected_status:
                totals["status_mismatches"] += 1
                totals["unexpected_status_changes"] += 1
                issues.append(
                    {
                        "route": route,
                        "type": "status_mismatch",
                        "expected": expected_status,
                        "actual": response.status_code,
                    }
                )
                continue

            location = response.headers.get("location", "")
            canonical = route_def.get("canonical", "")
            expected_path = _path_from_canonical(canonical) if canonical else ""
            if expected_path and not location.endswith(expected_path):
                totals["critical_seo_failures"] += 1
                issues.append(
                    {
                        "route": route,
                        "type": "redirect_target_mismatch",
                        "expected_location_suffix": expected_path,
                        "actual_location": location,
                    }
                )
                continue

            totals["redirect_passed"] += 1
            continue

        if expected_status == 410 or classification == "gone":
            response = _get(route, allow_redirects=False)
            if response.status_code != 410:
                totals["status_mismatches"] += 1
                totals["unexplained_gaps"] += 1
                totals["unexpected_status_changes"] += 1
                issues.append({"route": route, "type": "status_mismatch", "expected": 410, "actual": response.status_code})
            continue

        response = _get_html(route, allow_redirects=False)
        if response.status_code != expected_status:
            totals["status_mismatches"] += 1
            totals["unexplained_gaps"] += 1
            totals["unexpected_status_changes"] += 1
            issues.append(
                {
                    "route": route,
                    "type": "status_mismatch",
                    "expected": expected_status,
                    "actual": response.status_code,
                }
            )
            continue

        html = response.text

        if "Legacy page asset binding is unavailable" in html or "Legacy page asset request failed" in html:
            totals["critical_seo_failures"] += 1
            issues.append({"route": route, "type": "legacy_asset_error_visible"})

        if 'id="root"></div>' in html or "You need to enable JavaScript" in html:
            totals["critical_seo_failures"] += 1
            issues.append({"route": route, "type": "spa_shell_detected"})

        if "https://brightluxx.com" not in html:
            totals["critical_seo_failures"] += 1
            issues.append({"route": route, "type": "canonical_host_not_present"})

        canonical = _extract_canonical(html)
        expected_canonical = route_def.get("canonical")
        if expected_canonical and canonical != expected_canonical:
            totals["critical_seo_failures"] += 1
            issues.append(
                {
                    "route": route,
                    "type": "canonical_mismatch",
                    "expected": expected_canonical,
                    "actual": canonical,
                }
            )

        expected_title = route_def.get("title")
        if expected_title:
            title = _extract_title(html)
            if _normalize(title) != _normalize(expected_title):
                totals["critical_seo_failures"] += 1
                issues.append(
                    {
                        "route": route,
                        "type": "title_mismatch",
                        "expected": expected_title,
                        "actual": title,
                    }
                )

        expected_description = route_def.get("description")
        if expected_description:
            description = _extract_description(html)
            if _normalize(description) != _normalize(expected_description):
                totals["critical_seo_failures"] += 1
                issues.append(
                    {
                        "route": route,
                        "type": "description_mismatch",
                        "expected": expected_description,
                        "actual": description,
                    }
                )

        expected_h1 = route_def.get("h1")
        if expected_h1:
            h1_texts = _extract_h1_texts(html)
            if len(h1_texts) != 1:
                totals["critical_seo_failures"] += 1
                issues.append(
                    {
                        "route": route,
                        "type": "h1_count_mismatch",
                        "expected": 1,
                        "actual": len(h1_texts),
                    }
                )
            elif _normalize(h1_texts[0]) != _normalize(expected_h1):
                totals["critical_seo_failures"] += 1
                issues.append(
                    {
                        "route": route,
                        "type": "h1_text_mismatch",
                        "expected": expected_h1,
                        "actual": h1_texts[0],
                    }
                )

        expected_schema_types = {s for s in route_def.get("schemaTypes", []) if isinstance(s, str)}
        if expected_schema_types:
            jsonld_blocks = _extract_jsonld_blocks(html)
            if not jsonld_blocks:
                totals["critical_seo_failures"] += 1
                issues.append({"route": route, "type": "missing_jsonld"})
            else:
                discovered_types: set[str] = set()
                for block in jsonld_blocks:
                    try:
                        parsed = json.loads(block.strip())
                    except json.JSONDecodeError:
                        continue
                    _collect_schema_types(parsed, discovered_types)
                missing_types = sorted(expected_schema_types - discovered_types)
                if missing_types:
                    totals["critical_seo_failures"] += 1
                    issues.append(
                        {
                            "route": route,
                            "type": "missing_schema_types",
                            "missing": missing_types,
                        }
                    )

        if re.search(
            r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
            html,
            flags=re.IGNORECASE,
        ):
            totals["critical_seo_failures"] += 1
            issues.append({"route": route, "type": "unexpected_noindex"})

        totals["indexable_passed"] += 1

    payload = {
        "totals": totals,
        "sample_issues": issues[:200],
        "all_issue_count": len(issues),
    }
    _write_summary(payload)

    assert not issues, f"Route/SEO audit found {len(issues)} issues. See {AUDIT_SUMMARY_PATH}"
    assert totals["indexable_passed"] == totals["baseline_indexable"]
    assert totals["redirect_passed"] == totals["baseline_redirect"]


def test_sitemap_robots_llms_unknown_404_and_known_redirect_410_contracts():
    baseline = _load_baseline()
    indexable_routes = {item["route"] for item in baseline if item.get("classification") == "indexable"}

    sitemap_response = _get("/sitemap.xml")
    assert sitemap_response.status_code == 200
    sitemap_locs = re.findall(r"<loc>([^<]+)</loc>", sitemap_response.text)
    sitemap_paths = {urlparse(loc).path or "/" for loc in sitemap_locs}

    missing = sorted(indexable_routes - sitemap_paths)
    unexpected = sorted(sitemap_paths - indexable_routes)
    assert not missing, f"Sitemap missing indexable routes, sample: {missing[:10]}"
    assert not unexpected, f"Sitemap has unexpected routes, sample: {unexpected[:10]}"

    robots_response = _get("/robots.txt")
    assert robots_response.status_code == 200
    robots_text = robots_response.text
    assert "Sitemap: https://brightluxx.com/sitemap.xml" in robots_text
    assert not re.search(r"(?mi)^Disallow:\s*/\s*$", robots_text)

    llms_response = _get("/llms.txt")
    assert llms_response.status_code == 200
    assert len(llms_response.text.strip()) > 20

    unknown = _get_html("/__iter153_unknown_route__", allow_redirects=False)
    assert unknown.status_code == 404

    known_redirect = _get("/our-works", allow_redirects=False)
    assert known_redirect.status_code in (301, 308)
    assert known_redirect.headers.get("location") == "/projects"

    known_410 = _get("/products/hjdba", allow_redirects=False)
    assert known_410.status_code == 410


def test_live_products_api_parity_with_ssr_products_grid_and_detail_seo():
    api_products_response = _get("/api/products")
    assert api_products_response.status_code == 200
    payload = api_products_response.json()
    products = payload if isinstance(payload, list) else payload.get("products", [])
    assert isinstance(products, list)
    assert len(products) == 94

    products_page = _get_html("/products")
    assert products_page.status_code == 200
    html = products_page.text
    cards = re.findall(r'data-testid="products-product-card-[^"]+"', html)
    assert len(cards) == 94
    assert "application/ld+json" in html
    assert "Legacy page asset" not in html

    representative = []
    if products:
        representative = [products[0], products[len(products) // 2], products[-1]]

    for product in representative:
        slug = product.get("slug")
        if not isinstance(slug, str) or not slug:
            pytest.fail(f"Product missing slug in API payload: {product}")

        detail_api = _get(f"/api/products/{slug}")
        assert detail_api.status_code == 200
        detail_payload = detail_api.json()

        detail_page = _get_html(f"/products/{slug}")
        assert detail_page.status_code == 200
        detail_html = detail_page.text

        canonical = _extract_canonical(detail_html)
        assert canonical == f"https://brightluxx.com/products/{slug}"

        ld_blocks = _extract_jsonld_blocks(detail_html)
        assert ld_blocks, f"Missing JSON-LD on /products/{slug}"
        assert "Product" in detail_html or "application/ld+json" in detail_html

        api_name = detail_payload.get("name") or detail_payload.get("product_name")
        if isinstance(api_name, str) and api_name.strip():
            assert _alnum_normalize(api_name) in _alnum_normalize(unescape(detail_html))


def test_no_legacy_asset_errors_on_representative_routes_post_refactor():
    sample_routes = ["/", "/products", "/products/bl-cob125", "/dubai", "/contact", "/compare", "/blog"]
    for route in sample_routes:
        response = _get_html(route)
        assert response.status_code == 200
        html = response.text
        assert "Legacy page asset binding is unavailable" not in html
        assert "Legacy page asset request failed" not in html

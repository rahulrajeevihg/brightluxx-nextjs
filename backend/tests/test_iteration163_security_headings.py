"""
Iteration 163 regression gate.
# Modules/features: legacy content safety helpers, curated heading mapping,
# and critical legacy/product routes rendering with JSON-LD intact.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

import requests


BASE_URL = "http://127.0.0.1:8787".rstrip("/")
TIMEOUT = 45
ROOT = Path("/app")


def _get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)


def _extract_h1(html: str) -> str | None:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return re.sub(r"<[^>]+>", "", match.group(1)).strip()


def _node_eval_content_safety(script_tail: str) -> dict:
    source = (ROOT / "nextjs/lib/content-safety.ts").read_text(encoding="utf-8")
    js_source = source.replace(
        "export function validateTrustedHtml(html: string)",
        "function validateTrustedHtml(html)",
    ).replace(
        "export function safeJsonLd(item: string)",
        "function safeJsonLd(item)",
    ).replace(": unknown", "")
    program = f"{js_source}\n{script_tail}"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tmp:
        tmp.write(program)
        tmp_path = tmp.name
    result = subprocess.run(["node", tmp_path], capture_output=True, text=True)
    assert result.returncode == 0, f"node execution failed: {result.stderr}\n{result.stdout}"
    return json.loads(result.stdout.strip())


def test_legacy_and_commercial_routes_render_without_safety_or_asset_errors():
    inventory_response = _get("/_data/legacy-pages.json")
    assert inventory_response.status_code == 200
    inventory = inventory_response.json()
    assert isinstance(inventory, list)

    by_route = {item["route"]: item for item in inventory if isinstance(item, dict) and "route" in item}
    assert len(by_route) > 300

    products_response = _get("/api/products")
    assert products_response.status_code == 200
    products_payload = products_response.json()
    products = products_payload.get("products") if isinstance(products_payload, dict) else None
    assert isinstance(products, list)
    assert len(products) == 94
    first_slug = products[0]["slug"]

    critical_routes = [
        "/products",
        f"/products/{first_slug}",
        "/compare",
        "/contact",
        "/dubai",
    ]

    for route in critical_routes:
        response = _get(route)
        assert response.status_code == 200, f"route failed: {route}"
        html = response.text
        assert "Unsafe legacy HTML" not in html, f"unexpected unsafe-html banner on {route}"
        assert "Legacy page asset binding is unavailable" not in html, f"asset binding error on {route}"
        assert "Legacy page asset request failed" not in html, f"asset fetch error on {route}"

        if route in by_route:
            page = by_route[route]
            json_ld_count = len(page.get("jsonLd", [])) if isinstance(page.get("jsonLd"), list) else 0
            if json_ld_count > 0:
                scripts = re.findall(r'<script[^>]+type="application/ld\+json"', html, flags=re.IGNORECASE)
                assert len(scripts) >= json_ld_count

    products_page = _get("/products")
    cards = re.findall(r'data-testid="products-product-card-[^"]+"', products_page.text)
    assert len(cards) == 94


def test_validate_trusted_html_rejects_unsafe_patterns_and_allows_safe_markup():
    payloads = {
        "script_tag": "<section><script>alert(1)</script></section>",
        "inline_handler": "<button onclick=\"alert(1)\">X</button>",
        "javascript_url": "<a href=\"javascript:alert(1)\">x</a>",
        "iframe": "<iframe src=\"https://example.com\"></iframe>",
        "data_text_html": "<a href=\"data:text/html,<script>alert(1)</script>\">x</a>",
    }
    script_tail = f"""
const payloads = {json.dumps(payloads)};
const out = {{}};
for (const [name, value] of Object.entries(payloads)) {{
  try {{
    validateTrustedHtml(value);
    out[name] = false;
  }} catch (err) {{
    out[name] = String(err && err.message || '').includes('Unsafe legacy HTML');
  }}
}}
out.safe_html = validateTrustedHtml('<article><h1>Safe</h1><p>ok</p></article>');
console.log(JSON.stringify(out));
"""
    output = _node_eval_content_safety(script_tail)
    assert output["script_tag"] is True
    assert output["inline_handler"] is True
    assert output["javascript_url"] is True
    assert output["iframe"] is True
    assert output["data_text_html"] is True
    assert output["safe_html"] == "<article><h1>Safe</h1><p>ok</p></article>"


def test_safe_jsonld_escapes_script_breakouts_and_drops_invalid_json():
    valid_json_ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "name": "FAQ",
            "description": "Contains </script><script>alert(1)</script>",
        }
    )
    script_tail = f"""
const validInput = {json.dumps(valid_json_ld)};
const escaped = safeJsonLd(validInput);
const invalid = safeJsonLd('{{bad json');
const baseline = safeJsonLd(JSON.stringify({{"@context":"https://schema.org","@type":"Organization","name":"Brightluxx"}}));
console.log(JSON.stringify({{
  escaped,
  invalid,
  baseline,
  escaped_has_raw_script_close: escaped ? escaped.includes('</script>') : false
}}));
"""
    output = _node_eval_content_safety(script_tail)

    assert output["invalid"] is None
    assert isinstance(output["escaped"], str)
    assert output["escaped_has_raw_script_close"] is False
    assert "\\u003c/script\\u003e" in output["escaped"]

    baseline = json.loads(output["baseline"])
    assert baseline["@context"] == "https://schema.org"
    assert baseline["@type"] == "Organization"
    assert baseline["name"] == "Brightluxx"


def test_curated_routes_use_expected_headings_and_uncurated_route_keeps_source_h1():
    inventory = _get("/_data/legacy-pages.json").json()
    by_route = {item["route"]: item for item in inventory if isinstance(item, dict) and "route" in item}

    curated_expected = {
        "/dubai": "Dubai Displays",
        "/abu-dhabi": "Abu Dhabi",
        "/oman": "Oman Displays",
        "/solutions/education": "Education Displays",
        "/resources": "LED Resources",
        "/case-studies": "Project Stories",
        "/inspirations": "Display Ideas",
        "/ar-ae/dubai": "شاشات دبي",
    }
    for route, expected in curated_expected.items():
        response = _get(route)
        assert response.status_code == 200
        assert _extract_h1(response.text) == expected

    uncurated_route = "/applications"
    response = _get(uncurated_route)
    assert response.status_code == 200
    rendered_h1 = _extract_h1(response.text)
    assert rendered_h1 == by_route[uncurated_route]["h1"]


def test_analytics_source_keeps_stale_fallback_drop_guard_and_pii_safe_contract():
    source = (ROOT / "nextjs/lib/analytics.ts").read_text(encoding="utf-8")
    assert "if (event === 'page_view' && window.location.pathname !== eventPage) return;" in source
    assert "credentials: 'omit'" in source
    assert "const body = JSON.stringify({ event, page: eventPage, referrer: document.referrer || '', session_id: sessionId(), screen_width: window.innerWidth, ...details });" in source
    assert "email" not in source
    assert "phone" not in source

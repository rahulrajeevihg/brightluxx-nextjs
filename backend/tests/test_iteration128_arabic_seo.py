"""Iteration 128: Arabic /ar-ae SEO + sitemap regression checks."""

import json
import os
import re

import pytest
import requests
from dotenv import dotenv_values


frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")


# --- Arabic static HTML file checks ---
ARABIC_BUILD_CASES = [
    {
        "route": "/ar-ae/",
        "file": "/app/frontend/build/ar-ae/index.html",
        "canonical": "https://brightluxx.com/ar-ae/",
        "expects_hreflang": True,
        "en_href": "https://brightluxx.com/",
    },
    {
        "route": "/ar-ae/dubai",
        "file": "/app/frontend/build/ar-ae/dubai/index.html",
        "canonical": "https://brightluxx.com/ar-ae/dubai",
        "expects_hreflang": True,
        "en_href": "https://brightluxx.com/dubai",
    },
    {
        "route": "/ar-ae/uae",
        "file": "/app/frontend/build/ar-ae/uae/index.html",
        "canonical": "https://brightluxx.com/ar-ae/uae",
        "expects_hreflang": False,
        "en_href": None,
    },
]


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_jsonld_blocks(html: str):
    return re.findall(
        r'<script\s+type="application/ld\+json">(.*?)</script>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )


@pytest.mark.parametrize("case", ARABIC_BUILD_CASES)
def test_arabic_build_file_exists_with_meaningful_content_and_single_h1(case):
    html = _read(case["file"])
    assert "<html lang=\"ar\"" in html
    assert "dir=\"rtl\"" in html

    # Must include substantial Arabic body content, not just shell
    arabic_letters = re.findall(r"[\u0600-\u06FF]", html)
    assert len(arabic_letters) > 120, f"Arabic content appears too thin in {case['route']}"

    root_match = re.search(r'<div id="root">(.*?)</div><script', html, flags=re.DOTALL)
    assert root_match, f"Missing prerendered #root content for {case['route']}"
    root_html = root_match.group(1)
    h1_count = len(re.findall(r"<h1[\\s>]", root_html, flags=re.IGNORECASE))
    assert h1_count == 1, f"Expected exactly one H1 in prerendered root for {case['route']}, got {h1_count}"


@pytest.mark.parametrize("case", ARABIC_BUILD_CASES)
def test_arabic_build_canonical_jsonld_and_hreflang_behavior(case):
    html = _read(case["file"])

    canonical_match = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    assert canonical_match, f"Missing canonical on {case['route']}"
    assert canonical_match.group(1) == case["canonical"]
    assert canonical_match.group(1).startswith("https://brightluxx.com/")

    blocks = _extract_jsonld_blocks(html)
    assert blocks, f"No JSON-LD block on {case['route']}"
    for block in blocks:
        parsed = json.loads(block)
        assert isinstance(parsed, dict)
        assert "@type" in parsed

    alternates = re.findall(
        r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"',
        html,
        flags=re.IGNORECASE,
    )
    if case["expects_hreflang"]:
        lang_to_href = {lang: href for lang, href in alternates}
        assert "en-AE" in lang_to_href
        assert "x-default" in lang_to_href
        assert lang_to_href["en-AE"] == case["en_href"]
        assert lang_to_href["x-default"] == case["en_href"]
    else:
        assert alternates == [], f"Unexpected alternates on {case['route']}: {alternates}"


# --- Dynamic sitemap endpoint checks ---
def test_api_sitemap_contains_arabic_routes():
    resp = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=25)
    assert resp.status_code == 200
    assert "application/xml" in resp.headers.get("content-type", "")
    xml = resp.text
    assert "https://brightluxx.com/ar-ae/" in xml
    assert "https://brightluxx.com/ar-ae/dubai" in xml
    assert "https://brightluxx.com/ar-ae/uae" in xml

"""
Iteration 147 - Contact raw HTML regression checks
# Modules/features: OpenNext local worker raw-source contract, contact query context, route-status contract.
"""

from __future__ import annotations

import os
import re

import pytest
import requests


NEXT_PREVIEW_URL = os.environ.get("NEXT_PREVIEW_URL")
if not NEXT_PREVIEW_URL:
    pytest.skip("NEXT_PREVIEW_URL is not configured", allow_module_level=True)
NEXT_PREVIEW_URL = NEXT_PREVIEW_URL.rstrip("/")


@pytest.mark.parametrize("attempt", range(1, 11))
def test_contact_raw_html_has_canonical_single_h1_and_form_fields_repeated(attempt: int):
    response = requests.get(f"{NEXT_PREVIEW_URL}/contact", timeout=30)
    assert response.status_code == 200

    html = response.text
    assert '<link rel="canonical"' in html
    assert len(re.findall(r"<h1(?:\s|>)", html, flags=re.IGNORECASE)) == 1
    assert 'data-testid="contact-form"' in html
    assert 'data-testid="contact-name-input"' in html
    assert 'data-testid="contact-email-input"' in html
    assert 'data-testid="contact-phone-input"' in html
    assert 'data-testid="contact-submit-button"' in html


def test_contact_products_query_raw_html_contains_exact_context_codes():
    codes = ["BL-COB125", "BL-OH6", "BL-TX2"]
    products = ",".join(codes)

    response = requests.get(f"{NEXT_PREVIEW_URL}/contact", params={"products": products}, timeout=30)
    assert response.status_code == 200

    html = response.text
    assert 'data-testid="contact-product-context"' in html
    for code in codes:
        assert code in html
    assert "Pricing request for" in html


@pytest.mark.parametrize(
    "path,expected_status",
    [
        ("/products", 200),
        ("/products/bl-cob125", 200),
        ("/compare", 200),
        ("/contact", 200),
        ("/dubai", 200),
        ("/solutions", 200),
        ("/case-studies", 200),
        ("/resources", 200),
        ("/our-works", 308),
        ("/products/hjdba", 410),
        ("/sitemap.xml", 200),
        ("/robots.txt", 200),
        ("/llms.txt", 200),
        ("/this-route-should-not-exist-iteration-147", 404),
    ],
)
def test_next_preview_route_status_contract(path: str, expected_status: int):
    response = requests.get(f"{NEXT_PREVIEW_URL}{path}", timeout=30, allow_redirects=False)
    assert response.status_code == expected_status

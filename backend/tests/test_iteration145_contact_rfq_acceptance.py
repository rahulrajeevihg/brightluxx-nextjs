"""
Iteration 145 - Contact RFQ migration acceptance checks
# Modules/features: public leads submission, analytics tracking, and OpenNext route/status contract.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import requests


def _read_frontend_env_value(key: str) -> str | None:
    env_path = Path("/app/frontend/.env")
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None


PUBLIC_BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL") or _read_frontend_env_value("REACT_APP_BACKEND_URL")
if not PUBLIC_BACKEND_URL:
    pytest.skip("REACT_APP_BACKEND_URL is not configured", allow_module_level=True)
PUBLIC_BACKEND_URL = PUBLIC_BACKEND_URL.rstrip("/")

NEXT_PREVIEW_URL = os.environ.get("NEXT_PREVIEW_URL", "http://127.0.0.1:8787").rstrip("/")


def test_public_health_endpoint_ok():
    response = requests.get(f"{PUBLIC_BACKEND_URL}/api/health", timeout=30)
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "ok"
    assert isinstance(payload.get("database"), str)


def test_track_endpoint_accepts_expected_taxonomy_event():
    payload = {
        "event": "comparison_pricing_request",
        "page": "/compare",
        "session_id": "TEST_iteration145_track",
        "screen_width": 390,
        "comparison_codes": ["BL-COB125", "BL-OH6", "BL-TX2"],
        "form_type": "comparison",
    }
    response = requests.post(f"{PUBLIC_BACKEND_URL}/api/track", json=payload, timeout=30)
    assert response.status_code == 200
    body = response.json()
    assert body.get("ok") is True


def test_lead_submission_valid_payload_not_server_error():
    payload = {
        "name": "Test RFQ Iteration145",
        "company": "TEST Brightluxx QA",
        "email": "qa.iter145@brightluxx-example.test",
        "phone": "+971501234567",
        "city": "Dubai",
        "application": "Corporate",
        "timeline": "1-3 months",
        "budget": "AED 200k - 400k",
        "message": "Non-sensitive migration acceptance test submission. Please ignore.",
        "source": "comparison_request",
        "product_interest": "BL-COB125, BL-OH6, BL-TX2",
        "website": "",
        "fax": "",
    }
    response = requests.post(f"{PUBLIC_BACKEND_URL}/api/leads", json=payload, timeout=40)
    assert response.status_code < 500
    data = response.json()
    if response.status_code == 200:
        assert data.get("success") is True
        assert isinstance(data.get("message"), str) and data["message"].strip()
    else:
        assert response.status_code in (400, 422, 429)
        assert isinstance(data.get("detail"), str) and data["detail"].strip()


def test_lead_submission_rejects_invalid_phone():
    payload = {
        "name": "Test Invalid Phone",
        "company": "TEST Brightluxx QA",
        "email": "qa.valid145@brightluxx-example.test",
        "phone": "123",
        "city": "Dubai",
        "application": "Corporate",
        "message": "Phone validation test for migration gate.",
        "source": "comparison_request",
        "product_interest": "BL-COB125, BL-OH6, BL-TX2",
        "website": "",
        "fax": "",
    }
    response = requests.post(f"{PUBLIC_BACKEND_URL}/api/leads", json=payload, timeout=40)
    assert response.status_code == 422
    payload = response.json()
    assert isinstance(payload.get("detail"), str)
    assert "phone" in payload["detail"].lower()


def test_contact_raw_html_has_canonical_single_h1_and_form_fields():
    response = requests.get(f"{NEXT_PREVIEW_URL}/contact", timeout=30)
    assert response.status_code == 200
    html = response.text

    assert '<link rel="canonical"' in html
    assert len(re.findall(r"<h1[\s>]", html, flags=re.IGNORECASE)) == 1
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
        ("/our-works", 301),
        ("/products/hjdba", 410),
        ("/sitemap.xml", 200),
        ("/robots.txt", 200),
        ("/llms.txt", 200),
        ("/this-route-should-not-exist-iteration-145", 404),
    ],
)
def test_next_preview_route_status_contract(path: str, expected_status: int):
    response = requests.get(f"{NEXT_PREVIEW_URL}{path}", timeout=30, allow_redirects=False)
    assert response.status_code == expected_status

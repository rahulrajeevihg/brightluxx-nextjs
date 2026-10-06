"""
Iteration 161 transport regression gate.
# Modules/features: analytics ingest endpoint transport reliability and core product API contract.
"""

from __future__ import annotations

import requests


BASE_URL = "http://127.0.0.1:8787".rstrip("/")
TIMEOUT = 30


def test_api_track_accepts_page_view_payload():
    payload = {
        "event": "page_view",
        "page": "/products",
        "referrer": "",
        "session_id": "iter161-session",
        "screen_width": 1920,
    }
    response = requests.post(f"{BASE_URL}/api/track", json=payload, timeout=TIMEOUT)
    assert response.status_code in (200, 201, 202, 204)


def test_api_track_accepts_interaction_payload_without_pii():
    payload = {
        "event": "product_search",
        "page": "/products",
        "referrer": "",
        "session_id": "iter161-session",
        "screen_width": 1920,
        "search_term": "indoor",
    }
    response = requests.post(f"{BASE_URL}/api/track", json=payload, timeout=TIMEOUT)
    assert response.status_code in (200, 201, 202, 204)


def test_products_api_contract_still_returns_94_items():
    response = requests.get(f"{BASE_URL}/api/products", timeout=TIMEOUT)
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    products = payload.get("products")
    assert isinstance(products, list)
    assert len(products) == 94

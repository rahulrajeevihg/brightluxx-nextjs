"""
Iteration 143 - Stage D catalogue and finder API verification
- Public products source count and structure checks
- Live search endpoint validation for catalogue search term
"""

import os
from pathlib import Path

import pytest
import requests


def _read_backend_url_from_frontend_env() -> str | None:
    env_path = Path("/app/frontend/.env")
    if not env_path.exists():
        return None
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip()
    return None


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or _read_backend_url_from_frontend_env()
if not BASE_URL:
    pytest.skip("REACT_APP_BACKEND_URL is not configured", allow_module_level=True)
BASE_URL = BASE_URL.rstrip("/")


def _products_from_payload(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("products") or payload.get("data") or []
    return []


def test_products_source_returns_exactly_94_products():
    """/api/products is the single source of truth and must return 94 products."""
    response = requests.get(f"{BASE_URL}/api/products", timeout=30)
    assert response.status_code == 200

    products = _products_from_payload(response.json())
    assert isinstance(products, list)
    assert len(products) == 94

    sample = products[0]
    assert isinstance(sample.get("slug"), str) and sample["slug"].strip()
    assert isinstance(sample.get("name"), str) and sample["name"].strip()
    assert isinstance(sample.get("category"), str) and sample["category"].strip()


def test_products_category_filter_returns_matching_records():
    """Category filter should scope returned products to selected taxonomy."""
    response = requests.get(f"{BASE_URL}/api/products", params={"category": "indoor"}, timeout=30)
    assert response.status_code == 200

    products = _products_from_payload(response.json())
    assert len(products) > 0
    assert all(product.get("category") == "indoor" for product in products)


def test_search_endpoint_video_wall_returns_relevant_results():
    """Live /api/search should return product matches for 'video wall'."""
    response = requests.get(f"{BASE_URL}/api/search", params={"q": "video wall"}, timeout=30)
    assert response.status_code == 200

    payload = response.json()
    products = payload.get("products") if isinstance(payload, dict) else []
    assert isinstance(products, list)
    assert len(products) > 0

    joined_text = " ".join(
        f"{item.get('name', '')} {item.get('description', '')} {item.get('application', '')}".lower()
        for item in products[:20]
    )
    assert "video" in joined_text or "wall" in joined_text
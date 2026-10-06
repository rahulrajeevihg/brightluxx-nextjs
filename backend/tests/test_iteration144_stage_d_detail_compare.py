"""
Iteration 144 - Stage D product detail and compare API verification
- Product catalogue baseline and product detail payload checks
- Live compare API validation using real product codes
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


def test_catalogue_returns_94_products_and_bl_cob125():
    """/api/products should return the full 94-product catalogue and include bl-cob125."""
    response = requests.get(f"{BASE_URL}/api/products", timeout=30)
    assert response.status_code == 200

    products = _products_from_payload(response.json())
    assert isinstance(products, list)
    assert len(products) == 94
    assert any(item.get("slug") == "bl-cob125" for item in products)


def test_product_detail_bl_cob125_has_core_fields():
    """/api/products/{slug} should provide real title/content/spec/faq data for detail route rendering."""
    response = requests.get(f"{BASE_URL}/api/products/bl-cob125", timeout=30)
    assert response.status_code == 200

    product = response.json()
    assert product.get("slug") == "bl-cob125"
    assert isinstance(product.get("name"), str) and product["name"].strip()
    assert isinstance(product.get("description"), str) and product["description"].strip()
    assert isinstance(product.get("product_code"), str) and product["product_code"].strip()

    key_specs = product.get("key_specs") or []
    faq = product.get("faq") or []
    assert isinstance(key_specs, list) and len(key_specs) > 0
    assert isinstance(faq, list) and len(faq) > 0


def test_compare_api_returns_selected_real_products_with_specs():
    """/api/products/compare should return side-by-side payload for two real products."""
    catalogue_response = requests.get(f"{BASE_URL}/api/products", timeout=30)
    assert catalogue_response.status_code == 200

    products = _products_from_payload(catalogue_response.json())
    selected_codes = [item.get("product_code") for item in products if item.get("product_code")][:2]
    assert len(selected_codes) == 2

    compare_response = requests.post(f"{BASE_URL}/api/products/compare", json=selected_codes, timeout=30)
    assert compare_response.status_code == 200

    payload = compare_response.json()
    returned = payload.get("products") if isinstance(payload, dict) else []
    assert isinstance(returned, list)
    assert len(returned) == 2

    returned_codes = [item.get("product_code") for item in returned]
    assert set(returned_codes) == set(selected_codes)
    assert all(isinstance(item.get("key_specs") or [], list) for item in returned)

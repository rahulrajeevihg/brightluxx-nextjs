"""Iteration 123 — Smart Cache Purge verification: does approving a review actually
purge the SSR meta cache so the Product AggregateRating updates without a manual purge?
"""
import json
import os
import uuid

import pytest
import requests
from dotenv import dotenv_values

_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _env.get("REACT_APP_BACKEND_URL")).rstrip("/")
ADMIN = {"email": "admin@brightluxx.com", "password": "brightluxx2025"}
PRODUCT = "gamewall-sim-180"


def product_schema():
    r = requests.get(f"{BASE_URL}/api/ssr/meta", params={"path": f"/products/{PRODUCT}"}, timeout=45)
    r.raise_for_status()
    for s in r.json().get("schemas") or []:
        obj = json.loads(s)
        if obj.get("@type") == "Product":
            return obj
    return {}


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/admin/login", json=ADMIN, timeout=45)
    assert r.status_code == 200, r.text[:300]
    tok = r.json().get("access_token") or r.json().get("token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


def test_review_approval_purges_ssr_cache(admin_session):
    # 1. Warm the cache
    requests.post(f"{BASE_URL}/api/ssr/meta/clear-cache", timeout=45)
    before = product_schema().get("aggregateRating", {}).get("reviewCount", 0)

    # 2. Submit + approve a new review (should trigger clear_ssr_cache internally)
    email = f"TEST_purge_{uuid.uuid4().hex[:8]}@example.com"
    body = {"name": "TEST_QA Purge", "email": email, "rating": 3,
            "comment": "Cache purge verification review comment for QA."}
    assert requests.post(f"{BASE_URL}/api/products/{PRODUCT}/reviews", json=body, timeout=45).status_code == 200
    adm = admin_session.get(f"{BASE_URL}/api/admin/reviews",
                            params={"product_slug": PRODUCT, "limit": 100}, timeout=45).json()
    rid = [r for r in adm["reviews"] if r["email"] == email.lower()][0]["id"]
    assert admin_session.put(f"{BASE_URL}/api/admin/reviews/{rid}",
                             json={"status": "approved"}, timeout=45).status_code == 200

    live = requests.get(f"{BASE_URL}/api/products/{PRODUCT}/reviews", timeout=45).json()["stats"]
    cached = product_schema().get("aggregateRating", {}).get("reviewCount", 0)

    # cleanup
    admin_session.delete(f"{BASE_URL}/api/admin/reviews/{rid}", timeout=45)
    requests.post(f"{BASE_URL}/api/ssr/meta/clear-cache", timeout=45)

    assert cached == live["total_reviews"], (
        f"STALE SSR CACHE after review approval: schema reviewCount={cached} "
        f"(was {before}) but live approved reviews={live['total_reviews']}. "
        "clear_ssr_cache() in reviews.py resolves to the async route handler "
        "(name shadowing in ssr_meta.py) and is never awaited.")
